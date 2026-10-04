# SP-005A2 — Living Runtime Host Binding 架构

## CURRENT — HLV4-R0 authority 修订（2026-10-04）

当前任务 Base：`71063c189ba2de501acdadca61e212e1cfc722a4`；GOV-ARCHGATE1 已 canonical DONE。HLV0～HLV3 DONE；REAL_HOST_DRY_RUN_PASS CONFIRMED。HLV4-A = BLOCKED_BY_FROZEN_AUTHORITY_CONTRACT；ARCHITECTURE_CHANGE_REQUIRED = YES，已路由到 HLV4-R0；HOST_PATCH_REQUIRED = NO。原因是 A3仅授权SIMULATED_CONTACT；不是Hermes capability blocker。

[Real Delivery Authority合同](SP-005A4-HLV4-REAL-DELIVERY-AUTHORITY.md)冻结目标typed mode/purpose、default-deny RealDeliveryPolicy、内存one-shot validation grant与独立real/simulation consumer；R0 = DRAFT_REVIEW_PENDING，现有Runtime仍不具备现实用途。LOCAL_ORDER = HLV4-R0 → HLV4-R1 → HLV4-A → HLV4-B → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1；ROADMAP_DIRECTION_CHANGE = NO。HLV4-R1 / HLV4-A retry / HLV4-B / P1 = NOT AUTHORIZED，Memory Evolution V1 = PLANNED。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP；REAL_SEND = NO。本轮仅文档，无Host/Runtime/schema/Prompt修改；Full Private RP仍 BLOCKED_BY_OFFICIAL_HOST_CAPABILITY。下列旧治理状态为对应阶段历史，技术合同仅由R0目标显式修订部分补充；实现须另行授权，不自动改现有行为。

## HISTORICAL — R0 前治理记录

当前治理状态见 [Post-HLV3 Gate](GOV-ARCHGATE1-POST-HLV3-REVIEW.md)：HLV0～HLV3 DONE；HLV4 NEXT / NOT AUTHORIZED；REAL_HOST_SENT / ACKNOWLEDGED NOT ACQUIRED，ACK_VALIDATOR HOST_GAP。下列原状态、技术合同与计数保留为历史。

## HISTORICAL — 原 canonical state — A3 已合并

SP-005A3 = DONE；canonical main `eedc32b719336ba063b99da95eac4e2b6a56c0c5`，PR #34 Squash Merge，exact main push CI #36847806554 四矩阵 SUCCESS，已独立核验。B01-B34 = SIMULATED_PASS；B1-08_CORE_PASS / B1-09_CORE_PASS 保留。真实 Hermes/OpenClaw 验证仍 PENDING_REAL_HOST_VALIDATION；P1 未授权，H1/H2/Full Private RP BLOCKED。未来分层计划见 [HLV0](SP-005A4-HERMES-LIVING-VALIDATION.md)；本轮 NO_REAL_HOST_OPERATION = true / NO_REAL_SEND = true。

## HISTORICAL — 原冻结架构 / Draft 实施与验证记录

以下旧状态、原 Base 和“当前”表述指当时；技术合同、测试计数与证据原样保留，不覆盖顶部状态。

**A3 v3 当前实施状态（2026-10-01）**：统一 Base `b78b849b1bfac1cbd28359cfb317fd1d4cb84402`，已保留 GOV-DOC3 文档校准。A3 Host-neutral implementation 与自动验收见 [A3 验证报告](../SP-005A3-VALIDATION.md)；SP-005A3 = PENDING_INDEPENDENT_REVIEW，B0 / B1 Architecture / B1 Implementation = DONE。下文未实现、BLOCKED 和 deferred 描述是 A2/B1 冻结及 GOV-DOC3 时点的历史状态，不覆盖本段当前状态；冻结技术合同仍有效。P1 未授权，真实 Host 验收 PENDING_REAL_HOST_VALIDATION，Full Private RP / H1 / H2 BLOCKED。历史 Hermes 证据不升级为 Living Host PASS、ACK 或 Organic Contact real-send PASS。

**2026-10-01 当前状态校准**：B1 Architecture / Implementation = DONE；合并后 canonical main 为 `f83d36c76fea6de1a31b449535d5df6cea3909b5`。合并与 exact main push CI 证据见 [B1 验证映射](../SP-005A3-B1-VALIDATION.md)。下文历史 Base 与冻结合同保留；A3 Host 层仍 BLOCKED，恢复实施须另行授权。历史 Hermes legacy 测试不升级 Living R01–R12 或未执行的 Host 子集。

状态：SP-005A2 = DONE；SP-005A2-R1 = DONE。R1 固定 Base / canonical main：`861734b0c4179e56a3251a775d831cd246278d7f`（A2 原审计基线为 `84493be98d7ed675de6b859cafdb014a900325ca`）。SP-005A0 / A0-R1 / A1 和 H0 implementation 已 DONE。R1 仅修订 Session World Revision Fence 合同，不修改 Runtime 或添加 Core tests；新 facade/token/adapter 尚未实现。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。A2 / R1 架构 PR 只修改文档，不改变 [A0 + R1](SP-005A-LIVING-RUNTIME.md) 的状态机、预算、迁移或恢复规则。现状依据 [CURRENT_HOST_BINDING_AUDIT](SP-005A2-CURRENT-HOST-BINDING-AUDIT.md)。

## 1. 真源与四层边界

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

```text
Host Trigger Layer：tick / Owner action / inbound / context / execution / result
          ↓ 经认证的调用来源；不是模型权限字段
Trusted Binding / Capability Layer：认证、持久绑定、授权、撤销、幂等、路由
          ↓ LivingContext / LivingTickContext（仅受信代码构造）
Living Runtime Core：Scope、generation、Day、Schedule、reservation、Attempt
          ↓ CLAIMED 持久提交且事务结束，才可能交给执行器
Host Delivery Layer：受控外部副作用、渠道证据；不拥有生活业务真源
```

Host scheduler 只触发 tick，不持有 activity/contact schedule、预算、choice 或 follow-up 真源。模型只准备数据，不认证 Owner、不构造 Scope、不决定发送资格。PhotoOpportunity / VoiceOpportunity 可作为有界计划展示，不是媒体作业或发送授权；A3 不调用 ComfyUI/TTS。

只服务 SOUL continuity；拒绝 RP Living injection、RP private history、跨 World contact、Bridge bypass。A2 的局部联系执行合同不等于整个 Host 的 final-output transaction，不能约束所有原生模型回复、persistence/replay/delivery/stream。

## 2. Trusted binding 与身份封套

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

绑定由操作员在受信本地管理面显式建立：安装标识、instance、官方 Host 来源、Profile/Agent、认证 Owner、既有 ACTIVE SOUL Scope、明确 target。不得自动创建 Soul World，不从 workspace 或 agent 名猜 Scope，不接受正文、模型 tool 参数或手工 probe JSON 作为凭据。

候选 `HostIdentityEnvelope` 版本为 `SP-005A2-binding-v1`。下表的必填针对获准业务调用；发现阶段可以 UNKNOWN，但不能给依赖缺失字段的方法签发 token。

| 字段 | 要求与来源 | 稳定性 / 重验 |
| --- | --- | --- |
| host_kind、host_version、installation_evidence | 必填；官方包/checkout/加载来源由受信 connector 采集 | 安装或版本变化失效，重新 attestation |
| install_id、instance_id | 必填；操作员建立的不透明安装 ID + durable registry ID；路径不是 install_id | 长期稳定，每次核 registry；安装复制不能复用凭据 |
| host_identity | 必填；Hermes canonical HERMES_HOME/Profile；OpenClaw Gateway/config/profile、agentId、canonical workspace | 每次调用核对；不能只检查 OpenClaw agent/workspace |
| principal_binding、scope_binding | 必填；Owner 认证映射、完整 owner/soul/world/timeline 引用 | 每次解析当前映射与 Core Scope；tick 使用服务授权引用，不冒充在线 Owner |
| binding_revision、capability_revision | 必填；binding authority 单调版本及授予的方法集合 | target/Owner/Scope/Host 配置或能力变更撤销旧版本 |
| plugin_epoch、binding_runtime_epoch | 必填；可信 connector 和 authority 启动/加载代次 | per-load；旧调用凭据失效，不从模型接收 UUID |
| generation、core_runtime_id | 必填；当前 durable registry 与 World incarnation | 每次重验；不同于插件 epoch |
| session_binding、writer_epoch、world_revision、viewer、purpose | context/prepare/claim 和聊天 Owner action 必填；tick、入站事件、后台结果可无 chat session | 方法特定校验，缺失不建立隐式默认 Session |
| invocation_id、producer_namespace、received_at、provenance | 必填；受信事件标识、服务 namespace、aware UTC 接收时间、认证来源 | per-call；同一事件 retry 保持 operation key，时间不能来自正文 |
| target_binding_revision | prepare/claim/result 必填；已确认 target 映射的版本 | 每次与 Intent/Attempt 和当前授权核对 |

tick 的 expected policy revision 来自 authority 读取的当前 Core 策略；expected Living revision 由受信 command ticket 保存，不由模型提供。Owner 看到的变更命令绑定其确认时的 revision；冲突后重新确认，禁止偷偷取最新 revision 覆盖原决定。

### 凭据、进程与持久化

`binding token` 是 authority 签发的不可伪造不透明 capability handle，绑定上述身份、方法、时效及 invocation payload digest。不得进入 Prompt、模型参数、tool 文本或日志；仅限受保护本地 IPC，同 OS 信任边界，不能声称隔离同用户恶意进程。Host event ID/Intent ID 都不是 bearer 权限。

A3 候选 authority 采用每安装一个受信本地服务，拥有现有 Core runtime/session factory 生命周期，持有 snapshot 对象。服务单实例，工作连接显式附着同一 Core runtime_id；不能每次请求启动新 World incarnation。服务重启创建新 incarnation 并走既有恢复，旧 session/snapshot/tokens 全失效；插件 reload 不重建服务。当前仓库没有该服务。

绑定映射、revision、模式、撤销和调用关联日志存安装目录的独立受保护版本化 metadata；不是 Living schedule/quota 真源，也不是 Schema 9。单写者、原子替换、校验摘要、限制权限；损坏/丢失拒绝服务并由 Owner 重绑，不能从聊天恢复。Core durable receipt 是业务操作唯一收据，metadata 只关联调用；不声称两个存储原子提交。成功响应丢失时用原 operation ID 重查，不能生成新 ID 重做副作用。

authority 重建/reload barrier 会撤销旧 transport handles；仅服务端保有 epoch 活跃表。预检查到 Core 提交之间的 Scope/World 状态仍由同一 Core SQLite 事务重验。每实例 authority 串行处理绑定变更、claim 与执行权消费；不在现有非重入 durable lock 外再套同锁调用 Core。SQLite/durable 锁绝不跨网络、模型或 Host 等待。

### SP-005A2-R1：Session World Revision Fence

固定 Base 的 [LivingRuntime._authorize](../../runtime/life_engine/living_runtime.py) 已检查 Principal、Scope、Session OPEN、Session Principal/Scope、Session WriterEpoch 和 World WriterEpoch，但尚未检查 session 的 World revision。[Living projection](../../runtime/life_engine/living_projection.py) 已对不一致返回 `WORLD_STALE`。因此旧 session 可被 projection 拒绝，却仍可 prepare，甚至 claim 得到 `CLAIMED / execute=true`。这是 R1 固定 Base 的 Core 缺口；当前 SP-005A3-B0 已完成最小修复、独立审核、合并及 exact main push CI，状态为 DONE，具体证据见 [B0 验证映射](../SP-005A3-B0-VALIDATION.md)。本节冻结合同不变，A3 Host 层仍未实现。

所有 session-bearing `LivingContext` 必须携带受信 `session_id`、`writer_epoch`、`world_revision`；canonical 路径可继续使用 `PromptSessionContext`。这些字段只能由受信映射构造，不得来自 model text、tool arguments 或 Host 自报 JSON。对 query_context、prepare_contact、claim_attempt、session-bound Owner action 以及任何当前或未来的 session-authorized Living mutation，Core 必须验证：

```text
context.session.world_revision == current World.revision
```

不一致立即返回 `WORLD_STALE`，在 prepare、claim、Owner session command 或其它业务 mutation 前拒绝。`SESSION_STALE` 表示 Session binding / OPEN / WriterEpoch 等身份生命周期失效；`WORLD_STALE` 表示 Session 仍可识别，但所确认的 World revision 已过期。不得用 `SESSION_STALE` 代替 World revision 错误，语义与 Living projection / Prompt 保持一致。无 chat Session 的 `LivingTickContext` 不适用此 fence；无 session 的受信管理或 result-only 路径仍按原权限合同执行。

最终校验必须在 `LivingRepository.transaction()` 打开的同一事务内，顺序为：

```text
BEGIN transaction
→ load current World → validate Scope
→ validate Session → validate WriterEpoch → validate current World revision
→ validate Living root/generation
→ lookup operation receipt（命中则返回；claim 强制 execute=false）
→ 未命中：validate expected Living revision CAS → business mutation
COMMIT
```

Facade precheck 负责快速拒绝与 capability validation；Core transaction 是最终业务权限 fence，两层缺一不可。最小竞态为：facade 预检查看到 R1 → 另一事务将 World revision 改为 R2 → prepare/claim 进入 Core 事务。此时旧 session 必须 `WORLD_STALE`，零业务 mutation、零新增 Attempt、零发送资格；不得依赖事务外预检查或降级 legacy。Scope、Policy 并发变化继续由各自冻结规则与 Core 同事务校验/CAS 处理，不以本修订替换。

#### 授权重放与操作收据恢复

Authorization replay 必须先通过当前授权。旧 session 即使使用历史成功的 operation ID 和相同 payload，也必须先返回 `WORLD_STALE`；不得先返回 operation receipt 来绕过授权 fence。

Operation receipt recovery 则须先重新取得当前 World revision 对应的 fresh trusted session / ticket，再使用**原 operation ID + 原 payload**调用，保留原 producer namespace、principal、Scope、generation 等既有幂等关联。fresh 指重新取得受信授权上下文，不要求仅因 revision 更新而更换 session_id，也不改变既有 operation identity。此后才允许既有 receipt 机制工作：已提交则返回原 receipt，不重复 mutation；未提交则在有效授权下、通过既有 expected revision CAS 后执行。不静默更新原确认的 Living revision，也不承诺绕过其它授权或业务冲突。

已提交的 `begin_attempt` 在 fresh session 下重放仍必须 `execute=false`，保持同一 Attempt，不创建第二个 Attempt，不重新签发 execution permit。收据恢复不恢复外部发送资格；若原操作未提交，也必须遵守既有 begin_attempt 的首次合法 claim 规则。

遇到 `WORLD_STALE`，包括响应丢失、提交状态不明时，禁止自动生成新 operation ID、自动 retry mutation、自动重新 claim，或自动刷新 World revision 后静默继续。流程必须是：旧 session → `WORLD_STALE` → 重新取得 fresh trusted session/ticket → 原 operation ID + 原 payload → Core receipt 判定既有提交结果。具体未来场景见 [R1-01～R1-06 测试设计](../planning/SP-005A3-HOST-BINDING-TEST-MATRIX.md#r1-core-fence-未来测试设计)。

## 3. LivingHostFacade 与权限表

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

插件只能使用 facade 的公开有界合同，不调用 repository SQL、私有 `_root` 等方法。模型可传内容与由服务选择的对象引用；所有权限字段来自封套。Facade JSON 最大 16 KiB，context payload 继承 8 KiB；拒绝超限输入，status 默认 20 条、上限 100 条，用绑定 revision 的游标分页；不输出 secrets、全历史或 raw metadata。

公共响应：`contract_version, invocation_id, command_executed, result, error_code, retry_disposition, binding_revision, generation, living_revision`，按方法附最少内容。`command_executed=true` 不是 validation PASS，也不等于可发送。ERROR 明确携带原因；只有 claim 首次成功返回 execute=true。未知字段/枚举拒绝，不降级 legacy。

| 方法 | 调用者与输入 | Core 对应 / 输出约束 |
| --- | --- | --- |
| tick | scheduler 窄 capability + 稳定 invocation ID；无 chat session | LivingTickContext→tick；SILENT / RECOVERY_IN_PROGRESS / RECONCILIATION_REQUIRED / RESERVED / ERROR；无最终自然语言 |
| query_context | 受信 SOUL_RESPONSE session；模型不能选 viewer/Scope | projection.query/revalidate；返回 context handle 和有界数据，不授予 send |
| observe_inbound | 认证 connector event，非模型工具 | observe_inbound；返回去重结果及 revision，不自动创建 follow-up |
| prepare_contact | 与目标会话绑定的 preparation ticket、intent_id、content | prepare_intent；DECIDED→PREPARED；最大 512 UTF-8 bytes，超限拒绝；返回 material digest，不发送 |
| claim_attempt | 受信执行器；明确 target 的 active Soul session、prepared handle | begin_attempt；必须 execute=true 且 CLAIMED 才产生一次执行资格；模型不可调用 |
| submit_delivery_result | 受信 validator/collector；attempt_id、证据引用 | record_delivery；不要求旧 chat session 仍 OPEN，独立 result-only capability；无 send 权限 |
| status | Owner 管理面或受限 Soul session | Living.status 的脱敏、有界派生；不把所有 intents/days 直接放入模型 |

enroll、pause/resume、reconcile、timezone/target/policy update、显式 follow-up、manual activity change 仅允许 Owner authenticated action。聊天入口必须 active session + writer epoch；本地管理面可无聊天 session，但必须稳定 Owner principal、完整 Scope、generation、预期 revision 和显式确认。模型自然语言建议只生成待确认数据；工具调用或“主人说过”不构成确认。

## 4. Tick 与 inbound

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

tick 的 invocation ID 由 scheduler event 构造，producer namespace 隔离 Host/install/binding；同一触发 retry 沿用 ID。不同 ID 的重复 tick 仍靠 Core decision natural key、reservation 与单事务防重。RECOVERY_IN_PROGRESS 可按有界退避触发下一批新 tick，不能在恢复前生成内容或发送；RECONCILIATION_REQUIRED 必须进入 Owner 协调流程，不能映射 SILENT。

RESERVED 仅返回 intent_id/reason reference/revision/expiry，由 authority 建立后续 preparation ticket。不接受 Host 自己的预算计数、时间表或随机选择。Core trusted clock 为受信 aware UTC clock；received_at 是来源证据，不用它替代当前执行时间。

inbound dedupe key 为 `(install_id, host_identity, channel/account, external_event_id)`，映射至稳定 source namespace 与 Core event_id。必须认证 EXTERNAL_USER Owner，拒绝转发、工具结果、模型输出、群内其他人、子 agent 和 UNKNOWN provenance。received_at 取受信 connector 的首次接收时间并持久复用；重复内容不同事件不合并，同事件不同 digest 报冲突。无可靠 event ID 或 Owner 认证则不推进可信水位，返回 INBOUND_UNVERIFIED，不能用新 UUID 假装去重。正文不必存入 observation，也不能自行生成 schedule。

## 5. Context 与 Prompt 模板决定

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

Living snapshot 仅允许 SOUL_RESPONSE；必须核 principal、Soul viewer、ACTIVE Scope、OPEN Session、writer epoch、world revision、generation、Core runtime_id、Living/policy revision 与 valid_until。不能用于 Roleplay，也不是 permanent memory，不自动写 Story/Memory/Lore。Host reload 撤销旧 handle；重新 query 并在使用前 revalidate，不接受 Host 缓存对象自我验证。当前进程 seal 不可跨服务进程搬运，序列化副本不成为凭据。

正式加入 PromptSnapshot 需要新 section 的顺序、预算/裁剪、authority 和版本失效规则。结论：**PROMPT_TEMPLATE_UPGRADE_REQUIRED**。提出独立候选 SP-005A2-P1，模板候选 `SP-005A-living-prompt-v1`，尚未授权。A2 不升级 `SP-004K-prompt-v1`；A3 的 context adapter 仅结构化 query/validate 与 dry-run 展示，不实际拼入模型 prompt。不能通过 legacy prependContext、普通 tool 输出自动注入或伪装 Memory 字段绕过此门禁。

未来经单独审核的拼装需在模型提交前重新 query/revalidate 失效 snapshot；模型返回后的晚到输出约束仍是 Host 的独立 capability 缺口，不由 snapshot 解决。

## 6. Preparation、Claim 与外部边界

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

prepare_contact 仅存内容，不改 reason/target/quota、不新建 Intent、不登记 SENT/ACK。authority 在准备前检查 ticket 的 session/epoch/expiry/target/current binding；旧 material retry 用相同 operation+digest，变更 payload 报 IDEMPOTENCY_CONFLICT。Core 的单事务 revision CAS 继续有效；不能因 CAS 冲突静默重写内容。

claim_attempt 不再申请 quota；保留 A0-R1：reserved_count==cap 合法、当前 Intent 不自我 cooldown、cap/cooldown 后续变化不追溯撤销 reservation。执行敏感条件仍重验。quiet/inbound 阻断可终止旧 Intent、重开有效机会，但再次 ALLOW 是新 Decision/Intent/付费 reservation；已有 Attempt 不能重开重发。

```text
受信执行器 → facade 核身份/session/epoch/target/ticket
            → Core begin_attempt，同事务重验并提交 Attempt CLAIMED
            → 事务和 durable locks 结束
            → 首次 execute=true 的执行器消费本次内存执行权
            → 经单独授权的 Host external send（A3 默认禁止）
            → 独立 evidence validator → Core record_delivery
```

claim 响应只能送受信执行器，不能返回模型。重放 execute=false，即使 state=CLAIMED 也不获得 send 权；不得用新 invocation ID 重领。发送前检查当前 authority epoch 和 target，过期/撤销/连接丢失即放弃并协调，不能长期排队旧执行权。结果响应丢失不能由 Host 自动重试 send。Core transaction 与外部网络不原子，单次调用资格不保证网络恰好一次送达。

A3 默认 DRY_RUN / NO_REAL_SEND：默认不注册真实 transport。普通 dry-run 只预览，不 claim 正式实例；需要验证 CLAIMED/crash 时使用独立测试 instance + fake transport，可消耗测试 reservation，输出 SIMULATED，不产生真实 SENT/ACK 证据。没有真实发送授权时不能为了 UI 好看先 claim 正式 Intent 再无限悬置。

## 7. DeliveryEvidence 与崩溃

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

DeliveryEvidence v1：必填 attempt_id、绑定的 target、state、source、external event ID、observed_at（受信 UTC）、provider evidence reference/digest、validator identity/version。SENT/ACK 另必填 message ID、sent_at；ACK 需独立受信渠道确认及其 observed_at。received_at 可记录 collector 收到证据的时间；不能伪装为渠道发送时间。非发送失败可无 message ID/sent_at。scope/generation 从 authority 的 Attempt 关联取，不由证据正文授权。

validator 必须由受信部署注册，模型字符串、手工 JSON、工具文本、“已发送”、本地文件/prepare 成功皆非证据。provider 原始敏感数据存受保护外部 artifact，库内保持最小脱敏关联；validator 在锁外验证，Core 在锁内核关联及自然键。ACK 缺失只能停 SENT；SENT 证据也缺失则保持 UNKNOWN/协调，不能用“工具没报错”推断成功。

结果 submission 的 operation ID 与 source/event ID 分开：相同 event/digest 幂等，不同 digest 或跨 Attempt/target/message 冲突显式 error/RECONCILIATION_REQUIRED，禁止重复执行 send。旧 plugin token 不可提交；新 collector 经重新认证可对当前 generation 的历史 Attempt 使用 result-only capability。restore 后旧 generation 证据只进入 Owner 协调审计，不直接更新新代次。

| 崩溃位置 | 恢复结论 | 禁止行为 |
| --- | --- | --- |
| claim 前 | 无 Attempt 时可重新认证、重验并用原 operation 继续；先查 receipt | 不能假设 prior call 没提交 |
| CLAIMED commit 后、send 前 | 无法证明未发送时 UNKNOWN / RECONCILIATION_REQUIRED；重放 execute=false | 自动再次 claim/send |
| send 后、DB result 前 | 外部结果不确定；受信 evidence 补录或 Owner 协调 | 因 DB 无 SENT 就重发 |
| SENT 已提交、ACK 前 | 保留 SENT；可重复收集回执；无 ACK capability 就停 SENT | 重发以取得 ACK、伪造 ACK |

插件 reload 但 Core incarnation 未变时，Core 不会仅凭插件 UUID 自动把 CLAIMED 转 UNKNOWN。A3 authority 必须先阻断该绑定的新 claim，核对持久 invocation→Attempt 关联；不确定结果经受信 UNKNOWN 证据或 Owner reconcile 处理。此过程是待实现合同，不能描述成已有插件行为。authority 自身重启走 Core 新 incarnation 恢复后，先执行恢复 tick、处理遗留 CLAIMED，再开放业务。所有路径默认不退款。

### B1：关联尚未保存时的只读恢复

若 Core claim 已 durable commit，但 authority 在保存 invocation→Attempt 关联前崩溃，不能依赖 metadata 推断提交事实，也不能调用 begin_attempt 充当查询。按 [B1 冻结合同](SP-005A3-B1-OPERATION-RECOVERY-PROJECTION.md)，新 epoch 下独立认证的 recovery-only authority 使用原完整 identity / digest 查询 Core durable receipt，恢复经 Core 验证的关联，绝不取得 execute / execution permit。session-bound 查询仍先执行 B0 授权；authority-bound 是独立窄只读权限，不是普通 LivingContext(session=None) 绕过。只读查询不触发恢复 tick、不修改 Attempt；生命周期恢复与协调另走原合同。Core 查询已完成独立审核、合并及 exact main push CI，见 [B1 验证映射](../SP-005A3-B1-VALIDATION.md)；Host authority/epoch 未实现，A3 Host 实施仍待新任务授权。

## 8. Legacy 共存与显式切换

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

| 实例状态 | 唯一 Host 路由 |
| --- | --- |
| 未 enrollment | 保持 legacy context/wake；Schema 8 本身不切路 |
| 已 enrollment，但 binding 未激活/迁移窗口 | 返回 LIVING_HANDOFF_REQUIRED；不 fallback legacy |
| 已 enrollment + 显式激活 Living binding | 仅 facade；Prompt 尚未升级时 context 只能查询/展示，不能伪称模型已获得 Living prompt |

迁移顺序：停止旧 trigger 并排空/隔离旧在途调用 → Owner 明确 enrollment/handoff（初始 paused）→ 建立 binding/capability 与 session 映射 → dry-run 验证 → Owner 显式切换 routing mode/revision → 另行确认 resume。失败停在 paused/协调，不撤销 living_writer 以恢复旧 Engine。

A3 分发必须在任何 legacy 副作用前检查 enrollment，阻断 enrolled 的 legacy context/status/wake/prepare/ack/observe/loop/pause/resume/photo 等 Host 业务路径；doctor 和安装身份读可保留。旧 CLI 的操作员审计用途不得作为插件绕路。当前 Core 部分单写门禁已存在，但整体 Host 路由 fence 尚未实现。新旧 tick 不能同时拥有主动联系决策权；绑定模式必须持久显式，不按先调用的 API 决定。

## 9. Reload、restart、restore 与错误

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

| 事件 | Host/authority 行为 | Core 真源 |
| --- | --- | --- |
| plugin/Gateway reload | plugin/binding epoch 更新，撤销 token、取消旧 context handles、处理未决 claim、重做身份/capability probe | 不自动改变 generation；Day/预算/choice/follow-up 不重建 |
| Host restart | 重新认证并重建 Host session 映射；旧 epoch 全失效；不得恢复可发送 token | 若 authority 仍存活可维持 incarnation；若也重启则显式新 incarnation，恢复会话/Attempt，仍不改变 durable generation |
| Life Engine restore | 重新绑定 registry 新 generation、保持 paused，旧 token/handles/session 失效 | 待发隔离、CLAIMED→UNKNOWN、协调后另行 resume；不自动退额度 |

wrong instance、agent/profile、Scope、principal、Session、writer epoch、generation、target、Attempt、receipt、clock/corruption 均显式 ERROR；不转 SILENT、不 fallback、不无限重试。RECONCILIATION_REQUIRED 是可识别阻塞结果（有 error_code），不是正常静默。普通 quiet/budget 抑制才是 SILENT。Owner 暂停与撤销阻止尚未开始的副作用，但不能追回已经在网络中的请求；该限制必须如实记录。

## 10. Host Capability Matrix

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

AVAILABLE 表示在固定 Base 有该层代码/模拟契约；PARTIAL 表示只覆盖部分条件；MISSING 表示当前接入没有受信实现；BLOCKED 表示禁止使用；NOT_REQUIRED 表示该操作不需要。Host 两列不是实时上游版本认证，真实版本仍须 H0-RV 验证。

| Capability | Core required | Hermes current | OpenClaw current | A2 status |
| --- | --- | --- | --- | --- |
| stable principal | Owner/命令必需 | PARTIAL：sender/platform 匹配 | PARTIAL：external_user + sender/channel | MISSING：持久认证映射 |
| stable session | context/prepare/claim 必需；tick NOT_REQUIRED | MISSING：无 World session 映射 | MISSING：无 World session 映射 | MISSING：A3 映射 |
| scope binding | 完整 SOUL Scope | MISSING | MISSING | MISSING：显式绑定 |
| tick | AVAILABLE：Core | PARTIAL：旧 cron wake recipe | PARTIAL：旧 wake trigger | MISSING：新窄 adapter |
| context injection | projection AVAILABLE，模板未接入 | PARTIAL：legacy pre_llm_call | PARTIAL：legacy before_prompt_build | BLOCKED：等待模板独立升级 |
| prepare | AVAILABLE：Core | PARTIAL：legacy prepare | PARTIAL：legacy prepare | MISSING：Living facade |
| attempt claim | AVAILABLE：Core | MISSING | MISSING | MISSING：受信执行器 |
| outbound send | Core 不发送；需独立授权 | PARTIAL：原生渠道另验 | PARTIAL：原生渠道另验 | BLOCKED：默认 NO_REAL_SEND |
| SENT evidence | validator 必需 | MISSING：当前插件无 validator | MISSING：当前插件无 validator | MISSING：证据 adapter interface |
| ACK evidence | 无 ACK 可停 SENT | MISSING | MISSING | MISSING：不伪造 |
| plugin reload fencing | epoch 撤销必须 | PARTIAL：探测 UUID | PARTIAL：UUID/可选 hook assertActive | MISSING：authority 撤销机制 |
| late-response fencing | 私密 RP 必需 | BLOCKED | BLOCKED | BLOCKED：H1/H2 正交 |
| pre-send authorization | 联系需 CLAIMED | MISSING：Living 路径 | MISSING：Living 路径 | MISSING：局部执行器合同，非全 Host final gate |
| private RP isolation | H0 全部能力必需 | BLOCKED | BLOCKED | BLOCKED |

Hermes：后续 tick 可来自受信 scheduler callback，Owner 命令来自已认证明确 action；现有 pre_llm_call 只能证明 legacy hook 形状。实际 outbound 必须未来受控执行器独占，不沿用 cron 自动发布或模型工具发送旁路。当前无受信 receipt/final-output authorization 证明，只允许官方 Host；compatibility fork 不作依赖。

OpenClaw：Gateway/config/profile + agentId/workspace 一并绑定，不能选默认 agent；tool factory 可提供调用上下文材料，但不是 principal factory。before_prompt_build 与 session continuity 需真实版本探测；outbound 路由/回执另验。before_message_write、before_agent_finalize、message_sending、lifecycleRevision、transcript writer fence 不拼成已存在的统一 final-output transaction。H2 继续 BLOCKED。

## 11. 后续授权和验收

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

SP-005A2-R1 = DONE；SP-005A3-B0 = DONE，二者已完成合并与 exact main push CI。B1 implementation 的历史固定 Base 为 `a27caf372a263932346d5b193ca35c92fea6f5dd`。A3 发现 durable operation recovery 缺少公开只读查询，已停止实施；[B1 架构修订](SP-005A3-B1-OPERATION-RECOVERY-PROJECTION.md)冻结独立 authority-bound recovery 权限、exact identity / fingerprint 校验与无执行资格的投影。SP-005A3-B1 Architecture = DONE；SP-005A3-B1 Implementation = DONE；SP-005A3 = BLOCKED（Host 层未完成，恢复实施须另行授权）。架构与 implementation 已均为 DONE，恢复 A3 仍须重新授权，默认从新 canonical main 建立 v3；A3 v2 保持 clean，不继续实现。

A3 范围仍为受信本地 authority/facade、稳定绑定与 token、tick contract、结构化 context adapter、prepare/claim、delivery evidence adapter interface、enrolled legacy-path fence、fake transport / NO_REAL_SEND sandbox。A3 不默认改 Prompt，不实现真实渠道 validator、真实发送、媒体/语音、H1/H2；若需要 Schema 或其它冻结 Core 合同变化，仍须停止申请独立架构修订。R1 不需要 Schema 9，也不需要 Prompt Template 升级；DATA_SCHEMA = 8、Schema Signature = SP-005A-living-runtime-v1、Prompt Template = SP-004K-prompt-v1 保持不变。正式 Living Prompt 接入仍为 PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = NOT AUTHORIZED。

Prompt 接入候选 SP-005A2-P1 未授权；真实 Host 接线、真实发送需独立任务书和准确版本/目标授权。A2 不依赖 H0-RV PASS。未来测试见 [A3 与 H0-RV Living 扩展矩阵](../planning/SP-005A3-HOST-BINDING-TEST-MATRIX.md)，未执行项不能记 PASS。

Hermes real Host validation = PENDING_REAL_HOST_VALIDATION；OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED；H1 = BLOCKED；H2 = BLOCKED。A2 文档与 CI 通过不改变这些门禁。

## A3 v3 implementation 映射

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

Host 入口是 [LivingHostFacade](../../runtime/life_engine/living_host_facade.py)，由 [BindingAuthority](../../runtime/life_engine/living_host_binding.py) 签发封套与独立 capability。metadata 使用独立的 [BindingMetadata](../../runtime/life_engine/living_host_metadata.py)，不修改 Living Schema。per-install 进程锁与 authority mutex 串行化路由变更、签发/消费、claim、reload 和本地 fake side effect；Core 的管理/DB 锁在外部边界之前结束。

公开 `recover_operation` 仅包装 B1 `query_operation_recovery`，由当前 authority 根据原调用前已持久化的 exact identity / Core fingerprint 构造 RecoveryDelegation / LivingRecoveryContext。当前 recovery grantee 与 original actor 分离；独立 recovery capability 无 prepare/claim/delivery/permit 权限。投影只在当前进程恢复关联，永不发 permit，也不存入 metadata 冒充 Attempt truth。

capability 与 execution permit 由 [CredentialVault](../../runtime/life_engine/living_host_capability.py) 管理，为随机不透明 handle + HMAC，claims 仅在服务内存；一次消费、最多 60 秒 capability 与 10 秒 permit，绑定安装、实例、revision、authority/plugin epoch、generation、invocation、方法、target、payload/session identity，permit 另绑定 exact Attempt / SIMULATED_CONTACT。每个 authority start 和 plugin load/reload 都有新 epoch，旧权限不可恢复。Core generation 只由既有 durable lifecycle 决定。

[DeliveryEvidence / deterministic fake transport](../../runtime/life_engine/living_host_evidence.py) 是 SIMULATED provider 边界，无网络与真实渠道参数。SENT/ACK 要有独立 provider HMAC evidence、message identity 和时间；ACK 是单独 provider event。CLAIMED 不代表 SENT 或 ACK。NO_REAL_SEND 恒为 true；本阶段 claim 与 fake transport 仅允许隔离测试 authority，生产入口可做结构化预览，不消费正式实例 reservation。

可信管理面用 `authority.lifecycle_transition()` 串行 Core pause/target/restore 等 transition 与权限消费；它不定义业务 policy。消费前检查 Core paused/enabled 并撤销旧权限，resume 不恢复旧 permit。最后 registry generation 校验与内存消费还受既有 management barrier 保护；该锁在 transport 前释放，锁内不调用 Core，避免非重入 deadlock 与 DB/network 原子假象。

可信部署是进程内/同 OS 用户信任边界：不能把任意 Python 执行权当作不可信模型沙箱。没有公开 JSON enrollment、identity attestation、凭据序列化或模型签发入口。真实 connector、受保护 IPC 与服务启动器必须另行授权；A3 提供可验证本地组件与 dispatch fence，未安装真实 Host plugin。现有 legacy adapter 不自动切换；未来部署必须让所有业务入口先经过 `authority.route`，LIVING_PENDING/ACTIVE 拒绝 legacy 回调，Living 异常没有 fallback。

可信 Core runtime/session factory 的生命周期仍属安装服务：plugin reload 保持 Core incarnation；独立服务接管可经既有 Core factory 创建新 incarnation并走既有 UNKNOWN/reconciliation。authority epoch 本身不修改 Core generation、不隐藏 tick 或恢复 mutation。单独 authority 重新附着仍存活的 Core 时，同样撤销旧权限并保守冻结已有关联的 claim，直到可信协调；这不宣称 Core 已自动把 CLAIMED 改成 UNKNOWN。
