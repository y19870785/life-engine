# SP-005A4-HLV0 — Hermes Living Sandbox Validation 架构冻结

## CURRENT — HLV4-R1 实施（2026-10-04）

R0 = DONE / FROZEN；canonical main `88e699ca34cab463cd65be61edfdf61522b8952a`。R1 = IMPLEMENTED / DRAFT_REVIEW_PENDING；[R1验证报告](../validation/SP-005A4-HLV4-R1-REAL-DELIVERY-AUTHORITY.md)仅取得Host-neutral本地authority/intercept证据，不是Hermes Host/真实SENT。HLV4-A = BLOCKED，直至R1 canonical DONE且另行授权；HLV4-B = NOT AUTHORIZED。REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP；REAL_SEND = NO。DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。下列R0前后历史状态保持当时含义，不将原SIMULATED_CONTACT permit解释为REAL_CONTACT。

## HISTORICAL — HLV4-R0 authority 修订时状态（2026-10-04）

当前任务 Base：`71063c189ba2de501acdadca61e212e1cfc722a4`；GOV-ARCHGATE1 已 canonical DONE。HLV0～HLV3 DONE；REAL_HOST_DRY_RUN_PASS CONFIRMED。HLV4-A = BLOCKED_BY_FROZEN_AUTHORITY_CONTRACT；ARCHITECTURE_CHANGE_REQUIRED = YES，已路由到 HLV4-R0；HOST_PATCH_REQUIRED = NO。原因是 A3仅授权SIMULATED_CONTACT；不是Hermes capability blocker。

[Real Delivery Authority合同](SP-005A4-HLV4-REAL-DELIVERY-AUTHORITY.md)冻结目标typed mode/purpose、default-deny RealDeliveryPolicy、内存one-shot validation grant与独立real/simulation consumer；R0 = DRAFT_REVIEW_PENDING，现有Runtime仍不具备现实用途。LOCAL_ORDER = HLV4-R0 → HLV4-R1 → HLV4-A → HLV4-B → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1；ROADMAP_DIRECTION_CHANGE = NO。HLV4-R1 / HLV4-A retry / HLV4-B / P1 = NOT AUTHORIZED，Memory Evolution V1 = PLANNED。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP；REAL_SEND = NO。本轮仅文档，无Host/Runtime/schema/Prompt修改；Full Private RP仍 BLOCKED_BY_OFFICIAL_HOST_CAPABILITY。下列旧治理状态为对应阶段历史，技术合同仅由R0目标显式修订部分补充；实现须另行授权，不自动改现有行为。

## HISTORICAL — R0 前治理记录

## CURRENT CANONICAL STATE — Post-HLV3 / GOV-ARCHGATE1（2026-10-03）

canonical Base：`9d064d0a90d8d02a5dab04a6baee18bbbf6dcdc2`；PR #39 Squash Merge 与 exact main push CI #37122681930 四矩阵已独立核验。SP-005A4-HLV0 = DONE；SP-005A4-HLV1 = DONE；SP-005A4-HLV2 = DONE；SP-005A4-HLV3 = DONE。REAL_HOST_READONLY_PASS / REAL_HOST_LIFECYCLE_PASS / REAL_HOST_LIFECYCLE_AUTHORITY_PASS / REAL_HOST_DRY_RUN_PASS = CONFIRMED；REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP。

ARCHITECTURE_REVIEW_GATE = PASS；LOCAL_ORDER = HLV4 → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1。ARCHITECTURE_CHANGE_REQUIRED = NO；ROADMAP_DIRECTION_CHANGE = NO。完整证据、依赖与授权边界见 [GOV-ARCHGATE1 Gate 记录](GOV-ARCHGATE1-POST-HLV3-REVIEW.md)。GOV-ARCHGATE1 = DRAFT_REVIEW_PENDING；SP-005A4-HLV4 = NEXT / NOT AUTHORIZED，独立任务与明确授权前 REAL_SEND = FORBIDDEN。Roadmap state != execution authorization。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = AFTER_HERMES_ADAPTER_STABILIZATION / NOT AUTHORIZED；Memory Evolution V1 = AFTER_SP-005A2-P1 / PLANNED。OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED_BY_OFFICIAL_HOST_CAPABILITY（H1/H2 blocker 保留）。本轮 NO_REAL_HOST_OPERATION = true、NO_REAL_SEND = true；历史证据只引用，不重跑。

## HISTORICAL — HLV0 冻结时范围

下文阶段计划与权限表保留冻结合同；其中未执行/未授权及“本轮”均指HLV0时点，实际HLV1～3的独立DONE与当前HLV4 NEXT以顶部和Gate记录为准，不扩张原执行授权。

Phase：SP-005A4-HLV0；RESULT = DONE（canonical main `08bf82e89f7a4572f4931105cc5e6927ae1c5214` 已由 ChatGPT / 小雪独立核验；原 Base 为历史开工基线）。唯一 Base：`eedc32b719336ba063b99da95eac4e2b6a56c0c5`，PR #34 已 Squash Merge，parent `b78b849b1bfac1cbd28359cfb317fd1d4cb84402`；[main push #36847806554](https://github.com/y19870785/life-engine/actions/runs/36847806554) exact SHA / push / main 四矩阵 SUCCESS，已独立核验。

SP-005A3 = DONE；SP-005A3-B0 = DONE；SP-005A3-B1 Architecture / Implementation = DONE。DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；SP-005A2-P1 = NOT AUTHORIZED；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES。B01-B34 = SIMULATED_PASS；B1-08_CORE_PASS / B1-09_CORE_PASS 保留。Hermes real Host validation = PENDING_REAL_HOST_VALIDATION；OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED；H1 = BLOCKED；H2 = BLOCKED。NO_REAL_HOST_OPERATION = true；NO_REAL_SEND = true。

本轮只冻结 Architecture / Validation Plan / Governance Documentation，不实现 adapter、ACK validator 或 provider validator，不安装、运行、reload/restart Hermes，不调用任何 Living mutation 或 transport。不修改 Runtime/tests/Schema/Prompt/workflow。H-LV1～H-LV3 均 NOT_EXECUTED / NOT_AUTHORIZED，未来逐阶段明确授权；H-LV4 DEFINED_ONLY / NOT_AUTHORIZED。Media、Voice、Memory Evolution、P1、Full Private RP 不在范围内。

[A3 架构](SP-005A2-LIVING-HOST-BINDING.md)、[A3 验证](../SP-005A3-VALIDATION.md)、[B1 recovery](SP-005A3-B1-OPERATION-RECOVERY-PROJECTION.md)保持冻结。历史 [Hermes 2026-09-30](../validation/HERMES-COMPREHENSIVE-EVALUATION-2026-09-30.md)仅为 HISTORICAL_EVIDENCE，不是当前环境证据、Living PASS 或新权限。旧文档原文标识 HISTORICAL，历史计数/发送事实不删除。

## 六类真源

| 真源 | 所属层 / 允许证明 | 不允许证明 |
| --- | --- | --- |
| Host truth | 受信 Host process、Profile/Agent、platform、sender、channel、session、加载/重启事实 | Living quota、Intent、Attempt、commit truth |
| Core truth | durable generation、World/Scope/Session、schedule、budget/cooldown、Intent/Attempt、operation receipt | 网络发送或 ACK |
| Binding truth | per-install protected single-writer atomic versioned checksum metadata；可信绑定、routing、correlation/identity/digest/lifecycle | durable CLAIMED/SENT/ACK truth |
| Execution authority | 当前 authority/plugin epoch、binding revision、generation、exact target/Attempt/invocation/purpose/expiry 下的一次 permit | delivery evidence、可恢复发送资格 |
| Delivery evidence | 独立可信 provider evidence 经 Core delivery_validator.verify(evidence) | facade evidence_digest、模型文本或 CLI 成功 |
| Recovery truth | B1 query_operation_recovery 的只读 typed projection，恢复关联供 reconciliation | execute=true、新 permit、resend |

链路：Host Trigger → Trusted Binding / Capability → LivingHostFacade → Core begin_attempt durable CLAIMED commit → transaction ends → 首次 execute=true → memory-only one-time permit → consume 前最终 fence → isolated local side effect → trusted evidence → Core record_delivery。DB transaction != network transaction。CLAIMED != SENT != ACKNOWLEDGED。

Facade 八项：tick、query_context、observe_inbound、prepare_contact、claim_attempt、recover_operation、submit_delivery_result、status。tick 仅结构化，无模型/transport/permit；query_context 仅 SOUL_RESPONSE bounded LivingContextSnapshot，不注入最终 Prompt；prepare 只 DECIDED→PREPARED。Session-bearing transaction：current World → Scope → Session → WriterEpoch → WorldRevision → Living root → receipt/mutation；旧 session WORLD_STALE，receipt replay 不绕过。JSON envelope <=8 KiB、response <=16 KiB、status 默认20/硬上限100、未知安全字段拒绝；capability/secret 不进入 Prompt/log/transcript/model。

## 分阶段权限与退出门禁

| 阶段 | 性质 | 必须证明 / 独立阶段退出条件 |
| --- | --- | --- |
| H-LV1 | REAL HOST / READ ONLY / NO LIVING MUTATION / NO SEND | 当前实际版本/官方 checkout或package、独立 HERMES_HOME/Profile/Agent、已有 plugin discovery/loading 能力只读证据、process identity、Owner/sender/channel/target/session 来源、instance/permanent root/generation、binding 唯一性；错误 Host/Profile/Agent 只读校验拒绝；与历史环境逐字段比较。不得通过 load/reload 获取“discovery”。缺已加载证据即 UNKNOWN。无 enrollment/tick/inbound/prepare/claim/permit/fake send/cron/restart。所有强制来源有证据才可 REAL_HOST_READONLY_PASS；否则逐项 BLOCKED_BY_HOST_CAPABILITY 或 NOT_EXECUTED。 |
| H-LV2 | REAL HOST / ISOLATED TEST HOST / NO EXTERNAL DELIVERY | 独立授权后 plugin load/unload/reload、Host/Gateway与authority restart、epochs撤销、generation transition、identity/session/writer_epoch/world_revision、wrong Owner/channel/Profile/Agent、target变化与legacy fence；允许的 query 仅已有授权 SOUL session 的有界只读查询，不注入 Prompt。inbound 默认 DENY，若需 validation-only synthetic event 必须另行列出且零业务 mutation。permit 仅验证器拒绝旧/伪造凭据，不通过 claim 制造有效 permit；真实已签 permit 的 revoke 正例留 H-LV3。通过真实生命周期证据才可 REAL_HOST_LIFECYCLE_PASS。 |
| H-LV3 | REAL HERMES LIFECYCLE + REAL LIFE ENGINE CORE + FAKE/LOCAL SIDE EFFECT ONLY | 单独授权 adapter/test harness 后隔离 test authority，tick、query、可信合成inbound、prepare、claim、permit最终重验/consume/expiry/撤销、真实进程crash/recovery、幂等及并发；fake side effect 仅隔离 local journal，无网络。逐项矩阵通过且零真实 send 后可 REAL_HOST_DRY_RUN_PASS。 |
| H-LV4 | DEFINED_ONLY / NOT_AUTHORIZED | H-LV1～3 分别独立 PASS 后，ChatGPT/小雪重新审核并明确单独授权，才讨论一次 isolated real text delivery。仅专用测试 Host/bot/channel、Owner 本人、exact explicit target、明确单次预算；无fallback/default-last-route/生产Agent或Gateway/cron。还需独立 transport与SENT contract及所需实现授权；阶段 PASS 不自动关闭 NO_REAL_SEND。 |

H-LV0 文档 PASS 不授权任何后续执行。真实 Gateway restart 必须保存独立服务旧/新 process identity、启动/停止事件与新 live hook。fresh Python subprocess/os._exit 只证明 PROCESS_BOUNDARY，不是 Gateway restart；两类证据分别记录，不相互升级。restart/reload 不改变 Core generation 或 Living day/budget/cooldown/Intent/Attempt；durable restore 才改变 generation，恢复按冻结 Core 合同处理。

| 操作 | H-LV1 | H-LV2 | H-LV3 | H-LV4（未授权） |
| --- | --- | --- | --- | --- |
| 读取 Host version | ALLOW | ALLOW | ALLOW | ALLOW |
| 读取 identity/binding | ALLOW | ALLOW | ALLOW | ALLOW |
| plugin load | DISCOVERY ONLY（只读已有加载证据） | ALLOW | ALLOW | ALLOW |
| plugin reload | DENY | ALLOW | ALLOW | ALLOW |
| Gateway restart | DENY | ISOLATED ONLY | ISOLATED ONLY | ISOLATED ONLY |
| Living query_context | DENY | LIMITED（已有SOUL session只读） | ALLOW | ALLOW |
| observe_inbound | DENY | validation-only if separately permitted；零mutation | ALLOW | ALLOW |
| prepare_contact | DENY | DENY | ALLOW | ALLOW |
| claim_attempt | DENY | DENY | ALLOW | ALLOW |
| execution permit | DENY | validation-only / no transport / no issuance | ALLOW fake-only | ALLOW（另审 real用途） |
| fake transport | DENY | DENY | ALLOW | ALLOW |
| network send | DENY | DENY | DENY | future explicit authorization |
| cron / scheduled wake | DENY | DENY | DENY | separate later phase |
| production Host modification | DENY | DENY | DENY | DENY |

表中 ALLOW 仅定义未来获授权阶段内上限，不能被 HLV0 或上一阶段 PASS 触发。无法安全分类的操作 ARCHITECTURE_CHANGE_REQUIRED；不得默认放宽。

## 隔离环境与可信身份硬门禁

ISOLATED_HERMES_HOME = required；ISOLATED_PROFILE = required；ISOLATED_TEST_AGENT = required；ISOLATED_TEST_BOT = required；EXPLICIT_OWNER_ALLOWLIST = required；EXPLICIT_CHANNEL = required；EXPLICIT_TARGET = required；SEPARATE_LIFE_ENGINE_ROOT = required；PRODUCTION_GATEWAY_UNTOUCHED = required；PRODUCTION_CONFIG_UNTOUCHED = required；PRODUCTION_CRON_UNTOUCHED = required。

H-LV1 开始时先只读取得现有隔离环境证据；缺环境不得本阶段自动创建或改配置。专用 bot/channel 的配置只能离线只读核验，不发 probe。保存实际版本、安装来源/内容digest、测试Home/Profile/Agent/process及Gateway实例、root/instance/generation、绑定来源、credential隔离及网络禁用证明；与历史2026-09-30逐项 SAME/CHANGED/UNKNOWN，任一 UNKNOWN 不假设安全。原始证据仓库外受保护，文档仅脱敏引用、digest与来源，不记录 secret/raw capability、生产历史或真实私人ID。

Owner 绑定 (platform, trusted sender/principal identity, selected test Host identity, selected test Agent/Profile)。target 绑定 (platform, channel, destination identity, authority epoch, plugin epoch, generation, invocation, purpose)。Owner 和 target 是不同 typed identity，不能用同一个字符串代替；只用 display name/nickname 不合格。Host identity 来自 authenticated Host context，不接受 model output、Prompt、tool JSON自报、last route、most recent conversation猜测、fallback channel或environment assumption。稳定 external event identity + trusted provenance 才能 observe：same ID+same digest 幂等、same ID+不同digest conflict、无ID INBOUND_UNVERIFIED。

## A3 → Hermes 能力映射与来源台账

标签：KNOWN=本仓库已有合同或官方源码可确认的抽象，非当前安装实测；DISCOVERABLE=未来只读可取得候选来源但必须验证；UNKNOWN=没有足够证据；HOST_GAP=官方所查接口不能直接满足所需保证，需阻断对应验证项；NOT_REQUIRED_IN_THIS_PHASE=本轮无需实现。标签不等于 PASS。

2026-10-01 仅远程只读查看官方仓库，pin `e8c97320ac8691d4de92af49f98459f9ef9ddb08`；未访问安装的 Hermes。官方 [PluginContext / loader](https://github.com/NousResearch/hermes-agent/blob/e8c97320ac8691d4de92af49f98459f9ef9ddb08/hermes_cli/plugins.py)提供注册工具/hook抽象；[hook 参数表](https://github.com/NousResearch/hermes-agent/blob/e8c97320ac8691d4de92af49f98459f9ef9ddb08/website/docs/user-guide/features/hooks.md)列出 session/platform/sender 候选字段。字段存在不能证明身份受信、跨重启稳定性或执行前撤销。这是公开来源快照，不是 selected test Host version；未来必须核对实际安装并 pin 匹配来源。 官方来源内容 SHA-256：plugins.py = `31c99f61f61732557bb84429d014e943d2d51a753b2541ab5de3b196a893bf9a`；hooks.md = `ff807b43b605048dd6bc66b769ca5981754a114499a3bd1dfeb26ba68e89ec50`。

| A3 abstraction | 未来真实来源 / 证据 | 标签 / 失败处置 |
| --- | --- | --- |
| Binding Authority | A3 per-install本地受保护metadata与可信启动方；Hermes profile/process身份需独立比对 | KNOWN（A3）；DISCOVERABLE（Host identity），未知绑定拒绝 |
| HostIdentityEnvelope | authenticated inbound context→trusted mapper；不得将任意tool参数升格 | KNOWN（A3 type）；DISCOVERABLE（sender/platform候选）；mapper UNKNOWN |
| authority epoch | BindingAuthority 每次 start 新epoch，不持久复用 | KNOWN；真实启动关联 DISCOVERABLE |
| plugin epoch | A3每次真实load/reload新epoch；Hermes loader事件需捕获 | KNOWN（A3）；DISCOVERABLE（load）；unload/reload完备顺序 UNKNOWN |
| generation | Life Engine durable registry；不是Hermes session | KNOWN；Host↔root绑定 DISCOVERABLE |
| session identity | Hermes session_id候选 + Core trusted Session/WriterEpoch/WorldRevision | DISCOVERABLE（ID）；HOST_GAP（所查hook未直接提供Core writer_epoch/world_revision或稳定授权映射），需可信mapper设计与证据，不能填常量 |
| channel identity | authenticated platform inbound channel/destination元数据 | UNKNOWN（当前未核对所选平台receiver源码/实机），缺来源 BLOCKED_BY_HOST_CAPABILITY |
| target identity | selected测试channel明确destination与可信allowlist，禁止默认路由 | DISCOVERABLE（隔离配置）；runtime exact target source UNKNOWN |
| trusted inbound | platform event ID、sender/provenance 与防转发/子agent伪造来源 | UNKNOWN（稳定event ID和完整provenance链），未证明则 INBOUND_UNVERIFIED |
| Living facade invocation | 专用trusted adapter/harness调用八项facade；模型没有vault凭据 | KNOWN（A3）；Hermes adapter NOT_REQUIRED_IN_THIS_PHASE / 未实现 |
| execution permit consumer | dedicated trusted execution component，网络禁用local journal | KNOWN（fake）；Hermes生命周期绑定consumer UNKNOWN，未来需单独实现授权 |
| provider delivery result source | 实际平台API/provider签名或可验证message identity | UNKNOWN（未检查具体provider）；real validator NOT_REQUIRED_IN_THIS_PHASE；ACK contract HOST_GAP（未定义受信ACK），不得伪造 |
| recovery caller | trusted authority从原metadata exact identity/digest构造LivingRecoveryContext / RecoveryDelegation | KNOWN（A3）；真实caller wiring UNKNOWN |
| lifecycle transition authority | trusted管理面lifecycle_transition排序pause/target/restore与consume | KNOWN（A3）；Hermes全部管理入口能否被覆盖 UNKNOWN，不用observer hook当同步barrier |
| legacy routing fence | trusted metadata LEGACY/LIVING_PENDING/LIVING_ACTIVE；callback前dispatch | KNOWN（A3）；现有Hermes legacy入口接线 UNKNOWN，不假设旧插件已覆盖 |
| Full Private RP final-output commit | llm_final_output_commit独立合同 | NOT_REQUIRED_IN_THIS_PHASE；H1/H2仍BLOCKED |

HOST_GAP 是接口保证差距，非宣称整个官方Host永远没有能力。H-LV1重新发现后可提交新证据供独立审核；本轮不实现mapper/patch。若稳定可信session或同步管理边界无法建立，对应H-LV2/3记 BLOCKED_BY_HOST_CAPABILITY，不猜 API，不签有效capability。上述UNKNOWN均有明确隔离/拒绝策略，不阻止HLV0文档冻结；若发现必须改变A3冻结语义才能安全定义，立即STOP。

## 执行权限、生命周期与恢复

只有首次 Core begin_attempt 成功返回 execute=true 且 durable state=CLAIMED，事务结束后才发一次内存permit。Replay execute=false；recover_operation只包装 LivingRuntime.query_operation_recovery，禁止读取living_operations或调用mutation猜结果。COMMITTED != EXECUTE；RECOVERY != AUTHORIZATION；HISTORICAL CLAIMED != SEND PERMISSION。claim响应丢失→恢复Attempt关联→RECONCILIATION_REQUIRED→NO PERMIT→NO RESEND；NOT_COMMITTED也不是自动claim授权。

consumer在副作用前原子consume并检查current binding mode/target/Core target/paused/enabled/session authorization/current generation/current authority/plugin epoch/exact Attempt/invocation/purpose/expiry/once。最后generation barrier不可省。lifecycle_transition只由可信管理面排序pause、target及restore/generation transition与consume，不决定quota/policy，不跨transport持锁。authority restart旧capability/permit全失效；plugin reload旧plugin凭据/permit失效；Core generation/day/budget不重置。restore旧generation能力全部stale，CLAIMED遵循冻结Core恢复合同，conservative reconciliation，无resend。

H-LV3只能使用当前isolated test authority和SIMULATED_CONTACT permit；正式非isolated authority不能claim，fake provider只写独立local journal。H-LV4现实用途/transport尚未实现，也没有网络发送资格；不得通过关NO_REAL_SEND或改purpose绕过。未来若需要改变permit/BindingAuthority/DeliveryEvidence冻结语义，先 ARCHITECTURE_CHANGE_REQUIRED 并独立审架构，不能把HLV4定义当实施许可。

Living real delivery副作用前授权边界与Full Private RP的llm_final_output_commit是两个不同合同。Hermes Living validation does not require Full Private RP final-output commit boundary；H1 BLOCKED不阻止只读/生命周期/fake验证设计。Living permit也不能替代Full Private RP对最终输出/历史隔离/晚到结果的授权。

## Delivery evidence 与 reconciliation

H-LV0不实现ACK validator。H-LV3 fake证据仅 SIMULATED_PASS，不称REAL_HOST_SENT；journal为fake外部事实、Core为业务事实。permit consumed→fake journal committed→process crash→record_delivery absent时Core Attempt可仍CLAIMED，Host reconciliation，NO RESEND；不得把journal自动转Core SENT或恢复permit。真实restore若按既有Core规则转换UNKNOWN，记录真实新代次projection，不能从Host捏造状态。

未来provider message ID/API查询结果只有经独立受信SENT contract验证平台/target/Attempt/invocation/message identity与来源后，默认最多成为trusted SENT evidence。ACKNOWLEDGED必须另有可信ACK contract；model text、CLI rc=0、人工boolean、durable operation receipt、prepared message、CLAIMED均不能证明ACK或SENT。FAILED/UNKNOWN保留不确定性，不自动重发、不用新的operation ID规避幂等。人工reconciliation只读核对并作受信continuation decision；新业务授权若需要必须单独审核，不能恢复旧permit。

## Evidence 等级、报告与验收

| 等级 | 允许结论 |
| --- | --- |
| DESIGN_ONLY | 已冻结方案；未执行 |
| CORE_PASS | Core专用自动测试；不证明Host |
| SIMULATED_PASS | fake fixture/process通过；A3 B01–B34保持此级 |
| REAL_HOST_READONLY_PASS | H-LV1当前隔离环境只读来源与绑定通过 |
| REAL_HOST_LIFECYCLE_PASS | H-LV2真实load/reload/Gateway事件通过；非Python子进程替代 |
| REAL_HOST_DRY_RUN_PASS | H-LV3真实Hermes生命周期+Core+local fake通过；零网络 |
| REAL_HOST_SENT | 另授权H-LV4且可信SENT contract通过 |
| ACKNOWLEDGED | 单独可信ACK contract验证，不由message ID推导 |
| BLOCKED | 外部能力缺失；原因如BLOCKED_BY_HOST_CAPABILITY |
| FAIL | 已执行且违反合同/断言 |

不允许自动升级SIMULATED_PASS→REAL_HOST_PASS，也不允许one historical real send→Living real delivery PASS。每个case记录phase/authorization、exact Life Engine/Host source与安装版本、isolated环境digest、旧新epochs/generation/session、operation identity/digest、Core before/after projection、真实进程事件、permit结论（不含raw token）、local journal count、network count=0、recovery outcome、PASS/FAIL/BLOCKED、来源hash与时间。原始证据仓库外，脱敏summary独立审核；模型总结/人工boolean不签PASS。[详细矩阵](../planning/SP-005A4-HERMES-LIVING-VALIDATION-MATRIX.md)规定每项字段。

HLV0 PASS：A3 current状态校准、HISTORICAL preserved、权限分层/real-send gate/Owner-target来源/生命周期/恢复/证据边界明确、Private RP解耦、未知能力全部列出、零Host操作、Runtime/Schema/Prompt未改、链接/状态检查及完整unittest/exact Head四矩阵成功，并等待独立审核。Codex交付仅PENDING_INDEPENDENT_REVIEW。

FAIL：当前A3仍描述未实现；历史Host被升级；message ID当ACK；fake当真实send；recovery当执行权；H1当全部Living blocker；无real-send gate；默认target/fallback；允许production测试。BLOCKED只用于无法在冻结架构中安全定义的外部能力缺口，不因测试未执行自动记PASS。

STOP：Schema、Prompt、Core/business/Attempt/recovery/delivery/permit/BindingAuthority semantics需要改变；必须real send或production修改才能完成HLV0；发现Full Private RP依赖。立即ARCHITECTURE_CHANGE_REQUIRED，报告冻结合同、新gap、无法按现有架构解决的原因与最小可选方案；不得实施。未来real adapter实施授权不是本轮范围。

治理：Draft → 独立审核PASS → 明确授权Ready → 仅Mark Ready → 轻量终审PASS → 明确授权Squash Merge → canonical main/exact push四矩阵独立核验 → DONE。禁止Merge Commit/Rebase Merge/Auto Merge。HLV0 Draft与exact Head CI完成后停止，不开始H-LV1或任何Host操作。
