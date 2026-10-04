# SP-005A4-HLV4-R0 — Real Living Delivery Authority 合同

## CURRENT — HLV4-A0 专用 Hermes Adapter 边界冻结（2026-10-04）

R0 / R1 = DONE；R1 canonical main `0b733908ffdef059a43428af42f3b3cb83a9850e`。HLV4-A built-in Discord path = REJECTED：Hermes 0.21.3 `DiscordAdapter.send()` 的 override、split、fallback 与 retry 行为不能作为 REAL_CONTACT 最终边界。新的 [Dedicated Hermes Delivery Adapter 合同](SP-005A4-HLV4-DEDICATED-HERMES-DELIVERY-ADAPTER.md)规定独立 `life_engine_discord` 平台、generic `send()` 硬拒绝和专用受信入口；dedicated plugin route = ARCHITECTURE_FREEZE_PENDING，待独立审核和后续实现/真实隔离验证。built-in 路径 `HOST_PATCH_REQUIRED = YES`；dedicated plugin 路线条件性 `HOST_PATCH_REQUIRED = NO`。本次 `ARCHITECTURE_CHANGE_REQUIRED = NO`、`ROADMAP_DIRECTION_CHANGE = NO`；HLV4-B = NOT AUTHORIZED，REAL_SEND = NO，REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED。本文旧阶段快照保留历史含义。

## HISTORICAL — R1 实施状态（2026-10-04）

R0 = DONE / FROZEN；canonical main `88e699ca34cab463cd65be61edfdf61522b8952a`，PR #41 Squash Merge，exact main push CI #37175172979 四矩阵 SUCCESS，已经独立核验。R1 = IMPLEMENTED / DRAFT_REVIEW_PENDING；[R1本地验证报告](../validation/SP-005A4-HLV4-R1-REAL-DELIVERY-AUTHORITY.md)记录typed authority、one-shot grant、双consumer、本地intercept及crash/recovery证据。HLV4-A仍BLOCKED，待R1 canonical DONE和重新授权；HLV4-B NOT AUTHORIZED。Runtime目前无真实Host transport mapping；REAL_SEND=NO。下文R0原文是冻结目标合同和当时状态快照，R1实施不改变原设计史。

## HISTORICAL — R0 原始冻结合同

## 问题与冻结基线

任务 Base：`71063c189ba2de501acdadca61e212e1cfc722a4`。GOV-ARCHGATE1 已 canonical DONE；HLV0～HLV3 DONE，REAL_HOST_DRY_RUN_PASS CONFIRMED。R0 = DRAFT_REVIEW_PENDING；本文为待独立审核的合同冻结，不是已经部署的能力。Implementation / Runtime / Schema / Prompt / Hermes Patch / Host Operation / Real Inbound / Real Send = NO。

HLV4-A = BLOCKED_BY_FROZEN_AUTHORITY_CONTRACT；ARCHITECTURE_CHANGE_REQUIRED = YES；HOST_PATCH_REQUIRED = NO。根因是现有 A3 `BindingAuthority._issue_permit` 固定 `SIMULATED_CONTACT`，Facade 对 non-isolated authority 拒绝 `NO_REAL_SEND`；[HLV0](SP-005A4-HERMES-LIVING-VALIDATION.md)禁止翻转开关或改 purpose 绕过。该 authority contract 缺口已路由到 R0，不是 Hermes capability blocker。本文不修改现有代码，也不把原模拟 permit 升级成现实用途。

## Authority 模型与真源

Real delivery 是显式、正向、默认拒绝的 authority state，不是 SIMULATED_CONTACT 加关闭安全开关。仍使用同一 ExecutionPermit 抽象，不新增第二套可交给 consumer 的授权 token；grant 是可信 policy 内部资格，不能直接执行 transport。

| 字段或事实 | 真源与责任 | 生命周期与保存边界 |
| --- | --- | --- |
| Intent、Attempt CLAIMED、execute、Core generation、enabled/paused、WorldRevision、WriterEpoch | Core；Host policy 不决定 quota、reservation 或 Attempt truth | 既有 Core durable truth，Schema 8 不变 |
| install、profile/agent、owner、platform、server/channel、process lifecycle | 受保护 registry 与可信 Host projection；模型/显示名/last route 不可信 | 可持久保存身份配置；不是执行资格 |
| Binding identity、mode、authority epoch、adapter/plugin epoch、当前 lifecycle | Binding Authority 验证 Host 投影并管理撤销 | 当前执行状态与 epochs 在内存；持久部署配置不重建授权 |
| purpose、exact target、Attempt、invocation、generation、expiry、once、payload digest | permit claims；由可信 binding 从 Core 首次成功结果和 policy 构造 | opaque、memory-only，不写日志/DB/model/transcript |
| RealDeliveryPolicy、OneShotRealDeliveryGrant | 可信部署管理面；不成为 Core 业务 authority | policy 配置可持久；当前 grant、消费额度及 permit 不持久 |

## Binding Mode 与 Execution Purpose

定义 typed `BindingMode.SIMULATION` / `BindingMode.REAL_DELIVERY`，与既有 LEGACY / LIVING_PENDING / LIVING_ACTIVE routing state 正交；执行仍须 LIVING_ACTIVE。定义 typed `ExecutionPurpose.SIMULATED_CONTACT` / `ExecutionPurpose.REAL_CONTACT`，严格相等比较，未知值拒绝。

SIMULATION 只能签 simulated permit，REAL_DELIVERY 只能在显式 RealDeliveryPolicy ALLOW 后签 real permit。mode 本身不是 ALLOW；禁止通过 `isolated_test=false` 或 `NO_REAL_SEND=false` 推导现实权限。mode/policy/target 变更必须进入受信 lifecycle barrier，撤销旧 grant/permit，不能 reinterpret 已签 claims。

## RealDeliveryPolicy

Host-neutral policy 接受不可由调用方覆盖的 typed DeliveryContext：binding identity、authority epoch、adapter/plugin epoch、Core generation、exact target、Intent/Attempt、invocation、REAL_CONTACT purpose、current lifecycle、session/world 授权与 payload digest。仅输出 ALLOW / DENY。默认、缺字段、异常、未知 policy 或目标歧义均 DENY；不得 fallback 到 simulated 或另一 target。

policy 判断“此 binding 是否具备签发这个 exact context 的资格”，不判断 Core quota，不代替执行 revalidation。policy evaluation 与 grant reservation/permit issuance 在同一 Binding Authority barrier 中排序；ALLOW 不作为可序列化执行凭证。可信部署 factory 才能安装 policy；普通 BindingAuthority、model、prompt、工具参数不能启用 REAL_DELIVERY 或签 grant。

## Validation One-Shot Grant

`OneShotRealDeliveryGrant` 是 HLV4-B 的窄 policy realization：memory-only、non-transferable、short-lived（实现须设固定上限，验证建议不超过60秒）、绑定 authority/adapter epochs、generation、REAL_CONTACT、exact target、exact Intent/Attempt/invocation 与 text payload digest。没有 wildcard target 或任意后续 Attempt。

在 Core commit 前可由可信管理面设定 exact Intent/invocation 约束；首次 CLAIMED 响应后仅能绑定该 Intent 的 Core 返回 Attempt，不能由 caller指定替代 Attempt。grant 状态 UNBOUND → RESERVED → SPENT / REVOKED；RESERVED 只能关联一枚 permit。并发 reserve/issuance 必须原子；permit issue 失败、expiry、crash、deny 或 intercept 后额度均不退还，不重签。grant 不能直接调用 consumer，不能跨 authority、进程或 generation 传递。

固定预算为 1 Intent、1 Attempt、1 invocation、1 permit、1 exact target、1 text payload、最多1 transport invocation。HLV4-B 显式授权前不得创建 grant。该机制不是未来生产每条消息需人工审批的业务模型；未来 deployed policy 可在明确 enrollment/部署 policy 下提供受控 REAL_CONTACT，但 Routine/Proactive policy 本任务不实现、不授权、不提前冻结。

## Permit 签发与 Claims

顺序保持：Core begin_attempt → durable CLAIMED commit → Core transaction ends → 首次 execute=true → policy qualification → permit issue。Core begin_attempt 自身必须按现有规则先校验 current World/Scope/Session/WriterEpoch/WorldRevision，再处理 receipt 与 mutation；policy 不绕过 replay fence。可先拒绝无资格的执行请求，但不能先签 permit 或替代 Core CLAIMED。

policy 必须在签发时重验。若 commit 后 policy DENY/exception，Attempt 仍 CLAIMED，返回无 permit 并进入 reconciliation；不能补签、再 claim 或从历史结果重建执行资格。同 invocation replay execute=false，无新 permit。

permit 至少 seal 绑定 binding identity、authority epoch、adapter/plugin epoch、Core generation、Intent/Attempt、invocation、exact typed target、execution purpose、payload digest、expiry、single-use handle。expiry 不晚于 grant expiry；沿用短寿命原则，建议现有10秒上限。claims 不接受 model/Prompt/tool JSON；opaque handle 不序列化，不保存 raw permit，不将 digest 当可消费 token。

## Consumer Boundary 与 Final Delivery Guard

分别定义 SimulationConsumer 和 RealDeliveryConsumer；两者共享底层 vault 实现可以，但外部不可暴露 generic consume(any permit) 后由 caller选择网络的接口。SimulationConsumer 只接受 SIMULATED_CONTACT，RealDeliveryConsumer 只接受 REAL_CONTACT；双向 purpose mismatch REJECT。真实 consumer 绑定唯一 transport dependency，没有 generic router、retry ledger、fallback send 或 fan-out。

RealDeliveryConsumer 的唯一 final guard 在不可逆副作用前按受信 context 检查：REAL_DELIVERY / LIVING_ACTIVE mode、当前 authority、adapter/plugin epoch、current Core generation、exact owner/profile/agent/platform/server/channel、Attempt/invocation/purpose/payload、permit expiry/unused、Core enabled/paused、适用 session/world/WriterEpoch fences。缺少 session 且合同要求 session 时拒绝，不能以“不适用”跳过。

在同一执行 admission barrier 中完成 current checks 与原子 consume；最后 generation barrier 保留。消费后立即进入单个 transport 调用，不 await arbitrary work、不入 queue、不 split、不 reply fallback、不 thread override、不 forum auto-thread。trusted lifecycle transition 与最终 admission 必须有明确线性化顺序；transition 先则拒绝，admission 先则只允许已经 admitted 的一次调用。Core DB transaction 在 transport 前结束，Core management/install DB 锁不得跨网络；Binding execution admission barrier 的生命周期协调不等于 DB/network 原子事务。

adapter/guard exception 一律终止，不 fallback。consume 后未发送或结果丢失不恢复 permit，不退 grant；transport 已开始后异常属于不确定结果，协调而不自动 resend。无法在 frozen fences 下提供该排序则 STOP 独立审架构，不能只靠 precheck 宣称安全。

## Target Authority 与 Payload

TrustedDeliveryTarget 由 protected registry 和 authenticated Host identity 投影，typed 包含 provider/platform、server/guild、channel、owner、profile/agent 与 binding identity；Core target 与完整投影必须一一对应，canonical digest 包含全部安全字段，缺字段/歧义/不一致拒绝。禁止 default/last route、metadata override、prompt/model/message/display-name target。credentials 仅由 Host transport boundary 持有，不进 Core、permit、journal、exception 或测试 snapshot。

HLV4-B payload 仅固定、无敏感信息的单条文本；无 mention/command、attachment/image/audio/embed、reply/thread、markdown dependency。exact digest 在 grant、permit、guard 三处一致；模型不能替换文本。

## Lifecycle、Crash 与 Recovery

| 事件或 crash 点 | 执行权限结果 | durable knowledge |
| --- | --- | --- |
| CLAIMED 后 permit 前 crash | 无 permit，不能补签 | B1 可恢复 COMMITTED/CLAIMED |
| permit 后 guard 前、guard 后 consume 前 crash | 内存 permit/grant 丢失；restart 全拒绝 | reconciliation，无 send authorization |
| consume 后 pre-send intercept crash | permit/grant 已花费；无发送、无额度退还 | CLAIMED 不冒充 SENT |
| transport 后 result/record_delivery 丢失 | 不自动重发，不重建 permit | UNKNOWN 或 frozen Core允许的 CLAIMED + reconciliation；另行验证，不在R0执行 |
| authority restart、mode/policy/target transition | 撤销旧 grant/permit，fresh epoch | persistent route/session不授予权限 |
| adapter/plugin replacement | 撤销关联 capability/grant/permit | 无自动发送恢复 |
| Core generation transition | 旧 grant/permit stale | 既有恢复合同保持，不重置业务预算 |

B1 `recover_operation` 只恢复 knowledge/association，无 execute、无 REAL_CONTACT permit、无 grant restore、无 resend。COMMITTED 或历史 CLAIMED 永远不是执行授权；fresh authority 不能重建任何旧内存资格。persistent session/target/deployment policy 不恢复 outstanding grant。

## DeliveryEvidence 与 ACK

CLAIMED != SENT != ACKNOWLEDGED；DB transaction != network transaction。real permit、consume、transport invocation、pre-send intercept 均不是 SENT。后续 Host adapter须基于受信 provider result、exact channel/message identity、provider timestamp、transport return state 与 Attempt关联，通过独立 validator建立 DeliveryEvidence(SENT)，不能沿用 FakeEvidenceValidator 冒充真实结果。R0 不降低既有 DeliveryEvidence authority，不定义新的 Core delivery状态。

ACK_VALIDATOR = HOST_GAP；provider message ID、API success、CLI rc=0、manual boolean、model statement 均不是 ACK。REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED。

## NO_REAL_SEND 迁移与 isolated_test 分离

R0 保持当前 NO_REAL_SEND=True 和既有代码。R1 独立授权后采取兼容迁移：缺省 factory 仍是 SIMULATION + deny-real policy，原 isolated simulated调用与结果保持；真实 consumer 只可由显式可信 deployment factory配置 REAL_DELIVERY + RealDeliveryPolicy + typed REAL_CONTACT。不能删除或翻转全局开关作为资格；保留兼容标识也不让该布尔值参与 ALLOW推导。

EnvironmentIsolation、ExecutionPurpose、RealDeliveryAuthorization 分离。isolated_test 仅表示测试安装/fixture环境，不决定purpose或网络权限。隔离 Test Host + REAL_CONTACT是可表示组合，但只有独立real policy与后续授权才能执行；非隔离环境绝不隐式获得REAL_CONTACT。

现有 A3/HLV3 SIMULATED_CONTACT测试、B1 recovery、Session World Revision Fence必须维持既有行为与拒绝值；新增typed purpose可在边界兼容旧模拟调用，不能把旧字符串映射成real。无需新 Core durable truth：grant/permit属于 Binding内存，部署配置留受保护binding层；DATA_SCHEMA=8、SP-005A-living-runtime-v1、SP-004K-prompt-v1不变。

## Host-neutral Mapping 与安全不变量

Life Engine定义authority/policy/consumer合同；Hermes Adapter只投影trusted identity/target/lifecycle、唯一transport及provider evidence；OpenClaw以后独立映射，不新增DiscordRealPermit/HermesRealPermit。Host差异不得污染World/Memory/Story/Living Core。Living Real Delivery Authority != Full Private RP final-output commit authority；H1/H2/Full Private RP仍 BLOCKED_BY_OFFICIAL_HOST_CAPABILITY。

安全不变量：default deny；no implicit real mode；no bool-flip authorization；no simulated→real promotion；no real→simulation消费；no recovery→permit；no session→authority；no last-route/fallback target；no model/prompt-issued grant；no serialized raw permit；no persisted reusable grant；no cross-authority/epoch/generation复用；uncertainty => no side effect。

## R1 / HLV4-A 未来验收映射

以下均为 DESIGN_ONLY / NOT_EXECUTED，不是本轮测试结果。所有并发测试须使用 barrier/event，关键crash须fresh process + os._exit；不得用sleep race或普通exception代替。

| 合同 | R1未来实现验收 | HLV4-A未来Host边界验收 |
| --- | --- | --- |
| default deny、typed mode/purpose | 普通authority、缺policy、异常policy、bool flip均拒绝；real/sim双向错consumer拒绝 | 无grant不得抵达transport；provider配置歧义拒绝 |
| one-shot budget | 并发reserve/claim/issue/consume最多一枚permit及一次消费；deny/expiry不退grant | replay/expired/wrong Attempt/invocation/target/purpose均拒绝 |
| current fences | world/writer/generation/paused/enabled与receipt顺序回归；管理transition两种线性化顺序 | wrong owner/server/channel/profile/agent、old lifecycle全部拒绝 |
| crash/recovery | CLAIMED→permit前、permit→guard前、guard→consume前、consume→intercept后crash均无可恢复权限 | 对应H4A-CR01～04，真实Gateway restart拒旧permit/capability；persistent session不授权 |
| transport isolation | typed consumer唯一dependency，不允许generic dispatch/retry/fallback | dependency/code-path与instrumentation至少两类证据，thread/forum/split/reply/default/last-route/ledger全不可达 |
| evidence separation | permit/consume/intercept不投影SENT，fake validator不能签real结果 | 零真实transport invocation/network send/provider message creation；SENT仅冻结candidate |
| compatibility | 原A3/HLV3/B1全部回归通过，Schema/Prompt固定 | 不重写HLV1～3历史证据、不冒充ACK或Full Private RP |

## 后续 Scope、One-Shot Send Gate 与 STOP

LOCAL_ORDER = HLV4-R0 → HLV4-R1 → HLV4-A → HLV4-B → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1。ROADMAP_DIRECTION_CHANGE=NO，这是HLV4内部修订。R1、HLV4-A retry、HLV4-B均 NOT AUTHORIZED；R0经Draft/Ready/Squash/canonical/exact main CI/独立核验DONE后，仍须单独授权R1。

R1 future scope：实现typed mode/purpose、default-deny policy、one-shot grant生命周期、typed consumers、final fences与兼容/并发/恢复测试；不接真实Host、不发送，不能顺手改Core/schema/Prompt/B1。HLV4-A future scope：R1 canonical DONE并另行授权后，用真实隔离Host mapping与pre-send intercept验证final边界、零transport invocation、fallback不可达、crash/restart；最高 REAL_HOST_DELIVERY_BOUNDARY_PASS，不是SENT。

HLV4-B future Send Gate：HLV4-A canonical DONE + 独立明确real-send授权 + exact受保护Home/Profile/Agent/provider/owner/server/channel来源 + exact transport/consumer/guard + payload/evidence合同 + retry/fallback隔离 + credential/lifecycle核验 + 当前one-shot grant。grant安装只能在此Gate通过后；一次发送最多取得REAL_HOST_SENT，不取得ACK。SEND_GATE_INPUT不是发送授权。

非目标：Runtime/tests/migrations/workflow/Host patch/Host操作/permit或transport执行、R1实施、Prompt升级、Routine policy、Adapter Stabilization、P1、Memory Evolution、OpenClaw、Full Private RP。

STOP：若需要新Core truth/Schema 9则 SCHEMA_CHANGE_REQUIRED，不设计migration；Prompt更改则 PROMPT_CHANGE_REQUIRED；无法兼容HLV3/A3/B1/World fence则 ARCHITECTURE_CHANGE_TOO_DEEP；必须改Intent/Attempt/recovery/delivery真源或无法最终排序则独立架构审查；需要patch Hermes则 HOST_PATCH_REQUIRED。不得以harness绕过。本文冻结目标合同，不宣布R0 DONE、HLV4-A PASS、HLV4 DONE或真实发送权限。
