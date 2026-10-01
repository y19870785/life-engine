# SP-005A3-B0 — Session World Revision Fence 验证

固定 Base：`3367a8906060af129d7ee29ef4da7959926b5d0b`。SP-005A2 / SP-005A2-R1 = DONE；SP-005A3-B0 = DONE；SP-005A3 = BLOCKED（Host 层未完成，恢复实施须另行授权）。合同依据 [A2-R1](architecture/SP-005A2-LIVING-HOST-BINDING.md)与 [A3 测试矩阵](planning/SP-005A3-HOST-BINDING-TEST-MATRIX.md)。

## 最小修复与授权顺序

[LivingRuntime._authorize](../runtime/life_engine/living_runtime.py) 仅新增一条比较：session 的 `world_revision` 与同一 `LivingRepository.transaction()` 内读取的当前 World revision 不等时，`fail('WORLD_STALE')`。该比较在 Session OPEN / WriterEpoch 检查之后，在 `_root` 读取 Living root、operation receipt lookup、expected Living revision CAS 和业务 mutation 之前。既有 generation、Scope、Principal、Session identity 校验顺序不变；SESSION_STALE 与 WORLD_STALE 保持不同语义。

stale session 无权取回历史成功 receipt。重新取得当前 revision 的可信上下文后，保留 session_id、Principal、Scope、generation、producer 和原 operation ID/payload，才允许既有 receipt recovery。已提交 begin_attempt 返回原 Attempt 且 `execute=false`；未提交操作仍受 expected Living revision CAS 约束。本阶段没有实现 execution permit 或任何 transport。

## 实际测试映射

具体测试均位于 [test_living_runtime.py](../tests/test_living_runtime.py)。每个 WORLD_STALE 断言前后比较所有 Living 业务表、living_operations、living_transitions，包含 living_intents、living_attempts 和 root revision；历史记录保留但无新增 mutation。

| 合同场景 | 真实测试 | 验证内容 |
| --- | --- | --- |
| R1-01 | `test_r1_01_stale_prepare_no_mutation` | revision bump 后 prepare WORLD_STALE；Intent 仍 DECIDED，无 Attempt、无写入 |
| R1-02 | `test_r1_02_stale_claim_no_attempt` | PREPARED 后 revision bump，claim WORLD_STALE；无新增 Attempt、无状态变化 |
| R1-03 | `test_r1_03_precheck_then_independent_world_commit` | prepare/claim 各自先成功 query projection；独立 Python 进程通过另一 SQLite 事务提交 R2，进程退出同步后再调 Core，必须 WORLD_STALE；writer epoch 未变 |
| R1-04 | `test_r1_04_prepare_response_lost_authorization_before_receipt` | 子进程 prepare 提交后 os._exit(75)，不输出 response；旧 session 原操作重放 WORLD_STALE，fresh 同 session_id 返回持久 receipt，revision 不递增 |
| R1-05 | `test_r1_05_claim_response_lost_replay_never_executes` | 子进程 CLAIMED 提交后 os._exit(75)；持久 receipt 原有 execute=true，旧 session 重放仍 WORLD_STALE；fresh 重放 execute=false，Attempt 始终 1 条 |
| R1-06 | `test_r1_06_fresh_context_original_uncommitted_operations` | prepare/claim 未提交时以原 operation ID/payload 拒绝 stale 调用，再经 fresh 授权正常提交；首次合法 claim execute=true |
| CAS 不绕过 | `test_r1_fresh_context_does_not_bypass_living_cas` | stale World 优先 WORLD_STALE；fresh 上下文在无 receipt、expected Living revision 过期时，prepare/claim 均 REVISION_CONFLICT |
| Session 错误优先 | `test_r1_session_identity_precedes_world_fence` | stale writer epoch / closed Session 仍 SESSION_STALE，零业务写入 |
| 命令路径覆盖 | `test_r1_session_owner_commands_share_fence` | 逐个调用现有其它命令与只读入口，验证共同 fence；保留管理命令的既有拒绝语义 |
| 无 Session tick | `test_r1_narrow_tick_without_session_unchanged` | LivingTickContext 不要求 Session 字段；恢复、reservation 与原 operation 重放保持有效 |

进程场景复用 [living_process_fixture.py](../tests/living_process_fixture.py)，只增加 World revision 提交与 prepare/claim response-loss 模式。子进程附着同一 Core runtime_id，不创建新 incarnation，避免把 restart recovery 混入 response-loss 验证；没有 mock stale 值、真实 Host 或发送调用。

## 命令路径审计

create_followup、resolve_followup、cancel_followup、cancel_activity、observe_inbound、observe_environment、reschedule_activity、tick、prepare_intent、begin_attempt、record_delivery 均通过 `_command → _root → _authorize`；验证器和输入格式校验可在事务外先拒绝非法输入，但不能写入业务状态或返回成功 receipt。status、observation_context 经 `_root → _authorize`；living_projection.query 也经 `_root`。

configure、reconcile 既有规则在入口对任何 chat session 返回 AUTHORIZATION_DENIED；本阶段不开放这些管理权限。enroll 在同一事务直接 `_authorize` 后禁止 session enrollment。没有发现能够绕过 `_authorize` 执行业务 mutation 的 session-bound 路径，无需扩大架构或代码范围。

## 回归与证据边界

B06_CORE_FENCE_PASS：仅 World revision、WORLD_STALE、零 mutation/Attempt 与 Session 错误优先。B28_CORE_FENCE_PASS：仅 World revision 在预检查与 Core 事务之间更新的 prepare/claim 场景。B14_CORE_RECOVERY_PASS：仅 stale authorization first、原 operation 恢复、已提交 claim replay execute=false。上述均不等于整个 A3 B06/B28/B14 PASS；context handle、ticket、capability、authority、execution permit 和 Host 层并发仍待 A3。

B0 新增 10 项测试；完整 unittest 与 A1 T01–T14 / C01–C18 / P01–P16 的 48 项合同映射回归结果见 [验证记录](VALIDATION.md)。CI 使用 exact Head 的 Ubuntu / Windows × Python 3.11 / 3.12 四矩阵，最终 run 与 SHA 在 Draft PR 及交付报告中关联；自动测试通过不代替独立审核。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。无 migration、Prompt Runtime 或 Host Adapter 修改。SP-005A2-P1 = NOT AUTHORIZED；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES。Hermes / OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；R01–R12 = NOT_EXECUTED；Full Private RP / H1 / H2 = BLOCKED。B0 已完成审核、Squash Merge 与 exact main push CI；其完成不自动恢复 A3 主实现。
