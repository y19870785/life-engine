# Life Engine 后续开发路线 — 2026-09

## 当前判断

当前事实基线：`f83d36c76fea6de1a31b449535d5df6cea3909b5`（PR #32 squash commit）。SP-004 Core、A0/A1/A2、A2-R1、B0、B1 Architecture / Implementation 均 DONE；[B1 合并与 exact main push CI](../SP-005A3-B1-VALIDATION.md)四矩阵通过。B1 只补齐 durable operation 的受信只读查询，不实现 Host authority、capability、facade 或执行资格。完整 A3 仍 BLOCKED，等待基于新 canonical main 的剩余实施授权。

2026-09-30 Hermes 0.21.3 受控评测属于[历史快照](../validation/HERMES-COMPREHENSIVE-EVALUATION-2026-09-30.md)：上一轮一次受控文字发送的证据与当轮 Organic Contact 静默判定（当轮新发 0 条），不代表当前 Living Host 链路完成或 ACK 验证通过。Hermes / OpenClaw 真实 Host 验收仍 PENDING_REAL_HOST_VALIDATION。

Full Private RP 仍被 Host capability 阻塞：Hermes 官方实现尚未提供已验证的 final-output commit / session incarnation 合同；OpenClaw CAP0/CAP1 也没有找到可组成一次 fail-closed 授权的插件边界。已有 World/Roleplay Runtime 与生产 Host 私密 RP 是两件事。路线中任何阶段都不自动解锁 H1/H2 Adapter。

## 主线阶段

| 顺序 | 阶段 | 当前状态 | 目标与验收边界 |
| --- | --- | --- | --- |
| 1 | **GOV-DOC2** 当前状态、Host 沙箱指南与路线校准 | **DONE** | README、验证与已知问题同 canonical main 对齐；明确可测/不可测；提供[Host 沙箱指南](../HOST-SANDBOX-TESTING.md)。 |
| 2 | **SP-005H0 Host Integration Sandbox** | 实现 DONE；真实验证 PENDING_REAL_HOST_VALIDATION | 同一 canonical Life Engine 分别接真实 Hermes / OpenClaw，仅 Soul Continuity 与 sandbox-safe 功能。记录真实 Host version、插件加载、唯一 instance binding、错误 Profile/Agent 拒绝、重启恢复、status/wake/photo、本人受控聊天、实际发送与 receipt 区别、upgrade/reload 后重验。**不包含** Full Private RP、Host Core patch、Hermes/OpenClaw fork。 |
| 3 | **SP-005A0 Living Runtime Architecture** | **DONE；R1 DONE** | [冻结架构](../architecture/SP-005A-LIVING-RUNTIME.md)及[当前状态审计](../architecture/SP-005A-CURRENT-STATE-AUDIT.md)已合并；R1 仅澄清 Intent 预留与 Attempt 重验；冻结 time context、daily activity、location/weather/holiday context、主动联系和照片/语音计划、持久 schedule state、restart recovery 的真源与边界。它应是持久 domain/runtime，**不是 cron 脚本集合**。 |
| 4 | **SP-005A1 Living Runtime** | **DONE** | [A1 测试矩阵](SP-005A1-TEST-MATRIX.md)及 [48 项实施映射](../SP-005A1-VALIDATION.md)已完成独立审核及 exact main push CI；已实现 daily state、contact opportunities、cooldown、quiet hours、daypart、独立 LivingContextSnapshot 与 schedule recovery；Host 负责唤醒/发送，Life Engine 保留规则与状态真源。 |
| 5 | **SP-005A2 Living Runtime Host Binding Architecture** | **DONE** | [现状审计](../architecture/SP-005A2-CURRENT-HOST-BINDING-AUDIT.md)、[分层合同](../architecture/SP-005A2-LIVING-HOST-BINDING.md)与[未来测试矩阵](SP-005A3-HOST-BINDING-TEST-MATRIX.md)；只做文档，不接真实 Host。 |
| 6 | **SP-005A3 Living Host Binding Implementation** | **BLOCKED** | 候选 facade/token/tick/context query/prepare/claim/证据接口与 legacy fence；默认 DRY_RUN / NO_REAL_SEND；Prompt 正式接入须另审模板升级。 |
| 7 | **SP-005M Media Runtime** | NOT_EXECUTED | ComfyUI job、image identity、同日视觉连续性、媒体 receipt 与 retry semantics；区分“生成”“发送”“确认送达”。 |
| 8 | **SP-005V Voice** | NOT_EXECUTED | voice message、TTS provider abstraction、voice identity 与 delivery receipt，单独验证语音生命周期。 |

SP-005H0 的实现合并不等于真实 Host 验收：Hermes / OpenClaw 均保持 `PENDING_REAL_HOST_VALIDATION`。A0 是 Core 架构阶段，不依赖真实 Host PASS，也不宣称 Host 集成完成。A0/R1 已冻结架构；A1 经单独授权实施 Schema 8，Prompt v1 不变，自动迁移不等于 Living enrollment。

SP-005A2-R1 = DONE；SP-005A3-B0 = DONE；SP-005A3-B1 Architecture = DONE；SP-005A3-B1 Implementation = DONE。B0 的 [Session fence 与 receipt replay](../SP-005A3-B0-VALIDATION.md)和 B1 的 [只读 recovery](../SP-005A3-B1-VALIDATION.md)分别保留，不把 B06/B28/B14 Core 子集或 B1-08/B1-09 Core 子集升级成完整 Host PASS。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = NOT AUTHORIZED。A3 v2 保持冻结；未来默认从届时 canonical main 新建 v3，但名称、范围、B2/B3 等拆分均须后续任务书决定，本路线不创建开发任务。

## B1 后剩余工作的依赖顺序

1. **A3 Host Binding 剩余实现：BLOCKED**。需新授权；完成 trusted identity/session 映射、authority/capability、ticket/permit、完整副作用前 legacy fence、delivery evidence 接口、模拟 transport 和 B01–B34。Core truth 不迁移到 authority metadata。
2. **隔离真实 Hermes Gateway 验证：PENDING_REAL_HOST_VALIDATION**。在 A3 自动验收后另行授权，验证 live hook、独立 Gateway restart、owner/target 隔离、generation/revision/ticket 重验；历史 legacy 实测不能代替。OpenClaw 亦需单独真实验证。
3. **可信 receipt / delivery evidence：NOT_EXECUTED**。真实 provider validator 须独立设计与授权；当前 ACK validator 缺失。不能仅凭 message ID 或 API 回读消除 UNKNOWN。
4. **长期 Organic Contact 沙箱：BLOCKED**。先完成受控执行与 receipt policy 的验收；当前 B1 本身不足以启动。将来按 manual wake → isolated scheduled wake → organic contact → restart/recovery → multi-day observation 分段授权。每步均需 contact budget、cooldown、quiet hours、owner/target isolation、duplicate prevention、receipt policy 和停止条件；不直接进入生产，不自动启用 cron。
5. **ComfyUI 真实媒体闭环 / Voice：NOT_EXECUTED**。另立 Runtime 与真实环境任务，区分 job、生成、媒体发送和送达；文字链路通过不自动升级媒体能力。

Full Private RP 是独立的 Host capability 路线，继续 BLOCKED，不由上述进度自动解锁。B1 DONE ≠ A3 DONE；A3 DONE 也不等于 P1、H1/H2 或生产验收完成。Memory consolidation、dedupe、conflict/overwrite、importance/decay、controlled forgetting 等后续演进不在本轮实现。

## 并行的 Private RP capability watchers

- **Hermes**：关注 [NousResearch/hermes-agent PR #120170](https://github.com/NousResearch/hermes-agent/pull/120170)。仅在官方代码出现实际 final-output commit 实现、进入可核验版本后，重做 H1-CAP1 机械验证。实验性 [fork PR #1](https://github.com/y19870785/hermes-agent/pull/1) 维持 Draft 审计证据，fork 路线为 `STOPPED / FORK_ROUTE_TOO_DEEP`，不得作为生产 Host。
- **OpenClaw**：后续 release 只有出现统一 final-output transaction、assistant commit authorization 或 replay/delivery authorization 等实质能力变化，才重跑 H2-CAP0。2026.9.5 已审、2026.9.6 只读比对均未使 Full Private RP 获资格。版本号更新本身不解锁。

恢复 H1/H2 Full Private RP Adapter 的共同门禁是受信 `STABLE_PRINCIPAL`、`STABLE_SESSION`、`MESSAGE_PROVENANCE`、`ISOLATED_CONTEXT_LANE`、`HISTORY_ISOLATION`，以及 fail-closed final-output authorization、late-result fencing、授权前模型流抑制或缓冲。必须在目标 Host 版本与真实执行链证明，不能以 API 名称、模拟测试或 prompt 承诺代替。见 [H0 Host Integration 合同](../architecture/SP-004H-HOST-INTEGRATION.md)。

## 旁线与治理

SP-004L / 后续资产仓库、CharacterDefinition 升级、原始 PNG/avatar/package、历史导入映射继续保留为旁线，不阻塞 SP-005 主线。运行时、Schema 或 Host 接线的变化都要单独审查。

治理流程保持：**Codex 实现并创建 Draft PR → ChatGPT / 小雪独立审核 → 授权 Ready → Ready 后轻量终审 → 仅 Squash Merge → 合并后核 canonical main SHA + exact main push CI 四矩阵全绿 → DONE**。Codex 本地 PASS 或 Draft PR CI PASS 不等于独立审核 PASS；Draft PR 不得自动转 Ready，Ready 必须得到 ChatGPT / 小雪明确授权。Ready 后轻量终审还须确认 Head 未发生未经审核的变化。PR 合并成功本身不等于 DONE：取得新的 canonical main SHA，并核验由该 exact SHA 触发的 Ubuntu / Windows × Python 3.11 / 3.12 四矩阵 main push CI 全部成功后，才可标记 DONE。Host 沙箱通过也不自动满足 Full Private RP 门禁。
