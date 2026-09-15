# v0.4 双层身份验收记录

日期：2026-09-15。实现分支：`feat/metacognitive-roleplay`。开发预览，未部署到在线 Gateway。

## 自动化测试

命令：`python -m unittest discover -s tests -v`。

| 环境 | 结果 |
| --- | --- |
| Windows / Python 3.12 / Node 22.14 | 69 项，68 通过、1 跳过；跳过 Unix 专用 symlink 测试 |
| WSL Ubuntu / Python 3.11.15 / Node | 69 项全部通过，无跳过 |

测试覆盖 JSON V1/V2/V3 与 PNG tEXt 解析、头像保留、损坏输入拒绝、独立世界书、递归/循环/预算/大小写/禁用/位置、进入切换退出、同角色重入记忆、跨角色隔离、外键与 CHECK 约束、并发进入、迟到响应和记忆拒绝、重复事件去重、关闭记忆、Soul 日志隔离、角色模式生活脉冲静默，以及原有生活/主动联系/图片流程。

迁移测试验证 schema 2 源库不变、副本迁移、旧备份恢复、迁移失败入口不变、缺失数据库拒绝重建。Windows 清理错误通过关闭真实 SQLite 连接修复，没有跳过业务断言。

Hermes 桥接契约测试包含原生命令、pre/post Hook 与跨 Profile 拒绝；OpenClaw Node 契约测试包含导入、进入、世界书注入、退出、错误 Agent 拒绝。后者不是实际 OpenClaw Gateway 验收。

## 真实 Hermes 与模型

宿主为 WSL Hermes v0.21.2（2026.9.11，源码 476a45f4），选择用户指定的默认 Profile，使用该 Profile 原有 SOUL 和配置的 deepseek-v4-flash。探针运行真实 PluginManager、原生命令注册、生命周期 Hook 和 AIAgent，不用模拟模型答案。

运行方式见 [角色扮演指南](ROLEPLAY.md)。`tests/manual_hermes_probe.py --llm` 创建临时引擎与临时 Hermes 会话库；只让本次进程加载桥接插件。SOUL/config 的前后摘要一致，不保存或发布它们的原文；旧 Life Engine 数据、定时任务和在线 Gateway 未修改。

实测流程：导入星澜 → 原生进入 → 关键词星港激活月塔 → 模型区分原身份与角色 → 角色口吻谈月塔 → 模型调用真实记忆工具 → SQLite 查询确认 `scope=persona, card_id=1, session_id=2` → 中文“退出角色” → 最终 `mode=soul`，后续回答恢复原身份。

退出后模型明确称星澜是虚构表演，并可以提及留下的经历。跨会话同角色记忆加载由自动化测试验证，本次没有额外以新模型会话测长期回忆。

![真实 Hermes 隔离验收截图](demo/roleplay-hermes.png)

截图是 [探针原始结果 JSON](demo/roleplay-hermes.json) 的展示页截图；[HTML](demo/roleplay-hermes.html) 中节选模型原文和真实数据库结果，没有虚构聊天 UI 或改写回答。可执行 `python docs/demo/render_probe.py docs/demo/roleplay-hermes.json` 重建页面，再用浏览器截图。

## 联调发现与修复

早期探针的临时 SessionDB 导致 Hermes 选择了错误的身份目录；已改为显式绑定默认 Profile 的 ContextVar，并断言原 SOUL 实际加载。角色提示原先没有明确工具名，模型曾找不到 remember；已补齐实际工具名、action 和参数示例，并让 CLI 参数错误返回结构化 JSON。

模型曾把“虚构情节不是现实事实”误说成“不进入长期记忆”。已明确提示：persona 保存剧情，Soul 保存持久的虚构体验元记忆。最终对话保留在结果文件中，身份与记忆表达仍需持续评价。

最终模型运行中宿主曾报告一次输出长度截断警告；后续工具调用和最终回答成功完成，数据库与结束状态断言通过。该警告没有作为成功对话内容隐藏或改写。模型也会添加卡片未规定的虚构细节，因此这里只确认世界书信息被使用，不声称逐字忠实复述。

## 尚未验收

在线 Gateway 重新加载、真实私聊渠道命令、OpenClaw 实机、长历史下多轮稳定性、多人会话和 GPU/回执闭环尚未验证。程序退出是确定性状态转换；宿主历史及模型自然语言遵从不可能由这个插件保证 100%。角色数据本地存储，但使用云模型聊天时会随提示发送给已配置的服务。
