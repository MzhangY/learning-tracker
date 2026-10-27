# 学习追踪器 Learning Tracker

每天自动收集电脑上的学习活动（浏览器搜索、浏览记录、文件变动），每晚由 WorkBuddy 生成总结报告，你审查后把有用的内容留档。

## 工作流程

```
每小时收集器(可选) ──> data/日期.json ──> 每晚21:30 WorkBuddy自动化 ──> reports/日期.html
                                                                        │
                                              你在报告里勾选有用条目，导出 keep-日期.json
                                                                        │
                                              放入 keep/ 后运行 archive.py ──> D:\学习留档\日期\
```

## 文件说明

| 文件/目录 | 作用 |
|-----------|------|
| `collector.py` | 收集器：读取 Edge/夸克浏览器历史 + 扫描当天新建/修改的文件 |
| `window_tracker.py` | 实时窗口监控：每 10 秒记录前台活动窗口（程序名+标题），空闲 5 分钟自动暂停，形成活动时间线 |
| `config.json` | 配置：浏览器路径、扫描目录、排除名单、留档目录 |
| `data/` | 每天的原始收集数据（JSON） |
| `archive.py` | 留档脚本：按保留清单把文件**复制**到留档文件夹（绝不删原件） |
| `keep/` | 放报告里导出的保留清单 |
| `reports/` | 每晚生成的 HTML 总结报告 |

## 每日使用

1. **晚上 21:30** WorkBuddy 自动生成日报并打开（自动化任务：学习日报-每晚总结）
2. 浏览报告，勾选觉得有用的条目，点"导出保留清单"，把下载的 `keep-日期.json` 放进 `keep/` 文件夹
3. 运行留档：

```bash
python C:\Users\Windows\WorkBuddy\learning-tracker\archive.py
```

留档的文件会出现在 `D:\学习留档\<日期>\`，网页链接汇总在同目录 `网页链接.md`。

## 让收集更实时（可选，推荐）

系统安全策略不允许 AI 直接注册系统定时任务，请你在**自己的 CMD/PowerShell** 里运行这条命令，让收集器每小时自动运行：

```cmd
schtasks /Create /F /SC HOURLY /TN "LearningTrackerCollector" /TR "\"C:\Users\Windows\.workbuddy\binaries\python\versions\3.13.12\python.exe\" \"C:\Users\Windows\WorkBuddy\learning-tracker\collector.py\""
```

即使不注册，每晚 21:30 的自动化也会先跑一遍收集器再出报告，只是数据截止到 21:30 前的当天记录没有中途快照完整（浏览器历史不受影响，始终是完整的）。

删除定时任务（如需）：`schtasks /Delete /TN "LearningTrackerCollector" /F`

## 窗口实时监控（window_tracker.py）

记录"当前在用哪个软件、哪个文件/网页"，是晚间报告做时间线判断的核心数据。

**开机自启动（推荐）**：在你的 CMD 里运行以下两条命令，把它注册为登录时启动的常驻任务：

```cmd
schtasks /Create /F /SC ONLOGON /TN "LearningTrackerWindow" /TR "\"C:\Users\Windows\.workbuddy\binaries\python\versions\3.13.12\pythonw.exe\" \"C:\Users\Windows\WorkBuddy\learning-tracker\window_tracker.py\""
```

（`pythonw.exe` 无窗口静默运行；临时手动启动则用 `python window_tracker.py`。）
删除：`schtasks /Delete /TN "LearningTrackerWindow" /F`

数据落在 `data/window-日期.json`，每条记录含程序名、窗口标题、起止时间和分钟数；空闲超过 5 分钟自动暂停，不会把"挂机"算成学习时间。

## 调整配置

编辑 `config.json`：
- `scan_dirs`：增减要监控的目录（默认桌面/文档/下载/D:\PycharmProjects）
- `exclude_dir_names`：不想收录的目录名（已排除微信缓存等噪音）
- `archive_dir`：留档位置（默认 `D:\学习留档`）

## 手动命令

```bash
# 手动跑一次收集
python C:\Users\Windows\WorkBuddy\learning-tracker\collector.py

# 手动留档
python C:\Users\Windows\WorkBuddy\learning-tracker\archive.py
```

## 快速上手（新机器部署）

环境要求：Windows 10/11 + Python 3.10+（无需安装任何第三方库，全部使用标准库）。

```bash
git clone https://github.com/MzhangY/learning-tracker.git
cd learning-tracker
```

**第一步：改配置** `config.json`（按自己机器修改）：

- `browsers`：改成你浏览器 History 文件的实际路径。常见位置：
  - Chrome：`C:\Users\<你>\AppData\Local\Google\Chrome\User Data\Default\History`
  - Edge：`C:\Users\<你>\AppData\Local\Microsoft\Edge\User Data\Default\History`
  - 其他 Chromium 内核浏览器（夸克/360/Brave 等）同理，找到其 User Data 下的 `History` 文件即可
- `scan_dirs`：改成你要监控的目录（桌面/文档/下载/代码目录等）
- `archive_dir`：留档输出位置

**第二步：测试运行**

```bash
python collector.py        # 收集一次，看 data/ 是否生成了今天的 json
python window_tracker.py   # 窗口监控（Ctrl+C 停止），几分钟后切几个窗口再看 data/window-*.json
```

**第三步：配置常驻**（任选或都用）：

- 窗口监控开机自启：把启动命令放入"启动"文件夹（Win+R 输入 `shell:startup`），或用任务计划程序（`taskschd.msc`）创建"登录时启动"任务，程序填 `pythonw.exe`（静默运行）
- 收集器每小时运行：任务计划程序创建每小时任务运行 `collector.py`

**第四步：生成日报**（两种方式任选）：

- **有 AI 编程助手（WorkBuddy/Claude Code 等）**：创建一个定时自动化任务，让 AI 在每天固定时间读取 `data/` 下两个 json、归纳主题并生成 HTML 报告（报告格式参考本文件"每日使用"一节）
- **纯手动**：没有 AI 也可以，数据本身就是按时间线整理好的 JSON/清单，每晚人工浏览 `data\` 文件即可

## 隐私与安全说明（给所有使用者）

- 所有数据只存在本机，不上传任何服务器；浏览器历史通过复制临时副本读取，不影响浏览器运行
- 留档操作只复制、从不删除或移动原文件
- 若要把本项目推到自己的公开仓库，注意 `config.json` 含本机用户名路径、`data\` 含你的浏览记录，**务必先加入 .gitignore 再提交**（本仓库的 .gitignore 已默认排除）

## 隐私说明

- 所有数据只存在本机，浏览器历史通过复制临时副本读取，不影响浏览器运行
- 留档操作只复制、从不删除或移动原文件
- 浏览器记录涵盖 Edge 和夸克，其他浏览器可在 `config.json` 的 `browsers` 里添加其 History 文件路径
