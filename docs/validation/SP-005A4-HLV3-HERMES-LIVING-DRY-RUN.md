# SP-005A4-HLV3 — Hermes Living Dry-Run / Permit / Crash Recovery

> CURRENT GOVERNANCE NOTE：本报告的 HLV3 执行证据与 DONE 结论保留；下列下一阶段判断是 2026-10-03 时点的历史治理快照。当前 Soul Continuity 主线与 Host Integration 延期状态见 [GOV-SOUL-ROADMAP1](../architecture/GOV-SOUL-ROADMAP1-SOUL-CONTINUITY-MAINLINE.md)。

## HISTORICAL — 当时结果与治理边界

2026-10-03，在开工 Base `4c9c5aaf9e9ed2995086781e32241abf23436dcb` 上执行；验证结果 `PASS`。当前 `SP-005A4-HLV3 = DONE`、`REAL_HOST_DRY_RUN_PASS = CONFIRMED`：PR #39 已 Squash Merge 至 canonical main `9d064d0a90d8d02a5dab04a6baee18bbbf6dcdc2`，exact main push CI #37122681930 四矩阵 SUCCESS，并由 ChatGPT / 小雪独立确认。后续 Architecture Review Gate = PASS，顺序与独立授权边界见 [GOV-ARCHGATE1](../architecture/GOV-ARCHGATE1-POST-HLV3-REVIEW.md)。H-LV4 = NEXT / NOT AUTHORIZED；REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；Full Private RP 仍 BLOCKED_BY_OFFICIAL_HOST_CAPABILITY。下文case结果、计数、manifest及执行declaration保留原验证事实，不重跑、不修改。

本次真实执行 Life Engine Core mutation、durable CLAIMED、现有 A3 one-time permit issue/consume、local fake side effect、fresh-process crash 与 recovery query。没有真实 inbound，没有 provider message creation；`REAL_HOST_SENT / ACKNOWLEDGED` 均未取得，ACK validator 仍 `HOST_GAP`。

生产 Runtime、Core、Schema、Prompt、A3 合同与 Hermes source 均未修改。新增的四个 Python 文件只在 `tests/`，不被生产导入；CI 未提供真实 Host fixture 时明确使用 `CI_SYNTHETIC`，CI 只能提供 `SIMULATED_PASS`，不能代替本轮真实 Host 证据。

## 环境与真实 lifecycle

Hermes checkout `01382698fc32ec7740b6a204d9b7a6abeac74d33`，真实验证 Python `3.12.3`。Dedicated Home/install 与 Default 不同；Test profile 为 `life-engine-hlv-test`。protected registry 的 Owner 与 env admission 一致，explicit Server/Channel route 与既有 fixture 一致，registry 仍指向 Test Home；`.env` 是 expected owner 的非 symlink regular file，mode `0600`。这些原始标识只保存在仓库外。

启动前只读检查 delivery obligations、cron、resume/active turn、queue、notification 与 task state；只有已 delivered 的历史 obligation，无 pending/attempting/retry obligation。无 Test service/timer/container/worker 自动重启路径。两次启动均显式指定 Test Home、default launch profile 与 `--no-supervise`，未使用 replace 或 generic service start。fresh state 必须同时满足 running、exact child PID/start、`/proc` Home、named served profile 与 connected adapter，避免复用 stopped 文件中的历史 connected projection。

第一 lifecycle 运行完整 32-case suite，再由持续运行的 validation worker 签发 native permit/capability，等待实际 Gateway planned stop/restart。停止前核对 exact PID/start/Home，调用官方 `write_planned_stop_marker`，只 SIGTERM exact PID；两轮退出码均为 `0`，观察到 adapter disconnected 与 SessionDB shutdown。第二 lifecycle 的 process-start identity 不同，persistent install/profile/routing 不变。最终 Test PID absent、state stopped；Default PID/start/Home 全程一致。routing/profile/registry/credential 私有比对均一致，command-sync state 未变；每轮新增日志都出现 policy=off skip，没有新 sync attempt。

新增 Host 日志未出现 send/inbound/replay/cron 指标：`NO_SEND_OBSERVED`。这是 Host 日志观察，不冒充整个 Gateway 网络的 complete transport audit。下面的两个零计数是 **Living validation execution path** 的完整隔离计数；Gateway 自身 Discord connection 与 heartbeat 不属于 message delivery，也不作为 SENT 证据。

## 真实 binding 与 validation session

`HostGate` 每次进入 facade、recovery 或 final consume 前读取运行中的 Test Gateway state、`/proc` start/Home 与 install identity，匹配启动时 snapshot。Owner/profile/server/channel/install 请求字段只能与 protected fixture 比较，不能成为 authority 输入。错误身份在查询 operation 前拒绝。protected fixture 由本轮预检的 registry、exact routing 与既有 fixture 生成，不来自 model、prompt、工具 payload、last route 或显示名。

真实 protected provider 身份映射到独立 temporary Life Engine install 的 owner/principal/scope；不会把 Core fixture 创建到真实 Hermes Home。真实 provider target 转为 `LOCAL_FAKE:` 加 protected platform/server/channel 的 digest，不保留可送达地址。Core 自己生成 instance/generation、WorldRevision、WriterEpoch 与 SOUL session；Hermes process identity 不替代任何 Core 字段。

session provenance 明确为 `VALIDATION_SESSION / NOT_REAL_INBOUND`，真实 SessionSource hook 的 `HOST_GAP` 保留。LIFE worker 将 validation session metadata flush/fsync 到独立本地文件；Gateway restart 后原文件仍一致，但旧 permit/capability 被拒绝，恢复只返回 association。没有制造 Discord inbound，也没有把 synthetic Core session 称作 provider session。

Persistent identity + current process lifecycle + native A3 binding epoch/revision 构成 validation binding projection。A3 authority 关闭会清空 memory vault；新的 authority 保持 persistent host digest、产生新的 epoch。HostGate 拒绝旧 process snapshot，fresh native facade 再拒绝旧 capability/permit。这个组合只在 validation harness 中使用，不新增 Core contract，也不宣称 Hermes 有 native authority epoch/permit consumer。

## Transport 隔离与执行顺序

唯一构造路径是 `LivingHostFacade → validation consumer → LocalFakeTransport → local journal`。constructor 不接受 adapter、router、channel object、URL 或 credential；真实 transport 没有注册。独立 Python execution workers 不导入 Hermes Gateway/adapter/ledger；import fence 禁止 Discord/Telegram/WeChat、HTTP clients 与 generic Hermes delivery modules，audit hook 在任何 socket creation/connect/sendto/name resolution 之前 hard-deny。这些 fence 在 Core fixture mutation 之前安装，child crash worker 也独立安装；没有把 real transport 调用后再判断“不要发送”。

执行顺序为现有 facade 的 Core `begin_attempt` durable commit、transaction 结束、首次 `execute=true / CLAIMED`、native memory-only permit、final identity/Core generation/session/target/enabled/paused 检查与 consume，随后同步 local journal append/flush/fsync。consume 到 fake commit 之间没有 await、retry 或外部 transport。一个 permit 最多一条 journal event。journal 明确 `provider=LOCAL_FAKE`，含 event/Attempt/invocation、target digest、purpose、permit handle digest、timestamp 与 evidence digest，不保存 raw permit。

validator 使用冻结的 `FakeEvidenceValidator`，其 source 是 `LOCAL_FAKE_SIMULATED`。正常 fake evidence 可使隔离 Core Attempt 记录模拟 `SENT`；该状态只描述 fake fixture，不是 Discord/provider SENT。报告外部 delivery 的 `SENT / ACKNOWLEDGED = NOT_TESTED`。没有调用 ACK 路径。

generic Hermes ledger/retry、splitting、reply fallback、metadata.thread_id、forum auto-thread 均不存在于 fake-only dependency graph。unsupported target/URL/reply/metadata 参数直接 TypeError，无 journal；只有合法参数可 commit 一次。recovery consumer 无 transport 引用，不签 permit。credential 留在 Gateway boundary，validation workers 使用 env allowlist，不继承 provider credential；没有 model/prompt/transcript 接口。

## Case 实测

共同前置是 current real HostGate、独立 Core install/world/session、native A3 active authority、fake-only transport fence。每个用例独立 fixture。表中 transport 为 fake commits / real message sends；失败 consume 的 fake attempt 计数可增加，commit 不增加。所有用例 real transport invocation 与 network attempt 均为 `0`。恢复均为 native `recover_operation`，不直接读取 DB 来制造 recovery 结论；DB read-only snapshot 仅用于独立核对 business truth 未改变。

| Case | 操作、actual truth / rejection | Fake commit / recovery 增量 | 结果 |
| --- | --- | --- | --- |
| NORMAL-01 | prepare→claim→permit→consume→fsync fake→submit；Attempt=1、首次 permit=1、consume=1；fake Core SENT | 1；fake attempt/commit=1/1 | PASS |
| NORMAL-02 | 同 invocation replay execute=false，permit=None，Attempt 仍1 | 新增0 | PASS |
| DUP-01 | prepare 同 ID/digest 幂等；不同 material 为 IDEMPOTENCY_CONFLICT | 0 | PASS |
| DUP-02 | Barrier 同 invocation 并发 claim；仅一个 execute=true、permit 与 Attempt | 0 | PASS |
| DUP-03 | Barrier 两 consumer；一个成功，一个 CAPABILITY_STALE | 1 | PASS |
| PERMIT-01 | 重复 consume CAPABILITY_STALE | 总计1，第二次0 | PASS |
| PERMIT-02 | wrong target TARGET_MISMATCH | 0 | PASS |
| PERMIT-03/04/05 | wrong Attempt/invocation/purpose CAPABILITY_DENIED | 0 | PASS |
| PERMIT-06 | native authority close/reopen 后旧 permit CAPABILITY_STALE | 0 | PASS |
| PERMIT-07 | 独立 install 管理锁下 generation transition；GENERATION_STALE | 0 | PASS |
| PERMIT-08 | deterministic clock 超过现有10秒 TTL；CAPABILITY_EXPIRED | 0 | PASS |
| PERMIT-09 | 现有 lifecycle_transition + Core configure paused；EXECUTION_REVOKED | 0 | PASS |
| CR-01 | durable CLAIMED 前 os._exit(80)；Attempt=0、NOT_COMMITTED、无 permit/journal | 0；恢复0/0 | PASS |
| CR-02 | durable CLAIMED 后、response/permit 前 os._exit(81)；COMMITTED、CLAIMED，association 恢复 | 0；恢复0/0 | PASS |
| CR-03 | 丢失 Host association，fresh authority recovery 恢复；business snapshot 不变 | 0 | PASS |
| CR-04 | COMMITTED result 无 execute/permit；RECOVERY role 不能签 execution permit | 0 | PASS |
| CR-05 | historical CLAIMED 恢复只协调；新 claim RECONCILIATION_REQUIRED | 0 | PASS |
| CR-06 | permit issued 后 consume 前 os._exit(82)；fresh vault 不恢复 ExecutionPermit | 0；恢复0/0 | PASS |
| CR-07 | consume、append/flush/fsync 后 record_delivery 前 os._exit(83)；Core CLAIMED，delivery rows=0，journal=1 | 1；恢复0/0，无 resend | PASS |
| CR-08 | 同 fake evidence 重复提交仅一个 result；相同 evidence identity 改 provider reference→RECONCILIATION_REQUIRED，原 durable result 不被覆盖 | 总计1，提交新增0 | PASS |
| CR-09 | 可信 fake UNKNOWN evidence→Core UNKNOWN + reconciliation，不假装 FAILED/SENT/ACK | 0 | PASS |
| CR-10 | Event/barrier 两顺序：recovery 先完成 COMMITTED，再 close；close 先则 HOST_LIFECYCLE_STALE | 两顺序0 | PASS |
| LIFE-01 | 真实 Gateway restart 前 permit 保留于 worker；HostGate 拒旧 process，fresh native authority 拒旧 permit | 0 | PASS |
| LIFE-02 | 同一真实 restart，旧 native A3 recovery capability 在新 facade CAPABILITY_STALE | 0 | PASS |
| LIFE-03 | fsync validation session metadata 保持；恢复 association 无 permit，business truth 不变 | 0 | PASS |
| WRONG_OWNER / CHANNEL / PROFILE_AGENT | protected identity 比较拒绝 VALIDATION_IDENTITY_DENIED，无 fallback | 0 | PASS |
| WORLD_REVISION_FENCE | old session prepare replay（receipt 已存在）与 claim 均 WORLD_STALE | 0 | PASS |
| WRITER_EPOCH_FENCE | stale WriterEpoch SESSION_STALE | 0 | PASS |
| GENERATION_FENCE | claim、recovery、consume 均 GENERATION_STALE | 0 | PASS |
| RECOVERY_PRIVACY | 已存在/不存在 operation 的 wrong owner/profile/channel/server/install 均同一拒绝；business 不变 | 0 | PASS |

补充 privacy 测试曾错误地尝试为未关联 operation 签发 capability，得到 RECOVERY_IDENTITY_MISSING；该轮立即 planned stop，没有放宽合同。最终用既有旧 capability 比较存在/不存在 operation，两者均先 CAPABILITY_STALE；generation transition 后两者均先 GENERATION_STALE，重新完整真实 suite 与 restart probe 全部通过。

CR-01/02/06/07 都是 fresh Python subprocess 与 `os._exit`，不是 exception；stdout 均空，退出码分别80/81/82/83。phase marker 在退出前 flush/fsync，记录准确 injection point、permit issue/consume 与零 fence 计数。CR-02 使用现有 facade validation crash hook `after_claim_commit`，未 monkey patch Core。CR-07 不调用 record_delivery；恢复原操作 COMMITTED/CLAIMED、continuation=RECONCILIATION_REQUIRED，重复 recovery 后 journal byte-for-byte 不变。

CR-10 的 transition 是 validation binding barrier 与现有 A3 close，不是 Hermes plugin/config/profile reload。LIFE 的 Gateway restart 单独有真实 PID/start/log 证据，不能把 fresh Python crash 当 Gateway crash。Owner/target fixture、binding revision、Core generation、authority/plugin epoch mismatch 必须先拒绝，再查 operation；原 A3 binding/generation privacy 回归也随完整 suite 执行。

## 证据与可重复执行

真实 fixture、identity snapshot、每 case durable business snapshot、journal、crash phase marker、suite stdout/stderr、Gateway log delta、official stop 比对与 baseline/final config digest 保存在仓库外 protected evidence。目录 `0700`、文件 `0600` 已逐项核验。未提交 credential、私有 Home、PID、session/Owner/Bot/Server/Channel 原始标识或 provider response。

本轮 SHA-256 manifest digest：`821781ed2fb58e00aa2756357a385470c2b9b81aa62f12a5350684a5397a56a9`。Host lifecycle result：`5ea54c3f55eb8cb8b8fa1f0dec853aa2a9fa6d09a933eee737b84e94e266c249`；native LIFE result：`ca2a363412d6bb3450a836d34bde487864a6e4291bae4ffa5e130646cbfe9fcb`。

关键 case durable-state digests：CR-01 `bbee47a69b0752fc02585d69f68418b0cb0a3b6e0a8bb4cc16047da1aff47d5c`；CR-02 `fb3e1c3faf3dce7d18df129dce8a015b0af3ceb814282bab964e0685a4ef1047`；CR-06 `8d14cc650319e094131af84d441d77bcf1903c85f806076ad946010092a23dde`；CR-07 `c848f9c152fb9ebbecb1397cf7faf875fbad6171d193d50afdce7777be84223c`。其余每 case digest 见 protected manifest；不通过公开原始 identifiers 提高可重复性。

本地 synthetic 回归命令：`python -m unittest discover -s tests -p test_hlv3_validation.py -v`。真实 runner 先复验环境，再提供外部 `LIFE_ENGINE_HLV3_HOST_FIXTURE`（source=REAL_HOST_VALIDATION）与 protected evidence directory，运行同一32-case suite；`hlv3_lifecycle_worker.py` 通过 stdin/stdout barrier 等待外部官方 stop/restart。live worker 没有启动/停止 Gateway 权限。CI 不接触真实 Home 或 credential。

完整 suite 使用项目支持的 Python 3.12，Linux 本轮结果 `Ran 475 tests in 495.948s` / `OK`；本机默认3.10的初次执行因既有 `hashlib.file_digest` 不可用出现环境错误，未用于 PASS 证据，未修改生产代码。exact Head 四矩阵 CI 的结果由 Draft PR 的最终报告单独提供，不把旧 main/PR workflow 当本次 CI。

## Mandatory declaration（原验证执行快照；当前治理状态为 DONE）

```text
SP-005A4-HLV3 = PASS
ENVIRONMENT_GATE = PASS
REAL_TRANSPORT_ISOLATION = PASS
REAL_TRANSPORT_INVOCATION_COUNT = 0
REAL_NETWORK_SEND_COUNT = 0
REAL_INBOUND = NO
LIVING_CORE_MUTATION = YES
REAL_ATTEMPT = PASS
REAL_PERMIT_ISSUE = PASS
REAL_PERMIT_CONSUME = PASS
FAKE_TRANSPORT = PASS
FAKE_JOURNAL_DURABILITY = PASS
NORMAL_01 = PASS
NORMAL_02 = PASS
DUP_01 = PASS
DUP_02 = PASS
DUP_03 = PASS
PERMIT_01 = PASS
PERMIT_02 = PASS
PERMIT_03 = PASS
PERMIT_04 = PASS
PERMIT_05 = PASS
PERMIT_06 = PASS
PERMIT_07 = PASS
PERMIT_08 = PASS
PERMIT_09 = PASS
CR_01 = PASS
CR_02 = PASS
CR_03 = PASS
CR_04 = PASS
CR_05 = PASS
CR_06 = PASS
CR_07 = PASS
CR_08 = PASS
CR_09 = PASS
CR_10 = PASS
LIFE_01 = PASS
LIFE_02 = PASS
LIFE_03 = PASS
WRONG_OWNER = PASS
WRONG_CHANNEL = PASS
WRONG_PROFILE_AGENT = PASS
WORLD_REVISION_FENCE = PASS
WRITER_EPOCH_FENCE = PASS
GENERATION_FENCE = PASS
RECOVERY_PRIVACY = PASS
GENERIC_HERMES_RETRY_ISOLATED = PASS
MESSAGE_SPLITTING_UNREACHABLE = PASS
REPLY_FALLBACK_UNREACHABLE = PASS
THREAD_OVERRIDE_UNREACHABLE = PASS
FORUM_AUTO_THREAD_UNREACHABLE = PASS
REAL_SEND = NO
SENT = NOT_TESTED
ACKNOWLEDGED = NOT_TESTED
ACK_VALIDATOR = HOST_GAP
EVIDENCE_LEVEL = REAL_HOST_DRY_RUN_PASS
ARCHITECTURE_CHANGE_REQUIRED = NO
HOST_PATCH_REQUIRED = NO
DEFAULT_GATEWAY_MUTATED = NO
FINAL_TEST_GATEWAY_STATE = STOPPED
H_LV4_STARTED = NO
```

Recovery restores knowledge, never permission. durable CLAIMED 是历史 truth，不是第二次 side effect 的执行授权。原 Draft 交付时在 Draft/CI 后停止等待审核；当前 DONE 与后续 Gate 见顶部，不构成新执行授权。
