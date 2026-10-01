# SP-005A3-B1 — Durable Operation Recovery Projection

**2026-10-01 当前状态校准**：B1 Architecture / Implementation = DONE；合并后 canonical main 为 `f83d36c76fea6de1a31b449535d5df6cea3909b5`。合并与 exact main push CI 证据见 [B1 验证映射](../SP-005A3-B1-VALIDATION.md)。下文历史 Base 与冻结合同保留；A3 Host 层仍 BLOCKED，恢复实施须另行授权。历史 Hermes legacy 测试不升级 Living R01–R12 或未执行的 Host 子集。

## 状态与范围

架构冻结 Base：`76fee9bc82240dfcf52fb7a017175fbe7df40fc2`；implementation 历史固定 Base：`a27caf372a263932346d5b193ca35c92fea6f5dd`。

SP-005A3-B0 = DONE；SP-005A3-B1 Architecture = DONE；SP-005A3-B1 Implementation = DONE；SP-005A3 = BLOCKED（Host 层未完成，恢复实施须另行授权）。Core 只读入口已按单独授权实施，见 [B1 验证映射](../SP-005A3-B1-VALIDATION.md)。下文保留冻结合同，Host epoch/capability 不在本轮实现范围。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。SP-005A2-P1 = NOT AUTHORIZED；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES。不新增 Schema、migration、Prompt 接入或真实 Host 操作。Hermes / OpenClaw real Host validation 均为 PENDING_REAL_HOST_VALIDATION；Full Private RP、H1、H2 均为 BLOCKED。

本修订补充 [A2 Host Binding](SP-005A2-LIVING-HOST-BINDING.md) 的 crash recovery 缺口，不改变 B0 授权 fence、Core operation receipt、Attempt lifecycle 或 delivery semantics。架构审核、合并及 exact main push CI 完成后，仍须单独授权 B1 implementation；二者都 DONE 后才重新决定 A3 实施基线，默认从届时 canonical main 新建 v3，不自动续跑 A3 v2。

## 1. 缺口与唯一真源

架构冻结时 [LivingRuntime](../../runtime/life_engine/living_runtime.py) 的 `status()` 不提供 operation receipt / Attempt association，[Living projection](../../runtime/life_engine/living_projection.py) 也没有 recovery 查询。`begin_attempt()` 是 mutation command，不能为了探测是否提交而调用。

新增概念 `OperationRecoveryProjection`：只读查询原 operation 是否已 durable commit，以及对应的有界 durable receipt。唯一真源是 Core `living_operations` 及 Core 验证的 Attempt 关联。authority metadata 只能保存 invocation correlation、完整 operation identity、payload digest 和 Host lifecycle metadata；不得声明 CLAIMED、Attempt 存在、SENT 或 ACK，也不能在重启后替代重新查询。必须在原调用前保有足够的原 identity/digest 关联；缺失时 fail-closed，不能枚举数据库或猜测 identity 补救。

## 2. 查询身份与 fingerprint

每次只查询一个完整 canonical identity：`instance_id + generation + producer + operation_id`，并绑定 `action + expected payload digest + scope`。Scope 必须完整包含 owner、soul、world、timeline；Core 由已认证 instance / Scope 解析 root，数据库自然键仍为 `root_id + generation + producer + operation_id`。不得按裸 operation_id 全局查询，不提供 wildcard、list-all 或历史 receipts 列表。

v1 必须支持本次缺口涉及的 `prepare`（公开命令 `prepare_intent`）和 `begin_attempt`。采用显式 action allowlist，其他 action 在 v1 拒绝，不因底层有记录就透传；扩展须先冻结相应 receipt 类型与既有 fingerprint 映射。尤其 `enroll` 当前有不同的 canonical request 形状，不能套用以下格式。

复用 [living_domain.canonical / fingerprint](../../runtime/life_engine/living_domain.py) 和现有 `_command` request，禁止第二套 payload identity 算法：

```text
request = [action, payload, [owner_id, soul_id, world_id, timeline_id], original_principal_id]
expected_payload_digest = SHA256(UTF8(canonical(request)))
canonical = JSON(ensure_ascii=false, sort_keys=true, separators=(',', ':'), allow_nan=false)
prepare payload = [intent_id, material]
begin_attempt payload = intent_id
```

所有 identity 值沿用 Core 的字符串表示与原 request 值。digest 是上述完整 request 的小写 SHA-256 hex，不是 content 的 hash；必须与 durable `living_operations.fingerprint` 相等。producer / operation_id / generation 由查询自然键绑定；expected Living revision、session_id、writer epoch、World revision 不在现有 request fingerprint 内，不为 recovery 另行加入。它们的授权或 mutation CAS 职责保持分离。

可信调用方在原 invocation 时保存该 digest；未来实现必须复用 Core canonical 规则并做一致性测试，不能由模型生成权限材料。authority-bound 查询的新 recovery principal 与原 mutation actor 不必是同一身份，但必须受信绑定原 `original_principal_id` 及其 owner / producer 委托；不能用新 system principal 替换原 request 的 actor 重新计算 fingerprint。session-bound 查询必须保持原 actor / producer 绑定。digest 本身不构成权限。

查到记录后，Core 必须校验存储 request 的结构、action、Scope、原 actor 与授权范围，并重算存储 fingerprint、验证 receipt integrity；再与 expected digest 比较。合法记录与请求 digest / action 不匹配时 `IDEMPOTENCY_CONFLICT`，不返回 receipt；存储损坏显式 corruption error，不能伪装成 NOT_COMMITTED。越权 identity 在 lookup 前拒绝。

## 3. 权限模型：明确采用 authority-bound crash recovery

对于 claim committed → authority crash → association 丢失，冻结为 **Authority-bound recovery**。原 chat session 可能已经结束，不能要求用 mutation replay 才取得事实。概念 `LivingRecoveryContext` 表达独立且不可与 mutation context 互换的窄权限：

- instance_id、当前 generation、受信 principal / owner authority、完整 Scope。
- 被授予的 producer namespace、原 operation actor 绑定、authority provenance。
- 当前 authority runtime epoch / capability revision 的有效认证及只读方法授权。

具体 Python 类型和签名留 implementation，但上述独立权限类别不可省略。不是 `LivingContext(session=None)` 的管理员后门；普通无 session 的 LivingContext、tick capability、模型正文或普通 Host JSON 均不能取得此权。Core 的公开恢复入口只接受受信构造的对应权限，不能仅凭调用方自报 owner、producer、epoch 通过。受信部署负责建立 owner 委托和 authority provenance，A3 binding 负责当前 epoch/capability 验证，Core 负责当前 generation / Scope / principal delegation 与 exact identity 的最终校验。若实现无法在该边界 fail-closed，必须停止报告架构缺口。

recovery-only capability 只能 `query_operation_recovery`，不能 prepare、claim、生成 execution permit、send、提交任意 delivery state 或修改 Living state。新的 authority epoch 可经重新认证取得同 owner / Scope / producer 的 recovery-only 权限；旧 epoch/token 不能被恢复或转为新权限。不能在查询失败时降级为更宽的 context。

同时保留 **Session-bound recovery** 入口语义：调用方必须重新取得 fresh trusted session，完整执行 generation → Scope / SOUL / ACTIVE → Principal → Session binding / OPEN → WriterEpoch → WorldRevision → Living root 授权。`session.world_revision != current World.revision` 必须 `WORLD_STALE`，即使历史 receipt 存在也不能返回。禁止去掉 session 静默改走 authority-bound；后一种能力必须独立认证、独立授予。

authority-bound 不要求 chat Session / WriterEpoch / session WorldRevision，但仍在查询事务中验证当前 instance、generation、完整 Scope、SOUL / ACTIVE World、owner authority / actor 委托、producer 与 root。该例外仅适用于只读恢复，绝不扩大任何 session-bound mutation 权限。

## 4. 事务与零副作用

概念接口（不是本轮实现承诺的 Python 签名）：

```text
query_operation_recovery(trusted_context, producer, operation_id, action, payload_identity)
    -> OperationRecoveryProjection

read transaction / consistent snapshot
  -> current authorization
  -> current Living root / generation / Scope
  -> exact operation lookup
  -> canonical request fingerprint / expected digest verification
  -> typed bounded receipt / Attempt association projection
end
```

所有 Core 授权、root、receipt 和关联读取必须在同一事务快照完成。不得用 mutation `_command()` 实现，不能由 facade 外层检查替代 Core 最终校验；authority/facade 不得直接 SQL 查询 `living_operations` 或调用私有 `_root`。Core 内部如何复用授权逻辑留给 implementation，不改变 B0 mutation 顺序。

请求 generation 与当前 Core generation 不一致时，lookup 前 `GENERATION_STALE`。restore 后旧 receipt 即使仍在历史库中也不能跨代次查询并恢复执行权。root 与 trusted Scope 的 owner / soul / world / timeline 任一不匹配均 fail-closed；不得查询其他 producer 的 operation。

查询不需要 expected Living revision CAS；返回当前快照的 root revision 和历史 operation revision，二者明确区分。正常 mutation 的 expected Living revision CAS 完全保留。NOT_COMMITTED 只说明该授权快照未找到 exact operation；并发事务可在此后提交，不能将查询结果当作后续执行的独占资格。

查询不得创建 operation / Attempt，修改 Intent / root revision / last_evaluated_at，写 transition / receipt，改变 recovery state，触发 tick / transport 或新建 Core incarnation。数据库锁和只读校验可以存在，但所有成功、拒绝与损坏路径均须零业务写入。生命周期恢复另走已冻结 Core 流程，不能藏在查询内部。

## 5. 有界结果与 claim 的特殊约束

结果为 `NOT_COMMITTED` 或 `COMMITTED`，附经认证的 identity 与当前快照 revision；错误为显式 error，不转 NOT_COMMITTED / SILENT。COMMITTED 可含 action、operation_id、producer、generation、历史 revision、receipt_digest 和 typed receipt。未知输入字段拒绝，输出只允许冻结字段；不透传任意 JSON、原始 metadata、secret、token、permit 或 provider evidence。

v1 receipt 投影：`prepare` 为 id、revision；`begin_attempt` 为 attempt_id、历史 state、revision，或原已提交的 blockers、revision。**所有 recovery 输出都不包含 `execute` 字段**，包括嵌套 receipt。底层首次 claim receipt 即使保存 execute=true，也必须经类型验证和字段白名单投影，禁止返回原始 receipt 文本。

COMMITTED 表示 operation 提交，不保证 claim 成功：当前 begin_attempt 可以提交 blockers 而没有 Attempt。这时不能合成 attempt_id。存在关联时，Core 必须在同一快照验证 receipt attempt_id 指向同 root 下、属于 request intent_id 的真实 Attempt，并通过其 Intent / root 验证当前 generation；不从 ID 算法或 authority 缓存猜关联。历史 receipt 的 state 不能冒充当前 Attempt state；若返回后者，必须放入独立 `attempt.current_state` 字段。例如历史 CLAIMED、恢复后 UNKNOWN 可同时成立。关联异常 fail-closed，不返回虚假 NOT_COMMITTED。

`receipt_digest` 明确定义为经 Core integrity 验证的原 durable receipt fingerprint（当前 `receipt_fingerprint`），包含原始 receipt 的字段语义；它不声称等于剔除 execute 后的投影 JSON hash。调用方不能凭 digest 推导执行权。投影本身如需独立摘要，须另外命名，不混用。

经固定 Base 源码核对，现有 generic operation receipt 没有独立 JSON 字节上限；不能宣称沿用了不存在的限额。为新 recovery 边界冻结：canonical UTF-8 请求不超过 8 KiB；读取并投影的单个 durable receipt 不超过 8 KiB；完整 JSON 响应不超过 16 KiB。identity 字符串沿用 Core 非空、最多 512 UTF-8 bytes 规则；digest 固定 64 位 hex。超限显式拒绝，不截断、不当作 NOT_COMMITTED、不泄露部分 receipt。实现前须验证大小检查覆盖反序列化和返回路径，不能先无界 materialize 再截断；这不迁移或重写历史记录，也不修改既有 Core command 的 fingerprint / receipt 语义。

## 6. 崩溃与恢复

| 场景 | 查询与后续边界 |
| --- | --- |
| begin_attempt durable CLAIMED commit 后、response / association 尚未持久化即进程退出 | 新 authority epoch，旧 capability 失效；独立重新认证的 recovery context 用原 identity/digest 查询 COMMITTED，恢复经 Core 验证的 Attempt 关联；无 send permit，进入 reconciliation。 |
| Core commit 前退出 | 当前快照可返回 NOT_COMMITTED；不直接 send、不自动 claim。若仍需继续，必须重新取得正常 mutation 授权，用原 operation identity/payload 进入正常 claim path，由 Core receipt/CAS/eligibility 裁决。 |
| CLAIMED 已提交，fake / real 外部副作用是否发生未知 | receipt 只能证明 claim durable commit，不能证明 SENT；协调或收集 trusted evidence，不 resend。 |
| 原 chat 已结束 | 可用独立授予的 authority-bound recovery-only 权限；不能凭旧 session/token 越权，也不能签发 execution permit。 |
| durable restore 改变 generation | 旧 generation 请求拒绝；旧关联不转为当前 generation execution authority，保留原恢复/协调合同。 |

CLAIMED != SENT != ACK。B1 不改变 DeliveryEvidence、退款、Attempt lifecycle 或恢复算法。查询 COMMITTED begin_attempt 永远没有发送资格；NOT_COMMITTED 也不是“现在可以发送”。即使证明尚未发生外部发送，本 projection 仍不签发 permit。

正常可信 mutation context 仍可使用原 operation ID + 原 payload 重放，B0 保证 stale session 先 WORLD_STALE、fresh session 才恢复 receipt；已提交 claim replay 为 execute=false，无第二 Attempt。B1 不替代该机制：它专门解决不能安全重新调用 mutation command、却需要获知提交事实的 crash recovery。两者都不允许自动换 operation ID。

## 7. 冻结测试计划与 implementation 状态

以下保留验收场景，实际测试名称与证据见 [B1 验证映射](../SP-005A3-B1-VALIDATION.md)。B1-08 / B1-09 仅完成 Core 子集，不声称完整 Host 验收通过。

| 编号 | 场景 | 必须断言 | 状态 |
| --- | --- | --- | --- |
| B1-01 | 当前授权内 exact operation 不存在 | NOT_COMMITTED；零 mutation；不自动 claim/send；同 ID 的其他 producer 记录不可返回。 | PASS（仅 Core） |
| B1-02 | prepare 已提交 | COMMITTED，原 durable prepare receipt / revision / digest；查询不再次修改 Intent。 | PASS（仅 Core） |
| B1-03 | claim 已提交 | 校验 Attempt association，无 execute 字段、无 permit；另测 blockers receipt 无 Attempt、历史 CLAIMED 与当前 UNKNOWN 的区分及损坏关联拒绝。 | PASS（仅 Core） |
| B1-04 | 同 identity、错误 payload digest / action | IDEMPOTENCY_CONFLICT，不返回 receipt；canonical key ordering、UTF-8、原 actor 与新 recovery actor 的映射和原 Core fingerprint 一致。 | PASS（仅 Core） |
| B1-05 | 旧 generation，包括 restore 后旧 receipt 仍存在 | GENERATION_STALE，在 lookup 前拒绝；不恢复发送资格。 | PASS（仅 Core） |
| B1-06 | 错误 instance / owner / soul / world / timeline / producer 委托 | fail-closed、不泄露其他 receipt；裸 operation_id、wildcard、普通 session=None 和未知字段拒绝。 | PASS（仅 Core） |
| B1-07 | session-bound stale World + 已存在匹配 receipt | WORLD_STALE 在 receipt 返回前发生；同时覆盖 Session / WriterEpoch 失效，不自动转 authority-bound。 | PASS（仅 Core） |
| B1-08 | Core claim commit 后、关联保存前 authority 真实进程退出 | subprocess / fresh Python / os._exit 边界；新受信 recovery authority 读取原 identity，恢复关联但不 send；覆盖 commit 前退出、fake send 后 result 前退出，仅协调不重复外部调用。 | B1-08_CORE_PASS；Host DEFERRED_TO_A3 |
| B1-09 | 旧 authority epoch / capability 或权限升级尝试 | 拒绝；新 recovery-only 权限不能用于 prepare/claim/send/delivery；reload/revoke 与查询并发 fail-closed。 | B1-09_CORE_PASS；Host DEFERRED_TO_A3 |
| B1-10 | 成功、未提交、错误、超限及并发读取前后比较 | 所有 Living business tables、operations、root revision / last_evaluated_at、transitions、recovery state 完全不变；无 transport；验证 8/16 KiB 边界与一致快照，不返回部分或未经验证的 receipt。 | PASS（仅 Core） |

B1-08/B1-09 的 Host capability 与进程编排由后续 A3 实现阶段补齐；B1 Core implementation 必须明确其实际完成子集，不把 fixture 权限证明标成真实 Host 验收。[A3 矩阵 B14](../planning/SP-005A3-HOST-BINDING-TEST-MATRIX.md) 同时依赖 B0 mutation replay 与 B1 read-only lookup，两者分别映射；B06/B28/B14 目前仍仅保留 B06_CORE_FENCE_PASS、B28_CORE_FENCE_PASS、B14_CORE_RECOVERY_PASS。A1 48 项及 B0 R1 回归继续保留。本轮 Core 测试不代表 Host authority、epoch/token、permit 或 transport 已实现。

真实 Host R01–R12 = NOT_EXECUTED。未来模拟恢复验证必须标记 SIMULATED / NO_REAL_SEND / NOT_REAL_HOST_VALIDATION，不连接真实 transport。

## 8. Core implementation 边界

公开入口为 `LivingRuntime.query_operation_recovery(context, request)`，也可使用 `living_recovery.query_operation_recovery`；请求为严格 `OperationRecoveryRequest`，结果为不可变 `OperationRecoveryProjection`。`LivingRecoveryContext(principal, delegation)` 携带独立 `RecoveryDelegation`：Owner authority、grantee、原 actor、Scope、instance、generation、producer 和 provenance。它们与现有 Principal 一样，是受信本地进程提供的认证断言，不是凭证；没有 JSON factory、网络入口或 Host capability。普通 LivingContext(session=None) 拒绝，带 PromptSessionContext 的路径复用 B0 `_root/_authorize`。具体 Host 身份认证与旧 epoch/token 拒绝仍 DEFERRED_TO_A3。

只读仓储使用既有安装锁、SQLite mode=ro / query_only / 同一快照，保留 schema/runtime 检查；授权后校验当前 root 的既有 state_digest，按 exact identity 先检查 payload/receipt 字节长度再读取，验证所选 record、transition 关联及真实 Attempt。它不调用 mutation transaction 的全库 receipt materialization，不复制业务 eligibility。mutation 入口仅增补 recovery-only 类型拒绝，原合法 command 的 fingerprint、B0 fence、receipt、CAS、Attempt 和预算语义均未改变。
