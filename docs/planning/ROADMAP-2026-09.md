# Life Engine 后续开发路线 — 2026-09

## 当前判断

固定事实基线：B0 固定 Base / canonical main `3367a8906060af129d7ee29ef4da7959926b5d0b`；A1 Core 已 DONE，`DATA_SCHEMA = 8`。SP-004 已完成 World → Memory → Lore → Story → Bridge → Prompt Core Runtime 和 H0 Host Integration Contract。Session World Revision Fence 架构修订已 DONE，B0 最小 Core 修复待独立审核；Living Host Binding 主实现保持阻塞；真实 Host Sandbox 仍需独立授权与验证。完整进度见 [SP-004 当前快照](SP-004-IMPLEMENTATION-PLAN.md#2026-09-26-当前状态快照)。

Full Private RP 仍被 Host capability 阻塞：Hermes 官方实现尚未提供已验证的 final-output commit / session incarnation 合同；OpenClaw CAP0/CAP1 也没有找到可组成一次 fail-closed 授权的插件边界。已有 World/Roleplay Runtime 与生产 Host 私密 RP 是两件事。路线中任何阶段都不自动解锁 H1/H2 Adapter。

## 主线阶段

| 顺序 | 阶段 | 当前状态 | 目标与验收边界 |
| --- | --- | --- | --- |
| 1 | **GOV-DOC2** 当前状态、Host 沙箱指南与路线校准 | **DONE** | README、验证与已知问题同 canonical main 对齐；明确可测/不可测；提供[Host 沙箱指南](../HOST-SANDBOX-TESTING.md)。 |
| 2 | **SP-005H0 Host Integration Sandbox** | implementation DONE；真实验证 PENDING | 同一 canonical Life Engine 分别接真实 Hermes / OpenClaw，仅 Soul Continuity 与 sandbox-safe 功能。记录真实 Host version、插件加载、唯一 instance binding、错误 Profile/Agent 拒绝、重启恢复、status/wake/photo、本人受控聊天、实际发送与 receipt 区别、upgrade/reload 后重验。**不包含** Full Private RP、Host Core patch、Hermes/OpenClaw fork。 |
| 3 | **SP-005A0 Living Runtime Architecture** | **DONE；R1 DONE** | [冻结架构](../architecture/SP-005A-LIVING-RUNTIME.md)及[当前状态审计](../architecture/SP-005A-CURRENT-STATE-AUDIT.md)已合并；R1 仅澄清 Intent 预留与 Attempt 重验；冻结 time context、daily activity、location/weather/holiday context、主动联系和照片/语音计划、持久 schedule state、restart recovery 的真源与边界。它应是持久 domain/runtime，**不是 cron 脚本集合**。 |
| 4 | **SP-005A1 Living Runtime** | **DONE** | [A1 测试矩阵](SP-005A1-TEST-MATRIX.md)及 [48 项实施映射](../SP-005A1-VALIDATION.md)已完成独立审核及 exact main push CI；已实现 daily state、contact opportunities、cooldown、quiet hours、daypart、独立 LivingContextSnapshot 与 schedule recovery；Host 负责唤醒/发送，Life Engine 保留规则与状态真源。 |
| 5 | **SP-005A2 Living Runtime Host Binding Architecture** | **DONE** | [现状审计](../architecture/SP-005A2-CURRENT-HOST-BINDING-AUDIT.md)、[分层合同](../architecture/SP-005A2-LIVING-HOST-BINDING.md)与[未来测试矩阵](SP-005A3-HOST-BINDING-TEST-MATRIX.md)；只做文档，不接真实 Host。 |
| 6 | **SP-005A3 Living Host Binding Implementation** | **BLOCKED_BY_B0** | 候选 facade/token/tick/context query/prepare/claim/证据接口与 legacy fence；默认 DRY_RUN / NO_REAL_SEND；Prompt 正式接入须另审模板升级。 |
| 7 | **SP-005M Media Runtime** | PROPOSED | ComfyUI job、image identity、同日视觉连续性、媒体 receipt 与 retry semantics；区分“生成”“发送”“确认送达”。 |
| 8 | **SP-005V Voice** | PROPOSED | voice message、TTS provider abstraction、voice identity 与 delivery receipt，单独验证语音生命周期。 |

SP-005H0 的实现合并不等于真实 Host 验收：Hermes / OpenClaw 均保持 `PENDING_REAL_HOST_VALIDATION`。A0 是 Core 架构阶段，不依赖真实 Host PASS，也不宣称 Host 集成完成。A0/R1 已冻结架构；A1 经单独授权实施 Schema 8，Prompt v1 不变，自动迁移不等于 Living enrollment。

SP-005A2-R1 = DONE；SP-005A3-B0 = PENDING_INDEPENDENT_REVIEW。[B0 实施映射](../SP-005A3-B0-VALIDATION.md)记录 `_authorize` 最小修复、R1-01～R1-06 与 B06/B28/B14 Core 子集验证；不代表 A3 Host 层完成。SP-005A3 = BLOCKED_BY_B0，本轮完成 Draft 后停止，不恢复 A3 主实现。DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = NOT AUTHORIZED。

建议顺序：`GOV-DOC2 → SP-005H0 → SP-005A0 → SP-005A1 → SP-005A2 → SP-005A2-R1 → SP-005A3-B0（待独立审核）→ SP-005A3（B0 完成后恢复）→ SP-005M → SP-005V`。每个 PROPOSED 阶段仍需独立任务书、固定 Base、验收与授权；本路线不构成自动实现队列。

## 并行的 Private RP capability watchers

- **Hermes**：关注 [NousResearch/hermes-agent PR #120170](https://github.com/NousResearch/hermes-agent/pull/120170)。仅在官方代码出现实际 final-output commit 实现、进入可核验版本后，重做 H1-CAP1 机械验证。实验性 [fork PR #1](https://github.com/y19870785/hermes-agent/pull/1) 维持 Draft 审计证据，fork 路线为 `STOPPED / FORK_ROUTE_TOO_DEEP`，不得作为生产 Host。
- **OpenClaw**：后续 release 只有出现统一 final-output transaction、assistant commit authorization 或 replay/delivery authorization 等实质能力变化，才重跑 H2-CAP0。2026.9.5 已审、2026.9.6 只读比对均未使 Full Private RP 获资格。版本号更新本身不解锁。

恢复 H1/H2 Full Private RP Adapter 的共同门禁是受信 `STABLE_PRINCIPAL`、`STABLE_SESSION`、`MESSAGE_PROVENANCE`、`ISOLATED_CONTEXT_LANE`、`HISTORY_ISOLATION`，以及 fail-closed final-output authorization、late-result fencing、授权前模型流抑制或缓冲。必须在目标 Host 版本与真实执行链证明，不能以 API 名称、模拟测试或 prompt 承诺代替。见 [H0 Host Integration 合同](../architecture/SP-004H-HOST-INTEGRATION.md)。

## 旁线与治理

SP-004L / 后续资产仓库、CharacterDefinition 升级、原始 PNG/avatar/package、历史导入映射继续保留为旁线，不阻塞 SP-005 主线。运行时、Schema 或 Host 接线的变化都要单独审查。

治理流程保持：**Codex 实现并创建 Draft PR → ChatGPT / 小雪独立审核 → 授权 Ready → Ready 后轻量终审 → 仅 Squash Merge → 合并后核 canonical main SHA + exact main push CI 四矩阵全绿 → DONE**。Codex 本地 PASS 或 Draft PR CI PASS 不等于独立审核 PASS；Draft PR 不得自动转 Ready，Ready 必须得到 ChatGPT / 小雪明确授权。Ready 后轻量终审还须确认 Head 未发生未经审核的变化。PR 合并成功本身不等于 DONE：取得新的 canonical main SHA，并核验由该 exact SHA 触发的 Ubuntu / Windows × Python 3.11 / 3.12 四矩阵 main push CI 全部成功后，才可标记 DONE。Host 沙箱通过也不自动满足 Full Private RP 门禁。
