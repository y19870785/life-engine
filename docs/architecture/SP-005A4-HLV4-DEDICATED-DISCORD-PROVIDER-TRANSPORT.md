# SP-005A4-HLV4-A2-R0 — Dedicated Discord Provider Transport 架构候选

## 当前裁决与边界

本合同以 canonical main `d490c729960b119334cadefc023dfc1dd67f6137`、Hermes 0.21.3 源码 `01382698fc32ec7740b6a204d9b7a6abeac74d33`、该 checkout 中的 discord.py 2.7.1 与 aiohttp 3.14.3 为审计对象。A1 = DONE；A1 的 `LifeEngineDiscordAdapter(..., transport=None)` 是有意的默认拒绝，不是缺陷。A2 因 `REAL_TRANSPORT_IMPLEMENTATION_REQUIRED` 停止。本文只冻结 **待独立审查的架构候选**，不安装插件、不创建 client、不实现 transport、不访问 Host credential、不运行 Gateway 或网络请求。

`SELECTED_PROVIDER_BOUNDARY = PLUGIN_OWNED_ONE_SHOT_HTTP_MESSAGE_CREATE`；`SELECTED_PROVIDER_CLIENT_OWNER = isolated life_engine_discord plugin`；`PRIVATE_API_DEPENDENCY = NO`。这只是后续 A2-R1 的实施方向，不是可发送能力。A2-R1、A2 retry、HLV4-B 均未授权；`REAL_SEND = NO`，`REAL_HOST_SENT / ACKNOWLEDGED = NOT_ACQUIRED`，`ACK_VALIDATOR = HOST_GAP`。若 A2-R1 不能机械证明本合同，按下文 STOP，不改写一次性 Attempt 或 authority 语义。

## 固定源码证据与调用链

只读核对了安装于上述 Hermes checkout 的 `venv/lib/python3.11/site-packages/discord/abc.py`、`discord/http.py` 和 `aiohttp/client.py`，并对照 [discord.py v2.7.1 `abc.py`](https://github.com/Rapptz/discord.py/blob/v2.7.1/discord/abc.py)、[`http.py`](https://github.com/Rapptz/discord.py/blob/v2.7.1/discord/http.py)、[aiohttp v3.14.3 `client.py`](https://github.com/aio-libs/aiohttp/blob/v3.14.3/aiohttp/client.py)。[Discord Create Message](https://github.com/discord/discord-api-docs/blob/main/developers/resources/message.mdx#create-message) 与 [Rate Limits](https://github.com/discord/discord-api-docs/blob/main/developers/topics/rate-limits.mdx) 用于核对 provider 约定。SDK/package 版本、source digest 或相关行为改变时，默认拒绝 REAL_CONTACT，重新审计后才能放行。

| 层与源码位置 | 输入、目标、payload、await 与输出 | 重试、变更和风险 |
| --- | --- | --- |
| Hermes `plugins/platforms/discord/adapter.py:2901-2987`，built-in `DiscordAdapter.send()` | `chat_id`、content、reply/metadata；`_resolve_channel()` 后可能触达 `channel.send()`；返回 `SendResult` | `metadata.thread_id` 覆盖目标、forum create、format/truncate/split、reply fallback、多次 send、generic ledger/retryable 结果。`BUILTIN_DISCORD_SEND_REUSE = FORBIDDEN`，本合同不修改此路径。 |
| `discord/abc.py:1656-1717`，`Messageable.send()` | `await self._get_channel()`；`str(content)`；默认随机 nonce；`handle_message_parameters()` 组装 body；`await state.http.send_message(channel.id, params)`；成功后建 `Message`，可选 `delete_after` 另有 await | 目标获取和 payload 构造发生在方法内部；`allowed_mentions` 可与 client 默认值合并；不能保证 consume 后只余一次 HTTP 尝试。 |
| `discord/http.py:877-887`，`HTTPClient.send_message()` | 从 channel ID 生成 `POST /channels/{channel_id}/messages` Route；text-only JSON 传入 `request()`；返回 message JSON | 自身不提供 per-call retry-off；下层 `request()` 可能进行多个 POST。 |
| `discord/http.py:589-795`，`HTTPClient.request()` | 创建 Bot Authorization header、序列化 JSON；`await` global gate 和 `async with ratelimit`；循环中 `async with self.__session.request(...)`、读取响应；2xx 返回 JSON，4xx/5xx 可抛异常 | `for tries in range(5)`：429 按 `retry_after` sleep/continue；500/502/504/524 无条件 sleep/continue；指定连接重置 `OSError` sleep/continue。限流等待也位于 SDK 调用内部。一个 SDK call **不等于** 一个 HTTP POST attempt。 |
| `aiohttp/client.py:703-705, 858-895`，`ClientSession._request()` | 形成并 await 底层 request handler；默认可跟随 redirect；返回 HTTP response/抛连接异常 | 此版本内建的持久连接重试只针对 `IDEMPOTENT_METHODS`，不包括 POST；但默认 redirect 可重发请求。未来专用 POST 必须 `allow_redirects=False`、无 retry middleware，并锁定版本/行为。 |
| Discord REST | 第一次可能使 provider 创建消息的 `POST /channels/{channel_id}/messages` 网络动作；成功返回 message object | **真正不可逆边界**；Python 方法入口、coroutine、permit consume、SDK wrapper 入口都不是该边界。请求可能已到达而响应丢失，须 `UNKNOWN / NO RESEND`。 |

discord.py 2.7.1 的 `Ratelimit.acquire()` 在 `discord/http.py:456-487` 可 await bucket 恢复。故即使绕开其 retry loop，若直接在 consume 后调用 SDK HTTP 路径，仍会在不可逆动作前等待；不能把这种等待藏进“唯一 provider await”。

## 四候选比较与选择

| 候选 | retry / rate limit | credential、session、lifecycle 与目标 | 结论 |
| --- | --- | --- | --- |
| A `Messageable.send()` | 进入可重试的 `HTTPClient.request()`；内部 `_get_channel()`、body/mentions/nonce 构造；限流等待在调用内 | SDK client 持有 credential/session，易于 Host 归属，但 consume 后无法保证目标/payload 冻结，也无法界定一次 POST；Hermes built-in 调用还有额外 fallback | **REJECT**。公开 API 不能满足 A0 的 one permit → at most one irreversible attempt。 |
| B `HTTPClient.send_message()` | 仍进入同一 5 次循环；无 per-call retry-off；global/bucket await 在 consume 后 | 可传冻结 channel ID/body，保留 SDK auth/session/rate limit，但必须依赖私有 `HTTPClient`，且核心重试不消失 | **REJECT**。只消除 `Messageable` 层不能消除 HTTP 自动重试。 |
| C SDK one-shot internal wrapper | 要读取/替换 `HTTPClient.__session`、复制或绕过 `request()` 的锁、限流与认证逻辑；内部路径无稳定 one-shot 开关 | 私有属性、版本签名和 bucket 状态脆弱；不能 patch installed SDK、monkeypatch 或劫持 built-in | **REJECT**。将 SDK 内部复制到 wrapper 后实质上已是独立 HTTP 客户端，且维护风险更高。 |
| D 专用 plugin-owned one-shot HTTP capability | 独立 admission 在 consume 前；消费后只调用一次无重定向、无自动重试的 POST；429/5xx/reset 一律不重试 | 由 **同一个 isolated plugin owner** 管理 credential、session、限流、lifecycle；不进入 Core。必须独立解决与同 credential 的其它 REST client 的协调，A2-R1 证明无 duplicate owner、无 middleware/redirect/retry | **ACCEPT AS ARCHITECTURE CANDIDATE**。不是“裸 aiohttp + token”捷径；若 ownership、限流或一次 POST 证明失败，则 STOP。 |

本选择不 patch Hermes Core、built-in adapter 或 discord.py。未来 A2-R1 只可在专用 plugin 的受保护 Host scope 内构建 provider capability；不得把 raw Bot token 复制给 Core、grant、permit、receipt、journal、模型或证据。若同一 credential 被其它 adapter/client 独立持有且无法隔离或协调，`HOST_CAPABILITY_INSUFFICIENT`；不得以双客户端各自猜测限流继续。

## Provider capability、target 与 payload

专用 plugin 拥有一份受保护的 provider client/session 与 credential identity projection；它的 lifecycle 与 Gateway process、plugin epoch、adapter instance epoch、credential identity、application identity、exact target 和 Core generation 绑定。client recreation、disconnect 开始、credential/application/target 变更立即关闭新 admission 并撤销旧 capability/grant/permit；已进入受生命周期 lease 保护的单次 invocation 等待完成或归类 UNKNOWN，**不能撤回网络事务**。锁顺序沿用 A1：adapter lifecycle → BindingAuthority → Core management；不得持反向锁等待网络。

`SELECTED_TARGET_REPRESENTATION = FrozenTextChannelCapability`：Host 保护配置先验证 platform=`life_engine_discord`、provider=`discord`、bot/application、guild、channel、owner、profile、Agent 和 binding；只接受普通 guild text channel。先做 cache/GET/权限及 guild/channel 类型核验，冻结已解析 provider handle、channel ID、client/session identity 与 target digest；缺失或歧义即拒绝。thread、forum、DM、group DM、voice、stage 均拒绝；**consume 后无 lookup/fetch/DM create/thread resolution**。冻结 handle 不能在调用时重读 mutable adapter target。

`SELECTED_PAYLOAD_REPRESENTATION = FrozenUtf8TextJson`：在 consume 前完成固定 text 的 canonical UTF-8 编码、摘要、确切 JSON **bytes** 与 Content-Length；最大 2000 个 Unicode 字符且服从更小的已冻结安全上限，超限拒绝，不截断/分段。V1 只允许一条 text；`allowed_mentions={"parse":[]}`，禁用 user/role/everyone/here 全部 mention；无 reference、reply、file、attachment、embed、component、sticker、poll、thread、forum 或动态格式化。只含固定允许字段的 immutable body bytes 与 URL、Content-Type 在 guard 前冻结；consume 后不拼接、更换、重新序列化或扩展 payload。Discord 文档说明普通消息若省略 `allowed_mentions` 默认允许多类 mention，故必须显式禁用。

nonce 是可选关联线索，**不是授权或 exactly-once 依据**。discord.py 可自动生成 nonce 并写 `enforce_nonce=true`；Discord API 仅承诺对同作者近几分钟内的 nonce 检查，不能跨长期 recovery 提供去重保障。A2-R1 即使使用 nonce，也不得以它允许第二 POST、refund grant 或恢复 permit。

## 限流与唯一不可逆尝试

`RATE_LIMIT_ADMISSION_POSITION = PRE_CONSUME`：专用 plugin 在 final guard 前完成本地 route/global 限流 admission、必要等待、连接/session 健康及 target/body 准备。限流值来自 provider response headers，不能硬编码为长期额度；单一 credential owner 串行化相同 route 的 admission。该准备只能降低 429 风险，**不能保证 provider 不再返回 429**；动态限流的剩余风险由一次 POST + 不重试处理。若发现真正的限流等待只能在 consume 后插入且无法消除，`PROVIDER_BOUNDARY_INCOMPATIBLE`。

最终顺序：pre-consume target/client/payload/rate-limit freeze → final lifecycle 与 authority guard → atomic `consume_once()` → **唯一** `await one_shot_message_create(frozen_capability, frozen_body)`。该 await 包含发起一个 POST、读一次响应；不得再有 queue、arbitrary await、目标解析、payload mutation、SDK `HTTPClient.request()`、重定向、retry middleware、generic ledger、fallback、fan-out 或第二个 provider call。aiohttp 3.14.3 的源码显示 POST 不属于持久连接自动重试方法；未来实现仍必须显式禁重定向和中间件重试，并以 socket/HTTP trap 证明 **最多一次** MESSAGE_CREATE request。若实际依赖变更，默认拒绝，重新审计。

计数不可合并：`TRANSPORT_INVOCATION_COUNT` 计固定 port 进入；`SDK_SEND_INVOCATION_COUNT` 计 `Messageable.send()`/`HTTPClient.send_message()`（选 D 时必须为 0）；`HTTP_MESSAGE_CREATE_ATTEMPT_COUNT` 在请求首次可能上网前递增且每 permit 上限 1；`PROVIDER_ACCEPTED_COUNT` 只在受信响应核对通过后递增。HTTP attempt 并非 provider accepted；2xx 也并非 ACK。`HTTP_MESSAGE_CREATE_ATTEMPT_COUNT > 1` 是 `SAFETY_VIOLATION`。底层 TCP 重传不等于应用重新发起一个 HTTP request，但不能当作 provider exactly-once 证明。

## 结果、SENT 与恢复

| 结果类 | 规则 |
| --- | --- |
| `PRE_SEND_DENY` | consume 前 guard、target、payload、限流 admission 或 lifecycle 拒绝；无 HTTP attempt。不得由 caller 自行换 target 重试。 |
| `PROVIDER_CONFIRMED_SUCCESS` | 单次 POST 得到可信成功响应；仅形成 `SENT` **候选**，尚须独立 validator。 |
| `PROVIDER_CONFIRMED_REJECTION` | 仅当可信响应可明确证明没有创建消息时使用，例如明确的静态请求拒绝；仍不 refund、不重发。无法证明时降为 UNKNOWN。 |
| `RATE_LIMITED_NO_RETRY` | 唯一 attempt 返回 429；保存响应分类/限流窗口，业务上 `NOT_SENT_PROVEN`，禁止同 Attempt 自动 retry；若消息创建事实仍不确定，按 UNKNOWN reconciliation。 |
| `UNKNOWN` | 5xx、请求开始后的 reset/timeout、response lost、进程崩溃、不可验证响应或结果歧义；不标 FAILED_SAFE_TO_RETRY、SENT 或 ACK。 |

即使能证明 pre-wire failure，也不能由 transport 擅自发第二次 Attempt。`recover_operation` 只恢复 Core durable knowledge，绝不恢复 grant/permit/transport authority 或自动 resend。permit consumed 后 crash，无论本地是否看到 POST/响应，都默认 UNKNOWN + reconciliation；已 CLAIMED 的历史不授予新的执行资格。

未来 `DeliveryEvidence(SENT)` validator 至少核对 provider message ID、channel ID、受信 bot/application identity、唯一 request/Attempt/invocation 的本地关联及冻结 payload digest；provider response 本身不会天然携带 Life Engine Attempt/invocation，不能由 caller 自报填补。provider accepted 与可信 SENT 仍需分层；message ID、API success、CLI rc、模型声明均不是 `ACKNOWLEDGED`。本任务不实现 validator，`ACK_VALIDATOR = HOST_GAP`。

## A2 retry 的 hard intercept 与实施门槛

A2-R1 只可用 fake/inert provider boundary、源码 fence、单次请求 trap 测试；真实 Discord REST 禁止。后续 **另行授权** 的 A2 retry 必须在真实隔离 Gateway 中完成所有 target/client/payload/rate-limit 准备及 final guard，consume permit 后，在即将执行唯一 `one_shot_message_create` 的调用点放置不可切换、不可 fall-through 的 `HARD_PRE_SEND_INTERCEPT`。intercept 前不能宣称到达 last reversible point；intercept 必须证明 provider invocation、MESSAGE_CREATE HTTP attempt、network send 全为 0。A2 retry 也不能产生 SENT。

A2-R1 必须以测试证明：同 credential 单 owner、精确普通 text channel、fixed JSON、无 middleware/redirect/自动重试、限流等待仅在 consume 前、POST 上限 1、所有异常/429/5xx/reset 不重发、生命周期与 invocation 线性化、credential 不离开 Host/plugin。若必须 patch Hermes/discord.py，报告 `HOST_PATCH_REQUIRED`；若 one-shot retry 隔离失败，报告 `PROVIDER_RETRY_INCOMPATIBLE`；若 target、payload、限流或 client 必须在 consume 后重新解析/等待，报告 `PROVIDER_BOUNDARY_INCOMPATIBLE`；若 R0/R1/A0 的 authority/Attempt/permit/recovery/evidence 真源必须改变，报告 `ARCHITECTURE_CHANGE_REQUIRED`。本候选不要求 Schema 或 Prompt 变化：`DATA_SCHEMA = 8`、Schema Signature `SP-005A-living-runtime-v1`、Prompt Template `SP-004K-prompt-v1`。
