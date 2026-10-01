# SP-005A3-B1 Core implementation 验证映射

固定 Base：`a27caf372a263932346d5b193ca35c92fea6f5dd`。分支：`feat/sp-005a3-b1-operation-recovery`。

SP-005A3-B0 = DONE；SP-005A3-B1 Architecture = DONE；SP-005A3-B1 Implementation = PENDING_INDEPENDENT_REVIEW；SP-005A3 = BLOCKED_BY_B1。本轮只实现 [冻结的 B1 Core recovery 合同](architecture/SP-005A3-B1-OPERATION-RECOVERY-PROJECTION.md)，不实现 A3 Host Binding。

## API 与权限边界

公开入口是 [LivingRuntime.query_operation_recovery](../runtime/life_engine/living_runtime.py) 和 [living_recovery.query_operation_recovery](../runtime/life_engine/living_recovery.py)。调用方传入受信 context 与 `OperationRecoveryRequest`，返回不可变 `OperationRecoveryProjection`；`to_json()` 使用 Core canonical 序列化并检查完整响应上限。

`LivingRecoveryContext(principal, delegation)` 与 LivingContext 不可互换。`RecoveryDelegation` 是受信本地 Owner 部署断言，固定 owner_authority、grantee、original_actor、Scope、instance、generation、producer、provenance。和既有 Principal 一样，它不是 bearer credential：本地可信代码负责构造，Core 校验类型、同 Owner、grantee 与委托范围、当前 generation / World / Scope / root。没有从普通 JSON 构造权限的入口；不能将拥有任意 Python 执行权的进程视为不可信隔离区。本轮不提供 Host 身份验证、epoch/token 或网络边界，不能宣称 Host authority 已可投入使用。

session-bound 路径只接受带 `PromptSessionContext` 的 LivingContext，检查内部 principal/Scope/generation/runtime 映射并复用现有 `_root/_authorize`：Session OPEN / WriterEpoch → World revision → root → receipt。旧 session 即使有匹配 receipt 仍 WORLD_STALE。普通 LivingContext(session=None)、tick context 或模型/工具 JSON 不能替代独立恢复委托。

独立权限只可查询，不可用于 prepare、claim、tick、configure、enroll、reconcile 或 delivery mutation。Runtime 仅新增 public wrapper 和无效权限类型的提前拒绝；`_authorize`、operation fingerprint、合法 command receipt/CAS、预算、reservation、Attempt lifecycle 均未改变。

## 读取、完整性与输出

[只读仓储事务](../runtime/life_engine/living_repository.py) 沿用安装锁顺序，使用 SQLite `mode=ro`、`query_only=ON`、单次 `BEGIN` snapshot；不创建 incarnation，不调用 mutation `_command`，结束时 rollback/close。当前 generation/runtime/schema 校验后，在同一快照内完成授权、root、operation 和 Attempt 关联读取。

授权后复用当前 root 的既有 `state_digest`，随后按完整 instance / generation / producer / operation_id 查单条记录。先由 SQLite 计算 payload/receipt 字节长度，再在 Python 读取和解析；不执行 mutation transaction 的全库 receipts materialization。原 request 与 receipt 均复用 `living_domain.canonical/fingerprint`，验证存储结构、Scope、原 actor、revision、transition 关联和真实 Attempt / Intent / generation；不支持的 action 不透传。损坏返回明确错误，不伪装为 NOT_COMMITTED。

`prepare` 投影为 intent_id / revision；`begin_attempt` 投影为 attempt_id / historical_state / revision 或 blockers / revision。COMMITTED blockers 可没有 Attempt；不合成关联。`attempt.current_state` 与历史 receipt 状态分开。所有输出类型均无 execute 字段、不含 raw receipt、不签 execution permit；receipt_digest 始终是原 durable receipt fingerprint。

请求及所读 canonical request / durable receipt 上限 8 KiB，响应 16 KiB；identity 非空且最多 512 UTF-8 bytes，digest 为 64 lowercase hex。未知请求字段拒绝，超限拒绝且不截断。查询只证明当前快照的提交事实，不触发重试、claim、tick、恢复或发送。

## 逐项实测映射

测试文件：[test_living_recovery.py](../tests/test_living_recovery.py)。进程 fixture：[living_recovery_process_fixture.py](../tests/living_recovery_process_fixture.py)，并复用 B0 已有 [claim-lost os._exit fixture](../tests/living_process_fixture.py)。全部为 synthetic Core 测试，无真实 target / channel / transport。

| 合同 | 具体测试名称 | 结果与边界 |
| --- | --- | --- |
| B1-01 | `test_b1_01_absent_exact_identity` | CORE_PASS；NOT_COMMITTED，不泄露其他 producer 同 ID operation。 |
| B1-02 | `test_b1_02_prepare_typed_receipt` | CORE_PASS；typed prepare receipt、原 revision/digest、零 mutation。 |
| B1-03 | `test_b1_03_claim_association_and_historical_state`；`test_b1_03_committed_blockers_without_attempt`；`test_b1_03_broken_associations_fail_closed` | CORE_PASS；真实关联、历史 CLAIMED / 当前 UNKNOWN 分开、blockers 无 Attempt、损坏关联拒绝。 |
| B1-04 | `test_b1_04_digest_action_canonical_and_actor` | CORE_PASS；错误 digest/action、原 actor 与新 reader、UTF-8 和 key order，沿用 Core fingerprint。 |
| B1-05 | `test_b1_05_generation_and_restore` | CORE_PASS；旧 generation 拒绝，restore 后历史 receipt 仍存在也不返回。 |
| B1-06 | `test_b1_06_scope_producer_and_input_isolation`；`test_b1_06_current_world_and_root_authorization` | CORE_PASS；instance/完整 Scope/producer、wildcard、裸 ID、普通无 session context、JSON/未知字段拒绝；当前 World/Scope 再验。 |
| B1-07 | `test_b1_07_session_authorization_before_lookup` | CORE_PASS；匹配 receipt 已存在仍先 WORLD_STALE / SESSION_STALE；fresh session 可查，关闭 session 不降级。 |
| B1-08 | `test_b1_08_core_process_crash_before_association` | B1-08_CORE_PASS；claim durable commit 后 os._exit(75)，新 Python 进程仅调用 public recovery API，恢复关联，无 execute/写入/新 Attempt。 |
| B1-09 | `test_b1_09_core_context_cannot_widen_privilege` | B1-09_CORE_PASS；委托不能扩大 grantee/actor/owner/producer/instance/generation；recovery context 不能进入 mutation 或 delivery validator。 |
| B1-10 | `test_b1_10_bounds_before_json_materialization`；`test_b1_10_corrupt_current_state_checksum`；`test_b1_10_corrupt_record_and_unknown_receipt_fields`；`test_b1_10_readonly_connection_and_consistent_snapshot`，以及通用 `query` 全表前后比较 | CORE_PASS；成功/未提交/错误/冲突/损坏/超限零 mutation；readonly connection 拒写；真实线程与独立连接 mutation 不能把旧 receipt 和新 Attempt state 拼成混合快照。 |

并发测试在 receipt 已读取、Attempt SELECT 尚未执行处设置同步点，另一个线程调用既有 Core reconcile；第一次查询返回旧 root revision + CLAIMED，writer 提交后下一次查询返回新 revision + UNKNOWN。同步点只位于测试连接包装中，生产代码没有故障注入入口。逐次查询前后比较所有数据库表，包含 operations、transitions、root revision/last_evaluated_at、Intent、Attempt 和 World runtime metadata；写入用于造损坏或并发 mutation 的 fixture 明确在 query 外执行。

B1-08 的 Host authority epoch、遗失 Host association metadata、fake-send/DB-result crash 编排，以及 B1-09 的 plugin/authority epoch、token revoke、reload concurrency：**DEFERRED_TO_A3 / NOT_EXECUTED**。没有完整 B1-08 PASS / B1-09 PASS，也没有 Host token 实现。

## 回归与检查

- B1 专项：16 tests 通过。
- 完整 unittest：Windows / Python 3.12，397 tests，396 passed、1 skipped、0 failed、0 errors（306.494s）；另对最终异常归一化改动重跑 B1 16 项全部通过。[A1 48 合同映射](SP-005A1-VALIDATION.md)：52 个映射测试全部通过；[B0 R1 回归](SP-005A3-B0-VALIDATION.md)：10 项全部通过。
- exact Head PR CI 必须为 Ubuntu / Windows × Python 3.11 / 3.12 四矩阵 SUCCESS；运行号记录在 PR 与交付报告，不能代替独立审核。
- `git diff --check` 通过；本次 5 份变更文档的 44 个本地链接/锚点检查通过。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；无 migration。SP-005A2-P1 = NOT AUTHORIZED；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES。

Hermes / OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP / H1 / H2 = BLOCKED；R01–R12 = NOT_EXECUTED。本轮不实现 facade、Host authority、HMAC capability、execution permit、fake transport 或 legacy routing。Draft 交付后停止，不 Ready、不 Merge、不恢复 A3。
