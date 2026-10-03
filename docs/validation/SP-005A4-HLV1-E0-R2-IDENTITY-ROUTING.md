# SP-005A4-HLV1-E0-R2：Hermes 测试身份与显式路由证据

## Scope / Safety Declaration

Roadmap Stage：Real Host Integration → SP-005A4-HLV1 → Environment Gate Remediation → E0-R2 Identity / Routing Freeze。固定 Base：`f52042188fa960b0d66b99644334454d08995420`；沿用 `validation/sp-005a4-hlv1-e0-test-env` 和 Draft PR #37。本轮只固定 Dedicated Test Agent、Discord Bot/Server/Channel、Owner 与 Life Engine Test Home 的身份链。`TEST_GATEWAY_STARTED = NO`，`DEFAULT_GATEWAY_MUTATED = NO`，`REAL_SEND = NO`。

## R1 Preconditions / Test Home Identity

开始前复核 `origin/main` 与 PR #37 的已审核 Head；工作树 clean。Test Home 与 Default Home 的 realpath 不同，Hermes `install_id` 不同。Test `.env` 是 owner 正确的普通文件、非 symlink、mode `0600`；cron 文件集合仍为原始五文件，SQLite sidecar 为零。没有重新打开 `executions.db`。Test Gateway 经进程表核对未运行。Default Home 与 Default Gateway 均未修改。

当前 Test Home 对应独立 Hermes install ID；本地保留精确值，仓库不记录路径或 ID。Hermes 源码 `hermes_cli/install_identity.py` 将 `install_id` 定义为每个 install 持久且跨 profile 共享的身份；`hermes_constants.py` 与 `hermes_cli/profiles.py` 将 named profile 的合法 ID、目录及持久 identity marker 作为 Host-owned profile 身份来源。

## Test Agent Identity

静态检查确认 Test Home 原先没有 named profile。只在 Test Home 下新建 `life-engine-hlv-test`，使用 Hermes 合法 profile ID 与 `profile.yaml` 持久 marker；该 marker 仅写明 `TEST ONLY` 用途，不含人格、消息、Owner 或 credential。没有创建 alias、修改 Soul、初始化 Memory、复制 Bot token、配置 cron 或启动 Gateway。Test Home 的独立 install ID + named profile ID 构成可再次发现的 Test Agent 身份，区别于 Default Home 的 Agent。源码 `hermes_constants.py::named_profile_has_identity` 明确接受 `profile.yaml`；`hermes_cli.profiles::profile_exists` 与 `list_profile_names` 的静态核验均识别此 profile。实际 Gateway load 留待 E0-R3。

## Discord Credential / Bot / Server / Channel

Test `.env` 中已有 `DISCORD_BOT_TOKEN` 与单一 `DISCORD_ALLOWED_USERS`。仅在内存中读取 credential 并发出受控、认证的 Discord API v10 **GET**：`/users/@me`、`/channels/{channel_id}`、`/guilds/{guild_id}`。没有输出 token、Authorization header、响应正文、Bot/Server/Channel/Owner ID 或私人路径；没有执行 POST、PUT、PATCH、DELETE、Interaction、Webhook 或消息发送。

`GET /users/@me` 返回当前 authenticated bot identity，`bot=true` 且 ID 有效。Test Home 的 Host-owned `channel_directory.json` 中有一个明确的 Discord channel 候选；当前 `GET /channels/{id}` 返回相同 ID、文字 Channel 类型和所属 Server ID。使用同一 Bot credential 请求该 Server 返回成功且 Server ID 相符，证明 Bot 当前可访问该 Server。Server ID 与 Test Home 2026-09-30 本地历史探针的固定 ID 相同；目录中的 Server 名称亦与当前 API 元数据一致。名称仅作辅助对照，身份判定使用 ID。`SEND CAPABILITY = NOT_TESTED`，Bot 在线状态未测试。

Bot 的“测试专用”归属来自独立 Test Home 的既有 credential、当前认证 Bot identity、当前 Test Server membership 和本地历史 Server ID 对照；没有访问 Default Home credential，因此不声称完成生产 Bot 身份比对。历史材料未提供可独立对照的 Bot ID，故其历史同一性为 UNKNOWN；当前 credential 对应的 Bot 身份已在本地验证。为使后续可检测 credential / Bot identity 漂移，Test Home 内另存一份 mode `0600`、owner 为 Test 用户的本地 ID 对照记录，含 install/profile/Bot/Server/Channel ID 与查询来源，不含 token 或 Owner ID，不进入 Git。该记录仅是比较证据，`authority = false`；未来仍须重新取得当前 Host / Discord 证据。

## Explicit Target / Routing Chain

只在 Test Home `config.yaml` 增加最小 Hermes 配置：`gateway.multiplex_profiles = true`，一条 `gateway.profile_routes` 将 **Discord + 精确 Server ID + 精确 Channel ID** 指向 `life-engine-hlv-test`，并设置 `discord.allowed_channels` 为该单一 Channel ID、`discord.auto_thread = false`。没有通配目标、last route、最近会话推断或模型生成目标。ID 的来源是 Test Home Host-owned directory，经当前 Discord GET 重新验证后写入 Test Home 配置；仓库仅记录 `REDACTED_CHANNEL_ID` / `REDACTED_SERVER_ID`。

Hermes 源码 `gateway/config_loader.py::bridge_toplevel_keys` 会把该路由桥接到 Gateway 配置；`gateway/profile_routing.py::parse_profile_routes` 与 `match_profile_route` 静态核验：精确 Server + Channel 匹配，错误 Channel 不匹配；`plugins/platforms/discord/adapter.py::_get_allowed_channels` 使用允许列表。Gateway 实际装载和路由执行尚未验证，留给 E0-R3。这里的 profile route 是 Host inbound identity/routing fixture，**不是 Living execution permit，也不是外部发送授权**。

身份链：Life Engine canonical test registry → Dedicated Test Home / 独立 install ID → `life-engine-hlv-test` → Test Home 的认证 Discord Bot → 经当前 API 确认的 Test Server → 精确文字 Channel。Owner 由 Hermes Test `.env` 的 `DISCORD_ALLOWED_USERS` 与 Life Engine canonical protected registry 的 `owner_sender_id` 在本地逐值比对，一人且相等；registry 的 `host_home` 精确指向 Test Home，`owner_channel = discord`。未更改 Life Engine registry：当前 Hermes adapter 的 `host_agent_id` 为空（该字段在部署代码中用于 OpenClaw），Test Agent 关联作为本轮发现的环境 metadata 保留在 Test Home，不扩展 Core Schema。

| Identity | Current Evidence / Trust Source | Status |
| --- | --- | --- |
| Test Home | realpath 与 Default Home 分离；Test 配置与受保护 registry 指向一致 | VERIFIED |
| Test Install | Test / Default `install_id` 本地逐值比较不同 | VERIFIED |
| Test Agent | Test Home 下持久 Hermes named profile；Host profile API 静态识别 | VERIFIED |
| Owner | Test Home allowlist 与 Life Engine protected registry Owner 精确一致；`REDACTED_OWNER_ID` | VERIFIED |
| Discord Bot | Test Home credential → 当前认证 Bot ID；可访问历史 Test Server；ID 本地保留 | VERIFIED |
| Discord Server | 当前 Bot-authenticated GET、Channel 的 `guild_id` 与本地历史 Server ID 对照 | VERIFIED |
| Discord Channel | 当前 Bot-authenticated GET 返回文字 Channel；与 Host-owned directory ID 相同 | VERIFIED |
| Explicit Target | Test Home 配置的精确 Server + Channel route / 单一 allowed channel | VERIFIED |

## Historical vs Current Evidence

| 项目 | 2026-09-30 与当前关系 | 限制 |
| --- | --- | --- |
| Test Bot | UNKNOWN | 历史材料未提供可独立对照的 Bot ID；当前 Bot ID 已认证并本地留存 |
| Test Server | UNCHANGED | 本地历史探针的 Server ID 与当前 API ID 相同；不公开精确值 |
| Test Channel | UNCHANGED（相对 Test Home 历史 directory） | 目录记录的 Channel ID 经当前 API 重新确认；不把目录时间戳当当前证据 |
| Telegram Guidance | HISTORICAL_ONLY | 本轮不要求、不访问 Telegram |

## Unresolved Gaps / Final Result

`SP-005A4-HLV1-E0-R2 = PASS`：Test Home、install、Test Agent、Bot、Server、Channel、显式 Target、Owner Binding 和 Life Engine registry binding 均有当前证据。`ARCHITECTURE_CHANGE_REQUIRED = NO`。仍未验证 Test Gateway 首次启动、profile load、Discord adapter load、Bot 在线、实际 routing、send capability 或任何 Living operation；这些不因 R2 PASS 而升级。`SP-005A4-HLV1-E0 = BLOCKED / IN_PROGRESS`，`SP-005A4-HLV1 = BLOCKED`。E0-R3 首次受控启动须单独授权。

执行操作：Test Home / registry / Hermes 源码与配置的只读检查；上述三个 Discord 身份 GET；Test Home 下创建一个持久 Test profile marker 和一份受保护的本地比较记录；只修改 Test Home `config.yaml` 的显式路由和单 Channel gate；用 Hermes profile / route parser 静态复核。没有 Gateway start/stop/restart，没有 Default Home 或 Gateway mutation，没有 Discord/Telegram/微信发送，没有 Runtime、Schema、Prompt 变更，也没有开始 HLV1 retry 或 H-LV2/H-LV3/H-LV4。
