# SP-005A4-HLV4-A1 — Dedicated Hermes Delivery Adapter 本地实施验证

## 范围与结论

Base：`337f5f95d47929c0a63c86cf9e2f70a14b9f6ddb`。A0 = DONE；本轮实现 `life_engine_discord` 独立平台，使用 Hermes 0.21.3（源码 `01382698fc32ec7740b6a204d9b7a6abeac74d33`）官方 `PluginContext.register_platform()` / `PlatformEntry.adapter_factory` / `BasePlatformAdapter` 合同的本地 fixture。`integrations/hermes_living/` 是未来可安装的插件源码，**本轮未复制到真实 HERMES_HOME，未启动 Gateway，未读取 credential**。插件默认 factory 不注入 transport，`connect()` 不能建立可发送路径。

本轮最高证据为 `DEDICATED_ADAPTER_IMPLEMENTATION_PASS`（独立 Draft Review 待定）。`REAL_HOST_PLUGIN_LOAD`、profile isolation、真实 adapter/Gateway lifecycle、Discord SDK 最终调用位置与 `REAL_HOST_DELIVERY_BOUNDARY_PASS` 均为 `DEFERRED_TO_HLV4_A2`。A2 / HLV4-B 未授权；REAL_SEND = NO，REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP。

## 执行结构

既有 R1 `RealDeliveryConsumer.intercept()` 保持原样。新增 `deliver_bound()` 仅使用构造时绑定的固定 Host-neutral port；其 `preflight()` 不产生 side effect，然后沿用原 `_consume_real_permit()` 的 current authority、mode、target、Core enabled/paused、session/world/writer、generation、policy、expiry 与 once guard。消费后唯一操作是 `await port.invoke_exact(target, payload)`；不签第二类 permit，不写 SENT evidence。Hermes adapter 专用 `deliver_authorized_real_contact()` 仅调用此 consumer；标准 `send()` 和 generic 路径硬拒绝。A1 只注入 `InertExactTransport`，所以本地结果 `LOCAL_INERT` / `UNKNOWN` 均不是 SENT。

可信 adapter projection 包含独立平台名、profile、Agent、application identity、credential identity digest、adapter instance epoch、authority epoch 与 plugin epoch。此 digest 是 Host 凭据记录的非秘密身份标识，**不是 bot token 的哈希**。credential/application 变化、disconnect 或 authority plugin reload 撤销旧 permit；真实 Gateway/profile/reload 映射留给 A2。真实 credential 值不进入 Core、grant、permit、日志或测试。`TrustedDeliveryTarget` 仍是业务 exact target；bot/application 和 credential identity 留在 Host lifecycle projection，随 plugin epoch 变更撤销旧执行资格。

## Hermes generic side-effect surface 审计

已对所述确切 Hermes 源码 `gateway/platforms/base.py` 的发送、媒体、交互和 ledger 方法做只读审计，并在 adapter 中显式覆盖：`send`、`send_final_ledgered`、`_send_with_retry`、`send_draft`、`send_multiple_images`、`send_image`、`send_animation`、`send_voice`、`send_video`、`send_document`、`send_image_file`、`send_private_notice`、`send_exec_approval`、`send_slash_confirm`、`send_clarify`、`send_typing`、`edit_message`、`delete_message`、`create_handoff_thread`。这些调用返回非 retryable `REAL_CONTACT_AUTHORITY_REQUIRED` 或抛出同等拒绝；`send_final_ledgered` 在 inherited ledger bracket 写 obligation 前拒绝。未注册 `send_message_handler`、`standalone_sender_fn`、`cron_deliver_env_var`、model tool、webhook sender 或 fallback sender。generic default/last/reply/metadata route 只能落到拒绝面；真实 Gateway 中的 routing 行为仍需 A2 观察，不冒充本地 PASS。

插件源码不 import Discord、Telegram、HTTP、socket 或 OpenClaw provider client。测试使用独立 Hermes contract fixture、AST override/dependency 检查、inert transport trap 和 socket connect hard-deny；没有网络 provider dependency。真正 Discord SDK 接入及唯一不可逆 call site 是 A2 的独立门槛，不能把本地 inert port 当成其验证。

## Case 结果

| Case | 本地证据 / 状态 |
| --- | --- |
| A1-01～A1-11 | 独立平台名、官方 registry fixture、全部 generic surfaces 硬拒绝；metadata/reply/thread/forum/oversize 无 bypass；四种旁路未注册；PASS |
| A1-12～A1-20 | 模拟 permit 不能绑定 adapter；错误 target、intent、Attempt、invocation、payload，stale plugin/credential/application、paused Core、重复 consume 与 replay 拒绝；真实 R1 Core CLAIMED + REAL_CONTACT permit 到 inert port 最多一次；PASS |
| A1-21～A1-23 | transport exception / UNKNOWN 不 retry、不变 SENT；B1 recovery 无新 permit 或 resend；PASS |
| A1-24～A1-27 | 原 R1 intercept、A3/HLV3、B1、Session/World Revision Fence 由完整测试回归；PASS 以本 PR exact Head CI 为最终准据 |
| A1-28 | 无 provider import + socket connect hard-deny + transport 调用计数；本地 network invocation = 0；PASS |
| A1 crash | 新 `hlv4_a1_crash_worker.py` 在 CLAIMED→permit 前、permit→guard 前、guard→consume 前、consume→inert boundary 后四点用 fresh subprocess + `os._exit`；阶段记录 fsync，重启 recovery 无 permit / resend，Core 仍 CLAIMED。原 R1 CR01～CR04 同时保留；PASS 以完整测试为准 |
| Generic Hermes routing / real plugin load | `DEFERRED_TO_HLV4_A2`；本轮未启动真实 Gateway |

测试采取 deterministic `Barrier` 同步并发 permit consume；一枚 permit 最多一次 inert invocation。异常/UNKNOWN 后 Attempt 保持 CLAIMED，进入 reconciliation；不 refund grant、不重新签发、不自动 retry。`DATA_SCHEMA = 8`；Schema Signature = `SP-005A-living-runtime-v1`；Prompt Template = `SP-004K-prompt-v1`；R0/R1 authority、B1 recovery 与 DeliveryEvidence truth 未改。

## A2 的未决验证

A2 必须在另行授权后验证 plugin 实际加载、profile 与 credential 隔离、Gateway/adapter lifecycle、real provider SDK exact call site、consume 后无任意 await 的真实边界，以及 hard pre-send intercept。若 SDK 在调用前需要额外异步 target lookup、queue、retry 或 fallback，不能将 A1 的 inert 结果升级；须按 A0 STOP gate 报告。A1 不产生 `DeliveryEvidence(SENT)`，不解除 Full Private RP blocker。
