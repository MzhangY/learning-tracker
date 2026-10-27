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

## 隐私说明

- 所有数据只存在本机，浏览器历史通过复制临时副本读取，不影响浏览器运行
- 留档操作只复制、从不删除或移动原文件
- 浏览器记录涵盖 Edge 和夸克，其他浏览器可在 `config.json` 的 `browsers` 里添加其 History 文件路径
