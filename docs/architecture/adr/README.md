# Architecture Decision Records

采用文件名 `TASK-NNN-TITLE.md`，每份包含 Status、Context、Decision、Consequences、Verification。编号在任务内唯一。Implemented candidate 表示候选代码采用此决策，不代表 Independent Reviewer 已通过；审核结论需显式记录，不由作者自行标记 Accepted。

> 全部文档用途见 [文档索引](../../DOCUMENTATION-INDEX.md)；当前生命周期与证据见 [项目状态](../../PROJECT-STATUS.md)。本索引不将 ADR 的历史 Status 改为 Accepted。

## SP-004A

- [SP-004A ADR-001 — Soul World as World](SP-004A-001-SOUL-WORLD-AS-WORLD.md)
- [SP-004A ADR-002 — Reality and Canon Are Orthogonal](SP-004A-002-REALITY-AND-CANON.md)
- [SP-004A ADR-003 — Character Definition vs Character Instance](SP-004A-003-CHARACTER-DEFINITION-INSTANCE.md)
- [SP-004A ADR-004 — Pure Contracts and Writer Fencing](SP-004A-004-PURE-CONTRACT-FENCING.md)

## SP-004B

- [SP-004B-001 — Memory 语义、来源与接受权](SP-004B-001-MEMORY-SEMANTICS.md)
- [SP-004B-002 — Scope、Audience 与读取隔离](SP-004B-002-SCOPE-AUDIENCE-ISOLATION.md)
- [SP-004B-003 — 独立 Memory 修订、写入围栏与派生视图](SP-004B-003-REVISION-QUERY-CACHE.md)
- [SP-004B-004 — Schema 4 所有权、迁移与恢复安全](SP-004B-004-SCHEMA-4-MIGRATION.md)

## SP-004C

- [ADR-SP-004C-001 — 已接受事件是 Story 真源](SP-004C-001-STORY-EVENT-TRUTH.md)
- [ADR-SP-004C-002 — 确定性 Story 投影与重放](SP-004C-002-STORY-PROJECTION-REPLAY.md)
- [ADR-SP-004C-003 — Story 独立逻辑时钟与 World 生命周期](SP-004C-003-STORY-CLOCK-LIFECYCLE.md)
- [ADR-SP-004C-004 — 结构化事实、关系与 StoryThread](SP-004C-004-STORY-RELATIONSHIPS-THREADS.md)

## SP-004E

- [SP-004E-001 — 重启后的会话恢复与写入围栏](SP-004E-001-RESTART-SESSION-RECOVERY.md)
- [SP-004E-002 — Schema 3 副本迁移与整安装激活](SP-004E-002-SCHEMA-3-MIGRATION.md)

## SP-004F

- [ADR SP-004F-001 — Bridge Grant 授权与默认拒绝](SP-004F-001-BRIDGE-GRANT-AUTHORITY.md)
- [ADR SP-004F-002 — 精确预览、确认、幂等与 CAS](SP-004F-002-PREVIEW-CONFIRM-AND-IDEMPOTENCY.md)
- [ADR SP-004F-003 — 瞬时 BridgeProjection 与来源链](SP-004F-003-BRIDGE-PROJECTION-AND-LINEAGE.md)
- [ADR SP-004F-004 — 撤销、恢复与来源删除的不复活门禁](SP-004F-004-REVOCATION-RESTORE-AND-SOURCE-DELETION.md)
- [ADR SP-004F-005 — Prompt 消费与目标 Memory/Story 写入边界](SP-004F-005-PROMPT-AND-TARGET-PERSISTENCE-BOUNDARIES.md)

## SP-004H

- [ADR SP-004H-001 — Host Identity and Principal](SP-004H-001-HOST-IDENTITY-AND-PRINCIPAL.md)
- [ADR SP-004H-002 — Session Lane and History Isolation](SP-004H-002-SESSION-LANE-AND-HISTORY-ISOLATION.md)
- [ADR SP-004H-003 — Conversation Projection and Provenance](SP-004H-003-CONVERSATION-PROJECTION-AND-PROVENANCE.md)
- [ADR SP-004H-004 — Prompt Render, Submit and Revalidation](SP-004H-004-PROMPT-RENDER-SUBMIT-AND-REVALIDATION.md)
- [ADR SP-004H-005 — Late Response and Reconciliation](SP-004H-005-LATE-RESPONSE-AND-RECONCILIATION.md)
- [ADR SP-004H-006 — Bridge UX and Host Capabilities](SP-004H-006-BRIDGE-UX-AND-HOST-CAPABILITIES.md)

## SP-004J

- [ADR-SP-004J-001 — Lore 资产与版本身份](SP-004J-001-LORE-ASSET-VERSIONING.md)
- [ADR-SP-004J-002 — Lore 绑定、Scope 与观看身份](SP-004J-002-LORE-BINDING-SCOPE.md)
- [ADR-SP-004J-003 — Lore 激活、字面触发与递归](SP-004J-003-ACTIVATION-TRIGGERS-RECURSION.md)
- [ADR-SP-004J-004 — Lore 预算、排序与不可信内容](SP-004J-004-BUDGET-ORDERING-SAFETY.md)

## SP-004K

- [SP-004K-001 — Prompt 权威与类型化分节](SP-004K-001-PROMPT-AUTHORITY-AND-SECTIONS.md)
- [SP-004K-002 — Prompt 快照一致性与陈旧围栏](SP-004K-002-SNAPSHOT-CONSISTENCY-AND-STALE-FENCES.md)
- [SP-004K-003 — Prompt 预算与确定性裁剪](SP-004K-003-PROMPT-BUDGET-AND-DETERMINISTIC-TRIMMING.md)
- [SP-004K-004 — 观看身份、用途与子系统边界](SP-004K-004-VIEWER-PURPOSE-AND-SUBSYSTEM-BOUNDARIES.md)
