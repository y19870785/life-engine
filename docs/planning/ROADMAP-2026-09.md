# Life Engine 后续开发路线 — 2026-09

> **Soul Continuity Plan V2 = APPROVED_PLANNING_BASELINE / NOT_EXECUTION_AUTHORIZATION（已通过独立规划审核）**：当前主线的后续阶段与 M1.x Continuity Proof / Simulation Gate 见[开发计划](SOUL-CONTINUITY-DEVELOPMENT-PLAN.md)，SP-006S0 的设计范围见[架构冻结任务书候选](SP-006S0-ARCHITECTURE-FREEZE-TASK.md)。本页 2026-09 历史顺序与证据保持原时点语义；`SP-006S0 = NEXT / NOT AUTHORIZED`，本规划不授权 Host 操作。

## CURRENT GOVERNANCE OVERRIDE — GOV-SOUL-ROADMAP1

本页是 2026-09 阶段规划的历史记录；当前治理以 [GOV-SOUL-ROADMAP1](../architecture/GOV-SOUL-ROADMAP1-SOUL-CONTINUITY-MAINLINE.md) 为准。A2-R1 canonical implementation commit = `a552a2d0846ff024b930d0d802228b863a6da74f`，A2-R1 = DONE。Soul Continuity = `ACTIVE_MAINLINE`，唯一 NEXT 为 `SP-006S0 Soul Continuity Architecture Freeze / NOT AUTHORIZED`；Host Integration = `DEFERRED`，Full Private RP = `FROZEN_EXTERNAL_BLOCKER`。旧 HLV4 → Adapter Stabilization → P1 → Memory Evolution 顺序已被取代，下面表格及说明只表达当时计划，不构成当前执行顺序或授权。

`SP-005A2-P1 = RESEQUENCED_UNDER_SOUL_CONTINUITY_MAINLINE / NOT AUTHORIZED`；Memory Evolution V1 = `SOUL_CONTINUITY_MAINLINE / PLANNED / NOT AUTHORIZED`，具体依赖由 SP-006S0 评审。`REAL_HOST_SENT / ACKNOWLEDGED = NOT_ACQUIRED`，`ACK_VALIDATOR = HOST_GAP`，`REAL_SEND = NO`。

## HISTORICAL — Post-HLV3 / GOV-ARCHGATE1 当前状态快照（2026-10-03）

canonical Base：`9d064d0a90d8d02a5dab04a6baee18bbbf6dcdc2`；PR #39 Squash Merge 与 exact main push CI #37122681930 四矩阵已独立核验。SP-005A4-HLV0 = DONE；SP-005A4-HLV1 = DONE；SP-005A4-HLV2 = DONE；SP-005A4-HLV3 = DONE。REAL_HOST_READONLY_PASS / REAL_HOST_LIFECYCLE_PASS / REAL_HOST_LIFECYCLE_AUTHORITY_PASS / REAL_HOST_DRY_RUN_PASS = CONFIRMED；REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP。

ARCHITECTURE_REVIEW_GATE = PASS；LOCAL_ORDER = HLV4 → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1。ARCHITECTURE_CHANGE_REQUIRED = NO；ROADMAP_DIRECTION_CHANGE = NO。完整证据、依赖与授权边界见 [GOV-ARCHGATE1 Gate 记录](../architecture/GOV-ARCHGATE1-POST-HLV3-REVIEW.md)。GOV-ARCHGATE1 = DRAFT_REVIEW_PENDING；SP-005A4-HLV4 = NEXT / NOT AUTHORIZED，独立任务与明确授权前 REAL_SEND = FORBIDDEN。Roadmap state != execution authorization。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = AFTER_HERMES_ADAPTER_STABILIZATION / NOT AUTHORIZED；Memory Evolution V1 = AFTER_SP-005A2-P1 / PLANNED。OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED_BY_OFFICIAL_HOST_CAPABILITY（H1/H2 blocker 保留）。本轮 NO_REAL_HOST_OPERATION = true、NO_REAL_SEND = true；历史证据只引用，不重跑。

长期阶段与Gate见 [LIFE-ENGINE-DEVELOPMENT-ROADMAP](LIFE-ENGINE-DEVELOPMENT-ROADMAP.md)。SP-005A3 DONE；B01–B34 SIMULATED_PASS、B1 Core标签与历史真实发送边界保留。

2026-09-30 Hermes 0.21.3 受控评测属于[历史快照](../validation/HERMES-COMPREHENSIVE-EVALUATION-2026-09-30.md)：上一轮一次受控文字发送的证据与当轮 Organic Contact 静默判定（当轮新发 0 条），不代表当前 Living Host 链路完成或 ACK 验证通过。该历史发送不签发当前Living REAL_HOST_SENT；Hermes现已完成HLV1～3，真实Living发送仍未取得，OpenClaw仍PENDING_REAL_HOST_VALIDATION。

Full Private RP 仍被 Host capability 阻塞：Hermes 尚未取得独立通过的 Full Private RP final-output commit / session incarnation 证据；OpenClaw CAP0/CAP1 也没有找到可组成一次 fail-closed 授权的插件边界。已有 World/Roleplay Runtime 与生产 Host 私密 RP 是两件事。路线中任何阶段都不自动解锁 H1/H2 Adapter。

## HISTORICAL — 2026-09 主线阶段

| 顺序 | 阶段 | 当前状态 | 目标与验收边界 |
| --- | --- | --- | --- |
| 1 | **GOV-DOC2** 当前状态、Host 沙箱指南与路线校准 | **DONE** | README、验证与已知问题同 canonical main 对齐；明确可测/不可测；提供[Host 沙箱指南](../HOST-SANDBOX-TESTING.md)。 |
| 2 | **SP-005H0 Host Integration Sandbox** | 实现 DONE；真实验证 PENDING_REAL_HOST_VALIDATION | 同一 canonical Life Engine 分别接真实 Hermes / OpenClaw，仅 Soul Continuity 与 sandbox-safe 功能。记录真实 Host version、插件加载、唯一 instance binding、错误 Profile/Agent 拒绝、重启恢复、status/wake/photo、本人受控聊天、实际发送与 receipt 区别、upgrade/reload 后重验。**不包含** Full Private RP、Host Core patch、Hermes/OpenClaw fork。 |
| 3 | **SP-005A0 Living Runtime Architecture** | **DONE；R1 DONE** | [冻结架构](../architecture/SP-005A-LIVING-RUNTIME.md)及[当前状态审计](../architecture/SP-005A-CURRENT-STATE-AUDIT.md)已合并；R1 仅澄清 Intent 预留与 Attempt 重验；冻结 time context、daily activity、location/weather/holiday context、主动联系和照片/语音计划、持久 schedule state、restart recovery 的真源与边界。它应是持久 domain/runtime，**不是 cron 脚本集合**。 |
| 4 | **SP-005A1 Living Runtime** | **DONE** | [A1 测试矩阵](SP-005A1-TEST-MATRIX.md)及 [48 项实施映射](../SP-005A1-VALIDATION.md)已完成独立审核及 exact main push CI；已实现 daily state、contact opportunities、cooldown、quiet hours、daypart、独立 LivingContextSnapshot 与 schedule recovery；Host 负责唤醒/发送，Life Engine 保留规则与状态真源。 |
| 5 | **SP-005A2 Living Runtime Host Binding Architecture** | **DONE** | [现状审计](../architecture/SP-005A2-CURRENT-HOST-BINDING-AUDIT.md)、[分层合同](../architecture/SP-005A2-LIVING-HOST-BINDING.md)与[未来测试矩阵](SP-005A3-HOST-BINDING-TEST-MATRIX.md)；只做文档，不接真实 Host。 |
| 6 | **SP-005A3 Living Host Binding Implementation** | **DONE** | v3 facade/authority/capability/recovery/permit/证据接口与本地 dispatch fence 已实施，见 A3 验证报告；默认 DRY_RUN / NO_REAL_SEND；Prompt 正式接入须另审模板升级。 |
| 7 | **SP-005A4-HLV0** | **DONE** | 架构与验证计划已冻结，不授权执行。 |
| 8 | **GOV-ROADMAP1** | 长期路线基线 | 原预留局部Architecture Review Gate由本轮记录，方向不变。 |
| 9 | **SP-005A4-HLV1** | **DONE** | REAL_HOST_READONLY_PASS / E0 REAL_HOST_LIFECYCLE_PASS CONFIRMED。 |
| 10 | **H-LV2** | **DONE** | REAL_HOST_LIFECYCLE_AUTHORITY_PASS CONFIRMED；持久身份与执行权分离。 |
| 11 | **H-LV3** | **DONE** | REAL_HOST_DRY_RUN_PASS CONFIRMED；fake不是真实SENT/ACK。 |
| Gate | **ARCHITECTURE REVIEW GATE** | **PASS** | 独立决定HLV4 → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1。 |
| Gov | **GOV-ARCHGATE1** | **DRAFT_REVIEW_PENDING** | 文档记录Gate结论，不实施，不发布真实发送授权。 |
| 12 | **H-LV4** | **NEXT / NOT AUTHORIZED** | separate task + explicit authorization；严格单Intent/Attempt/permit/isolated target/text/side effect。 |
| 后续 | **Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1 → Routine → Media → Voice → Relationship → OpenClaw** | **PLANNED；P1 NOT AUTHORIZED** | P1 AFTER_HERMES_ADAPTER_STABILIZATION，Memory V1 AFTER_SP-005A2-P1；其余原顺序保留，Full Private RP独立BLOCKED。 |

SP-005H0的实现与整体sandbox验收不由本Gate升级；Hermes Living HLV1～3已DONE，但REAL_HOST_SENT未取得，OpenClaw real Host validation仍PENDING_REAL_HOST_VALIDATION。A0 是 Core 架构阶段，不依赖真实 Host PASS，也不宣称 Host 集成完成。A0/R1 已冻结架构；A1 经单独授权实施 Schema 8，Prompt v1 不变，自动迁移不等于 Living enrollment。

SP-005A2-R1 = DONE；SP-005A3-B0 = DONE；SP-005A3-B1 Architecture = DONE；SP-005A3-B1 Implementation = DONE。B0 的 [Session fence 与 receipt replay](../SP-005A3-B0-VALIDATION.md)和 B1 的 [只读 recovery](../SP-005A3-B1-VALIDATION.md)分别保留，历史 Core 子集标签保留；A3 本地 Host 子集另以 SIMULATED_PASS 记录，不扩大为真实 Host PASS。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = NOT AUTHORIZED。A3 v2 为 HISTORICAL 冻结分支；A3 v3 已从 R1 Base 独立实现并合并。本轮 GOV-ARCHGATE1 不开始 P1、真实 Host、Media、Voice、HLV4 或 Memory Evolution。

## HISTORICAL — 当时执行依赖与授权边界

1. HLV0～HLV3已独立DONE，Architecture Review Gate PASS；GOV-ARCHGATE1当前仅记录结论，仍须完整Draft/Ready/Merge/canonical-main治理后才DONE。
2. GOV-ARCHGATE1完成不授权发送；HLV4另发独立任务书，在separate task + explicit authorization前REAL_SEND=FORBIDDEN。
3. 冻结局部顺序为HLV4 → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1；不能以NEXT/PLANNED代替授权。
4. Adapter Stabilization只收敛Host mapping/gaps；P1先冻结Prompt Projection contract，再扩Memory类型，避免倒逼authority、budget/trimming。SP-005A2-P1仍NOT AUTHORIZED，Memory Evolution V1仍PLANNED。
5. Routine、Media、Voice、Relationship与OpenClaw按长期路线依赖逐项授权，不并行大规模改两套Host Adapter。长期Organic Contact / scheduled wake须另立阶段，不直接启用cron。

Full Private RP = BLOCKED_BY_OFFICIAL_HOST_CAPABILITY；H1 = BLOCKED_BY_OFFICIAL_HERMES_HOST_CAPABILITY；H2 = BLOCKED。Living validation与final-output commit边界分离，H1 blocker不阻止只读/lifecycle/fake验证；Living permit不能替代RP授权。

后续每个SP/RFC/ADR/实施/验证任务必须声明 `Roadmap Stage` 与 `Why Now`。不属当前阶段默认NOT AUTHORIZED；任何阶段顺序/重大Runtime/Host优先级/安全边界变更须先改Roadmap、独立架构审核、用户确认，再发布实施任务。不得先实现后补路线。

## 并行的 Private RP capability watchers

- **Hermes**：关注 [NousResearch/hermes-agent PR #120170](https://github.com/NousResearch/hermes-agent/pull/120170)。仅在官方代码出现实际 final-output commit 实现、进入可核验版本后，重做 H1-CAP1 机械验证。实验性 [fork PR #1](https://github.com/y19870785/hermes-agent/pull/1) 维持 Draft 审计证据，fork 路线为 `STOPPED / FORK_ROUTE_TOO_DEEP`，不得作为生产 Host。
- **OpenClaw**：后续 release 只有出现统一 final-output transaction、assistant commit authorization 或 replay/delivery authorization 等实质能力变化，才重跑 H2-CAP0。2026.9.5 已审、2026.9.6 只读比对均未使 Full Private RP 获资格。版本号更新本身不解锁。

恢复 H1/H2 Full Private RP Adapter 的共同门禁是受信 `STABLE_PRINCIPAL`、`STABLE_SESSION`、`MESSAGE_PROVENANCE`、`ISOLATED_CONTEXT_LANE`、`HISTORY_ISOLATION`，以及 fail-closed final-output authorization、late-result fencing、授权前模型流抑制或缓冲。必须在目标 Host 版本与真实执行链证明，不能以 API 名称、模拟测试或 prompt 承诺代替。见 [H0 Host Integration 合同](../architecture/SP-004H-HOST-INTEGRATION.md)。

## 旁线与治理

SP-004L / 后续资产仓库、CharacterDefinition 升级、原始 PNG/avatar/package、历史导入映射继续保留为旁线，不阻塞 SP-005 主线。运行时、Schema 或 Host 接线的变化都要单独审查。

治理流程保持：**Codex 实现并创建 Draft PR → ChatGPT / 小雪独立审核 → 授权 Ready → Ready 后轻量终审 → 仅 Squash Merge → 合并后核 canonical main SHA + exact main push CI 四矩阵全绿 → DONE**。Codex 本地 PASS 或 Draft PR CI PASS 不等于独立审核 PASS；Draft PR 不得自动转 Ready，Ready 必须得到 ChatGPT / 小雪明确授权。Ready 后轻量终审还须确认 Head 未发生未经审核的变化。PR 合并成功本身不等于 DONE：取得新的 canonical main SHA，并核验由该 exact SHA 触发的 Ubuntu / Windows × Python 3.11 / 3.12 四矩阵 main push CI 全部成功后，才可标记 DONE。Host 沙箱通过也不自动满足 Full Private RP 门禁。
