# ADR SP-004F-005 — Prompt 消费与目标 Memory/Story 写入边界

状态：**F0 架构候选 / 待独立审核**。关联[主文档](../SP-004F-CONTROLLED-WORLD-BRIDGE.md)与[Prompt 架构](../SP-004K-PROMPT-RUNTIME.md)。

## 决策

Prompt-only 路径是 `source Runtime → BridgeProjection → PromptBridgeProjection → K BRIDGE_CONTEXT`，不生成目标持久数据。当前 [`PromptSectionKind.BRIDGE_CONTEXT`](../../../runtime/life_engine/prompt.py) 只是 Enum 预留，`PromptSection` 明确拒绝；F0 不修改 K。未来 F1/K 扩展只能接受受信投影适配器，核对 grant current/revision/expiry、来源 version、target Scope/viewer/Session/WriterEpoch/runtime/generation、audience 与 `PROMPT_CONTEXT`。K 在 assemble 和 Host 发送前 revalidate 时均须重验；F 不直接修改 PromptSnapshot。Bridge 内容只能为 `UNTRUSTED_CONTENT_DATA`，不能成为 Runtime Control、工具许可或 Story/Memory 接受权。

Bridge 使用独立 `bridge_bytes` Prompt 预算，完整 item `PREFIX` 裁剪；建议固定次序为 Story → Lore → Memory → Bridge → Conversation，本地 World Memory 先于外来授权上下文。每项保留 grant、来源 Scope/子系统/对象身份标签。PromptSnapshot 中 grant、投影和来源版本的 fingerprint/token 必须使撤销、改版、删源及目标会话变化导致旧快照 stale；单凭提示词要求模型忽略不再授权内容无效。

持久目标 Memory 必须先做精确 `USE` 预览、Owner 确认，再调用 target MemoryRuntime 的 candidate/create/accept 门禁；不复制源 SQL row。自动跨域内容默认候选，不因源 Memory ACCEPTED 而自动成为目标 canon。当前 [`MemoryRuntime`](../../../runtime/life_engine/memory_runtime.py) 对 `SourceType.BRIDGE` 返回 `INVALID_SOURCE`，现有 lineage 也限同 Scope；F1 若启用此目的，必须另审受信来源、跨 Scope lineage、源删除后的目标依赖和目标 audience，不能绕验证器或直接 `INSERT world_memories`。若这些安全条件未解决，先只提供 prompt-only 用途。

持久目标 Story 必须经 `BridgeProjection → StoryEventProposal → target trusted acceptance`；不直接写 StoryState 或 `story_events`。当前 Story source reference 不携完整 Bridge Scope/grant lineage；F1 若启用须设计类型化引用。`RealityStatus.FICTIONAL` 到 Soul 仍虚构，源 CanonStatus 或 accepted Story 不自动确权目标。H 负责未来用户意图、预览 UI、显式确认、HostCapabilities 与模型调用；F/K 都不接 Hermes/OpenClaw 或宿主聊天库。

Bridge 持久仓储只管 grant/revision、audit、idempotency 和撤销控制；BridgeProjection 自身不成为数据表。审计保留操作身份、Scope、grant revision、projection fingerprint、目标结果 ID 和时间，不复制正文或聊天全文。Prompt-only “实际已消费”只可由未来 H 在发送时报告，不能让只读 K 组装/重验写审计。

## 理由与后果

三条目标消费路径有不同真源和权限：K 只读派生视图，Memory 决定谁记得，Story 决定目标世界发生了什么。共享 BridgeProjection 不得把这些边界压成一次数据库复制。F0 不启用 Prompt Section、目标写入或 Host 适配。

## F1 实现状态

**IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**。F1 仅经 `PromptBridgeProjection.from_bridge_projection()` 受信适配器启用 `BRIDGE_CONTEXT`；按本地 Memory → Bridge → Conversation 排序、独立预算及完整项裁剪，所有共享正文保持 DATA。旧快照在 Grant 撤销、来源或目标围栏变化时重验失败。未增加 `persist_to_memory()`、`persist_to_story()`、模型 API 或 Host 适配；Memory 的 `SourceType.BRIDGE` 拒绝和 Story source refs 原样保持。
