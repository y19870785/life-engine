# SP-005A3 与 H0-RV Living 扩展测试设计

**A3 v3 当前证据**：R1 Base `b78b849b1bfac1cbd28359cfb317fd1d4cb84402`。下文冻结设计与 GOV-DOC3 历史状态保持；实际可执行映射见本页末尾及 [A3 验证报告](../SP-005A3-VALIDATION.md)。SP-005A3 = PENDING_INDEPENDENT_REVIEW；全部新增证据为本地 SIMULATED / NO_REAL_SEND / NOT_REAL_HOST_VALIDATION。

**2026-10-01 当前状态校准**：B1 Architecture / Implementation = DONE；合并后 canonical main 为 `f83d36c76fea6de1a31b449535d5df6cea3909b5`。合并与 exact main push CI 证据见 [B1 验证映射](../SP-005A3-B1-VALIDATION.md)。下文历史 Base 与冻结合同保留；A3 Host 层仍 BLOCKED，恢复实施须另行授权。历史 Hermes legacy 测试不升级 Living R01–R12 或未执行的 Host 子集。

本表保留 [A2 架构](../architecture/SP-005A2-LIVING-HOST-BINDING.md)的验收设计；R1 Core 场景已有 [B0 实测映射](../SP-005A3-B0-VALIDATION.md)，其余 A3 Host 场景仍是未来设计。SP-005A2 = DONE；SP-005A2-R1 = DONE；R1 固定 Base：`861734b0c4179e56a3251a775d831cd246278d7f`。SP-005A3-B0 = DONE；B1 implementation 的历史固定 Base 为 `a27caf372a263932346d5b193ca35c92fea6f5dd`。SP-005A3-B1 Architecture = DONE；SP-005A3-B1 Implementation = DONE；SP-005A3 = BLOCKED（Host 层未完成，恢复实施须另行授权）。自动化只使用隔离 fixture/fake transport，不访问生产 Host；真实验证另行授权，默认 DRY_RUN / NO_REAL_SEND。

## A3 自动化合同矩阵

| 编号 | 输入 / 故障 | 必须断言 |
| --- | --- | --- |
| B01 | 相同 tick invocation 重放、不同 invocation 并发 | 收据幂等，不重复 reservation/Day；Core 自然键有效 |
| B02 | 旧 generation token | GENERATION_STALE，零业务写入/发送 |
| B03 | wrong instance、安装复制、错误 Hermes Profile | 拒绝；不能只凭路径/instance 字符串通过 |
| B04 | wrong principal、正文伪造 Owner、转发/子 agent | 拒绝，不推进 inbound 或执行 Owner command |
| B05 | wrong/closed session、跨 Soul session | query/prepare/claim 拒绝；tick 合法窄 capability 可无 session |
| B06 | stale writer epoch 或 stale World revision | 分别按 SESSION_STALE / WORLD_STALE 拒绝；旧 session、context handle、prepare ticket、claim ticket 失效，不 fallback legacy，零新增 Attempt；World revision fence 必须在 Core 事务内生效 |
| B07 | snapshot 超时、Living/policy revision 变化、seal 被改 | 重取 projection；8 KiB 边界；不得缓存自验 |
| B08 | plugin reload 与旧请求并发 | epoch 撤销，旧 ticket 不可 claim，新代次不继承 execute=true |
| B09 | Host restart，authority 保持运行 | 不重抽 choice、不重置 Day/budget/cooldown/follow-up |
| B10 | authority 也重启 | 新 incarnation，旧 session/snapshot 失效；先恢复 CLAIMED；不能每请求重建 incarnation |
| B11 | Life Engine restore | 新 generation、paused/协调、CLAIMED→UNKNOWN；旧 receipt 不直接写新代次 |
| B12 | prepare replay / 同 key 不同内容 | 幂等/IDEMPOTENCY_CONFLICT；不改 target/reason/quota；512 bytes 超限拒绝 |
| B13 | claim replay / 新 invocation 再 claim 同 Intent | 只有首次 execute=true + CLAIMED，其余 execute=false，无第二次 external call |
| B14 | claim 前 crash / commit 后响应丢失，随后 World revision 更新 | 旧 session 先 WORLD_STALE；重新取得 fresh trusted session/ticket 后，仅用原 operation ID + 原 payload 恢复；已提交 claim 返回 execute=false、无第二个 Attempt/新 execution permit。超时不能当未提交，不自动换 ID、重试 mutation 或刷新 revision 静默继续。另覆盖 authority crash 丢失关联：新 recovery-only authority 用原 exact identity/digest 经 B1 只读 lookup 恢复 durable Attempt 关联；不调用 mutation 探测，不返回 execute、不签 permit，只协调 |
| B15 | CLAIMED 后 send 前、send 后记录前 crash | UNKNOWN/协调，不自动重发；fake 外部计数不超过一次 |
| B16 | SENT 后 ACK 前 crash、无 ACK Host | 保留 SENT，不重发不伪造 ACK；无 SENT 证据不升级 |
| B17 | duplicate receipt，同 source/event/digest | 幂等状态推进，不生成 Attempt |
| B18 | receipt digest/target/message/Attempt 冲突 | ERROR/协调，零重发；模型/手工布尔 evidence 拒绝 |
| B19 | enrolled legacy context/wake/status/prepare/ack/observe/photo/loops | 分发前 LIVING_HANDOFF_REQUIRED；不先写旧 observation 或创建备份 |
| B20 | Schema 8 未 enrollment | legacy 行为继续，无隐式 enrollment |
| B21 | RP purpose、跨 World、Bridge 绕路 | 拒绝 Living context，H0 gate 不变 |
| B22 | 默认 dry-run + transport spy | 零真实 send；正式 instance 预览不 claim；隔离 fake 标 SIMULATED |
| B23 | inbound retry、同事件不同摘要、非 Owner | 稳定去重/冲突拒绝，received_at 不漂移；正文不变 follow-up |
| B24 | 满额与自身 cooldown；policy 降 cap | 复用 A1 C13–C16；claim 不重新申请 quota，下一 Intent 仍受限 |
| B25 | Intent 后 quiet/inbound，准备后 target 变化 | C17–C18 取消/重评；target mismatch 拒绝；不退款 |
| B26 | binding metadata 半写/丢失/损坏 | fail-closed，不从模型/旧 probe/path 重建权限；只用原 operation ID 恢复 |
| B27 | IPC 越权、token 泄露尝试、模型传 generation/revision | 拒绝；不输出 token/secrets；过期/错误方法 capability 拒绝 |
| B28 | prepare/claim 与 World revision、Scope、Policy mutation 并发 | 即使 facade 预检查通过，Core 同事务仍按各自冻结规则重验/CAS；World revision 已变则旧 session WORLD_STALE，零业务 mutation、零新增 Attempt、零发送资格；不悄悄刷新陈旧确认的 revision |
| B29 | OpenClaw 同 agent/workspace、不同 Gateway/config | binding mismatch；二元组不足以通过 |
| B30 | 大量 status 历史、分页间 revision 变化 | 有界脱敏，游标失效；命令成功不等于验证 PASS |
| B31 | 当前模板与候选 context adapter | 模板未变，无 Living 自动 prepend/Memory 伪装，只结构化 dry-run |
| B32 | reload 后 incarnation 未变且有 CLAIMED | authority 阻断新 claim 并协调，不称 Core 已因 plugin epoch 自动恢复 UNKNOWN |
| B33 | session 关闭后 result-only submission | 新认证 collector 可记录当前 generation 的原 Attempt 结果，但不能发送 |
| B34 | revoked epoch 与发送执行权竞争 | 当前执行器最多消费一次；发送前失效即停；已在途只收集/协调，不能声称可撤回 |

A3 必须逐项映射具体测试，保留 A1 的 48 项回归。A2 不添加空壳自动测试。Claim 故障至少用新进程与进程退出，不能只 mock exception；Core 并发继续包含双进程竞态。

## B1 Durable Operation Recovery 未来测试设计

[B1 架构与 B1-01～B1-10 计划](../architecture/SP-005A3-B1-OPERATION-RECOVERY-PROJECTION.md)冻结 exact identity、原 Core fingerprint、授权先于 lookup、有界 typed receipt 和零 mutation。Core 实测名称见 [B1 验证映射](../SP-005A3-B1-VALIDATION.md)。B1-01～B1-07 / B1-10 已完成 Core 自动测试；B1-08_CORE_PASS（真实子进程 commit 后退出再只读恢复），B1-09_CORE_PASS（权限类型与委托隔离）。Host epoch/token、revoke/reload、transport 部分 DEFERRED_TO_A3 / NOT_EXECUTED，不能标完整 B1-08/B1-09 PASS。

B14 的 B0 子集是 fresh trusted mutation context + 原 operation replay → execute=false；B1 增加 authority crash + lost association → 独立只读查询 → 无执行资格。两者不是同一个接口。B06_CORE_FENCE_PASS、B28_CORE_FENCE_PASS、B14_CORE_RECOVERY_PASS 保持；不得升级成完整 B06/B28/B14 PASS。A3 必须等待 B1 architecture 与 implementation 均 DONE 后重新授权。

## R1 Core fence 未来测试设计

以下保留 R1-01～R1-06 冻结设计，现已在单独授权的 B0 中映射到真实测试并通过，见 [具体测试与证据边界](../SP-005A3-B0-VALIDATION.md)。仅 B06/B28/B14 的 Core 子集通过，不宣称完整 A3 PASS。所有带 session 的 LivingContext（包括 session-bound Owner action）均须先授权，再允许 receipt recovery 或 mutation；LivingTickContext 无 chat session，不受此 fence 影响。下列 fresh session 指重新取得当前受信授权上下文，保持原 operation 的 producer/principal/Scope/generation 关联；不得把 freshness 当成新 operation identity。

| 编号 | 输入 / 交错顺序 | 必须断言 | 关联 |
| --- | --- | --- | --- |
| R1-01 | World revision 更新，Session OPEN / WriterEpoch 仍有效；旧 session prepare_intent | WORLD_STALE；Intent 状态与 Living revision 不变，零业务 mutation | B06 |
| R1-02 | 已 PREPARED，World revision 更新；旧 session begin_attempt | WORLD_STALE；零新增 Attempt，Intent 状态与 Living revision 不变，无发送资格 | B06 |
| R1-03 | facade 预检查看到 R1；另一事务提交 World revision R2；prepare/claim 才进入 Core 事务，两个方法分别验证 | 同一 Core 事务读取 R2 并拒绝旧 session，WORLD_STALE；零业务 mutation、零新增 Attempt、零发送资格，不能以预检查通过代替最终 fence | B28 |
| R1-04 | prepare 已提交但 response 丢失，随后 World revision bump；以原 operation ID + 原 payload 先旧 session、再 fresh trusted session 重放 | 旧 session WORLD_STALE，不能读 receipt 绕过授权；fresh session 返回原 receipt，Intent/业务 revision 不重复变化 | B14、B06 |
| R1-05 | claim 已提交但 response 丢失，随后 World revision bump；以原 operation ID + 原 payload 先旧 session、再 fresh trusted session 重放 | 旧 session WORLD_STALE；fresh session 返回既有 Attempt receipt 且 execute=false；无第二个 Attempt、无重新签发 execution permit、无再次外部调用 | B14、B13 |
| R1-06 | World revision bump 后重新取得 fresh trusted session；执行尚未提交的正常 prepare/claim | 其它授权与 expected revision CAS 有效时成功；首次合法 claim 才可 execute=true。覆盖原调用在提交前失败、fresh session 沿用原 operation ID + 原 payload 的恢复，不自动重试或换 ID | B06、B14 |

R1-03 应使用独立事务与明确同步点控制竞态顺序；R1-04/R1-05 的响应丢失必须保留真实进程边界设计（subprocess / fresh Python process / os._exit），不得仅靠 mock exception。B0 验证 Core receipt 与 execute 行为；execution permit、context handle、ticket 的 Host 层断言留给 A3，不在 B0 实现 facade。还须回归 session-bound Owner mutation 的 fence 与无 session tick 的既有行为；Scope/Policy 并发按原冻结规则验证，不改变预算、恢复或 Attempt lifecycle。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = NOT AUTHORIZED。

## H0-RV Living 未来真实隔离矩阵

各 Host 独立出报告；原始证据存仓库外并脱敏。先提供官方版本/checkout/package、Profile/Agent、Gateway（适用时）、测试 instance/Session、明确本人 target 和隔离证明。无安全环境记 NOT_EXECUTED，不重启生产服务。

| 编号 | 验证 | 证据与通过边界 |
| --- | --- | --- |
| R01 | plugin installed/enabled/loaded | 分开保存安装、启用、实际工具及本代 hook；文件不等于加载 |
| R02 | exact instance / wrong identity rejection | registry 封套、正确/错误 Profile/Agent/workspace/Gateway；无跨实例读取 |
| R03 | Living tick / duplicate wake | facade 响应、Core receipt/revision，无重复 reservation |
| R04 | context query / snapshot revalidation | SOUL session/epoch/revision/valid_until；reload 后旧 handle 拒绝；模板授权前不注入 |
| R05 | Owner inbound | 真实受信 event ID/Owner 判定/去重摘要；不导入生产历史 |
| R06 | prepare / claim | 隔离测试 instance，PREPARED→CLAIMED，回放 execute=false |
| R07 | fake/no-send dry-run | transport 隔离证明、零渠道调用；不标真实 SENT/ACK |
| R08 | plugin reload | 新 epoch/hook、旧 token 拒绝、generation 不变；不称 Gateway restart PASS |
| R09 | 测试 Host restart | 只操作完全隔离服务；Day/choice/budget/follow-up 不变，否则 NOT_EXECUTED |
| R10 | receipt availability probe | 只读确认 message/event/ACK 来源；无能力记 UNKNOWN/LIMITED，不自动发送 |
| R11 | restore 演练 | 独立副本、新 generation、旧 token 拒绝、paused/协调；不操作生产 |
| R12 | 未来真实发送 | 另授权准确本人 target；分别保存 GENERATED/PREPARED/CLAIMED/SENT/ACK，缺 ACK 停 SENT |

A2-R1 本轮 R01–R12 全部 NOT_EXECUTED。Hermes real Host validation = PENDING_REAL_HOST_VALIDATION；OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP / H1 / H2 = BLOCKED。

## A3 v3 可执行证据映射

测试文件：[test_living_host_binding.py](../../tests/test_living_host_binding.py)。每一行的测试实际断言上述冻结矩阵结果，状态仅为本地 SIMULATED_PASS；Core 专项回归另见 A1/B0/B1 验证文件。B24 完整 C13–C16 与 B25 quiet/inbound 行为由冻结 A1 专项一并执行。

| ID | executable test ID | expected result / evidence |
| --- | --- | --- |
| B01 | `test_b01_duplicate_tick_concurrent` | 重复 tick 不重复 reservation/Day |
| B02 | `test_b02_generation_stale` | GENERATION_STALE，零 mutation |
| B03 | `test_b03_install_instance_host_identity` | 安装/实例/Profile identity 不符拒绝 |
| B04 | `test_b04_principal_provenance_forgery` | 伪造 principal/provenance 与 JSON identity 拒绝 |
| B05 | `test_b05_wrong_closed_session` | wrong/closed session 拒绝，窄 tick 无 session |
| B06 | `test_b06_world_fence_prepare_claim_replay` | prepare/claim/replay WORLD_STALE；fresh replay无重复 Attempt |
| B07 | `test_b07_snapshot_revalidation` | snapshot 到期重验拒绝、8 KiB、seal不输出 |
| B08 | `test_b08_reload_old_request` | plugin epoch 撤销旧 claim capability |
| B09 | `test_b09_host_reload_preserves_business` | reload 不重置 Living tables/generation |
| B10 | `test_b10_authority_restart_epochs` | authority 新 epoch；旧 capability 拒绝，真实 fresh process重启 |
| B11 | `test_b11_restore_generation_all_credentials` | registry generation变化时 capability/recovery/permit全部拒绝，配合既有Core restore回归 |
| B12 | `test_b12_prepare_replay_conflict_concurrent` | 并发prepare幂等、摘要冲突、512字节限制 |
| B13 | `test_b13_claim_replay_concurrent` | 并发claim仅一次permit；replay/new invocation无第二Attempt |
| B14 | `test_b14_process_commit_response_lost_recovery` | P1真实commit后os._exit；B1恢复关联，无execute/permit/send |
| B15 | `test_b15_process_claimed_and_sent_crashes`；`test_b15_p4_fake_send_before_result_crash` | P3/P4真实退出；CLAIMED只协调，fake journal最多一次 |
| B16 | `test_b16_sent_ack_are_distinct` | CLAIMED/SENT/ACK分开，restart不伪造ACK |
| B17 | `test_b17_delivery_duplicate_submit_concurrent` | 并发delivery replay仅一条结果 |
| B18 | `test_b18_untrusted_delivery_conflict` | 未验证evidence拒绝；可信冲突进入协调 |
| B19 | `test_b19_all_legacy_paths_fenced` | 所有业务dispatch回调在副作用前拒绝，无fallback |
| B20 | `test_b20_legacy_pending_explicit` | LEGACY显式路由继续；PENDING拒绝legacy |
| B21 | `test_b21_rp_and_model_envelope_rejected` | RP目的/模型JSON/未知字段拒绝 |
| B22 | `test_b22_no_real_send_preview` | NO_REAL_SEND=true，预览无claim，非隔离transport拒绝 |
| B23 | `test_b23_inbound_stable_identity` | 稳定eventID/首次时间去重，摘要冲突与无ID拒绝 |
| B24 | `test_b24_quota_no_self_cooldown` | 满额reservation可claim，自身cooldown不误阻，后续Intent受限 |
| B25 | `test_b25_claim_target_change_concurrent` | target变更先行零Attempt；claim先行则permit撤销，零send |
| B26 | `test_b26_metadata_corruption_missing_single_writer` | 双writer/损坏/丢失fail closed，不重建权限 |
| B27 | `test_b27_capability_method_expiry_consume_bounds` | wrong method/expiry/duplicate consume/模型权限字段拒绝，repr脱敏 |
| B28 | `test_b28_lifecycle_and_core_race_fence` | Core事务前World交错拒绝；reload/restart旧permit失效且generation不变 |
| B29 | `test_b29_gateway_config_identity_bound` | 相同agent/workspace不同Gateway/config拒绝 |
| B30 | `test_b30_status_bounds_cursor` | 默认20/上限100/游标CAS/120项脱敏分页 |
| B31 | `test_b31_prompt_template_unchanged` | Schema8/Signature/Prompt v1，纯structured snapshot |
| B32 | `test_b32_reload_claimed_requires_reconciliation` | reload后未完成CLAIMED冻结；Core state不冒充UNKNOWN |
| B33 | `test_b33_result_only_after_session_closed` | session关闭后独立collector可record result，无claim权限 |
| B34 | `test_b34_permit_duplicate_concurrent_and_revoked` | permit并发consume最多一次，失效权限不发消息 |

B06_CORE_FENCE_PASS / B28_CORE_FENCE_PASS / B14_CORE_RECOVERY_PASS 继续保留。完整本地 Host 证据为 B06_SIMULATED_PASS / B14_SIMULATED_PASS / B28_SIMULATED_PASS；不代表真实 connector 或生产服务已验收。B28 同时覆盖冻结的 Core transaction race 与本次任务书追加的 Host lifecycle。

B1-08 的 Host 子集由 B14/P1、B15/P3/P4 与 before-claim subprocess 映射；B1-09 的 Host 子集由 `test_b1_09_recovery_capability_never_execution`、`test_recovery_reload_barrier_and_no_privilege_upgrade` 映射。只有本地 Host 子集 SIMULATED_PASS，B1 原 Core 标签不修改，真实 Host R01–R12 仍 NOT_EXECUTED。

并发补充：`test_capability_concurrent_consume_once`；`test_lifecycle_races_claim_reload_restart`；`test_claim_authority_restart_race`；`test_recovery_reload_barrier_and_no_privilege_upgrade`。permit 参数/expiry/authority restart：`test_permit_wrong_fields_expired_and_authority_restart`。metadata无业务真源：`test_metadata_contains_only_identity_and_missing_cannot_reinitialize`。JSON上限：`test_response_and_envelope_bounds`。
