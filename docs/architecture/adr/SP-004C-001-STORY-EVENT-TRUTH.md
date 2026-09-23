# ADR-SP-004C-001 — 已接受事件是 Story 真源

状态：**PROPOSED / PENDING_INDEPENDENT_REVIEW**。固定基线 `0028faedc36e00c52b9328e15a43fa81c31f9475`。本 ADR 只冻结未来 C1 合同，不实施 Runtime。总览见[SP-004C0 主文档](../SP-004C-STORY-RUNTIME.md)。

## 背景

当前 World 生命周期和角色最小 `Values` 已持久化；Memory 记录知识及受众，Lore 记录固定设定。它们都不能证明故事中发生了某件事。模型、宿主或角色卡中的一句叙述也没有接受权限。若把这些材料直接改成 StoryState，将无法区分提议、设定、记忆和已发生事件。

## 决策

每个完整 WorldScope 的有序、不可变 `AcceptedStoryEvent` 日志是唯一 Story 历史真源。`StoryEventCandidate` 是短暂提案，第一版不持久化。新 World 的 Story 投影为空；初始事实只能经显式 bootstrap 接受成为事件。EventId 使用现有 `IdKind.EVENT`。每个事件记录事件种类、payload version、Scope、连续序号、逻辑刻度、来源分类、受信接受操作者、审计时间及可选纠正目标；内容字段有界且按种类校验，不能是任意解释的 JSON。

第一版只接受受信 Owner 管理命令，或当前开放 Session 的显式受信 accept 命令。Session 需在事务内检查 Principal、Scope、ACTIVE、绑定、WriterEpoch、runtime_id 和 StoryRevision。模型输出、Lore 激活、Memory 命中、普通 Host 消息都只能启发候选，不能独自 accept；SourceType 不授予权限。`accepted` 是 Story 日志状态，不等于 `CanonStatus.ACCEPTED`；RealityStatus/CanonStatus 保留各自来源分类，Story 不能提升现实真实性。

已接受事件不 UPDATE、不 DELETE。修正采用新普通事件携带 `supersedes_event_id`，目标必须是同 Scope 较早事件；新 payload 以明确 SET/REMOVE/THREAD 状态变化前向改变**当前**投影。重放不会删除旧事件或改写它过去的作用。纯 `NARRATIVE_EVENT` 只进历史，不从正文抽取结构化变化；其后续修正仍需新叙事事件明确说明。更复杂的追溯重算与物理删除不在 C1。

接受幂等身份为 `(producer, source, slot)`，规范指纹覆盖 Scope、预期 StoryRevision、类型、payload、provenance、来源引用和纠正目标，不覆盖首次生成的随机 EventId。同键同指纹先返回原回执，同键异指纹拒绝，其他请求才进入 CAS。来源引用是 lineage，不自动跨系统读取或授权。

## 后果与验证

Story 不再随模型口吻或 Lore/Memory 增减而隐式变化；代价是上游必须提供明确接受操作。C1 必须测试模型/Lore/Memory 不自动确权、Owner/Session 两条受信路径、重试回执、并发冲突、跨 World/Timeline 禁止修正、旧事件不可变及新事件前向改变投影。事件文本即使含 Prompt 指令也始终是数据，不授予工具、Memory audience、Bridge grant 或 Host 权限。

## C1 实现状态

C1 候选通过显式 Owner/Session 接受写入不可变事件日志；同键幂等在 CAS 前重放，`supersedes_event_id` 只作前向修正，不删改旧事件。状态为 **IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**，原决策不变。
