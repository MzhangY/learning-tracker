# 学习活动日报 · 执行记录

## 2026-10-27 15:40
- 运行 collector.py：搜索 10 / 浏览 139 次 / 文件 211，输出 data/2026-10-27.json
- 生成报告 reports/2026-10-27.html（浅色主题，含概览 + 三组明细 + 导出保留清单按钮）
- 归类结果：教资认定 11 项、政务登录与实名 22 项、AI 技术学习（飞书/Claude Code/GitHub）14 项、搜索引擎入口 6 项、普通话报名 1、本地 Neo4j 1、其他 1；文件按目录分 17 组，文档/代码 196 个，其余 15 个折叠
- 工具沉淀：archive_tmp/gen_report.py <日期> 可一键复现报告（OVERVIEW/THEME_TAGS/THEME_RULES 常量按天更新，THEME_RULES 按 host+title 顺序匹配）
- 注意：CSS 里含 % 号，模板首段不能用 % 格式化，已改为 @DATE@ 占位替换
