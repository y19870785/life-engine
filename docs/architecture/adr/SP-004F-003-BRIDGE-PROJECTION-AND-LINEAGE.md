# ADR SP-004F-003 — 瞬时 BridgeProjection 与来源链

状态：**F0 架构候选 / 待独立审核**。关联[主文档](../SP-004F-CONTROLLED-WORLD-BRIDGE.md)。

## 决策

`BridgeProjection` 是由当前受信 grant、来源 Runtime 授权结果、明确请求及目标消费围栏派生的**瞬时有界数据**。它不是 MemoryRecord、StoryEvent、StoryState、数据库同步或 Prompt 权限。它至少携 grant_id/revision、双完整 Scope、DataClass、Purpose、精确 target audience/Session、字段、完整有序 items、source versions、`BridgeLineage`、源 reality/canon、过期/有效性、规范 fingerprint 和实例 HMAC token；token 防篡改但不作登录凭据。一个投影只服务一个目标 viewer，不提供通用跨角色 blob。当前墙钟与随机数不参与规范 fingerprint；相同 grant/source snapshot/request/budget 得到相同项、顺序和 fingerprint。时间用于当前 expiry 围栏，不由投影自称有效。

Memory 来源优先是 `SessionMemoryContext + MemoryQueryResult` 的精确查询，逐条核对来源 ACL、LIVE/ACCEPTED、删除控制与不透明 query version。Owner 明确按 MemoryId 选择是不同的管理路径，必须标注其 authority，不把 Owner 全量视图伪装为 Session viewer。Story 来源只能是有界 `SessionStoryContext → StoryProjection`，再限于当前角色 state 和 viewer relationships；不读取 Owner StoryState、完整日志、world_facts 或 open_threads。来源 Runtime token 不解码、不用裸 revision 替代 Session 围栏。

每个 `BridgeLineage` 记源 World/Timeline、子系统、精确对象 ID/版本、源 audience、RealityStatus/CanonStatus、grant ID/revision 与 projection fingerprint。目标若以后显式持久化，须保存可核验的来源链；不能只留下复制正文。`FICTIONAL`/`FICTIONAL_SHARED_EXPERIENCE` 到 Soul 仍是虚构，`CanonStatus.ACCEPTED` 不自动变成目标 Story 接受，来源受众也不直接复制成目标受众。

`BridgeBudget` 独立于 PromptBudget，限制 item 数、单项及总 UTF-8 bytes。投影只选请求和 grant 允许字段；来源授权顺序与 item identity 排序固定，逐项完整纳入，遇无法容纳项停止或失败，不切半、不跳过大项找小项，也不用 LLM 选材。Grant revoke/改版/过期、来源 version/删除、目标 Session/epoch/runtime/generation 变化使旧投影 stale。投影不持久化为 canonical 表；可审计 fingerprint/来源引用而非全文。

## 理由与后果

有目标受众与 lineage 的派生投影，才能同时解释“这段内容从哪里来”“可给谁看”和“撤销后哪份结果必须作废”。F1 必须在使用前重验当前资格；仅校验 HMAC 不能证明 grant 仍有效。

## F1 实现状态

**IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**。F1 的投影为瞬时对象，不建表；Memory 保留来源 RealityStatus/CanonStatus，Story 仅输出 source viewer 的角色状态和相关关系，Soul 来源没有逐项现实 provenance 时保持 `UNKNOWN`，不会被 Bridge 宣称为观察事实。规范指纹覆盖授权、双 Scope、双 Session、来源版本、完整项、lineage 与实际预算；HMAC 后仍逐次重验 Grant 和来源。
