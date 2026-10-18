# 角色使用主 Agent 能力（试用）

> **状态范围（2026-10-18）**：本页试用代码已通过 [#58](https://github.com/y19870785/life-engine/pull/58) 进入 main；#60 的验证辅助工具与诊断先并入 #59，再随其进入主线。当前能力与证据见[项目现状](PROJECT-STATUS.md)、[统一基线](planning/W0-W1-CHARACTER-BASELINE.md)和[本周复盘](reports/WEEKLY-REVIEW-2026-10-18.md)，文档用途见[索引](DOCUMENTATION-INDEX.md)。W1 完整 T1 仍 `T1_FAILED / HOST_DEPENDENCY_GAP`，T2 `BLOCKED`；代码合并不是 Host/媒体/模型体验验收。[后续计划](planning/NEXT-DEVELOPMENT-PLAN-2026-10.md)为 `PROPOSED / NOT_EXECUTION_AUTHORIZATION`。以下示例不单独授予 Host 操作权限，继续使用隔离 Profile；历史 W1 无模型测试的工具为空、provider/渠道发送为0，不把该次限制当作产品能力配置。

角色卡决定故事身份、默认玩家身份、文风与世界。工具和技能由可信本地管理配置提供，卡片正文不能自行授予权限。角色可以自然描写走到电脑边或拿起手机，实际操作结果必须来自工具，不能把意图叙述当成执行成功。

本版支持在独立角色 Profile 中配置宿主工具权限，继承主 Agent 的已启用 toolsets 与技能目录。ComfyUI 可以通过已有技能、terminal 与 skill_view 使用，不代表内置了新的媒体工具或已经验证出图。工具的凭据、环境、服务可用性仍由 Host 管理。

## 配置

先由管理者核对主 Profile 的实际工具集合与技能来源，备份目标 Profile 配置。不要复制主 Agent 的 SOUL、历史、后台任务或凭据。共享技能可使用当前 Host 支持的 skills.external_dirs；目标 Profile 的同名本地技能可能优先。MCP 外部服务需要单独验证连接和权限，不能从工具名称推断已经接通。

建立一个私有 JSON 数组，列出允许的实际工具名称。用安装后的 card.json SHA256 配置：

```sh
python tools/hermes_capabilities.py \
  --profile-home /home/user/.hermes/profiles/card-trial \
  --tools-file /home/user/private/host-tools.json \
  --expected-card-sha <安装卡SHA256>
```

命令写入 `.life-engine-character-capabilities.json`，保存此前配置，不改 card.json 或 V2 World 数据。插件将该清单与本轮 Host 实际提供的工具 schema 取交集，pre_tool_call 再核验授权未漂移及本轮确实提供过该工具。没有配置时仍按原卡 allowed_tools 限制；配置损坏或绑定不符时拒绝工具并报告配置暂不可用。

开启宿主 toolsets 后退出旧聊天，再打开新 CLI。仅加允许清单不会让 Host 提供工具；仅启用 Host 工具也不会绕过角色插件的限制。角色技能应通过技能列表或 skill_view 获取，不将 127 个技能全文灌入角色提示。

## 停用与限制

将 sidecar 的 enabled 设为 false 后新开聊天，回到原卡的工具限制；停用继承配置可恢复备份的 Profile 配置。插件更新仍使用正式签名 receipt 的 restore/apply，保留原卡摘要及 V2 sidecar/root；不能覆盖后假装旧 receipt 没有漂移。

本版先解决能力可见与可用。**V2 跨会话连续性仍保守跳过包含工具中间消息的轮次**；同会话工具历史由 Hermes 保留。尚未验收跨会话媒体引用、统一工具结果记录、场景自动提取、固定角色脸/声线或 Telegram 媒体投递。不要把继承技能称为媒体闭环已完成，也不要宣称任何图片已生成或发送。

[统一故事入口](HERMES-CHARACTER-ONBOARDING.md)已提供原卡故事介绍、默认 user 身份提示与开场选择。角色身份仍由原卡正文承担；选择其他开场的新故事使用新的独立 Profile/World，不能混入已有 World。
