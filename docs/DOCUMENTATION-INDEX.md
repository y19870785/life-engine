# 项目文档索引与全量复核记录

复核基准日：2026-10-18；文档整合跨日至 10-19，周统计窗口保持 10-12—10-18。固定代码输入 `baa59729babf9ac56a17e02c682de2e3086e3575`。本轮逐文件复核原有 123 份 tracked Markdown / reStructuredText / `.txt` 文档，并新增下列 5 份，形成 128 份文档目录。裸 `LICENSE` 不在扩展名统计内，许可原文同样保留。

## 从这里开始

| 需要了解什么 | 入口 |
| --- | --- |
| 当前能做什么、证据到哪一层 | [项目状态](PROJECT-STATUS.md) |
| 最近一周发生了什么 | [开发周报](reports/WEEKLY-REVIEW-2026-10-18.md) |
| 多代理开发的得失、怎样优化 | [开发方式复盘](planning/DEVELOPMENT-WORKFLOW-REVIEW-2026-10.md) |
| 下一步的目标、依赖、验收和停止点 | [后续计划（提案）](planning/NEXT-DEVELOPMENT-PLAN-2026-10.md) |
| 文档职责和历史范围 | 本索引 |

## 本轮怎样处理所有文档

原有20份当前入口均校准状态、模块边界或导航；66份冻结技术合同/历史记录、33份ADR、2份legacy和2份法律文件保持原文。全量更新不等于把历史预算、失败或当时Draft状态改成今天结果，也不为每个合同复制一份CURRENT。

冻结合同的技术约束仍按其自身规则有效；“冻结/历史”分类不表示合同已废止。旧阶段的NEXT、授权、测试数量和Base只绑定对应时点，当前生命周期统一读取PROJECT-STATUS。新计划是提案，不能覆盖已冻结架构或激活后续阶段。

维护时先改当前状态和受影响模块指南；新设计/验证保留固定对象、日期和证据边界。旧原件不倒填新CI或成功。外部资料只保留其原检查日期，本次本地链接检查不代表今天上游兼容性已验证。

## 新增文档

| 文件 | 职责 |
| --- | --- |
| [docs/PROJECT-STATUS.md](../docs/PROJECT-STATUS.md) | 当前状态与代码/Host/交付证据索引 |
| [docs/DOCUMENTATION-INDEX.md](../docs/DOCUMENTATION-INDEX.md) | 全部原有文档逐文件分类与维护规则 |
| [docs/reports/WEEKLY-REVIEW-2026-10-18.md](../docs/reports/WEEKLY-REVIEW-2026-10-18.md) | 2026-10-12—10-18时间线、能力和失败复盘 |
| [docs/planning/DEVELOPMENT-WORKFLOW-REVIEW-2026-10.md](../docs/planning/DEVELOPMENT-WORKFLOW-REVIEW-2026-10.md) | 多代理与证据门禁的优缺点、工程改进提案 |
| [docs/planning/NEXT-DEVELOPMENT-PLAN-2026-10.md](../docs/planning/NEXT-DEVELOPMENT-PLAN-2026-10.md) | H0—H3及工程/正式主线准入准备；不授权实施 |

## 当前入口与使用指南（20）

已校准当前状态或导航；模块命令与安全边界按实际功能保留。

| 文件 | 本轮处置 |
| --- | --- |
| [README.md](../README.md) | 状态/边界/导航已校准 |
| [START-HERE.md](../START-HERE.md) | 状态/边界/导航已校准 |
| [docs/HERMES-CHARACTER-CAPABILITIES.md](../docs/HERMES-CHARACTER-CAPABILITIES.md) | 状态/边界/导航已校准 |
| [docs/HERMES-CHARACTER-CARD-IMPORT.md](../docs/HERMES-CHARACTER-CARD-IMPORT.md) | 状态/边界/导航已校准 |
| [docs/HERMES-CHARACTER-CONTINUITY-V2.md](../docs/HERMES-CHARACTER-CONTINUITY-V2.md) | 状态/边界/导航已校准 |
| [docs/HERMES-CHARACTER-ONBOARDING.md](../docs/HERMES-CHARACTER-ONBOARDING.md) | 状态/边界/导航已校准 |
| [docs/HOST-SANDBOX-TESTING.md](../docs/HOST-SANDBOX-TESTING.md) | 状态/边界/导航已校准 |
| [docs/KNOWN-ISSUES.md](../docs/KNOWN-ISSUES.md) | 状态/边界/导航已校准 |
| [docs/LIVING-RUNTIME.md](../docs/LIVING-RUNTIME.md) | 状态/边界/导航已校准 |
| [docs/OPERATIONS.md](../docs/OPERATIONS.md) | 状态/边界/导航已校准 |
| [docs/SOURCES.md](../docs/SOURCES.md) | 状态/边界/导航已校准 |
| [docs/VALIDATION.md](../docs/VALIDATION.md) | 状态/边界/导航已校准 |
| [docs/architecture/adr/README.md](../docs/architecture/adr/README.md) | 状态/边界/导航已校准 |
| [docs/compatibility/SILLYTAVERN-COMPATIBILITY.md](../docs/compatibility/SILLYTAVERN-COMPATIBILITY.md) | 状态/边界/导航已校准 |
| [docs/planning/CODEX-STAGE-AUTONOMY-PLAN.md](../docs/planning/CODEX-STAGE-AUTONOMY-PLAN.md) | 状态/边界/导航已校准 |
| [docs/planning/EXPERIENCE-FIRST-X1-TRIAL.md](../docs/planning/EXPERIENCE-FIRST-X1-TRIAL.md) | 状态/边界/导航已校准 |
| [docs/planning/LIFE-ENGINE-DEVELOPMENT-ROADMAP.md](../docs/planning/LIFE-ENGINE-DEVELOPMENT-ROADMAP.md) | 状态/边界/导航已校准 |
| [docs/planning/ROADMAP-2026-09.md](../docs/planning/ROADMAP-2026-09.md) | 状态/边界/导航已校准 |
| [docs/planning/SOUL-CONTINUITY-DEVELOPMENT-PLAN.md](../docs/planning/SOUL-CONTINUITY-DEVELOPMENT-PLAN.md) | 状态/边界/导航已校准 |
| [docs/planning/W0-W1-CHARACTER-BASELINE.md](../docs/planning/W0-W1-CHARACTER-BASELINE.md) | 状态/边界/导航已校准 |

## 冻结技术合同、阶段计划与验证记录（66）

原Base/日期/授权/计数/失败保持；技术合同不因本周复盘失效。

| 文件 | 本轮处置 |
| --- | --- |
| [docs/SP-005A1-VALIDATION.md](../docs/SP-005A1-VALIDATION.md) | 复核后保留原文 |
| [docs/SP-005A3-B0-VALIDATION.md](../docs/SP-005A3-B0-VALIDATION.md) | 复核后保留原文 |
| [docs/SP-005A3-B1-VALIDATION.md](../docs/SP-005A3-B1-VALIDATION.md) | 复核后保留原文 |
| [docs/SP-005A3-VALIDATION.md](../docs/SP-005A3-VALIDATION.md) | 复核后保留原文 |
| [docs/architecture/GOV-ARCHGATE1-POST-HLV3-REVIEW.md](../docs/architecture/GOV-ARCHGATE1-POST-HLV3-REVIEW.md) | 复核后保留原文 |
| [docs/architecture/GOV-SOUL-ROADMAP1-SOUL-CONTINUITY-MAINLINE.md](../docs/architecture/GOV-SOUL-ROADMAP1-SOUL-CONTINUITY-MAINLINE.md) | 复核后保留原文 |
| [docs/architecture/M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md](../docs/architecture/M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md) | 复核后保留原文 |
| [docs/architecture/SP-004-GAP-ANALYSIS.md](../docs/architecture/SP-004-GAP-ANALYSIS.md) | 复核后保留原文 |
| [docs/architecture/SP-004-PERSISTENT-WORLD-RUNTIME.md](../docs/architecture/SP-004-PERSISTENT-WORLD-RUNTIME.md) | 复核后保留原文 |
| [docs/architecture/SP-004A-WORLD-DOMAIN-MODEL.md](../docs/architecture/SP-004A-WORLD-DOMAIN-MODEL.md) | 复核后保留原文 |
| [docs/architecture/SP-004B-WORLD-MEMORY.md](../docs/architecture/SP-004B-WORLD-MEMORY.md) | 复核后保留原文 |
| [docs/architecture/SP-004C-STORY-RUNTIME.md](../docs/architecture/SP-004C-STORY-RUNTIME.md) | 复核后保留原文 |
| [docs/architecture/SP-004D-WORLD-INSTANCE-RUNTIME.md](../docs/architecture/SP-004D-WORLD-INSTANCE-RUNTIME.md) | 复核后保留原文 |
| [docs/architecture/SP-004E-WORLD-SQLITE-PERSISTENCE.md](../docs/architecture/SP-004E-WORLD-SQLITE-PERSISTENCE.md) | 复核后保留原文 |
| [docs/architecture/SP-004F-CONTROLLED-WORLD-BRIDGE.md](../docs/architecture/SP-004F-CONTROLLED-WORLD-BRIDGE.md) | 复核后保留原文 |
| [docs/architecture/SP-004G-CHARACTER-IMPORT-IR.md](../docs/architecture/SP-004G-CHARACTER-IMPORT-IR.md) | 复核后保留原文 |
| [docs/architecture/SP-004H-HOST-INTEGRATION.md](../docs/architecture/SP-004H-HOST-INTEGRATION.md) | 复核后保留原文 |
| [docs/architecture/SP-004J-LORE-RUNTIME.md](../docs/architecture/SP-004J-LORE-RUNTIME.md) | 复核后保留原文 |
| [docs/architecture/SP-004K-PROMPT-RUNTIME.md](../docs/architecture/SP-004K-PROMPT-RUNTIME.md) | 复核后保留原文 |
| [docs/architecture/SP-005A-CURRENT-STATE-AUDIT.md](../docs/architecture/SP-005A-CURRENT-STATE-AUDIT.md) | 复核后保留原文 |
| [docs/architecture/SP-005A-LIVING-RUNTIME.md](../docs/architecture/SP-005A-LIVING-RUNTIME.md) | 复核后保留原文 |
| [docs/architecture/SP-005A2-CURRENT-HOST-BINDING-AUDIT.md](../docs/architecture/SP-005A2-CURRENT-HOST-BINDING-AUDIT.md) | 复核后保留原文 |
| [docs/architecture/SP-005A2-LIVING-HOST-BINDING.md](../docs/architecture/SP-005A2-LIVING-HOST-BINDING.md) | 复核后保留原文 |
| [docs/architecture/SP-005A3-B1-OPERATION-RECOVERY-PROJECTION.md](../docs/architecture/SP-005A3-B1-OPERATION-RECOVERY-PROJECTION.md) | 复核后保留原文 |
| [docs/architecture/SP-005A4-HERMES-LIVING-VALIDATION.md](../docs/architecture/SP-005A4-HERMES-LIVING-VALIDATION.md) | 复核后保留原文 |
| [docs/architecture/SP-005A4-HLV4-DEDICATED-DISCORD-PROVIDER-TRANSPORT.md](../docs/architecture/SP-005A4-HLV4-DEDICATED-DISCORD-PROVIDER-TRANSPORT.md) | 复核后保留原文 |
| [docs/architecture/SP-005A4-HLV4-DEDICATED-HERMES-DELIVERY-ADAPTER.md](../docs/architecture/SP-005A4-HLV4-DEDICATED-HERMES-DELIVERY-ADAPTER.md) | 复核后保留原文 |
| [docs/architecture/SP-005A4-HLV4-REAL-DELIVERY-AUTHORITY.md](../docs/architecture/SP-005A4-HLV4-REAL-DELIVERY-AUTHORITY.md) | 复核后保留原文 |
| [docs/architecture/SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md](../docs/architecture/SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md) | 复核后保留原文 |
| [docs/planning/CODEX-STAGE-AUTONOMY-R2-REVIEW.md](../docs/planning/CODEX-STAGE-AUTONOMY-R2-REVIEW.md) | 复核后保留原文 |
| [docs/planning/EXPERIENCE-FIRST-AGENT-WORLD-SEED-DRAFT.md](../docs/planning/EXPERIENCE-FIRST-AGENT-WORLD-SEED-DRAFT.md) | 复核后保留原文 |
| [docs/planning/EXPERIENCE-FIRST-SOUL-CONTINUITY-PLAN-DRAFT.md](../docs/planning/EXPERIENCE-FIRST-SOUL-CONTINUITY-PLAN-DRAFT.md) | 复核后保留原文 |
| [docs/planning/EXPERIENCE-FIRST-X0-SCENARIO-BASELINE-DRAFT.md](../docs/planning/EXPERIENCE-FIRST-X0-SCENARIO-BASELINE-DRAFT.md) | 复核后保留原文 |
| [docs/planning/EXPERIENCE-FIRST-X1-INTERACTIVE-SANDBOX-TASK-DRAFT.md](../docs/planning/EXPERIENCE-FIRST-X1-INTERACTIVE-SANDBOX-TASK-DRAFT.md) | 复核后保留原文 |
| [docs/planning/M1-A-PRIMITIVE-ADMISSION-EVIDENCE.md](../docs/planning/M1-A-PRIMITIVE-ADMISSION-EVIDENCE.md) | 复核后保留原文 |
| [docs/planning/M1-A-STORAGE-DESIGN-TASK-DRAFT.md](../docs/planning/M1-A-STORAGE-DESIGN-TASK-DRAFT.md) | 复核后保留原文 |
| [docs/planning/M1-A-STORAGE-DESIGN.md](../docs/planning/M1-A-STORAGE-DESIGN.md) | 复核后保留原文 |
| [docs/planning/M1-P0-CRASH-RECOVERY-MATRIX.md](../docs/planning/M1-P0-CRASH-RECOVERY-MATRIX.md) | 复核后保留原文 |
| [docs/planning/M1-P0-IMPLEMENTATION-GATE.md](../docs/planning/M1-P0-IMPLEMENTATION-GATE.md) | 复核后保留原文 |
| [docs/planning/SP-004-IMPLEMENTATION-PLAN.md](../docs/planning/SP-004-IMPLEMENTATION-PLAN.md) | 复核后保留原文 |
| [docs/planning/SP-004-MIDTERM-REVIEW-2026-09.md](../docs/planning/SP-004-MIDTERM-REVIEW-2026-09.md) | 复核后保留原文 |
| [docs/planning/SP-004-QUALITY-GATES.md](../docs/planning/SP-004-QUALITY-GATES.md) | 复核后保留原文 |
| [docs/planning/SP-004A-QUALITY-GATES.md](../docs/planning/SP-004A-QUALITY-GATES.md) | 复核后保留原文 |
| [docs/planning/SP-004D-QUALITY-GATES.md](../docs/planning/SP-004D-QUALITY-GATES.md) | 复核后保留原文 |
| [docs/planning/SP-004E-QUALITY-GATES.md](../docs/planning/SP-004E-QUALITY-GATES.md) | 复核后保留原文 |
| [docs/planning/SP-004G-QUALITY-GATES.md](../docs/planning/SP-004G-QUALITY-GATES.md) | 复核后保留原文 |
| [docs/planning/SP-004R-PR3-SUPERSESSION.md](../docs/planning/SP-004R-PR3-SUPERSESSION.md) | 复核后保留原文 |
| [docs/planning/SP-005A1-TEST-MATRIX.md](../docs/planning/SP-005A1-TEST-MATRIX.md) | 复核后保留原文 |
| [docs/planning/SP-005A3-HOST-BINDING-TEST-MATRIX.md](../docs/planning/SP-005A3-HOST-BINDING-TEST-MATRIX.md) | 复核后保留原文 |
| [docs/planning/SP-005A4-HERMES-LIVING-VALIDATION-MATRIX.md](../docs/planning/SP-005A4-HERMES-LIVING-VALIDATION-MATRIX.md) | 复核后保留原文 |
| [docs/planning/SP-006S0-ARCHITECTURE-FREEZE-TASK.md](../docs/planning/SP-006S0-ARCHITECTURE-FREEZE-TASK.md) | 复核后保留原文 |
| [docs/planning/SP-006S0-CONTINUITY-VALIDATION-MATRIX.md](../docs/planning/SP-006S0-CONTINUITY-VALIDATION-MATRIX.md) | 复核后保留原文 |
| [docs/planning/SP-006S0-IMPLEMENTATION-PLAN.md](../docs/planning/SP-006S0-IMPLEMENTATION-PLAN.md) | 复核后保留原文 |
| [docs/validation/HERMES-COMPREHENSIVE-EVALUATION-2026-09-30.md](../docs/validation/HERMES-COMPREHENSIVE-EVALUATION-2026-09-30.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV1-E0-R1-SECURITY-REMEDIATION.md](../docs/validation/SP-005A4-HLV1-E0-R1-SECURITY-REMEDIATION.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV1-E0-R2-IDENTITY-ROUTING.md](../docs/validation/SP-005A4-HLV1-E0-R2-IDENTITY-ROUTING.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV1-E0-R3-GATEWAY-FIRST-START.md](../docs/validation/SP-005A4-HLV1-E0-R3-GATEWAY-FIRST-START.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV1-E0-R3-R1-GATEWAY-REMEDIATION.md](../docs/validation/SP-005A4-HLV1-E0-R3-R1-GATEWAY-REMEDIATION.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV1-E0-R3-R2-GATEWAY-LIFECYCLE-CLOSURE.md](../docs/validation/SP-005A4-HLV1-E0-R3-R2-GATEWAY-LIFECYCLE-CLOSURE.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV1-HERMES-READONLY-DISCOVERY.md](../docs/validation/SP-005A4-HLV1-HERMES-READONLY-DISCOVERY.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV2-HERMES-HOST-LIFECYCLE-AUTHORITY.md](../docs/validation/SP-005A4-HLV2-HERMES-HOST-LIFECYCLE-AUTHORITY.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV3-HERMES-LIVING-DRY-RUN.md](../docs/validation/SP-005A4-HLV3-HERMES-LIVING-DRY-RUN.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV4-A1-DEDICATED-ADAPTER.md](../docs/validation/SP-005A4-HLV4-A1-DEDICATED-ADAPTER.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV4-A2-R1-PROVIDER-TRANSPORT.md](../docs/validation/SP-005A4-HLV4-A2-R1-PROVIDER-TRANSPORT.md) | 复核后保留原文 |
| [docs/validation/SP-005A4-HLV4-R1-REAL-DELIVERY-AUTHORITY.md](../docs/validation/SP-005A4-HLV4-R1-REAL-DELIVERY-AUTHORITY.md) | 复核后保留原文 |
| [docs/validation/W1-HERMES-TEXT-BASELINE.md](../docs/validation/W1-HERMES-TEXT-BASELINE.md) | 复核后保留原文 |

## 架构决策原件（33）

原Status/Decision不改；完整分组导航见[ADR索引](architecture/adr/README.md)。

| 文件 | 本轮处置 |
| --- | --- |
| [docs/architecture/adr/SP-004A-001-SOUL-WORLD-AS-WORLD.md](../docs/architecture/adr/SP-004A-001-SOUL-WORLD-AS-WORLD.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004A-002-REALITY-AND-CANON.md](../docs/architecture/adr/SP-004A-002-REALITY-AND-CANON.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004A-003-CHARACTER-DEFINITION-INSTANCE.md](../docs/architecture/adr/SP-004A-003-CHARACTER-DEFINITION-INSTANCE.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004A-004-PURE-CONTRACT-FENCING.md](../docs/architecture/adr/SP-004A-004-PURE-CONTRACT-FENCING.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004B-001-MEMORY-SEMANTICS.md](../docs/architecture/adr/SP-004B-001-MEMORY-SEMANTICS.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004B-002-SCOPE-AUDIENCE-ISOLATION.md](../docs/architecture/adr/SP-004B-002-SCOPE-AUDIENCE-ISOLATION.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004B-003-REVISION-QUERY-CACHE.md](../docs/architecture/adr/SP-004B-003-REVISION-QUERY-CACHE.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004B-004-SCHEMA-4-MIGRATION.md](../docs/architecture/adr/SP-004B-004-SCHEMA-4-MIGRATION.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004C-001-STORY-EVENT-TRUTH.md](../docs/architecture/adr/SP-004C-001-STORY-EVENT-TRUTH.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004C-002-STORY-PROJECTION-REPLAY.md](../docs/architecture/adr/SP-004C-002-STORY-PROJECTION-REPLAY.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004C-003-STORY-CLOCK-LIFECYCLE.md](../docs/architecture/adr/SP-004C-003-STORY-CLOCK-LIFECYCLE.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004C-004-STORY-RELATIONSHIPS-THREADS.md](../docs/architecture/adr/SP-004C-004-STORY-RELATIONSHIPS-THREADS.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004E-001-RESTART-SESSION-RECOVERY.md](../docs/architecture/adr/SP-004E-001-RESTART-SESSION-RECOVERY.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004E-002-SCHEMA-3-MIGRATION.md](../docs/architecture/adr/SP-004E-002-SCHEMA-3-MIGRATION.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004F-001-BRIDGE-GRANT-AUTHORITY.md](../docs/architecture/adr/SP-004F-001-BRIDGE-GRANT-AUTHORITY.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004F-002-PREVIEW-CONFIRM-AND-IDEMPOTENCY.md](../docs/architecture/adr/SP-004F-002-PREVIEW-CONFIRM-AND-IDEMPOTENCY.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004F-003-BRIDGE-PROJECTION-AND-LINEAGE.md](../docs/architecture/adr/SP-004F-003-BRIDGE-PROJECTION-AND-LINEAGE.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004F-004-REVOCATION-RESTORE-AND-SOURCE-DELETION.md](../docs/architecture/adr/SP-004F-004-REVOCATION-RESTORE-AND-SOURCE-DELETION.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004F-005-PROMPT-AND-TARGET-PERSISTENCE-BOUNDARIES.md](../docs/architecture/adr/SP-004F-005-PROMPT-AND-TARGET-PERSISTENCE-BOUNDARIES.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004H-001-HOST-IDENTITY-AND-PRINCIPAL.md](../docs/architecture/adr/SP-004H-001-HOST-IDENTITY-AND-PRINCIPAL.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004H-002-SESSION-LANE-AND-HISTORY-ISOLATION.md](../docs/architecture/adr/SP-004H-002-SESSION-LANE-AND-HISTORY-ISOLATION.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004H-003-CONVERSATION-PROJECTION-AND-PROVENANCE.md](../docs/architecture/adr/SP-004H-003-CONVERSATION-PROJECTION-AND-PROVENANCE.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004H-004-PROMPT-RENDER-SUBMIT-AND-REVALIDATION.md](../docs/architecture/adr/SP-004H-004-PROMPT-RENDER-SUBMIT-AND-REVALIDATION.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004H-005-LATE-RESPONSE-AND-RECONCILIATION.md](../docs/architecture/adr/SP-004H-005-LATE-RESPONSE-AND-RECONCILIATION.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004H-006-BRIDGE-UX-AND-HOST-CAPABILITIES.md](../docs/architecture/adr/SP-004H-006-BRIDGE-UX-AND-HOST-CAPABILITIES.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004J-001-LORE-ASSET-VERSIONING.md](../docs/architecture/adr/SP-004J-001-LORE-ASSET-VERSIONING.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004J-002-LORE-BINDING-SCOPE.md](../docs/architecture/adr/SP-004J-002-LORE-BINDING-SCOPE.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004J-003-ACTIVATION-TRIGGERS-RECURSION.md](../docs/architecture/adr/SP-004J-003-ACTIVATION-TRIGGERS-RECURSION.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004J-004-BUDGET-ORDERING-SAFETY.md](../docs/architecture/adr/SP-004J-004-BUDGET-ORDERING-SAFETY.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004K-001-PROMPT-AUTHORITY-AND-SECTIONS.md](../docs/architecture/adr/SP-004K-001-PROMPT-AUTHORITY-AND-SECTIONS.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004K-002-SNAPSHOT-CONSISTENCY-AND-STALE-FENCES.md](../docs/architecture/adr/SP-004K-002-SNAPSHOT-CONSISTENCY-AND-STALE-FENCES.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004K-003-PROMPT-BUDGET-AND-DETERMINISTIC-TRIMMING.md](../docs/architecture/adr/SP-004K-003-PROMPT-BUDGET-AND-DETERMINISTIC-TRIMMING.md) | 复核后保留原文 |
| [docs/architecture/adr/SP-004K-004-VIEWER-PURPOSE-AND-SUBSYSTEM-BOUNDARIES.md](../docs/architecture/adr/SP-004K-004-VIEWER-PURPOSE-AND-SUBSYSTEM-BOUNDARIES.md) | 复核后保留原文 |

## 旧版参考（2）

仅供v0.2历史维护，不作为新角色/新Living部署入口。

| 文件 | 本轮处置 |
| --- | --- |
| [V02-README.md](../V02-README.md) | 复核后保留原文 |
| [docs/V02-OPERATIONS.md](../docs/V02-OPERATIONS.md) | 复核后保留原文 |

## 法律与来源声明（2）

原文保留，不因工程状态更改版权或许可。

| 文件 | 本轮处置 |
| --- | --- |
| [LICENSES/Life-Engine-MIT.txt](../LICENSES/Life-Engine-MIT.txt) | 复核后保留原文 |
| [NOTICE.md](../NOTICE.md) | 复核后保留原文 |

## 检查边界

本轮针对文档进行文件清单覆盖、链接目标/本地锚点、实际diff、历史原文保持及能力声明审核；不重跑真实Host、模型或渠道。文档PR的Head CI和合并状态属于该PR自己的证据，不与本索引代码输入SHA混用。
