# SP-004 — PR #3 Gap Analysis

状态：PROPOSED / PENDING_INDEPENDENT_REVIEW。日期：2026-09-16。

Implementation Authorization: NOT AUTHORIZED。Merge Authorization: NOT AUTHORIZED。

比较对象固定为 main `81ee02b561ac90641c3632f750ffd86a48310cf7` 与 [Draft PR #3](https://github.com/y19870785/life-engine/pull/3) head `ab227f2179eeaa7ded662d612508a98ad5cdf04a`。PR #3 的新能力尚未进入 main。目标来自本次 [RFC](SP-004-PERSISTENT-WORLD-RUNTIME.md)，不是已实现的要求；本分析不批准或否决 PR #3 的合并。

## 1. Current Capability → Target Architecture

下表中所有动作均为未来建议。KEEP 保留能力；ADAPT 调整边界；MIGRATE 转换数据；DEPRECATE 停止新增依赖而保留兼容；REPLACE 用新的职责模型替代旧假设，不代表本轮删除代码。

| Area / Current Capability | Target Architecture | Gap | Risk | Migration Requirement | Recommended Action |
| --- | --- | --- | --- | --- | --- |
| Character Card：V1/V2/V3 JSON、PNG tEXt，原文/parsed JSON/头像入库，名称唯一 | 版本化 CharacterDefinition + 世界内 CharacterInstance | 卡片兼作运行身份和记忆归属，没有定义版本与实例 | 同一角色多个故事无法隔离；改定义可能改变历史解释 | 保留原文和头像，旧 card ID 映射到定义版本与默认 legacy 实例 | KEEP 解析与本地存储；ADAPT 至 IR；MIGRATE 归属；DEPRECATE 卡名作为身份键 |
| World Book：内嵌/独立条目绑定 card_id，关键词递归、优先级、预算、depth 投放 | Lore IR 作为可复用设定；WorldState 为另一个实体 | 世界书是静态知识，既没有世界实例也没有真实状态变化 | 把百科条目误当作已发生事件；同卡跨世界共用知识 | 源条目/顺序/来源保留，先关联定义，世界选择具体版本 | KEEP 有界扫描；ADAPT 格式字段和受众；REPLACE “World Book 就是 World” 假设 |
| Roleplay Session：单活动索引，enter/switch/exit；结束保留摘要 | World 独立存活，SessionBinding 只是一次参与；lease/epoch | 没有 suspend/resume/archive 生命周期；活动范围是整实例 | 同 Profile 不同聊天串角色；结束 session 不足以恢复世界 | 旧 session → 历史绑定；同卡默认 legacy World，歧义显式标记 | KEEP 事务/幂等退出；MIGRATE session；REPLACE 全局活动角色作为运行根 |
| Roleplay Memory：persona/card/session FK，remember 与退出生成摘要；最近 8 条检索 | world/timeline/audience 的 WorldMemory 与 StoryState | 无 world_id、timeline、类型化 canon；摘要非故事真源 | 同卡多世界串记忆；旧细节退出检索窗口后缺乏结构化进度 | 原文归档不丢；摘要保留为 legacy memory，不自动转 canon | KEEP FK 和来源；MIGRATE 命名空间；ADAPT 检索；DEPRECATE 最近摘要作为故事状态 |
| Persona / Soul Isolation：persona 查询隔离、RP 不注入生活日志、aside 读取 Soul；自动写 roleplay_meta | 双向显式 World Bridge，类型化真实性，宿主 context lane | 只有文本虚构标签，无可审计许可；aside 无字段范围/目的授权 | 模型将剧情当真实事实；私密 Soul 数据经宿主历史留在 RP | 旧 meta 标 legacy_unreviewed；未来默认 deny，不伪造历史 grant | KEEP 默认分区；ADAPT 数据类型；REPLACE 自动全文摘要提升与无范围 aside |
| Database Schema：v3 的卡片、条目、session、message、memory；card 删除级联 | World/Timeline 为持久边界，定义共享且版本固定 | 世界/故事对象缺失；卡片生命周期拥有历史 | 删除模板会删除经历；难以审计历史关系和事件 | 副本分阶段迁移、映射与兼容投影；停止旧 writer 后切换 | KEEP SQLite/约束/备份；MIGRATE 数据；DEPRECATE 卡删除即删故事 |
| Hermes Adapter：原生 /rp、Profile scope、pre/post Hook、turn 去重及 stale 检查 | 通用认证 envelope + capability contract + per-session binding | Profile 不等于参与者；宿主历史/记忆可能超出插件控制 | 跨聊天污染；Hook 失败时只有提示级降级 | 宿主绑定映射到稳定 Soul，历史外部 ID 作 provenance | KEEP 插件边界；ADAPT scope/能力协商；不重写宿主 |
| OpenClaw Adapter：agentId/workspace、可信来源、原生命令与前置上下文；Node 契约测试 | 与 Hermes 共用 Runtime 行为契约，宿主只负责转换与投递 | Gateway 命令名全局；助手消息记录与 Hermes 不对称；尚未实机证明隔离 | 多实例命令冲突、不同宿主记忆完整性不同 | 保留绑定信息；引入 host_event_id 与消息能力声明 | KEEP 鉴权/作用域检查；ADAPT 命令路由和事件归一；实机验收后再扩大声明 |
| Import Pipeline：read_local/parse_card/normalize_book 直接写 card 与 entries | Importer → versioned IR → 用户选择定义/世界实例 | 导入、定义和世界创建职责未分；解析结果字段仍接近外部格式 | 被外部格式扩展锁定；隐含改世界状态 | 原包哈希、映射版本、诊断和损失清单；不执行扩展 | KEEP 边界检查；ADAPT 为 IR 提案；DEPRECATE 导入即运行的未来设计 |
| Prompt Construction：SOUL 规则 + card/lore/persona excerpts，约 23 KB 内部预算 | 从已授权 World/Story/Memory 快照生成表现投影 | Prompt 是唯一组合出的“世界视图”，无 Runtime canon/revision | 对话补写被误当世界更新；长历史下身份混淆 | 保留口吻规则与预算；引用 world/timeline/revision，状态迁移先于渲染切换 | KEEP 元身份与有界上下文；REPLACE Prompt 作为运行核心的路线 |
| Life State / Scheduler：日计划、静默、领取/prepare/ack；RP 时静默 | Soul World 的生活与现实投递策略；虚构世界单独时钟和授权推进 | config.world 是日常模板，不是 World；调度仍依赖宿主 | 模拟日程升级成现实事实，剧情动作变为现实通知 | days/contacts 来源保留，首次映射 Soul World；未来时钟拆分 | KEEP 原联系账本；ADAPT 时钟/投递边界；不新增后台任务 |

## 2. Evidence Index

以下链接固定到被审查的 PR head；文件名后的符号是定位线索，避免活动分支变化影响结论。

| 证据 | 支持的发现 |
| --- | --- |
| [rp_cards.py](https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_cards.py) `parse_card/read_local` | PNG CRC/大小检查；chara/ccv3；原包与头像；字段规范化，不是完整 V3 实现承诺 |
| [rp_lore.py](https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_lore.py) `normalize_book/activate_lore_entries` | 保守 UTF-8 字节预算、字面关键词、递归与顺序；不是精确 tokenizer |
| [rp_schema.py](https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_schema.py) `TABLES` | 单 active 索引、card/session 复合 FK、删除级联；无 world/timeline 实体 |
| [rp_sessions.py](https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_sessions.py) `remember/finish/record_message` | 自动 meta、最后 3 条摘要/摘录、最多 64 条会话消息、可选 expected_session |
| [rp_prompt.py](https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_prompt.py) `build_prompt` | 同卡最近 8 条记忆、aside 取 Soul 最近记忆、深度插入插件摘录窗口 |
| [rp_commands.py](https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_commands.py) `dispatch` | 角色命令、delete 卡片、aside 返回上下文而非独立模型请求 |
| [durable.py](https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/durable.py) `upgrade/migrate_state/context_text/instance_id` | 副本迁移、缺库保护、宿主相关表现层和路径绑定、中文退出控制 |
| [bridges.py](https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/bridges.py) `HERMES/OPENCLAW` | 原生 API 在 adapter，宿主 scope 与消息记录差异 |
| [test_roleplay.py](https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/tests/test_roleplay.py) | 卡片、触发、状态、隔离、晚到写入、迁移；不能证明未实现的 World Runtime |
| [PR #3 validation](https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/docs/ROLEPLAY-VALIDATION.md) | 历史真实 Hermes 隔离探针说明；本轮未重跑真实模型，不当作在线 Gateway 证据 |

## 3. Priority and Compatibility

先处理边界，再添加叙事功能：world/timeline 标识、明确所有权、writer epoch、默认拒绝桥接是未来进入 World Runtime 的前置门槛。Character IR 与 WorldMemory 必须在多世界写入开启前可用。高级故事线、后台模拟、Timeline Branching 可以推后。

PR #3 可以保留为受控角色扮演预览候选，是否合并由独立审核决定。建议避免继续增加仅以 card_id 为根的新业务状态，避免扩大自动 meta 或 aside 读取范围；不要求本轮改动 PR #3。未来兼容层保留 `/rp` 入口和旧数据读能力，在多世界歧义时要求选 world，不默选可能泄密的世界。

最大风险不是“没有更多角色字段”，而是把当前的卡片归属和自动摘要复制固化为世界持久性及授权模型。对它们的替换应在映射、回滚、原有功能回归和宿主契约具备之后分阶段进行。
