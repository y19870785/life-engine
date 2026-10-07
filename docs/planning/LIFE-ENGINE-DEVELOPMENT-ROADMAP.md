# Life Engine 长期开发路线与阶段治理

## Soul Continuity Plan V2 — APPROVED_PLANNING_BASELINE / NOT_EXECUTION_AUTHORIZATION

[后续开发计划](SOUL-CONTINUITY-DEVELOPMENT-PLAN.md)保留当前三轨方向，并把顺序细化为 M0 架构冻结 → M1 Soul Identity Core V1 → **M1.x Continuity Proof / Simulation Gate** → M2 Memory Evolution V1 + Read-only Prompt Projection → M3 Relationship + Autobiographical Memory → M4 Soul / Relationship Continuity Evolution + Living Integration → M5 Proactive Life / Routine + Media → M6 Voice + Host Expansion。`M1.x` 是显式门禁，后续实施任务编号仍须独立冻结；[SP-006S0 架构合同](../architecture/SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md)内容状态为 `APPROVED_ARCHITECTURE_BASELINE / NOT_IMPLEMENTATION_AUTHORIZATION`，M1/M1.x/M2 均未获实施授权。

**CURRENT stage override：**`SP-006S0 = DONE`；`M1 = ACTIVE_STAGE`；仅 [M1-P0 Continuity Persistence Protocol Freeze](../architecture/M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md) 获 `AUTHORIZED / PROTOCOL_FREEZE_ONLY`。M1 Schema、Migration、Soul Identity/Continuity Write Path、M1-A 及后续实施，M1.x 与 M2 均 `NOT AUTHORIZED`。M1-P0 的[崩溃矩阵](M1-P0-CRASH-RECOVERY-MATRIX.md)和[实施门禁](M1-P0-IMPLEMENTATION-GATE.md)是设计文档，不是测试 PASS 或执行许可；下文旧状态属于其明确标注的历史快照。

M0 已冻结六种 Continuity、机械 verdict / evidence、离线 Simulation Harness 与 Minimal Prompt Projection Contract；M1.x 必须在大规模 Memory Evolution 前提供 continuation、fork、mismatch、unknown 的可验证边界，`UNKNOWN` 默认 fail-closed。M2 才从可信 Identity、Memory、World 和 Relationship Context 派生只读投影；完整 SP-005A2-P1 不自动前移。首个产品里程碑同时验证身份和记忆连续性，数据库恢复成功不能替代 Soul Continuity PASS。Host 回归只在实质官方能力证据出现后进入独立评审，Full Private RP 继续封存。规划状态仍为 `APPROVED_PLANNING_BASELINE / NOT_EXECUTION_AUTHORIZATION`；本轮仅授权 M1-P0 协议文档，不授权 Runtime。

## HISTORICAL GOVERNANCE SNAPSHOT — GOV-SOUL-ROADMAP1 / Soul Continuity Mainline

[本次治理记录](../architecture/GOV-SOUL-ROADMAP1-SOUL-CONTINUITY-MAINLINE.md)以 GOV-SOUL-ROADMAP1 governance Base `a552a2d0846ff024b930d0d802228b863a6da74f` 开工，正式取代此前 HLV4 后续局部顺序。此段为 `HISTORICAL SNAPSHOT`，记录当时三轨状态：Soul Continuity = `ACTIVE_MAINLINE`；Host Integration / Real Delivery = `DEFERRED`；Full Private RP = `FROZEN_EXTERNAL_BLOCKER`。A2-R1 = DONE；真实 Host plugin load、delivery boundary、SENT、ACK 未取得。下文旧 CURRENT 均为 `SUPERSEDED CURRENT SNAPSHOT`，原技术合同与历史证据保留。

GOV-SOUL-ROADMAP1 冻结时的高层顺序为：GOV-SOUL-ROADMAP1 → **SP-006S0 Soul Continuity Architecture Freeze** → Soul Identity / Continuity Core V1 → Prompt Projection Integration → Memory Evolution V1 → Relationship Memory → Autobiographical Memory → Soul / Relationship Continuity Evolution → Living Integration → Proactive Life / Routine → Media Runtime → Voice Runtime。此处 `HISTORICAL SNAPSHOT` 中的 `SP-006S0 = NEXT / NOT AUTHORIZED` 仅表示当时尚未授权；上方当前架构内容状态已取代该生命周期判断。原治理方向不变；P1 = `RESEQUENCED_UNDER_SOUL_CONTINUITY_MAINLINE / NOT AUTHORIZED`，Memory Evolution V1 = `SOUL_CONTINUITY_MAINLINE / PLANNED / NOT AUTHORIZED`。

A2 retry、HLV4-B、Hermes Living Adapter Stabilization、OpenClaw Living Adapter real validation = `DEFERRED / NOT AUTHORIZED`。Full Private RP 的 H1/H2 外部 Host blocker 保留，但不阻塞 Soul Continuity；RP Core Runtime 不删除。`DATA_SCHEMA = 8`、`Schema Signature = SP-005A-living-runtime-v1`、`Prompt Template = SP-004K-prompt-v1`、`PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES`。Roadmap state != execution authorization。

## HISTORICAL — HLV4-A2-R1 Provider Transport 实施候选（2026-10-05）

A2-R0 = DONE；canonical main `9ebfdebe50bd766c513742267e7bfbdfb1170238`。A2-R1 已获独立实施授权，当前仅建立默认 fail-closed 的 [plugin-owned one-shot provider transport](../architecture/SP-005A4-HLV4-DEDICATED-DISCORD-PROVIDER-TRANSPORT.md)及 fake/inert 测试，待 Draft Review。A2 retry 与 HLV4-B 未授权；`REAL_HOST_DELIVERY_BOUNDARY_PASS / REAL_HOST_SENT / ACKNOWLEDGED = NOT_ACQUIRED`，`ACK_VALIDATOR = HOST_GAP`，`REAL_SEND = NO`。局部顺序仍是 A2-R1 → A2 retry → HLV4-B → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1。下文 A2-R0 CURRENT 为历史阶段快照。

## HISTORICAL — HLV4-A2-R0 Provider Transport 架构候选（2026-10-05）

R0 / R1 / A0 / A1 = DONE；A2 因 `REAL_TRANSPORT_IMPLEMENTATION_REQUIRED` 停止，A1 默认无 provider transport 仍是正确的安全状态。[A2-R0 架构候选](../architecture/SP-005A4-HLV4-DEDICATED-DISCORD-PROVIDER-TRANSPORT.md)仅冻结单次 Discord MESSAGE_CREATE 尝试、SDK retry 隔离与 UNKNOWN / NO RESEND。局部顺序为 A2-R0 → A2-R1 → A2 retry → HLV4-B → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1；后续各阶段均未获执行授权，NEXT 不是授权。`REAL_SEND = NO`，`REAL_HOST_SENT / ACKNOWLEDGED = NOT_ACQUIRED`，`ACK_VALIDATOR = HOST_GAP`。以下 A1 CURRENT 为历史阶段快照。

## HISTORICAL — HLV4-A1 Dedicated Adapter 本地实施（2026-10-04）

R0 / R1 / A0 = DONE；canonical main `337f5f95d47929c0a63c86cf9e2f70a14b9f6ddb`。A1 = IMPLEMENTED / DRAFT_REVIEW_PENDING，见 [A1 验证报告](../validation/SP-005A4-HLV4-A1-DEDICATED-ADAPTER.md)；本地代码/测试最高为 `DEDICATED_ADAPTER_IMPLEMENTATION_PASS`，不等于真实 Host 证据。A2 real Host validation 和 HLV4-B one-shot send 均 NOT AUTHORIZED；REAL_SEND = NO，REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED，ACK_VALIDATOR = HOST_GAP。路线方向不变：A1 → A2 → HLV4-B → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1；NEXT 不等于执行授权。以下 A0 CURRENT 为历史快照。

## HISTORICAL — HLV4-A0 Dedicated Hermes Delivery Adapter（2026-10-04）

R0 / R1 = DONE；canonical main `0b733908ffdef059a43428af42f3b3cb83a9850e`。HLV4-A built-in Discord path = REJECTED；dedicated `life_engine_discord` plugin route = ARCHITECTURE_FREEZE_PENDING。见 [A0 边界合同](../architecture/SP-005A4-HLV4-DEDICATED-HERMES-DELIVERY-ADAPTER.md)：官方 Hermes plugin registry 创建独立平台，generic `send()` 必须硬拒绝，专用入口须受 REAL_CONTACT authority 与最终 guard 约束。built-in 路径需要 Host patch；dedicated plugin 路线条件性无需 Host patch。下一步须先独立审定 A0，再另行授权 HLV4-A runtime 验证；HLV4-B = NOT AUTHORIZED，REAL_SEND = NO。`ARCHITECTURE_CHANGE_REQUIRED = NO`、`ROADMAP_DIRECTION_CHANGE = NO`；REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP。Full Private RP blocker 不变。下文 CURRENT 为当时历史快照。

## HISTORICAL — HLV4-R0 authority 修订（2026-10-04）

当前任务 Base：`71063c189ba2de501acdadca61e212e1cfc722a4`；GOV-ARCHGATE1 已 canonical DONE。HLV0～HLV3 DONE；REAL_HOST_DRY_RUN_PASS CONFIRMED。HLV4-A = BLOCKED_BY_FROZEN_AUTHORITY_CONTRACT；ARCHITECTURE_CHANGE_REQUIRED = YES，已路由到 HLV4-R0；HOST_PATCH_REQUIRED = NO。原因是 A3仅授权SIMULATED_CONTACT；不是Hermes capability blocker。

[Real Delivery Authority合同](../architecture/SP-005A4-HLV4-REAL-DELIVERY-AUTHORITY.md)冻结目标typed mode/purpose、default-deny RealDeliveryPolicy、内存one-shot validation grant与独立real/simulation consumer；R0 = DRAFT_REVIEW_PENDING，现有Runtime仍不具备现实用途。LOCAL_ORDER = HLV4-R0 → HLV4-R1 → HLV4-A → HLV4-B → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1；ROADMAP_DIRECTION_CHANGE = NO。HLV4-R1 / HLV4-A retry / HLV4-B / P1 = NOT AUTHORIZED，Memory Evolution V1 = PLANNED。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP；REAL_SEND = NO。本轮仅文档，无Host/Runtime/schema/Prompt修改；Full Private RP仍 BLOCKED_BY_OFFICIAL_HOST_CAPABILITY。下列旧治理状态为对应阶段历史，技术合同仅由R0目标显式修订部分补充；实现须另行授权，不自动改现有行为。

## HISTORICAL — R0 前治理记录

## 1. 治理地位与当前事实

本路线由 GOV-ROADMAP1 冻结，作为后续 SP / RFC / ADR / Implementation Task / Validation Task 的阶段顺序与 Gate 依据。Roadmap 不是愿望清单；值得做不等于现在授权做。Roadmap Stage 与 Why Now 无法明确回答时，默认 NOT AUTHORIZED。

Roadmap Stage: Post-HLV3 Architecture Review Gate / GOV-ARCHGATE1。
Why Now: HLV0～HLV3 已独立 DONE；GOV-ROADMAP1 预留的 Architecture Review Gate 已完成独立评审，本轮记录结论，不实施下一阶段。

本任务 canonical Base：`9d064d0a90d8d02a5dab04a6baee18bbbf6dcdc2`；PR #39 Squash Merge、唯一 parent `4c9c5aaf9e9ed2995086781e32241abf23436dcb`、exact main push CI #37122681930 四矩阵成功，已经独立核验。SP-005A3 = DONE；SP-005A4-HLV0 / HLV1 / HLV2 / HLV3 = DONE。GOV-ROADMAP1 的原长期方向保留，本轮只解析原预留局部顺序；[Gate证据与决定](../architecture/GOV-ARCHGATE1-POST-HLV3-REVIEW.md)是当前治理记录。

ARCHITECTURE_REVIEW_GATE = PASS；LOCAL_ORDER = HLV4 → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1；ARCHITECTURE_CHANGE_REQUIRED = NO；ROADMAP_DIRECTION_CHANGE = NO。GOV-ARCHGATE1 = DRAFT_REVIEW_PENDING；HLV4 = NEXT / NOT AUTHORIZED，独立任务书与明确授权前 REAL_SEND = FORBIDDEN。Roadmap state != execution authorization。

REAL_HOST_READONLY_PASS / REAL_HOST_LIFECYCLE_PASS / REAL_HOST_LIFECYCLE_AUTHORITY_PASS / REAL_HOST_DRY_RUN_PASS = CONFIRMED；REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP。B01–B34 = SIMULATED_PASS，历史 Core 标签不升级。OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED_BY_OFFICIAL_HOST_CAPABILITY；H1 / H2 blocker 保留。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = AFTER_HERMES_ADAPTER_STABILIZATION / NOT AUTHORIZED；Memory Evolution V1 = AFTER_SP-005A2-P1 / PLANNED。

本轮仅 Docs / Governance：不改 Runtime、Python、tests语义、Schema、数据库、Prompt或workflow，不操作 Hermes/OpenClaw、Bot、cron或Gateway，不重跑历史验证，不执行 Living/permit/fake或real transport。NO_REAL_HOST_OPERATION = true；NO_REAL_SEND = true。当前执行状态见 [ROADMAP-2026-09](ROADMAP-2026-09.md)，冻结技术边界见 [HLV0架构](../architecture/SP-005A4-HERMES-LIVING-VALIDATION.md)及 [HLV矩阵](SP-005A4-HERMES-LIVING-VALIDATION-MATRIX.md)。

## 2. 长期目标

构建可在 Hermes、OpenClaw 等 Host 旁运行的通用 Personal Agent Runtime，让 Agent 跨时间、跨进程重启、跨长期关系持续存在，具有可信世界状态、长期记忆、故事与关系连续性、时间意识、安全主动行为，以及后续照片、语音和生活化表达。目标体验是 Agent 与用户生活在连续的同一时间线中，不在每次会话重新开始。

保持 Host-neutral、Agent-neutral、World-aware、Persistent、Fail-closed、Auditable、Recoverable。Runtime 不硬编码为小雪、Discord、Telegram、Hermes 或 OpenClaw 专用；“小雪”是其中一个 Agent / Soul / World 使用实例，不是 Runtime 本身。Host 差异封装在 Adapter / Binding Layer，共享业务真源和安全合同。

## 3. 当前 Runtime 基线与职责

已形成能力链：World → Memory → Lore → Story → Prompt → Bridge → Living → Host Binding。箭头表达已建立的能力链，不表示可互相写入或替代真源。

| 层 | 职责 / 权威边界 |
| --- | --- |
| World | 世界、Timeline、Subject / Scope 与隔离边界 |
| Memory | Subject 知道 / 记得什么；受World与可见范围约束 |
| Lore | 世界设定；不是已发生事件 |
| Story | 实际发生过什么；接受事件后的故事真源 |
| Prompt | 从可信状态派生给模型的投影，不是真相来源，不是authority |
| Bridge | Worlds间显式授权的受控投影，默认拒绝；不自动写入目标Memory/Story |
| Living | Agent是否具有主动行为资格；预算、cooldown、quiet hours等由Core决定 |
| Host Binding | Host能否安全执行已授权行为；身份、binding、capability与副作用前执行权限 |

Core Runtime已达到进入真实Host验证的阶段。当前首要工作是证明 Life Engine → Living Host Binding → Real Hermes → 真实Host生命周期 → 安全Side Effect，不继续无限扩展Core，也不把自动测试当真实Host证据。

## 4. 推荐执行顺序与 Gate

| 顺序 | 阶段 | 当前状态 / 进入与退出边界 |
| --- | --- | --- |
| 0 | SP-005A4-HLV0 架构与验证计划冻结 | DONE；只完成文档，不授权Host操作 |
| 1 | GOV-ROADMAP1 长期路线治理 | 长期路线基线；原预留Gate现由GOV-ARCHGATE1记录，方向不变 |
| 2 | SP-005A4-HLV1 Hermes Read-only Discovery | DONE；REAL_HOST_READONLY_PASS CONFIRMED |
| 3 | H-LV2 Hermes Lifecycle Validation | DONE；REAL_HOST_LIFECYCLE_AUTHORITY_PASS CONFIRMED |
| 4 | H-LV3 Living Dry Run | DONE；REAL_HOST_DRY_RUN_PASS CONFIRMED，零真实send |
| Gate | ARCHITECTURE REVIEW GATE / GOV-ARCHGATE1 | Gate PASS；结论记录DRAFT_REVIEW_PENDING，非执行授权 |
| 5 | H-LV4 Isolated Real Text Delivery | NEXT / NOT AUTHORIZED；必须另发独立任务书与real-send授权 |
| 6 | Hermes Living Adapter Stabilization | PLANNED；收敛验证发现的adapter/identity/lifecycle/evidence/recovery/diagnostics gap |
| 7 | SP-005A2-P1 Living Prompt Integration | AFTER_HERMES_ADAPTER_STABILIZATION / NOT AUTHORIZED |
| 8 | Memory Evolution V1 | AFTER_SP-005A2-P1 / PLANNED；先冻结Prompt Projection contract |
| 9 | Proactive Life / Routine Runtime | PLANNED；由可信状态产生Intent，Living仍决定可否执行 |
| 10 | Media Runtime | PLANNED；一致视觉表达、artifact与delivery语义 |
| 11 | Voice Runtime | PLANNED；Media稳定后，统一World/Memory/Relationship/Living来源 |
| 12 | Relationship / Autobiographical Evolution | PLANNED；Core Soul与关系表达分离 |
| 13 | OpenClaw Living Adapter | PLANNED；Hermes成熟模式验证Host-neutral后映射，不同时大规模推进 |
| 14 | Full Private RP | BLOCKED；独立等待官方Host capability解锁，不因其它阶段PASS自动进入 |

Architecture Review Gate已由ChatGPT / 小雪独立评审并正式确定上述局部顺序；GOV-ARCHGATE1只记录已下达结论，Codex不自行改顺序。每阶段仍须separate task与explicit authorization；NEXT/PLANNED/DEFINED不是执行许可。

## 5. 第一阶段：Hermes Living Real Host Validation

### H-LV1：只读发现与 Binding Validation

SP-005A4-HLV1已DONE；以下保留该阶段验证边界，不重新授权执行。REAL HOST / READ ONLY / NO HOST MUTATION / NO LIVING MUTATION / NO REAL SEND。目标是用当前真实环境证据逐项确认HLV0的DISCOVERABLE / UNKNOWN / HOST_GAP：实际安装版本/官方来源、Home/Profile/Agent/process、已有plugin发现与加载证据、可信Owner/sender/channel/target/session来源、Life Engine root/instance/generation及binding唯一性，wrong Host/Profile/Agent拒绝。

只读发现不能触发plugin load/reload、Gateway restart、enrollment、tick/inbound mutation、prepare、claim、permit或send；没有已加载证据就保留UNKNOWN。历史2026-09-30仅参考，不能假定环境仍相同。来源不能满足稳定可信身份则相应case BLOCKED_BY_HOST_CAPABILITY，不猜API。全部证据经独立审核才可REAL_HOST_READONLY_PASS；这也不自动授权HLV2。

### H-LV2：生命周期、身份与 Session

HLV2已DONE；以下保留其独立授权与证据边界，不重跑或扩大范围。重点Host startup、Binding load、plugin/authority/session lifecycle、Gateway restart、plugin reload、authority restart、generation/epoch transition、stale capability拒绝。核心问题是旧authority/permit/session/generation能否错误获得执行资格。

默认NO EXTERNAL DELIVERY。只操作专用测试Host，真实Gateway restart与fresh Python process证据分开。restart/reload不重置Core generation/day/budget/cooldown或durable Intent/Attempt；restore改变generation、旧能力全部stale。有效permit撤销的完整正例按HLV0留HLV3，HLV2不得为验证方便claim或发送真实消息。独立真实生命周期证据通过后才能REAL_HOST_LIFECYCLE_PASS。

### H-LV3：Living Dry Run

HLV3已DONE，REAL_HOST_DRY_RUN_PASS CONFIRMED；原阶段需单独授权真实Hermes生命周期驱动 tick → prepare_contact → claim_attempt → execution permit → fake/local side effect → delivery/recovery simulation。NETWORK SEND = NO；fake只写isolated local journal。所需adapter/harness若尚不存在，必须在当前阶段范围单独任务与架构审核后实施，不能把验证任务隐含变成adapter开发。

至少覆盖quiet hours、cooldown、daily cap、rolling cap、recent inbound、trusted identity、stale session/world、generation/authority mismatch、duplicate claim、permit replay、crash/restart recovery与target mismatch。继续执行HLV0 RV/CR矩阵、最终generation barrier、legacy副作用前fence，真实subprocess/os._exit故障注入不能冒充真实Gateway事件。

HLV3 DONE确认真实Host lifecycle下的fake执行安全；REAL_HOST_DRY_RUN_PASS已CONFIRMED，fake不是REAL_HOST_SENT。后续Architecture Review Gate已PASS，当前只记录结论，真实网络Side Effect仍未授权。

### H-LV4：隔离单次真实文本交付

当前NEXT / NOT AUTHORIZED，且SP-005A4-HLV4 != AUTHORIZED_FOR_EXECUTION。HLV0～3 DONE和Gate PASS不是发送许可，必须另发独立任务书与明确授权。专用Host/bot/channel、Owner本人、exact验证target、明确单次预算、可信provider SENT contract及必要实现均需先过独立Gate。当前SIMULATED_CONTACT permit不能改用途直接用于网络发送；NO_REAL_SEND不能自动关闭。

第一次严格限定one Intent、one Attempt、one execution permit、one explicitly verified isolated test target、one text message、one transport side effect。禁止auto retry、bulk send、fallback/default-last-route target、production target、multi-channel fanout、message splitting、reply fallback、thread override、forum auto-thread。cron/scheduled wake属于之后另立阶段，不由HLV4授权。

## 6. 本机环境背景与重新验证原则

以下环境背景保留GOV-ROADMAP1时点；HLV1～3的当前已确认范围以各阶段证据及Gate记录为准，不能由背景推导新的授权。本轮没有读取WSL或Host配置。

用户说明Windows下的WSL已存在Hermes与OpenClaw，并配置过微信、Telegram、Discord；此前有Life Engine/Hermes专用Discord Server/Test Bot。历史工作流为Hermes Telegram channel → 用户引导/控制 → Hermes → Discord isolated test channel执行测试。

原HLV1任务的只读核验要求是：Discord bot当前有效性、server/channel identity、Owner allowlist、Telegram routing、Hermes Profile/Agent/Gateway、Life Engine permanent root/instance/generation、OpenClaw与微信channel的存在及scope，均不能只凭历史聊天或本段说明签PASS。只读证据不能通过发送probe获得；不足就UNKNOWN/BLOCKED。

优先Dedicated Test Host Context、Dedicated Test Agent/Bot/Channel、Explicit Owner Allowlist、Explicit Target、Separate Life Engine Root，并保持生产Gateway/config/cron untouched。Control / Guidance Channel与Test Delivery Channel分开：历史Telegram是控制来源之一，Discord是隔离delivery环境；未来验证仍成立才优先沿用。控制来源不会自动变成可信Owner、发送资格或fallback destination。生产微信/Telegram、个人正常使用频道、生产Agent/Gateway不得直接成为实验side-effect目标。

## 7. 永久冻结的 Delivery / Recovery 边界

CLAIMED != SENT != ACKNOWLEDGED；DB transaction != network transaction。Core transaction → Attempt CLAIMED durable commit → transaction ends，之后首次成功execute=true才可Host执行授权与one-time permit → consume前完整重验 → external side effect → trusted delivery evidence → Core record_delivery。Core须验证provider evidence，facade digest不是provider truth；模型说“我已经发送”、CLI rc=0、人工boolean、prepared或CLAIMED都不是Delivery Evidence。

可信message ID/API结果经独立SENT contract验证后最多证明SENT；ACKNOWLEDGED需要独立可信ACK contract。fake journal仅为本地模拟证据。没有ACK不能伪造或用重复发送补齐。

Recovery != Authorization。query_operation_recovery可恢复durable operation association，COMMITTED/historical CLAIMED不能生成或恢复permit、resend、automatic retry。claim durable commit但response lost→B1只读projection→关联恢复→reconciliation→NO PERMIT / NO RESEND；不改operation ID猜结果。发送后Core结果丢失也只能UNKNOWN/冻结合同允许的conservative reconciliation，不能重建旧权限。

## 8. 第二阶段：Hermes Integration Stabilization

HLV4后先收敛adapter gap、identity mapping、lifecycle mapping、target validation、delivery evidence mapping、recovery integration与operational diagnostics。Host differences belong in Adapter / Binding Layer，不污染World/Memory/Story/Living Core；需要改变共享authority、安全语义、Attempt生命周期、permit、recovery或delivery semantics时STOP / ARCHITECTURE_CHANGE_REQUIRED，不能把Host便利条件转成Core policy。

## 9. Architecture Review Gate：P1 与 Memory Evolution V1

该Gate已完成独立评审，ARCHITECTURE_REVIEW_GATE = PASS，决定HLV4 → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1。选项、依赖分析、理由与剩余Host gaps见GOV-ARCHGATE1记录；这解析原预留局部顺序，不改变长期方向。

P1 = AFTER_HERMES_ADAPTER_STABILIZATION / NOT AUTHORIZED。未来至少冻结PromptSnapshot section ordering、budget/trimming、authority、version invalidation、fingerprint/integrity semantics；不得用legacy prependContext、ordinary tool output、fake Memory field或ad-hoc prompt injection绕过。Memory Evolution V1 = AFTER_SP-005A2-P1 / PLANNED：它会增加长期状态投影类型，先明确Prompt Projection contract，避免随后倒逼Memory authority、预算与裁剪。Prompt模板/HMAC/fingerprint/预算裁剪不因本轮文档治理改变。

## 10. 第三阶段：Memory Evolution

长期“同一个人”的体验需要World Memory逐步发展Working Memory、Episodic Memory、Semantic Memory、Relationship Memory、Autobiographical Memory；再加入Consolidation、Deduplication、Conflict Resolution、Supersession、Importance、Decay、Controlled Forgetting。具体存储/检索/删除语义须各自SP/RFC/ADR，不在本路线设计Schema。

Retrieval不等于最近N条全进入Prompt；应逐步综合人物相关度 × World相关度 × 时间相关度 × 事件重要度 × 关系相关度。该表达是选择维度，不提前冻结评分公式。Memory仍是Subject的知识/经历投影，不能替代Story事实或Lore设定；Prompt仍是派生投影，不能成为记忆权威。世界隔离、controlled forgetting与可审计supersession必须保持。

## 11. 第四阶段：Proactive Life / Routine Runtime

Living回答“是否允许主动联系”；未来Life/Routine回答“为什么此刻产生联系意图”。组合World State、Time、Calendar/Weather Context、Memory、Relationship、Recent Interaction、Living Policy产生Proactive Intent，再由Living决定执行资格。

不把长期体验做成08:30固定早上好、12:00固定吃饭了吗、22:00固定晚安的Cron Bot。调度只是唤醒来源，不是业务authority或Intent真源；没有合适Intent就静默，不承诺每日填满预算。

## 12. 第五阶段：Media Runtime

World State + Time + Location Context + Weather + Current Activity + Character Identity + Relationship Context → Media Intent → ComfyUI / Media Provider → Media Artifact → Host Delivery。

优先Character / World / Temporal / Context Consistency，表现当前World中的Agent此刻可能产生的照片，避免随机图片与文字世界脱节。artifact/job、生成、prepared、发送及receipt分别记录；Provider abstraction保持Host-neutral，真实ComfyUI与渠道测试需另授权，不由文本验证自动通过。

## 13. 第六阶段：Voice Runtime

Media稳定后推进Agent Identity + Voice Identity + Current Context + Emotion/Expression + Speech Style → Voice Runtime → Audio Artifact → Host Delivery。文字、照片、语音共享World、Memory、Relationship、Living State，不能成为三个独立人格系统。TTS/provider、artifact生命周期、发送与证据各自验证；照片链路PASS不等于Voice授权。

## 14. 第七阶段：Relationship / Personality Evolution

Core Soul + Relationship State + Shared Experience + Current Context → Personality Expression。Core Soul与Relationship-dependent expression分离；长期关系变化不简单通过直接重写Soul实现。同一Agent因长期共同经历形成不同表达，保留身份连续性、世界隔离与可审计关系状态。Autobiographical演进与Memory阶段积累衔接，不能将未核验模型叙事当Story事实。

## 15. OpenClaw正式目标路线

OpenClaw仍是正式目标Host。Hermes Living Integration未稳定前，不同时大规模推进两套Adapter。先Hermes Living Adapter → Host-neutral contract validation → OpenClaw Living Adapter，用成熟Binding模式映射Host差异，分别取得真实环境与生命周期证据。OpenClaw已存在的用户环境说明不是Adapter PASS，也不需要在本轮操作它。

## 16. Full Private RP 独立 blocker

Full Private RP = BLOCKED_BY_OFFICIAL_HOST_CAPABILITY；H1 = BLOCKED_BY_OFFICIAL_HERMES_HOST_CAPABILITY；H2 = BLOCKED。这是已审核能力门禁，非本任务重新调查官方upstream后的结论。Hermes尚缺已验证满足要求的统一final-output commit boundary，理想合同如llm_final_output_commit(candidate, context) → ALLOW | DROP，DROP terminal、callback failure fail closed；OpenClaw同样缺已验证统一final-output transaction boundary。

等待upstream能力成熟后单独版本/执行链验证，不侵入式魔改Hermes/OpenClaw，不绕authority或伪造安全边界。Living permit不能替代final-output commit；H1 blocker不阻止Living只读/lifecycle/fake验证。Living真实集成PASS也不自动解锁原始历史隔离、晚到结果、授权前streaming或Full Private RP。

## 17. 防跑偏治理与任务声明

每个未来SP、RFC、ADR、Implementation Task、Validation Task必须声明：

```text
Roadmap Stage: <当前对应阶段及Gate>
Why Now: <为何属于当前阶段、依赖证据和单独授权>
```

任务不属于当前阶段默认NOT AUTHORIZED。实现简单、顺手能做、代码相关、未来肯定需要都不是提前开发理由。发现旁线需求先记录提案，不写实现；NEXT只是准备发布任务，不是开始执行。

任务应另列固定Base、范围/禁止范围、预置Gate、输出证据、完成/停止点与是否需要Host mutation/send权限，不能由代码依赖或green CI推导授权。每项阶段完成须独立证据，不自动升级SIMULATED_PASS→REAL_HOST_PASS或历史real send→当前Living PASS。

## 18. Roadmap变更规则与治理流程

改变阶段顺序、新增重大Runtime、提前Runtime、跳过Validation Gate、改变Host优先级或安全边界，必须先改Roadmap → ChatGPT/小雪独立架构审核 → 用户确认 → 再发布实施任务。不得先实现后补Roadmap；Architecture Review Gate的局部调整也适用，Codex不得自行改顺序。

继续Codex实现/文档 → Draft PR → ChatGPT/小雪独立审核 → 明确授权Ready → Codex仅Mark Ready → 轻量终审 → 明确授权Squash Merge → Codex Squash Merge → exact main push CI → ChatGPT/小雪独立核canonical main及四矩阵 → DONE。禁止Merge Commit/Rebase Merge/Auto Merge。merge本身不等于DONE，PR Head CI不能代替canonical main push CI。

GOV-ARCHGATE1 Draft与exact Head CI交付后立即STOP，不Ready/Merge、不操作Host、不启动HLV4/Adapter Stabilization/P1/Memory Evolution。HLV1～3历史证据只引用；每个未来实施/验证阶段重新另立任务与授权。

## 19. STOP / ARCHITECTURE_CHANGE_REQUIRED

当前阶段无法在冻结架构下安全实现，且涉及Schema semantics、Prompt/Memory/Story authority、Attempt lifecycle、Recovery/Delivery semantics、Execution Permit、Authority lifecycle、Host trust boundary、World isolation或Bridge security时，停止并报告ARCHITECTURE_CHANGE_REQUIRED。报告冻结合同、发现gap、无法在现有架构解决的原因、最小可选方案及需经过的Roadmap/架构Gate；不得自行重构继续实施。

固定canonical main漂移则STOP并报告新SHA，不换Base或rebase本任务。需要真实Host操作/send才能完成文档治理、需要production改动或把Full Private RP变成Living前置依赖，也必须STOP。没有证据的能力保留UNKNOWN/BLOCKED，不用Prompt或model声明填补。
