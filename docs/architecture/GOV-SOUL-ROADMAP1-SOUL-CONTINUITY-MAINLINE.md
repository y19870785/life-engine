# GOV-SOUL-ROADMAP1 — Full Private RP 封存与 Soul Continuity 主线

## 决定与依据

GOV-SOUL-ROADMAP1 governance Base = `a552a2d0846ff024b930d0d802228b863a6da74f`。该 SHA 是本治理 PR 开工时的 canonical main，不是合并后的 canonical main。本记录取代 [GOV-ARCHGATE1](GOV-ARCHGATE1-POST-HLV3-REVIEW.md) 确定的后续局部执行顺序。GOV-SOUL-ROADMAP1 是治理与文档任务；本记录不修改 Runtime、Schema、Prompt、Host Adapter 或 provider transport，不授予任何后续实施或真实发送权限。

此前顺序为 A2-R1 → A2 retry → HLV4-B → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1。A2-R1 已完成可审计的本地 provider transport 实现；真实 Host plugin load、delivery boundary、SENT 与 ACK 仍未取得。Full Private RP 仍受官方 Host capability 阻塞。让单一 Host 的边界长期锁住项目主线，已不符合 Life Engine 的核心目标：同一个 Agent 跨会话、重启、关系发展、模型变化与未来 Host 迁移持续生活在同一时间线中。

## 新三轨模型

| 轨道 | 当前治理状态 | 边界 |
| --- | --- | --- |
| Track A — Soul Continuity | `ACTIVE_MAINLINE` | 建立 Host-neutral、Model-neutral、Persistent、Auditable、Recoverable、Fail-closed 的连续性 Runtime；仅下一架构阶段可提案，尚未授权实施 |
| Track B — Host Integration / Real Delivery | `DEFERRED` | 保留 HLV0～HLV3、HLV4-R0/R1/A0/A1/A2-R0/A2-R1 的代码、合同和证据；A2 retry、HLV4-B、Hermes Adapter Stabilization、OpenClaw Living Adapter real validation 均 `NOT AUTHORIZED` |
| Track C — Full Private RP | `FROZEN_EXTERNAL_BLOCKER` | Core RP Runtime 保留；Hermes H1 与 OpenClaw H2 的官方 final-output 授权缺口不因 Living 成果而解除 |

`DEFERRED` 不等于取消；`FROZEN_EXTERNAL_BLOCKER` 不等于失败、放弃或删除。Roadmap state 不构成执行授权。

## Soul Continuity 主线

Soul Continuity 不等于 Prompt Persona。`Soul != Prompt != Model != Session != Host != Character Card != World != Memory`；这些对象参与连续性，但不能单独冒充 Soul Identity。Prompt 只能从当前可信状态派生投影。Soul 也不能取代 Story、Memory 或 World 的真源。

高层顺序为 GOV-SOUL-ROADMAP1 → **SP-006S0 — Soul Continuity Architecture Freeze** → Soul Identity / Continuity Core V1 → Prompt Projection Integration → Memory Evolution V1 → Relationship Memory → Autobiographical Memory → Soul / Relationship Continuity Evolution → Living Integration → Proactive Life / Routine → Media Runtime → Voice Runtime。仅本治理任务获授权；`SP-006S0 = NEXT / NOT AUTHORIZED`，其余阶段均须独立任务与明确授权。

SP-006S0 应定义 SoulIdentity、SoulInstance、SoulContinuityGeneration、Soul lifecycle，以及 Soul 与 World、Agent、Character、Host、Model、Session 的关系；还须给出跨日、跨进程及跨 Host 判断“同一个 Soul”的机械证据。Identity、Session、Memory、Relationship、Autobiographical、World、Living、Prompt Continuity 必须分别建模。本文不预定其实现、Schema 或 authority 变更。

Memory Evolution V1 服务于 Soul Continuity，而非单纯增加记忆数量。长期范围保留 Working、Episodic、Semantic、Relationship、Autobiographical Memory，以及 Consolidation、Deduplication、Conflict Resolution、Supersession、Importance、Decay、Controlled Forgetting。`Memory Evolution V1 = SOUL_CONTINUITY_MAINLINE / PLANNED / NOT AUTHORIZED`。`SP-005A2-P1 = RESEQUENCED_UNDER_SOUL_CONTINUITY_MAINLINE / NOT AUTHORIZED`；Prompt Projection 与 Memory Evolution 的具体接口和顺序留待 SP-006S0 评审。

既有真源继续分立：Lore 是世界设定，Memory 是 Subject 知道或记得什么，Story 是实际发生过什么，Prompt 是派生投影，Bridge 是 World 间受控投影，Living 是主动行为资格，Host Binding 是 Host 执行资格。Original Soul 不得被 Roleplay 覆盖；Soul World 与 RP World 默认隔离，跨 World 默认拒绝，只有显式 Controlled Bridge 可作有界投影。Full Private RP 封存不删除 World、Timeline、Character Instance、Lore、Story、Memory、Bridge 或已完成的 RP Core Runtime。

## Host Integration 延期边界

`SP-005A4-HLV4-A2-R1 = DONE`，canonical implementation 为 `a552a2d0846ff024b930d0d802228b863a6da74f`，来自 [PR #46](https://github.com/y19870785/life-engine/pull/46) 的 Squash Merge。后续若重新激活，应从该成果继续，不能重设计已冻结的 provider transport。真实证据仍为 `REAL_HOST_PLUGIN_LOAD = NOT_ACQUIRED`、`REAL_HOST_DELIVERY_BOUNDARY_PASS = NOT_ACQUIRED`、`REAL_HOST_SENT = NOT_ACQUIRED`、`ACKNOWLEDGED = NOT_ACQUIRED`、`ACK_VALIDATOR = HOST_GAP`、`REAL_SEND = NO`。A2 retry、HLV4-B、Hermes Living Adapter Stabilization、OpenClaw Living Adapter real validation 均 `DEFERRED / NOT AUTHORIZED`。

## Full Private RP 外部阻塞与重新激活

`FULL_PRIVATE_RP = FROZEN_EXTERNAL_BLOCKER`。Hermes：`BLOCKED_BY_OFFICIAL_HERMES_HOST_CAPABILITY`，H1 = BLOCKED。OpenClaw：`BLOCKED_BY_UNIFIED_FINAL_OUTPUT_COMMIT_BOUNDARY`，H2 = BLOCKED。Living REAL_CONTACT 不能替代 final-output commit authority。

只有出现新的官方 Host 能力证据，才可提出重新激活：Hermes 须提供机械可验的 final-output commit boundary 并满足既有 H0/H1 合同；OpenClaw 须提供覆盖首次 assistant 持久化、replay、final delivery、late result 与授权前 streaming 的统一 fail-closed boundary；或新 Host 的官方 extension/plugin API 满足既有 Full Private RP Host Contract。其后仍需新 source audit、架构评审、独立任务与明确授权。Prompt 指令、模型遵从、best-effort hook、legacy send、monkeypatch、private Host API、实验 fork 或未验证 callback 都不能替代这些安全合同。

## A2-R1 最终状态与治理偏差

[Exact main push CI #37297156541](https://github.com/y19870785/life-engine/actions/runs/37297156541) 的 event = `push`、branch = `main`、head SHA = `a552a2d0846ff024b930d0d802228b863a6da74f`；attempt 1 = CANCELLED，attempt 2 = CANCELLED，最终有效 attempt 3 = completed / success，Ubuntu 与 Windows × Python 3.11、3.12 全部 SUCCESS。`SP-005A4-HLV4-A2-R1 = DONE` 是最终技术 Gate，不升级真实 Host 或发送证据。

`CI_RECOVERY_GOVERNANCE_DEVIATION = YES`：attempt 2 再次取消后，依当时授权应 `STOP / REPEATED_CI_CANCELLATION`，但随后继续执行 attempt 3。此偏差必须保留，不以成功 CI 抹去。`CODE_DRIFT = NO`、`CANONICAL_MAIN_DRIFT = NO`、`ARCHITECTURE_DRIFT = NO`、`REAL_HOST_OPERATION = NO`、`REAL_SEND = NO`、`TECHNICAL_EVIDENCE_INVALIDATED = NO`。这里记录已独立确认的历史事实，不把取消视为成功，也不授权补做 Host 验证。

## 不变合同与非授权边界

`DATA_SCHEMA = 8`、`Schema Signature = SP-005A-living-runtime-v1`、`Prompt Template = SP-004K-prompt-v1`、`PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES`。`CLAIMED != SENT != ACKNOWLEDGED`；recovery 只恢复知识，不恢复执行权；UNKNOWN 不自动重发。

本治理任务不实施 SP-006S0、Memory Evolution、P1、A2 retry、HLV4-B 或 Full Private RP，不操作 Host、credential、provider network 或真实发送。Soul Continuity Sandbox 只可在独立授权下受控测试；Full Private RP 不得生产启用。下一步唯一 `NEXT` 是 SP-006S0 的独立架构任务书。
