# SP-005A4-HLV4-R1 — Real Delivery Authority 实施验证

## 当前结论与边界

Base：`88e699ca34cab463cd65be61edfdf61522b8952a`。R0 = DONE / FROZEN；本轮 R1 = IMPLEMENTED / DRAFT_REVIEW_PENDING。REAL_SEND = NO。HLV4-A = BLOCKED，等待 R1 canonical DONE 后另行授权重试；HLV4-B = NOT AUTHORIZED。REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP。

本轮只修改 Host-neutral Runtime binding/facade/capability 与 tests；未修改 Core Intent/Attempt、B1 recovery、DeliveryEvidence、Schema、Prompt、Hermes/OpenClaw。没有 Host 操作、真实 inbound、真实 transport 或真实 send。`DATA_SCHEMA = 8`、`SP-005A-living-runtime-v1`、`SP-004K-prompt-v1` 保持。

## 实施映射

`BindingMode.SIMULATION / REAL_DELIVERY` 与既有 `LEGACY / LIVING_PENDING / LIVING_ACTIVE` 正交；默认 BindingAuthority 为 SIMULATION，普通 non-isolated simulation claim 仍 `NO_REAL_SEND`。只有可信本地 `RealDeliveryBindingFactory` 可构造 REAL_DELIVERY binding 并安装 typed target/policy；`isolated_test` 只决定隔离fixture属性，不构成真实资格，`NO_REAL_SEND` 布尔值不参与 ALLOW 推导。

`ExecutionPurpose.SIMULATED_CONTACT / REAL_CONTACT` 为严格 Enum。原 A3 模拟路径保留；real permit 使用同一 `ExecutionPermit`/vault抽象，Core durable CLAIMED + 首次 execute=true 之后才签发。real claims绑定binding identity、当前authority/plugin epoch、Core generation、Core返回Attempt、Intent、invocation、typed target digest、payload digest、purpose、TTL/single-use。grant 在内存按 UNBOUND→RESERVED→SPENT / REVOKED，scope为exact Intent/invocation/target/payload；policy deny、异常、expiry或issue失败均不退款、不补签，历史 CLAIMED无法产生第二枚permit。grant/permit禁止pickle；进程restart后vault/grant为空。

`RealDeliveryPolicy` 默认DENY，只有精确 `PolicyDecision.ALLOW` 才允许签发，未知值和异常拒绝。consume前再次检查当前binding mode/routing、typed target、Core enabled/paused/generation、session/world/writer、当前policy、grant/permit exact claims与expiry；management generation barrier后一次性consume。`SimulationConsumer`与`RealDeliveryConsumer`分立且双向错purpose拒绝。R1 real consumer固定返回 `LOCAL_PRE_TRANSPORT_INTERCEPT`，不接受transport/sink/URL/channel/router参数，不生成DeliveryEvidence或Core SENT。

BindingMode在单个authority生命周期内不可变；mode切换须关闭旧authority并创建新epoch。route/target/policy/plugin/lifecycle transition、authority restart、Core generation变化使旧资格失效；Core session/route persistence不恢复grant。`recover_operation`仍只恢复知识与关联，不能签grant、permit或send；CLAIMED != SENT != ACKNOWLEDGED。

## 验证矩阵与证据分类

| 用例 | 验证内容 | 本轮结果 |
| --- | --- | --- |
| R1-NORMAL | Core CLAIMED后签real permit，一次本地intercept，重复consume拒绝、同invocation replay无permit | PASS |
| R1-DEFAULT/POLICY | 默认模拟、无grant、DENY policy、policy exception、bool flip、非隔离默认claim均拒绝real authority | PASS |
| R1-TYPE | 模拟permit→real consumer、real permit→模拟consumer均拒绝；未知purpose不隐式转换 | PASS |
| R1-FIELDS | 错Intent、Attempt、invocation、typed target、payload均拒绝；严格typed target缺失字段或多目标分隔符拒绝 | PASS |
| R1-LIFECYCLE | expiry、plugin reload、authority restart、policy/target transition、pause、generation与World fence拒绝旧资格 | PASS |
| R1-CONCURRENCY | barrier并发grant reserve、同invocation claim/permit issue、permit consume及admission/transition排序 | PASS |
| R1-CR01～04 | fresh Python subprocess + `os._exit(80..83)`；CLAIMED→permit前、permit→guard前、guard→consume前、consume→intercept后分别崩溃 | PASS |
| R1-RECOVERY | 每个crash后fresh authority恢复，CLAIMED保持，grant/permit未重建，零local intercept/retry | PASS |
| R1-TRANSPORT | 静态AST依赖检查 + socket hard-deny执行，real consumer无transport参数，零网络调用 | PASS |
| R1-COMPATIBILITY | A3/HLV3/B1/World Revision/Living Runtime与完整supported suite | Python 3.12最终源码：510 tests OK（skipped=1） |

CR03 的child-only instrumentation在vault.consume入口 `os._exit`，只定位final guard已通过但尚未消费；不进入生产路径。CR04在固定local interceptor后退出，未创建provider result或SENT。四个child均无stdout；phase marker仅含注入点、exit code与零网络/transport计数。fresh authority B1 recovery不含execute/permit，Core Attempt仍CLAIMED。

`REAL_TRANSPORT_DEPENDENCY = NONE`；真实 provider transport函数未注册。静态import AST覆盖真实consumer与binding；运行时socket hard-deny覆盖合法execution路径。`REAL_TRANSPORT_INVOCATION_COUNT = 0`、`REAL_NETWORK_SEND_COUNT = 0`、`LOCAL_INTERCEPT_EXECUTION_MAX = 1`。这里只证明本地R1执行边界，不升级为真实Hermes Host证据。HLV3历史 `REAL_HOST_DRY_RUN_PASS` 保留，不重跑真实Host。

## 后续 Gate

R1 Draft/Ready/Squash/canonical main/exact main push CI与独立核验完成之前，HLV4-A retry不得启动。即使R1 DONE，HLV4-A仍需独立授权；HLV4-B需更后续单独真实发送授权。R1不取得REAL_HOST_SENT或ACK，不解决SessionSource/ACK Host Gap与Full Private RP。
