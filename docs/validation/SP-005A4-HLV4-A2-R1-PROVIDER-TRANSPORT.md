# SP-005A4-HLV4-A2-R1 — Dedicated Discord Provider Transport 本地验证

> CURRENT GOVERNANCE NOTE：本报告保留 Draft 阶段的原始本地验证证据与当时限制。[GOV-SOUL-ROADMAP1](../architecture/GOV-SOUL-ROADMAP1-SOUL-CONTINUITY-MAINLINE.md) 记录 A2-R1 最终 DONE、attempt 1/2 CANCELLED、attempt 3 SUCCESS 及治理偏差；Host Integration 后续已 `DEFERRED / NOT AUTHORIZED`。本报告不证明真实 Host plugin load、provider delivery、SENT 或 ACK。

## 范围与证据上限

固定 Base：`9ebfdebe50bd766c513742267e7bfbdfb1170238`。本轮依据已冻结的 [A2-R0 Provider Transport 合同](../architecture/SP-005A4-HLV4-DEDICATED-DISCORD-PROVIDER-TRANSPORT.md)实现 plugin-owned one-shot `MESSAGE_CREATE` 边界。只使用 synthetic credential、fake resolver 与 fake provider session；未安装真实 Hermes plugin、未启动 Gateway、未读取 Test Bot credential、未连接 Discord 或进行任何 provider HTTP 请求。`REAL_HOST_PLUGIN_LOAD / REAL_HOST_LIFECYCLE / REAL_HOST_DELIVERY_BOUNDARY_PASS / REAL_HOST_SENT / ACKNOWLEDGED = NOT_ACQUIRED`；`ACK_VALIDATOR = HOST_GAP`。

## 实施边界

`provider_ownership.py` 在 session factory 调用之前，以受保护的完整 inventory 对 raw credential 做内存精确比较。Hermes 原生 `(platform, fingerprint)` claim 不用于跨 platform 独占判定。同 token 在 built-in `discord`、其它 plugin、其它 profile、第二 REST owner 或同 platform 第二 adapter 中出现均拒绝；不同 token 不误拒。被撤销但尚未关闭的 authenticated session 继续占有 credential，避免新旧 owner 重叠。inventory 的 **真实 Hermes 来源及完整性** 仍须 A2 retry 在隔离 Host 中独立证明；本地 `complete=True` fixture 只证明拒绝算法，不是 Host 事实。

同一 `DiscordRestOwnership` 拥有 provider session 与 `RateLimitDomain`。后者同时记录 credential-global 和 route 限流，从任何 authenticated REST route 的响应更新状态，并在 consume 前保守串行化 admission；已阻塞时不等待、不消耗 permit。未知初始 bucket 允许一次尝试，429 更新限流知识但不重试。受保护 resolver 须在 consume 前交付普通 guild text channel 的精确 projection；缺 resolver、类型不符或 target 不一致即拒绝。payload 在 consume 前固定为 UTF-8 JSON bytes，显式 `allowed_mentions.parse=[]`，无 split、reply、attachment 或动态转换。

最终路径为 A1 adapter lifecycle lease → provider `prepare_exact()` → R1 final guard / permit consume → 内存一次性 admission → `invoke_exact()`。prepared 对象未被 R1 consumer arm 时不能调用 provider；attempt 在 credential owner 中最多预留一次。官方 `adapter_factory(config)` 创建的默认 adapter 仍为 `transport=None`；仅受信 Host 管理面可在 bind 前调用 `install_trusted_provider_transport()`，且 transport 必须来自同一个 `PlatformConfig` 对象。`_AiohttpOneShotSession` 仅经显式生产 factory 创建，要求已审计 aiohttp `3.14.3`，使用一次 `post(..., allow_redirects=False)`，没有 SDK `HTTPClient`、redirect follow、retry middleware 或第二 POST。没有 Host binding、完整 inventory、受保护的本地 resolver、审计过的 session capability、REAL_CONTACT grant/permit 时，真实路径不可执行。

## 本地测试结果

`tests/test_hlv4_a2_r1_provider.py` 的 46 项专项测试已通过；覆盖同/跨 platform 与 profile 的 fake credential 冲突、官方 PlatformConfig.token factory、session 创建顺序、第二 REST owner、global/route 限流（含 429 作用域不明时保守阻塞整个 credential）、普通 text channel、固定 payload、真实 R1 Core permit 与 generic send fail-closed、429/500/502/504/524/reset/timeout/3xx 的单次分类、错误 channel/缺 message ID、直接 prepared 调用拒绝、mutable adapter reread 防护，以及受控 application transition 和同 event loop disconnect。相关 A1 lifecycle 六类 transition、A1 crash/recovery、R1/A3/HLV3/B1/World fence 回归纳入完整测试。

PR #46 Draft Review 的 F01–F03 修订继续保持上述合同。生产 `TrustedProviderTransportFactory.create()` 拒绝调用方提供的 `session_factory`，仅使用模块内 `AiohttpOneShotSessionFactory`；版本不是 `aiohttp 3.14.3` 即拒绝。`create_inert_test_only()` 只接受内置无网络 `InertTestProviderSession`，任意 retrying/third-party session 被拒绝。生产与测试 transport 均要求模块内不同的 seal；生产 transport 要求经过审计的 session seal。HTTP attempt counter 在该唯一已审计 capability 的不可逆调用前递增，不再把任意 duck-typed `post_once()` 的一次调用误当作一次 HTTP 尝试。

`ProtectedLocalTextChannelResolver` 是 frozen、本地只读的精确 projection；生产 factory 对其作 exact-type gate。它没有 credential、session、REST 或 rate-limit state；network-capable、credential-bearing、second-owner resolver 均在 session 创建和 permit consume 前拒绝。真实 projection 的来源、完整性和 channel/guild/application 身份仍留给 A2 retry，若必须新增第二 authenticated REST owner 则按 `HOST_CAPABILITY_INSUFFICIENT` 停止。provider 路径的 deterministic 三阶段矩阵覆盖 disconnect、credential/application rotation、adapter recreation 与 target transition；另测第二 credential owner claim，以及同 event loop 中 disconnect 等待、credential/application rotation 明确拒绝。外部 socket connect/create/sendto 陷阱在 provider 集成测试范围内启用；Windows asyncio 本地 loopback 控制管道不属于外部网络。

`aiohttp 3.14.3` 的已冻结源码审计中，`IDEMPOTENT_METHODS = GET / HEAD / OPTIONS / TRACE / PUT / DELETE`，不含 `POST`；因此持久连接自动重试不适用于本 `MESSAGE_CREATE`。生产 `ClientSession` 显式使用空 middleware、`trust_env=False`、`raise_for_status=False`，唯一 POST 设置 `allow_redirects=False`。结构测试用 fake aiohttp client 证明一次 `.post()`、无 redirect follow；未创建真实 session 或网络请求。响应读取、限流观察与结果解析中的异常均分类为 `UNKNOWN`，不重试、不补发。

完整测试与 exact Head CI 的数量、平台结论以本 Draft PR 最终运行记录为准；本报告不会把 fake success 写成 `DeliveryEvidence(SENT)`。`PROVIDER_CONFIRMED_SUCCESS` 在这里仅为 fake response 的结构性 SENT 候选，非真实 provider 事实；`UNKNOWN` 与 recovery 都不创建 permit 或 resend。

## 后续 Gate

A2 retry 未授权。真实隔离 Host 的 protected config inventory 完整性、plugin load/profile ownership、credential/application projection、target resolver 与真正 SDK/HTTP call-site 前 hard intercept 均须在未来任务中验证。本轮不取得 `REAL_HOST_DELIVERY_BOUNDARY_PASS`，更不取得 `REAL_HOST_SENT` 或 `ACKNOWLEDGED`。`DATA_SCHEMA = 8`、Schema Signature `SP-005A-living-runtime-v1`、Prompt Template `SP-004K-prompt-v1` 保持不变。
