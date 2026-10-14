# Hermes 角色连续性 V2（试用）

> **状态范围（2026-10-14）**：本文描述 #56—#59 堆叠 Draft 的试用能力；本轮固定实现 Base 为 #59 `1d1ec6b7681684cbc44458e94344c261c5a2011b`，不是已合并主线承诺。当前能力、历史证据和 W0/W1 验收状态见 [统一基线](planning/W0-W1-CHARACTER-BASELINE.md)。以下安装示例不单独授予 Host 操作权限；本轮仅新隔离 Profile、工具集合为空、REAL_SEND = NO。

本版在原生角色卡 V1 上增加后台连续性，不改写作者正文与世界书。适用于独立命名 Profile 的普通文本 CLI / Chat Completions；暂未接通 Telegram、Gateway、子 Agent、工具轮次、压缩后轮次或多模态消息。没有启用 V2 的 Profile 仍按 V1 运行。

## 能体验什么

- 同一 Profile、同一安装卡绑定一个独立 ROLEPLAY World 和 CharacterInstance。新 Hermes 会话建立新的 Core SessionBinding，继续原世界。
- 正常结束且已经保存的用户原话进入 Memory。它只证明用户说过这些话，内容标记为 USER_CLAIMED，不证明现实事实。
- 模型最终回复进入 Story，来源为 MODEL，内容为 FICTIONAL / CANDIDATE。可以自然续写角色日常；候选剧情不能自动确认玩家过去的承诺。
- 新会话读取最近至多 12 个完整记录，按时间排列。提示要求用户最新明确纠正优先。有历史时略过卡片开场，避免重新启动同一段故事。

这是原话与候选叙事的连续性试用。尚未实现语义事实抽取、纠正后的结构化撤销、长时记忆筛选、离线日常推进、关系自动演化或完整酒馆扩展。候选片段可能包含模型编造，仍须依靠来源区分与模型遵循提示；不能据此宣布角色体验完全合格。作者设定继续由原卡提示承载，未拆成完整 Core Lore。

## 写入条件与恢复

pre_llm_call 保留当前用户消息对象、原文和数据库水位；Host 保存后赋予该对象 message_uid。post_llm_call 只收集最终回复线索，on_session_end 才请求后台写入。

后台独立检查：轮次 completed=true、failed=false、interrupted=false，退出原因为正常文本 stop/end_turn；当前 session 中两个 UID 各对应唯一活动、未压缩、无工具调用的数据库行；原文摘要相同，用户行在回复行之前，回复行晚于轮前水位。缺 UID、失败、取消、截断、错内容、重复 UID 或无保存证据时跳过。该证明只说明本地保存，**不说明消息送达或 ACK**。

绑定检查先于读取 Host 行，当前 World 会话授权检查先于幂等重放和写入。journal 在独立文件内记录进度，使用已有 Core 幂等 API 恢复 Memory/Story 的部分写入；不修改 life.db 的 schema。仅完整 COMMITTED 记录进入上下文。恢复失败时上下文暂不可用，不静默丢弃待恢复记录。三个存储操作并非单个跨库事务。

每轮重新校验启用时固定的 Host 生命周期文件实际 SHA256，包括本地已有修改。Host 升级后不自动继续记录，应重新验证语义并由管理端处理配置。不能用版本标签代替实文件核验。

## 安装与启用

先按 [V1 指南](HERMES-CHARACTER-CARD-IMPORT.md) 安装本版原生插件。目标 Profile 不应同时启用旧版记忆/世界书桥接插件。先退出目标 Profile 的旧聊天，再操作。不要修改主 Profile 或复用旧版数据根目录。

以下命令在本版仓库根目录执行，路径为示例。Python 必须是可执行本版运行时的解释器。card.json 是插件安装后的原生计划，不能用原始 PNG 代替。

```sh
python tools/hermes_continuity.py init \
  --root /home/user/life-engine-card-world \
  --profile-home /home/user/.hermes/profiles/card-trial \
  --card /home/user/.hermes/profiles/card-trial/plugins/life-engine-character-card/card.json

python tools/hermes_continuity.py enable \
  --root /home/user/life-engine-card-world \
  --profile-home /home/user/.hermes/profiles/card-trial \
  --card /home/user/.hermes/profiles/card-trial/plugins/life-engine-character-card/card.json \
  --host-root /home/user/.hermes/hermes-agent
```

init 创建全新独立数据根并冻结运行时代码。已有匹配 continuity.json 时可查询状态；已有未完成初始化的目录会拒绝覆盖，应保留现场另选新目录。启用只写目标 Profile 的 `.life-engine-continuity.json`，并备份上次配置。该文件和数据根由可信本地管理者维护，不是模型工具。插件通过固定参数的独立 Python 子进程读写 Core，模型无需也不会获得文件/管理工具权限。

新开 CLI 会话：先告诉角色一件可核对的小事，并让她描述符合角色的当下活动；结束后另开新会话问后续。可以询问是否记得原话、是否延续同一个场景，并明确纠正一次模型编造的玩家经历。不要只靠同会话聊天判断跨会话记忆通过。

## 查看与停用

```sh
python tools/hermes_continuity.py status \
  --root /home/user/life-engine-card-world \
  --profile-home /home/user/.hermes/profiles/card-trial \
  --card /home/user/.hermes/profiles/card-trial/plugins/life-engine-character-card/card.json

python tools/hermes_continuity.py disable \
  --root /home/user/life-engine-card-world \
  --profile-home /home/user/.hermes/profiles/card-trial \
  --card /home/user/.hermes/profiles/card-trial/plugins/life-engine-character-card/card.json
```

停用后新开聊天即可回到 V1；不删除卡片、世界或记忆。完整移除插件仍使用 V1 签名 receipt 的回退命令；先停用 V2，并保留独立数据根。若已有旧版 native receipt，升级前按原 receipt 回退，再从本版重新 apply，不覆盖同名插件。

检查 `.life-engine-continuity-last-turn.json` 的 COMMITTED / WRITE_SKIPPED / CONTEXT_UNAVAILABLE，以及原有 `.life-engine-card-last-request.json` 的世界 ID、记录数与开场模式。trace 只存元数据；完整原话与剧情保存在私有数据根。命令行错误不构成成功体验或投递证明。

单条用户文本和回复各限 12000 UTF-8 字节，上下文记录总预算 48000 字节，按完整条目保留。超限本轮不记录。没有完整记录时不虚构已有记忆；停用、写回失败或 Host 文件变化均应在体验台账中明确记录。相关数据、源卡与日志不要提交公开 Git。
