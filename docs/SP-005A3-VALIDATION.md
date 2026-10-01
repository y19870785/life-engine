# SP-005A3 v3 — Living Host Binding 验证报告

SP-005A3 = PENDING_INDEPENDENT_REVIEW；SP-005A3-B0 = DONE；SP-005A3-B1 Architecture = DONE；SP-005A3-B1 Implementation = DONE。审核前不转 Ready、不 Merge、不开始下一阶段。

## 基线与代码范围

R1 唯一 Base：`b78b849b1bfac1cbd28359cfb317fd1d4cb84402`。分支：`feat/sp-005a3-living-host-binding-v3`。创建时 origin/main = HEAD = merge-base = Base，worktree clean。Base 直接 parent 是 `f83d36c76fea6de1a31b449535d5df6cea3909b5`，GOV-DOC3 仅文档变更已保留。[main push CI 36833987594](https://github.com/y19870785/life-engine/actions/runs/36833987594)：push/main/exact Base/completed/success，Ubuntu / Windows × Python 3.11 / 3.12 四矩阵 SUCCESS。

Head SHA、commit 数量、完整 changed files、Draft PR URL 和 exact Head CI URL 以提交后的 PR 交付报告为准，避免将自引用 SHA 写入其自身 commit。实现不使用旧 A3 分支；没有 cherry-pick、merge、rebase 或整体复制旧实现。

Runtime 新增五份文件：

- [living_host_binding.py](../runtime/life_engine/living_host_binding.py)：HostIdentityEnvelope、per-install BindingAuthority、可信管理面、路由、epoch、能力签发/校验、原调用 identity/digest、独立 recovery delegation、permit boundary。
- [living_host_metadata.py](../runtime/life_engine/living_host_metadata.py)：版本化独立本地 metadata、HMAC checksum、私有权限、单写者 lease、原子 replace / fsync；不接触 Living business tables。
- [living_host_capability.py](../runtime/life_engine/living_host_capability.py)：随机 opaque handle + HMAC、仅内存 claims、脱敏 repr、一次消费与 lifecycle revoke。
- [living_host_facade.py](../runtime/life_engine/living_host_facade.py)：八个 bounded 方法及 trusted executor ClaimOutcome。
- [living_host_evidence.py](../runtime/life_engine/living_host_evidence.py)：DeliveryEvidence v1 result-only verifier 与 local deterministic fake transport。

Tests 新增 [test_living_host_binding.py](../tests/test_living_host_binding.py) 和 [living_host_process_fixture.py](../tests/living_host_process_fixture.py)。文档修改 A2 implementation status、A3 matrix、roadmap、B1 follow-up，并新增本报告；不覆盖 GOV-DOC3 历史 Hermes 评测。既有 Core、Schema、Prompt 和 tests 文件无变更。

CI [tests.yml](../.github/workflows/tests.yml) 仅将 job timeout 从 15 调整为 25 分钟：Base Windows job 已接近 14 分钟，新增真实进程回归需要余量；四矩阵、完整测试命令与安全权限不变。本机默认 Python 3.10.9 缺少既有代码所需的 hashlib.file_digest / sqlite3.SQLITE_BUSY；正式本地完整验收使用 Python 3.12，不修改 Core 兼容语义。

## Authority、路由与 metadata

Binding Authority 仅由可信本地部署调用，不提供模型 tool/JSON enrollment、身份签发、HMAC 或 raw capability 输出。Owner / Scope / install / instance /完整 Host identity 来自显式可信注册；安装位置摘要进一步防止复制目录后复用旧 metadata。身份字符串只是注册断言，真实 Hermes/OpenClaw 安装 attestation、IPC 与服务启动器不在本阶段。信任边界与既有 Principal 一样，为本地可信代码 / 同 OS 用户；任意 Python 或同用户恶意进程不属于模型隔离区。

同安装 lease 跨进程锁定，metadata 目录另有生命周期单写者锁。Windows 用当前 SID 的受保护 DACL，POSIX 目录 0700 / 文件 0600。secret 单独文件、随机 32 bytes，不进入 Git、Prompt、transcript、普通日志、Living DB 或业务 fixture。自动化仅使用独立 deterministic test key。metadata 限 1 MiB，checksum/version/字段集合损坏或丢失立即拒绝；已有 enrollment marker/secret 时不重新初始化缺失 metadata。

metadata 只保存身份/Owner/Scope/target 的注册映射、routing revision/mode、invocation correlation、完整 operation identity / expected Core payload digest、inbound 首次接收时间与摘要、安装生命周期证据。correlation 不保存 Attempt ID、CLAIMED/SENT/ACK 或 receipt。Core recovery 投影得到的关联只保留在当前 authority 内存，不作为业务真源。

routing mode 仅 LEGACY / LIVING_PENDING / LIVING_ACTIVE，从校验后的可信 metadata 读取。已 enrolled 的注册默认 PENDING；未 enrolled 注册可 LEGACY。ACTIVE 需要已存在的 Core enrollment 且 target 一致。`route(callback)` 在任何 legacy 回调前 fence；PENDING/ACTIVE 返回 LIVING_HANDOFF_REQUIRED，不能 fallback。LEGACY 另校验 Core 未 enrollment，防止路由 metadata 与 Core 注册不一致时产生副作用。尚未给真实插件接线；所有未来真实业务入口必须经过同一 dispatcher。

## Lifecycle 与 capability

每次 authority start 新 `binding_runtime_epoch`，不持久化复用；每次 plugin load/reload 新 `plugin_epoch`。reload 清空旧 capability、permit 与 snapshot handle，不创建 Core generation，不改 Day/budget/cooldown/Intent/Attempt。存在未决 claim 时只冻结执行路径并要求 reconciliation，不声称 Core 已将 CLAIMED 自动改为 UNKNOWN。authority 重启不恢复旧 permit，旧 capability/epoch 拒绝，历史 claim correlation 要求 trusted continuation；独立服务接管 Core incarnation 使用既有可信 Core factory/恢复流程，不藏在只读 recovery 中。

每次校验重读 durable registry generation；restore 后旧 envelope、普通/recovery capability 和 permit 全部 GENERATION_STALE。实际 durable restore/CLAIMED→UNKNOWN 合同沿用 A1/B1 既有真实恢复回归；Host 另注入 registry generation 变化验证权限拒绝。

capability 为 `nonce.HMAC` 的 opaque 本地对象，claims 留在内存。绑定 install/instance、binding revision、authority/plugin epoch、generation、allowed method、invocation、exact target、canonical payload digest，以及封套中 trusted session identity。capability TTL 最多 60 秒、默认 30 秒，一次消费；凭据不放进 facade JSON。未知字段、错误方法、错误身份、过期、重复消费均拒绝。所有摘要复用 Core canonical JSON / SHA256，禁止 repr / unordered / locale serialization。

recovery-only capability 独立角色与方法 allowlist，只用于 recover_operation，另绑定 metadata 中 exact recovery identity/digest。当前 authority 根据 Owner、Scope、producer、original actor、当前 install/generation/epoch provenance 构造 RecoveryDelegation 与 LivingRecoveryContext；当前 recovery grantee 与 original actor 分离。模型/tool JSON 不构造有效权限；recovery 不能用于 prepare、claim、delivery 或 permit 签发。

HostIdentityEnvelope 为受信不可变类型，带 seal；session-bearing identity 包含 session_id / writer_epoch / world_revision / runtime_id / generation / purpose / viewer，以及 Principal / Scope / provenance。原始 JSON、自报 Owner、转发/UNKNOWN provenance 不能代替可信封套。序列化封套 <= 8 KiB；Facade 完整响应 <= 16 KiB，超限 fail closed。

## Facade 与外部副作用

- `tick`：窄 scheduler context → Core tick，只返回结构化结果；不调模型/transport，不签 permit。
- `query_context`：仅 SOUL_RESPONSE → bounded LivingContextSnapshot；seal 和 revalidation handle 留 authority。无 PromptSnapshot 拼装、RP 注入、Story/Memory/Lore 修改。
- `observe_inbound`：要求稳定 external event ID、EXTERNAL_USER provenance、认证 Owner 和 canonical digest。相同 event+payload 幂等；不同 digest 冲突；首次 received_at 持久复用；无 ID 返回 INBOUND_UNVERIFIED。
- `prepare_contact`：Core DECIDED→PREPARED，512 UTF-8 bytes；调用前保存 exact identity/digest；不 claim/permit/send。
- `claim_attempt`：仅 trusted executor 与隔离测试实例；Core begin_attempt 首次 execute=true + CLAIMED durable commit 结束后才发内存 permit。Replay execute=false，历史 receipt 的 execute=true 不会重签。
- `recover_operation`：只包装 LivingRuntime.query_operation_recovery；不读 living_operations、不调用 mutation 探测、不签 permit、不触发 transport。COMMITTED + Attempt association 只进入 reconciliation。
- `submit_delivery_result`：独立 collector/result-only capability，验证 typed provider evidence → Core record_delivery；不要求旧 chat session OPEN，不授予 send。
- `status`：默认 20、硬上限 100，revision/binding revision 游标，有界脱敏；无 capability/secret/raw receipt/full history/任意 DB rows。实现通过现有 Core status 读取业务结果后白名单投影，未新增私有 SQL 或 Core API；Core status 内部现有 materialization 不变。

World fence 最终由 B0 Core 同事务完成：current World→Scope→Session→WriterEpoch→WorldRevision→Living root→receipt/CAS/mutation。Facade 不悄悄更新陈旧 session/revision；receipt replay 也先受当前授权。B06 与 B28 同时验证 Host path 和 Core transaction 前交错。

one-time execution permit 为 opaque memory-only、10 秒 TTL；绑定 current authority/plugin epoch、generation、target、Attempt、invocation、SIMULATED_CONTACT purpose。consume 与 lifecycle 在同一 authority mutex 下；wrong target/Attempt/invocation/epoch、expired、重复 consume 拒绝。发送前重验当前 target 与原 trusted session；permit 消费后仍保留未决 claim 生命周期关联，直到可信结果登记或协调。它不是 SENT/ACK evidence，也不持久化为业务真源。

外部边界严格为 Core CLAIMED commit→DB/安装事务锁结束→permit→原子消费→fake 外部副作用→provider evidence→Core record_delivery。DB 与外部副作用不原子。Fake provider 无网络、真实渠道、真实用户或正式 Owner target；只写隔离本地 journal，并可注入进程退出。SENT 需要签名 provider reference / message identity / sent_at；ACK 是独立已验证 fake provider event。FAILED / UNKNOWN 为独立结果；CLAIMED != SENT != ACKNOWLEDGED。

NO_REAL_SEND = true，本任务没有关闭。正式实例默认只作结构化预览，claim/fake transport 需要独立隔离测试 authority。没有真实 transport、Hermes/OpenClaw adapter、生产 plugin 安装、调度/cron、Media、Voice 或 RP 接线。

## 自动验收与恢复证据

[B01–B34 executable mapping / expected result](planning/SP-005A3-HOST-BINDING-TEST-MATRIX.md#a3-v3-可执行证据映射)全部有实际 unittest。Host 专项 44 tests，结果 SIMULATED_PASS。B06 / B14 / B28 的完整本地 Host 子集通过；原 B06_CORE_FENCE_PASS / B14_CORE_RECOVERY_PASS / B28_CORE_FENCE_PASS 与 B1-08_CORE_PASS / B1-09_CORE_PASS 原样保留。

B14 两个合同分别成立：fresh valid session + 同 operation mutation replay 返回既有 receipt、execute=false、无第二 Attempt；authority 关联丢失时只使用原 exact identity/digest 经 B1 read-only projection 恢复。后者 COMMITTED / historical CLAIMED 不表示执行权，响应中没有 execute/permit，业务表前后不变，fake journal无新增。

真实进程边界使用 subprocess + fresh Python + os._exit，未以 exception 冒充 crash：

| process ID | executable evidence | expected result |
| --- | --- | --- |
| P1 | B14 / `claim-lost` / exit 81 | CLAIMED 已 durable commit，response stdout 空、Host association缺失；新 authority B1 COMMITTED恢复关联；NO PERMIT / no resend。 |
| P2 | B10 / `restart` / exit 84 | fresh Python启动新 authority epoch、打印 generation后退出；generation不变、旧capability拒绝。 |
| P3 | B15 / `claimed-crash` / exit 82 | 首次 claim+permit 后 send 前退出；permit丢失，当前CLAIMED进入协调。 |
| P4 | B15 / `sent-crash` / exit 83 | permit consumed、本地 fake journal append+fsync后退出；record_delivery未执行；最多一条fake外部记录，Core仍CLAIMED只协调。 |
| pre-commit | `before-claim` / exit 80 | correlation先保存、claim未调用；B1 NOT_COMMITTED；仍不自动claim/send。 |

Concurrency：duplicate tick（同与不同 invocation）、prepare、claim、capability consume、permit consume、delivery result submit；claim vs target change、plugin reload、authority restart；recovery vs close/reload transition。线程 barrier/event 控制实际竞争；Core World/Scope/Policy 并发与双进程 quota 回归沿用既有 A1/B0/B1。

B1-08/B1-09 Host authority/capability 子集为 SIMULATED_PASS，仅在本轮测试实际通过后记录；不能升级真实 Host PASS。A1 48 contract IDs、B0 10 R1 tests、B1 16 specialized tests 与 complete unittest 必须全部继续通过，运行计数/时间与 exact Head CI 记录在交付报告。没有改变 Core business semantics 或 operation fingerprint。

本地实测：Windows / Python 3.12.10 完整 unittest 441 tests，440 passed、1 skipped、0 failures/errors，383.529s；skip 为既有 Unix-only symlink 测试。日志逐项确认 A1 48 IDs 对应 52 tests PASS、B0 10 tests PASS、B1 16 tests PASS。最后 Windows ACL 加固后重跑 Host 专项 44 tests 全部 PASS（53.812s）。5 份变更文档的 58 个本地链接/锚点通过，B01–B34 executable ID 映射及 Host source boundary 检查通过。完整 exact Head 四矩阵仍由 Draft PR CI 再验证，不用本地环境替代。

## 验证门禁与后续状态

提交前必须 git diff --check、文档本地链接/锚点及 executable test ID 映射校验通过；Draft 后 exact Head CI 为 Ubuntu / Python 3.11、Ubuntu / Python 3.12、Windows / Python 3.11、Windows / Python 3.12 全部 SUCCESS。PR 为新的 OPEN / Draft / NOT MERGED / Auto Merge OFF；Head/Base、changed files 与 clean worktree在交付时再次核验。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = NOT AUTHORIZED。无 Schema 9 / migration / Prompt fingerprint/HMAC/预算裁剪修改。

Hermes real Host validation = PENDING_REAL_HOST_VALIDATION；OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED；H1 = BLOCKED；H2 = BLOCKED。GOV-DOC3 历史 Hermes 综合评测不升级为 Living Host PASS、ACKNOWLEDGED、Organic Contact real-send PASS 或 Full Host validation PASS。

完成 implementation、tests、docs、NEW Draft PR 与 exact Head CI 后立即停止，等待 ChatGPT / 小雪独立审核。
