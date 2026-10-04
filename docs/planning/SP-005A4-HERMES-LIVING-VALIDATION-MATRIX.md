# SP-005A4-HLV0 — Hermes Living Validation 测试矩阵

## CURRENT — HLV4-A0 专用 Adapter 架构候选（2026-10-04）

R0 / R1 = DONE；R1 canonical main `0b733908ffdef059a43428af42f3b3cb83a9850e`。HLV4-A built-in Discord path = REJECTED；dedicated `life_engine_discord` plugin route = ARCHITECTURE_FREEZE_PENDING，见 [A0合同](../architecture/SP-005A4-HLV4-DEDICATED-HERMES-DELIVERY-ADAPTER.md)。`HOST_PATCH_REQUIRED_FOR_BUILTIN_PATH = YES`；`HOST_PATCH_REQUIRED_FOR_DEDICATED_PLUGIN_ROUTE = NO`（须在未来 HLV4-A 验证）。本轮只冻结文档；A0 runtime / Host validation = NOT_EXECUTED；HLV4-B = NOT AUTHORIZED；REAL_SEND = NO；REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP。`ARCHITECTURE_CHANGE_REQUIRED = NO`、`ROADMAP_DIRECTION_CHANGE = NO`。以下 R1 状态为历史快照，不是当前授权。

## HISTORICAL — HLV4-R1 实施（2026-10-04）

R0 = DONE / FROZEN；canonical main `88e699ca34cab463cd65be61edfdf61522b8952a`。R1 = IMPLEMENTED / DRAFT_REVIEW_PENDING；[R1验证报告](../validation/SP-005A4-HLV4-R1-REAL-DELIVERY-AUTHORITY.md)仅取得Host-neutral本地authority/intercept证据，不是Hermes Host/真实SENT。HLV4-A = BLOCKED，直至R1 canonical DONE且另行授权；HLV4-B = NOT AUTHORIZED。REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP；REAL_SEND = NO。DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。下列R0前后历史状态保持当时含义，不将原SIMULATED_CONTACT permit解释为REAL_CONTACT。

## HISTORICAL — HLV4-R0 authority 修订时状态（2026-10-04）

当前任务 Base：`71063c189ba2de501acdadca61e212e1cfc722a4`；GOV-ARCHGATE1 已 canonical DONE。HLV0～HLV3 DONE；REAL_HOST_DRY_RUN_PASS CONFIRMED。HLV4-A = BLOCKED_BY_FROZEN_AUTHORITY_CONTRACT；ARCHITECTURE_CHANGE_REQUIRED = YES，已路由到 HLV4-R0；HOST_PATCH_REQUIRED = NO。原因是 A3仅授权SIMULATED_CONTACT；不是Hermes capability blocker。

[Real Delivery Authority合同](../architecture/SP-005A4-HLV4-REAL-DELIVERY-AUTHORITY.md)冻结目标typed mode/purpose、default-deny RealDeliveryPolicy、内存one-shot validation grant与独立real/simulation consumer；R0 = DRAFT_REVIEW_PENDING，现有Runtime仍不具备现实用途。LOCAL_ORDER = HLV4-R0 → HLV4-R1 → HLV4-A → HLV4-B → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1；ROADMAP_DIRECTION_CHANGE = NO。HLV4-R1 / HLV4-A retry / HLV4-B / P1 = NOT AUTHORIZED，Memory Evolution V1 = PLANNED。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP；REAL_SEND = NO。本轮仅文档，无Host/Runtime/schema/Prompt修改；Full Private RP仍 BLOCKED_BY_OFFICIAL_HOST_CAPABILITY。下列旧治理状态为对应阶段历史，技术合同仅由R0目标显式修订部分补充；实现须另行授权，不自动改现有行为。

## HISTORICAL — R0 前治理记录

## CURRENT CANONICAL STATE — Post-HLV3 / GOV-ARCHGATE1（2026-10-03）

canonical Base：`9d064d0a90d8d02a5dab04a6baee18bbbf6dcdc2`；PR #39 Squash Merge 与 exact main push CI #37122681930 四矩阵已独立核验。SP-005A4-HLV0 = DONE；SP-005A4-HLV1 = DONE；SP-005A4-HLV2 = DONE；SP-005A4-HLV3 = DONE。REAL_HOST_READONLY_PASS / REAL_HOST_LIFECYCLE_PASS / REAL_HOST_LIFECYCLE_AUTHORITY_PASS / REAL_HOST_DRY_RUN_PASS = CONFIRMED；REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP。

ARCHITECTURE_REVIEW_GATE = PASS；LOCAL_ORDER = HLV4 → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1。ARCHITECTURE_CHANGE_REQUIRED = NO；ROADMAP_DIRECTION_CHANGE = NO。完整证据、依赖与授权边界见 [GOV-ARCHGATE1 Gate 记录](../architecture/GOV-ARCHGATE1-POST-HLV3-REVIEW.md)。GOV-ARCHGATE1 = DRAFT_REVIEW_PENDING；SP-005A4-HLV4 = NEXT / NOT AUTHORIZED，独立任务与明确授权前 REAL_SEND = FORBIDDEN。Roadmap state != execution authorization。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = AFTER_HERMES_ADAPTER_STABILIZATION / NOT AUTHORIZED；Memory Evolution V1 = AFTER_SP-005A2-P1 / PLANNED。OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED_BY_OFFICIAL_HOST_CAPABILITY（H1/H2 blocker 保留）。本轮 NO_REAL_HOST_OPERATION = true、NO_REAL_SEND = true；历史证据只引用，不重跑。

以下HLV1～3 Draft交付快照、HLV0设计预期与技术合同原样保留为历史；历史case PASS不等于当时已经canonical DONE，当前治理状态以上文为准。

## HISTORICAL — HLV3 Draft 执行结果

在 canonical Base `4c9c5aaf9e9ed2995086781e32241abf23436dcb` 上执行 HLV3，结果 `PASS`，最高证据 `REAL_HOST_DRY_RUN_PASS`；见 [HLV3 Living Dry-Run / Crash Recovery](../validation/SP-005A4-HLV3-HERMES-LIVING-DRY-RUN.md)。真实隔离 Gateway lifecycle 下执行32个 validation-only case，并持有 native A3 permit/capability 跨真实 planned stop/restart，LIFE-01～03 拒绝旧权限；Core mutation、CLAIMED、permit issue/consume、append/flush/fsync local fake journal 与 CR-01/02/06/07 fresh-process crash 均真实执行。NORMAL、DUP、PERMIT-01～09、CR-01～10、identity/world/writer/generation/privacy fences 的实际结果均 PASS，逐项边界与证据类型见报告；没有把下文 HLV0 全部冻结 RV 预期整体升级。

Living validation execution path 的 real transport invocation/network send 均0，fake-only DI + import/socket hard-deny；Gateway 自身新增日志为 NO_SEND_OBSERVED。protected validation session 明确 NOT_REAL_INBOUND。Default 未变、config match、command sync off，最终 Test stopped；没有生产 Runtime/Core/Hermes patch。Fake Core SENT 不代表真实 provider SENT，SENT/ACKNOWLEDGED 仍 NOT_TESTED，ACK/complete SessionSource/native permit consumer gaps 保留。H-LV4 仍 NOT_AUTHORIZED，Full Private RP 仍 BLOCKED_BY_OFFICIAL_HERMES_HOST_CAPABILITY；HLV3 Draft 当时尚待独立治理；现已 DONE，Gate 结论见顶部当前状态。本节是当前 HLV3 实测；以下 HLV1/HLV2及HLV0历史原文保留。

## HISTORICAL — HLV2 Draft 执行结果

在 canonical Base `991a988c9f8c2a80eda834697af81957fbe8688d` 上独立执行 HLV2，结果 `PASS`；证据见 [Hermes Host Lifecycle / Authority](../validation/SP-005A4-HLV2-HERMES-HOST-LIFECYCLE-AUTHORITY.md)。两轮真实 Test Gateway start/planned stop、Test profile load、Discord connection/disconnection、persistent identity 与不同 process-start identity 已验证；Default Gateway 未变、config fingerprint 一致、command sync off 且无新 attempt，最终 Test stopped。旧 authority/capability 的 REJECT 来自实际 lifecycle facts + synthetic local inert comparison；没有真实 capability/permit/执行管线验证，不将冻结 RV/CR 预期整体改成 PASS。

`EVIDENCE_LEVEL = REAL_HOST_LIFECYCLE_AUTHORITY_PASS`。完整 SessionSource hook、native authority/plugin epoch、native permit consumer 与 ACK validator 的 HOST_GAP 保留；named Test profile 无既有 session，session persistence 仅观察历史 default metadata，配合源码/local comparison 分类。`REAL_INBOUND / REAL_SEND / LIVING_OPERATION / PERMIT_CONSUMED = NO`；普通 Hermes recovery 仍 MAY_RESEND，Living recovery 未连接。REAL_HOST_DRY_RUN_PASS 尚未取得，SENT / ACKNOWLEDGED 未测试。H-LV3 = NOT_AUTHORIZED；H-LV4 = DEFINED_ONLY / NOT_AUTHORIZED；Full Private RP = BLOCKED_BY_OFFICIAL_HERMES_HOST_CAPABILITY。下文 HLV0/HLV1 为保留的阶段历史，当前有限 HLV2 结果以上述独立证据为准。

## HISTORICAL — HLV0 canonical state

Phase = SP-005A4-HLV0；RESULT = DONE（canonical main `08bf82e89f7a4572f4931105cc5e6927ae1c5214` 已由 ChatGPT / 小雪独立核验；原 Base 为历史开工基线）；Base = `eedc32b719336ba063b99da95eac4e2b6a56c0c5`。SP-005A3 = DONE；B01-B34 = SIMULATED_PASS；B1-08_CORE_PASS / B1-09_CORE_PASS 保留。DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；SP-005A2-P1 = NOT AUTHORIZED；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES。Hermes real Host validation = PENDING_REAL_HOST_VALIDATION；OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED；H1 = BLOCKED；H2 = BLOCKED。NO_REAL_HOST_OPERATION = true；NO_REAL_SEND = true。

本矩阵为 DESIGN_ONLY；全部case NOT_EXECUTED，不能把预期写成实际PASS。H-LV1/2/3均待独立执行授权；H-LV4 = DEFINED_ONLY / NOT_AUTHORIZED。权威权限、能力来源与STOP见 [HLV0架构](../architecture/SP-005A4-HERMES-LIVING-VALIDATION.md)；现有 [A3 B01–B34 executable mapping](SP-005A3-HOST-BINDING-TEST-MATRIX.md)只是 SIMULATED_PASS。历史2026-09-30仅 HISTORICAL_EVIDENCE，重新取得当前证据。

上述 `DESIGN_ONLY / NOT_EXECUTED` 是 **HLV0 冻结时的历史状态**，不是本 Draft 的 HLV1 当前结果。E0 已另行取得隔离环境的 `REAL_HOST_LIFECYCLE_PASS`；[HLV1-R1 当前只读证据](../validation/SP-005A4-HLV1-HERMES-READONLY-DISCOVERY.md)在同一 Draft PR #37 中记录 `ENVIRONMENT_GATE = PASS`、`SP-005A4-HLV1-R1 = PASS`（待独立审核），最高仅 `REAL_HOST_READONLY_PASS`。H-LV2/3/4 的 mutation、fake side effect、真实发送场景仍 `NOT_EXECUTED / NOT_AUTHORIZED`，不能由 E0/HLV1 自动升级。

## HISTORICAL — HLV1-R1 Draft 能力映射

固定 Test Home 的当前身份、配置与受保护 registry 已重新比对；Discord Bot/Server/Channel 只通过当前认证 GET 核对。源码与本轮 venv 解析到同一 Hermes checkout `01382698fc32ec7740b6a204d9b7a6abeac74d33`、package metadata `0.21.3`。标签表示只读来源/缺口，**不是集成测试 PASS**；完整路径、限制与脱敏证据见 HLV1-R1 报告。

| A3 / HLV0 item | Current Hermes read-only finding | Status | Evidence level / next gate |
| --- | --- | --- | --- |
| Host identity / Binding Authority | Test Home install ID、持久 named profile、E0 process identity、Life Engine registry | KNOWN | REAL_HOST_READONLY_PASS；Authority wiring 未实现 |
| authority epoch / plugin epoch | plugin manager force reload 与 Gateway/adapter lifecycle 可定位；A3 epoch 非 Hermes 原生字段 | DISCOVERABLE | H-LV2 验证撤销排序 |
| Core generation | Life Engine protected registry/Core，不能由 Hermes session 推断 | KNOWN | REAL_HOST_READONLY_PASS（来源） |
| Owner / trusted inbound | Discord provider author/message/guild/channel ID 与 adapter admission | KNOWN | 未制造 inbound；pairing 等路径需独立 Owner fence |
| HostIdentityEnvelope / session identity | SessionSource、profile namespaced key、SessionEntry.session_id | DISCOVERABLE | plugin platform-event hook 不传完整 source；H-LV2 处理 |
| Explicit trusted outbound target | DeliveryTarget 显式 chat_id 与 Discord adapter send(chat_id) | KNOWN | origin/home/thread override 不可用于 Living |
| Plugin / Gateway lifecycle | PluginManager、GatewayRunner、adapter connect/disconnect | KNOWN | E0 lifecycle PASS 独立保留；H-LV2 验证旧能力拒绝 |
| Execution permit consumer | DeliveryTransport → DiscordAdapter.send → channel.send | DISCOVERABLE | 无现成 permit hook；H-LV3 前必须专用执行 fence |
| DeliveryEvidence | provider message ID / SendResult 为 SENT 候选 | DISCOVERABLE | 独立 validator 未实现；不得称 SENT |
| ACK validator | 无可信最终交付 ACK 合同 | HOST_GAP | ACKNOWLEDGED 不得由 API success 推出 |
| Recovery association | Session origin 与 Hermes 普通 delivery ledger；A3 B1 只读 recovery | DISCOVERABLE | 通用 ledger 可重送，Living 必须隔离 |
| Auto retry | boot ledger sweep、reconnect/flood、base retry、Discord reference fallback | KNOWN | CLASSIFIED；H-LV3 前确认 Living 路径不自动 resend |
| Capability Vault | A3 内存 Vault 与 Hermes profile-scoped Test Home credential | DISCOVERABLE | 不暴露 raw capability/token |

RV-01 的 **Test Gateway lifecycle** 由 E0 独立记录，不将本矩阵全部 RV-01 预期升级；RV-10/11/12 在 HLV1 只完成身份来源发现，错误身份的实时拒绝测试仍留 H-LV2。其余 RV/CR 场景仍按下文冻结预期，未执行。Exact route 无直接只读 runtime projection，保持 `HOST_GAP_ACCEPTED` 的间接一致性边界；Living real send、ACK、Full Private RP 均未授权。

## 场景统一前置与证据规则

以下每项 Preconditions 都包含：该phase单独授权；架构所列11项隔离门禁全部已核验；exact测试Host/Agent/Profile/bot/channel/Owner/target、separate root/instance/generation；当前可信session与Core writer_epoch/world_revision（需要时）；网络send被禁用；生产Gateway/config/cron untouched。缺任一则 BLOCKED，不能执行。测试管理动作通过可信lifecycle_transition排序，不跨transport持锁，不修改冻结business policy。

Transport count 是“本case新增fake local journal entries / real network calls”；所有case real=0。Core基线及变更由受信只读projection/receipt核验，Host metadata只存关联，不宣称业务状态。permit字段记录判断而非raw token。Recovery result引用B1公有query_operation_recovery；未提交NOT_COMMITTED不是新执行许可；没有原exact operation identity/digest则 UNKNOWN/拒绝，不猜operation。所有case automatic resend = forbidden，Resend allowed? = NO。

真实Gateway restart证据须旧/新Gateway process identity、服务stop/start日志、重新load的live hook及绑定；fresh Python/os._exit证据单列PROCESS_BOUNDARY。CR使用真实subprocess/fresh Python/os._exit（隔离fixture），不能用monkeypatch exception冒充。Gateway故障注入仅在未来隔离服务获得单独授权后执行，缺安全注入点记BLOCKED，不操作生产。

## RV-01 — Host startup

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV1 / H-LV2。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | H-LV1只读检查已运行测试Host；真正startup留H-LV2单独授权；包含统一隔离/授权前置 |
| Operation | 读取运行版本/process/root/binding；H-LV2启动独立测试Host |
| Crash / transition point | 旧Host退出/新Host启动边界；H-LV1不触发transition |
| Durable truth expected | Core generation与已有day/budget/Intent/Attempt不变 |
| In-memory truth expected | 新process不继承旧内存credentials；若authority同时重启则新epoch |
| Host truth expected | 身份与当前安装/Profile/Agent唯一匹配；错误Host拒绝 |
| Permit expected | H-LV1无permit；H-LV2不签permit |
| Transport count expected | 0 / 0 |
| Recovery result expected | 无operation则N/A；已有未决claim仅只读恢复/协调 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-01只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-02 — plugin initial load

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV2。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 已有plugin/harness由另一实施任务授权；此处不安装；包含统一隔离/授权前置 |
| Operation | 在独立Host显式load并捕获实际注册/加载事件 |
| Crash / transition point | 首次load边界 |
| Durable truth expected | Core业务状态与generation不变 |
| In-memory truth expected | 新plugin_epoch；authority epoch仅随authority start改变 |
| Host truth expected | 真实load证据，文件存在不算loaded |
| Permit expected | 不签permit |
| Transport count expected | 0 / 0 |
| Recovery result expected | 无新operation；已有CLAIMED仅协调 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-02只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-03 — plugin reload

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV2；有效permit正例H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | H-LV2用拒绝测试凭据；H-LV3有未消费isolated permit；包含统一隔离/授权前置 |
| Operation | isolated unload/reload，竞争旧capability/permit调用 |
| Crash / transition point | reload revoke先行与consume先行两种排序 |
| Durable truth expected | reload本身不改generation/day/budget/cooldown/Intent/Attempt |
| In-memory truth expected | 新plugin_epoch；旧capability/permit失效，snapshot重取 |
| Host truth expected | 真实旧hook移除/新hook加载，旧请求拒绝 |
| Permit expected | reload先行拒绝；consume已先行最多一次local side effect，不声称撤回 |
| Transport count expected | H-LV2 0 / 0；H-LV3 0或1 / 0 |
| Recovery result expected | COMMITTED关联仅reconciliation，不重签 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-03只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-04 — Gateway restart

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV2；未决claimH-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 安全独立Gateway服务与stop/start证据；不能用fresh Python替代；包含统一隔离/授权前置 |
| Operation | 停止/启动测试Gateway并重新核验binding |
| Crash / transition point | 真实Gateway process终止/重新启动 |
| Durable truth expected | generation与Living业务保持；未决CLAIMED不冒充SENT |
| In-memory truth expected | 旧plugin/permit失效；authority若独立未重启其epoch不伪称改变 |
| Host truth expected | 旧新Gateway身份与新live hook证据完整 |
| Permit expected | 旧permit拒绝；H-LV2零issuance |
| Transport count expected | 0 / 0 |
| Recovery result expected | 有未决claim则B1 COMMITTED关联，NO PERMIT |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-04只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-05 — authority restart

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV2 / H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | per-install protected single-writer metadata；原operation关联存在或已丢失；包含统一隔离/授权前置 |
| Operation | 真实终止authority进程并fresh process启动 |
| Crash / transition point | authority start边界 |
| Durable truth expected | Core generation/business不变 |
| In-memory truth expected | 新binding_runtime_epoch；vault/permit不可恢复 |
| Host truth expected | current install绑定重验；旧authority调用stale |
| Permit expected | 旧permit全拒绝，不持久恢复 |
| Transport count expected | 0 / 0 |
| Recovery result expected | 原exact identity/digest恢复COMMITTED关联，仅协调 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-05只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-06 — target change

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV2；claim raceH-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 可信管理面指定新测试target，旧target受信但已stale；包含统一隔离/授权前置 |
| Operation | lifecycle_transition内变更target，旧请求与consume竞争 |
| Crash / transition point | target transition与claim/consume排序 |
| Durable truth expected | 若target先行claim拒绝零Attempt；claim先行保留CLAIMED不退款 |
| In-memory truth expected | binding revision变化，旧capability/permit失效 |
| Host truth expected | 新target需exact绑定；无fallback/default route |
| Permit expected | 旧target permit拒绝；consume先行最多一次fake且只原exact target |
| Transport count expected | H-LV2 0 / 0；H-LV3 0或1 / 0 |
| Recovery result expected | CLAIMED仅reconciliation，不能自动迁移发送 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-06只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-07 — generation transition

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV2 / H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | separate root备份/restore安全路径；旧凭据已记录脱敏摘要；包含统一隔离/授权前置 |
| Operation | 可信restore改变Core generation，并在最后precheck后注入transition race |
| Crash / transition point | management barrier内generation与permit consume排序 |
| Durable truth expected | 新generation；CLAIMED恢复结果按冻结Core restore contract，不由Host伪造 |
| In-memory truth expected | 旧normal/recovery capability与permit全stale |
| Host truth expected | 绑定当前registry generation，拒绝旧receipt跨代写 |
| Permit expected | GENERATION_STALE，零新副作用；最后generation barrier成立 |
| Transport count expected | 0 / 0 |
| Recovery result expected | 当前受信新generation recovery按B1；不可恢复执行权 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-07只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-08 — stale session

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV2 rejection；mutation路径H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 旧closed/wrong session与fresh trusted session分开；包含统一隔离/授权前置 |
| Operation | 用旧session query/prepare/claim/consume；fresh session只读协调 |
| Crash / transition point | session关闭/替换后旧请求 |
| Durable truth expected | 旧请求零mutation/零新增Attempt |
| In-memory truth expected | 旧session权限拒绝，不刷新原envelope授权 |
| Host truth expected | 真实Host session continuity与Core mapping分别记录 |
| Permit expected | 旧session permit拒绝 |
| Transport count expected | 0 / 0 |
| Recovery result expected | 当前recovery-only权限可读projection；无execute |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-08只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-09 — stale World revision

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV2 rejection；prepare/claim/replay H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | Core World已更新，WriterEpoch可仍有效；原receipt存在；包含统一隔离/授权前置 |
| Operation | 旧revision prepare/claim/receipt replay及facade path |
| Crash / transition point | 预检后World先提交，Core事务再进入 |
| Durable truth expected | WORLD_STALE；业务revision/Attempt不新增，receipt不绕过授权 |
| In-memory truth expected | 旧envelope/handle拒绝，不静默更新revision |
| Host truth expected | Host来源与当前Core World明确区分 |
| Permit expected | 零新permit；旧session不执行 |
| Transport count expected | 0 / 0 |
| Recovery result expected | fresh trusted read-only recovery COMMITTED只关联；fresh mutation replay execute=false |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-09只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-10 — wrong Owner

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV1只读来源；H-LV2/3拒绝。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | wrong principal/platform/forwarded/subagent与Owner allowlist不匹配；包含统一隔离/授权前置 |
| Operation | 测试受信拒绝路径；model/tool JSON伪造identity也拒绝 |
| Crash / transition point | 进入授权前拒绝 |
| Durable truth expected | 零inbound/prepare/claim业务mutation |
| In-memory truth expected | 不造有效envelope/capability |
| Host truth expected | Owner来源必须Host认证；昵称不能授权 |
| Permit expected | 无permit |
| Transport count expected | 0 / 0 |
| Recovery result expected | 未经授权不得lookup，拒绝不泄漏operation存在 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-10只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-11 — wrong channel

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV1只读来源；H-LV2/3拒绝。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | platform相同但测试channel/destination不匹配；包含统一隔离/授权前置 |
| Operation | wrong channel query/execution请求与旧target请求 |
| Crash / transition point | channel/target fence前拒绝 |
| Durable truth expected | 零业务mutation/新Attempt |
| In-memory truth expected | 不签capability或permit |
| Host truth expected | 拒绝，无last route或fallback channel |
| Permit expected | 无permit/旧target拒绝 |
| Transport count expected | 0 / 0 |
| Recovery result expected | 错误binding recovery拒绝；不泄漏结果 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-11只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## RV-12 — wrong Profile / Agent

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV1只读校验；H-LV2/3拒绝。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 相同路径或instance字符串但不同selected Host/Profile/Agent；包含统一隔离/授权前置 |
| Operation | 提交wrong identity binding校验，比较多root/配置/Gateway |
| Crash / transition point | binding authorization前拒绝 |
| Durable truth expected | 零跨instance读取/写入 |
| In-memory truth expected | 没有有效capability |
| Host truth expected | install/root/Host/Profile/Agent完整绑定拒绝 |
| Permit expected | 无permit |
| Transport count expected | 0 / 0 |
| Recovery result expected | 错误install/context拒绝lookup |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；RV-12只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## CR-01 — before Core commit crash

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | PREPARED与correlation已持久保存；claim未commit；包含统一隔离/授权前置 |
| Operation | fresh process在begin_attempt前退出；可另测安全事务rollback注入点 |
| Crash / transition point | os._exit在Core commit前，保存真实退出点 |
| Durable truth expected | 无新Attempt；原PREPARED/业务基线不变，事务rollback按Core |
| In-memory truth expected | vault丢失；无permit |
| Host truth expected | 关联可存在但不是CLAIMED truth |
| Permit expected | 无permit，恢复不签 |
| Transport count expected | 0 / 0 |
| Recovery result expected | NOT_COMMITTED；不能自动claim或换operation ID |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；CR-01只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## CR-02 — durable CLAIMED / response lost

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 有效isolated executor/session；原exact operation identity/digest；包含统一隔离/授权前置 |
| Operation | begin_attempt提交后响应写出前os._exit |
| Crash / transition point | durable CLAIMED commit后，response lost |
| Durable truth expected | 一个CLAIMED Attempt，operation COMMITTED |
| In-memory truth expected | 没有成功返回的execution资格；旧vault进程丢失 |
| Host truth expected | response/Attempt association未保存；不能按超时猜未提交 |
| Permit expected | NO PERMIT |
| Transport count expected | 0 / 0 |
| Recovery result expected | B1 COMMITTED+Attempt association，RECONCILIATION_REQUIRED |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；CR-02只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## CR-03 — Host loses Attempt association

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | CR-02后correlation保留但Attempt association missing；包含统一隔离/授权前置 |
| Operation | 新authority读取原identity/digest，只调用recover_operation |
| Crash / transition point | association写入前crash，不删除Core truth |
| Durable truth expected | CLAIMED/receipt不变 |
| In-memory truth expected | 新authority epoch；recovery-only capability |
| Host truth expected | Host恢复association只是关联，不存claimed/send真源 |
| Permit expected | NO PERMIT |
| Transport count expected | 0 / 0 |
| Recovery result expected | COMMITTED typed projection关联恢复，零mutation |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；CR-03只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## CR-04 — recover_operation COMMITTED

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 当前install/generation/Owner/Scope/producer/original actor delegation受信；包含统一隔离/授权前置 |
| Operation | recovery-only capability查询既有operation |
| Crash / transition point | 无mutation；与当前生命周期同步校验 |
| Durable truth expected | operation receipt/Attempt/business不变 |
| In-memory truth expected | 只读权限，不能调用claim/prepare/transport |
| Host truth expected | 恢复关联，记录reconciliation |
| Permit expected | NO PERMIT，返回无execute authorization |
| Transport count expected | 0 / 0 |
| Recovery result expected | COMMITTED != EXECUTE；bounded typed projection |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；CR-04只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## CR-05 — historical CLAIMED recovery

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 旧COMMITTED receipt可能历史execute=true；当前未决CLAIMED；包含统一隔离/授权前置 |
| Operation | trusted recovery读历史projection；另测fresh合法mutation replay |
| Crash / transition point | authority/plugin已重启，旧权限stale |
| Durable truth expected | 原Attempt仍一条，历史receipt不生成新Attempt |
| In-memory truth expected | 新recovery capability不恢复旧permit |
| Host truth expected | reconciliation，无automatic retry |
| Permit expected | NO PERMIT；mutation replay execute=false |
| Transport count expected | 0 / 0 |
| Recovery result expected | COMMITTED/historical CLAIMED，仅association |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；CR-05只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## CR-06 — permit issued / process crash

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 首次execute=true CLAIMED，内存permit已发但未consume；包含统一隔离/授权前置 |
| Operation | fresh process在issue后、consume前os._exit |
| Crash / transition point | permit仅内存，进程死亡 |
| Durable truth expected | CLAIMED已提交；无delivery evidence |
| In-memory truth expected | permit丢失，不重建；authority/plugin旧epoch拒绝 |
| Host truth expected | 未决claim只协调 |
| Permit expected | 旧permit失效，恢复NO PERMIT |
| Transport count expected | 0 / 0 |
| Recovery result expected | COMMITTED关联；不能用receipt历史execute=true签permit |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；CR-06只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## CR-07 — permit consumed / fake side effect / Core record lost

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 首次permit与local fake journal，network禁用；包含统一隔离/授权前置 |
| Operation | consume后fake journal append+fsync，再os._exit，未record_delivery |
| Crash / transition point | fake provider journal durable；Core result尚未commit |
| Durable truth expected | Core Attempt=CLAIMED，无SENT/ACK；实际restore另按冻结Core规则 |
| In-memory truth expected | permit已consume且进程丢失，不恢复 |
| Host truth expected | fake journal一条，Host reconciliation；不能称real SENT |
| Permit expected | NO PERMIT |
| Transport count expected | 1 / 0；恢复增量0 / 0 |
| Recovery result expected | COMMITTED关联；UNKNOWN/reconciliation，不自动resend |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；CR-07只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## CR-08 — delivery result duplicate

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 一个fake journal可信evidence；collector result-only权限；包含统一隔离/授权前置 |
| Operation | 并发重复submit相同evidence，另提交冲突digest/identity |
| Crash / transition point | record_delivery首次commit前后交错 |
| Durable truth expected | 相同evidence幂等仅一次结果；冲突拒绝/协调，CLAIMED/SENT/ACK区分 |
| In-memory truth expected | result-only无执行权限 |
| Host truth expected | 可信provider来源与Core验证，facade digest不是truth |
| Permit expected | 无新增permit |
| Transport count expected | 已有1 / 0；提交增量0 / 0 |
| Recovery result expected | 既有projection可只读核验，无重复Attempt/结果副作用 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；CR-08只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## CR-09 — UNKNOWN result

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | 不能证明provider SENT/ACK；原CLAIMED已存在；包含统一隔离/授权前置 |
| Operation | 可信collector按冻结合同登记UNKNOWN或保持CLAIMED协调，分别标明 |
| Crash / transition point | 不可判定外部结果，不假装失败/成功 |
| Durable truth expected | 冻结Core可接受UNKNOWN时record；否则保留CLAIMED，不擅改生命周期 |
| In-memory truth expected | 无新permit |
| Host truth expected | UNKNOWN/reconciliation，不用人工boolean补SENT/ACK |
| Permit expected | NO PERMIT |
| Transport count expected | 0或既有1 / 0；恢复增量0 / 0 |
| Recovery result expected | 按实际projection记录UNKNOWN或historical CLAIMED，无执行授权 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；CR-09只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## CR-10 — recovery concurrent with lifecycle transition

状态：DESIGN_ONLY / NOT_EXECUTED；阶段：H-LV3。

| 字段 | 冻结预期 |
| --- | --- |
| Preconditions | recovery-only capability，另线程可信reload/target/restore/close；包含统一隔离/授权前置 |
| Operation | 同步barrier控制recovery先行和transition先行，按现有authority排序 |
| Crash / transition point | query authorization与lifecycle/generation transition竞争 |
| Durable truth expected | 只读business不变；restore独立按Core合同改变generation |
| In-memory truth expected | 旧epoch/revision/generation拒绝，当前合法查询有界返回 |
| Host truth expected | 旧结果不能为新lifecycle创建执行权 |
| Permit expected | NO PERMIT（两种排序） |
| Transport count expected | 0 / 0 |
| Recovery result expected | 合法当前COMMITTED或stale拒绝；无私有DB读、无mutation探测 |
| Resend allowed? | NO；automatic resend forbidden |
| PASS condition | 上述各层预期与计数全部由独立原始证据证明；网络调用0、生产untouched；CR-10只取得对应phase证据等级 |
| FAIL condition | 任何预期不符、错误identity被接受、stale绕过、重复Attempt/permit/transport、recovery授予执行权、fake冒充real、message ID当ACK、生产改动；不能取得证据则BLOCKED而非PASS |

## 补充覆盖与独立审核记录

H-LV1必须记录version/Home/Profile/Agent/process/permanent root/instance/generation/Owner/channel/target/session及2026-09-30对照；无法证明唯一binding即BLOCKED。H-LV2将plugin load/unload/reload、真实Gateway restart、authority restart分列，不能拿P2 fresh Python覆盖RV-04。

H-LV3另覆盖：duplicate tick/prepare/claim（同invocation幂等、同ID不同digest conflict）；claim vs target/reload/authority restart；capability concurrent consume；permit duplicate consume、wrong target/Attempt/invocation/purpose/epoch/generation、expiry；consume前pause/enabled/session及最后generation barrier；delivery duplicate；recovery vs lifecycle。期望只有首次execute=true+CLAIMED可签一枚permit，重复consume最多一条fake journal记录，replay/recovery零permit，零真实网络。trusted inbound无稳定ID INBOUND_UNVERIFIED，sameID+samepayload幂等，同ID不同digest conflict；query仅SOUL_RESPONSE、无Prompt注入；status默认20/上限100及JSON bounds。LEGACY继续显式路由；PENDING/ACTIVE在任何legacy callback副作用之前LIVING_HANDOFF_REQUIRED，失败无fallback。

CR-01/02/06/07需subprocess/fresh Python/os._exit、准确注入点、退出码、stdout缺失/已返回情况、Core projection、metadata关联、journal fsync证据；与真实Host生命周期单独关联，不以测试进程身份冒充Gateway身份。不存在安全crash注入点则BLOCKED，不能patch生产或放宽A3。

证据报告逐case包含authorization、exact code/Host versions、environment摘要、前后epochs/generation/session、原operation/digest、上述12字段的actual值、证据文件digest、expected vs actual、PASS/FAIL/BLOCKED。原始身份/密钥仓库外受保护，报告脱敏。独立审核允许REAL_HOST_READONLY_PASS / REAL_HOST_LIFECYCLE_PASS / REAL_HOST_DRY_RUN_PASS逐级确认；不自动升级成REAL_HOST_SENT或ACKNOWLEDGED。

H-LV4这里只定义one isolated real text delivery计划；未来先H-LV1～3独立PASS，再独立架构/实现/real-send授权与预算、provider SENT contract、explicit target。cron属于separate later phase。未实现的真实transport、可信mapper及ACK contract都列为待发现/待单独设计，不在HLV0实现。
