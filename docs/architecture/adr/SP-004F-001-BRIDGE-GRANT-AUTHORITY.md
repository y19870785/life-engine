# ADR SP-004F-001 — Bridge Grant 授权与默认拒绝

状态：**F0 架构候选 / 待独立审核**。关联[主文档](../SP-004F-CONTROLLED-WORLD-BRIDGE.md)。本 ADR 不修改当前纯 [`evaluate_bridge()`](../../../runtime/life_engine/domain_policy.py)。

## 决策

没有当前有效 `BridgeGrant` 即 `DENY`。同 Owner、同 Soul、同 CharacterDefinition 或同 Principal 只可能满足资格前提，均不产生共享权。现有 `BridgeRequest` 是期望操作、`BridgePolicy` 是最小 eligibility policy、`evaluate_bridge()` 是纯判断；三者不是受信 grant store。F1 另建持久 `BridgeGrant`，可将其有限政策面投影给 eligibility kernel，不删除当前纯函数，也不把新持久状态塞进 `domain_policy.py`。

Grant 使用既有 `DomainId(IdKind.GRANT)` 与单调独立 `BridgeGrantRevision`：稳定 grant_id、精确 Owner Principal、完整 source/target `WorldScope`、单个 DataClass、最小字段集合、单个 Purpose、精确 target audience、aware UTC expires_at、状态及创建审计。首次 revision 至少 1；修改、缩小、扩大、续期、撤销都推进 revision，旧投影立即 stale。持久状态 `ACTIVE/REVOKED`；`EXPIRED` 由可信当前时间导出而非额外自动状态写入。Bridge revision 不推进 World、Memory、Story 或 Lore 的修订。

首版架构 DataClass 为 `MEMORY` 与 `STORY_PROJECTION`；`EXPLICIT_CONTEXT` 预留但不启用，Lore/Definition 不桥。`BridgeFieldRegistry` 限定每类字段：Memory 候选为 content/kind/subjects/reality_status/canon_status/source_reference；Story 仅当前角色 state 与 viewer relationships。`world_facts`、`open_threads`、event log 不在首版 allowlist。请求字段必须是非空、无通配的 grant/registry 交集；`*`、all/everything、未知字段拒绝。Purpose 为 `PROMPT_CONTEXT`、`PERSIST_TARGET_MEMORY`、`PERSIST_TARGET_STORY_CANDIDATE`，一 grant 一 Purpose，不可隐式升级用途。

Grant audience 只表达**目标** viewer，首版为精确 `SOUL` 或 `CHARACTER_INSTANCE`，必须属于 target Scope；不使用 `WORLD`/Owner/任意角色通配。源 Memory audience 仍须独立授权与记录。`OwnerBridgeContext` 只能由受信上游提供，用于 grant/preview/revoke/持久确认；`SessionBridgeContext` 为当前目标 OPEN Session、epoch/runtime/generation/viewer 的消费围栏。grant_id、Principal 数据结构、自然语言或模型输出都不是身份认证/授权凭据。只有受信 Owner 操作可建立、扩权、续期和撤销授权；角色与模型不能 grant。

F1 首版建议方向仅 Soul↔Roleplay；Roleplay↔Roleplay 有架构扩展位但默认拒绝。同 World Bridge 拒绝，两个 Scope 的 timeline_id 必须逐项匹配实际对象。扩大字段、audience、purpose 或 expiry 是新授权动作，需要 GrantPreview 和 Owner 确认；缩小也推进 revision，防止旧结果继续使用。过期和撤销始终硬拒绝。

## 理由与后果

boolean allow_bridge 或 Owner 身份无法表达“哪个来源的哪些字段，给哪个角色，为何用途，到何时”。独立 grant 版本使预览、投影和 Prompt 能统一检测授权变化，同时保留 World 默认隔离。F0 不创建 grant、迁移 Schema 或改变现有代码；F1 须分别实现受信持久层、CAS 与 fail-closed 恢复。
