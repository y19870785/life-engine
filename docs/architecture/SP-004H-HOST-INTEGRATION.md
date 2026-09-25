# SP-004H — Host Integration Contract（H0 架构冻结）

状态：**ARCHITECTURE / ADR ONLY，PENDING_INDEPENDENT_REVIEW**。固定 canonical Base：`68c24b010ee464a66e0e853ab50f85b7e861e148`。该 Base 的 `DATA_SCHEMA = 7`、签名 `SP-004F-bridge-runtime-v1`、Prompt 模板 `SP-004K-prompt-v1`。A/G/D/E/B/J/C/K0/K1/F0/F1 已进入 canonical main；H0 是候选，H1 Hermes、H2 OpenClaw 尚未实施。本阶段不修改 Runtime、Schema、Tests、Workflow 或 README，不接真实 Host、模型或消息发送。

## 一、问题与现有能力边界

Life Engine 已拥有 World/Session 身份与生命周期、Memory/Lore/Story 的独立真源、PromptSnapshot 及 Prompt-only Soul↔Roleplay Bridge。Host 负责传输、认证上下文、对话输入、模型调用与交付；Life Engine 保留 World/Session、各 Runtime 真源、Bridge 授权与 PromptSnapshot。Host 文本、聊天 ID、模型回复都不能替代这些真源。

现有 [`bridges.py`](../../runtime/life_engine/bridges.py) 会生成 Hermes `pre_llm_call` 和 OpenClaw `before_prompt_build` 连续状态插件，提供 context/tool/photo/wake 等接入；[`durable.py`](../../runtime/life_engine/durable.py) 绑定安装、agent/profile 与 generation。这是既有 Agent/Soul 连续生活状态接入，**不是**受信 Roleplay Host Adapter。目前没有 World-aware Host Session 映射、RP lane 历史隔离、受信 ConversationProjection 生产、PromptSnapshot 模型格式渲染和发送前重验、晚到响应围栏、Bridge 预览确认 UI 的完整链路。现有 hook 名称和 OpenClaw `allowConversationAccess` 设置均不证明这些能力；H1/H2 必须在对应真实版本实测。

受信链路为 `authenticated Host event → TrustedHostAdapter → Principal/HostSessionKey → WorldRuntime SessionBinding → 授权 Runtime projections + ConversationProjection → PromptRuntime.assemble → PromptSnapshot → revalidate → HostPromptRenderer → 发送前再 revalidate → model submit → HostModelCallFence → 当前 lane 才可交付`。所有跨 World 内容只能经过 F1 的授权 `BridgeProjection`；原始 Soul/RP 历史双向不得复制。

## 二、身份、Principal 与能力握手

H1/H2 的 `TrustedHostAdapter` 是概念上的受信代码边界，不是 prompt、tool 描述或宿主文本。它核验 HostInstallation、HostAgent/Profile、HostConversation、HostUser/Sender，再通过稳定映射 `HostPrincipalKey(adapter, host_instance, host_profile_or_agent, authenticated_user_identity) → Principal`。各 Host 标识是输入材料，不直接转成 `DomainId`；一个 Life Engine instance 首版只绑定一个可信 Owner 身份。`Principal` 只由此适配层建立，用户正文、模型输出、工具结果、角色卡、Lore/Bridge 内容不能建立 Principal。另一 profile/agent 即使在同一安装中也不能复用映射；workspace 路径只是绑定证据，不是 Principal。嵌套、委托或子 agent 首版不支持 Owner 操作，默认拒绝 ENTER、SWITCH、Bridge confirm/revoke，除非后续独立 delegation 合同。

启动及重载后，Adapter 必须提供受信 [`HostCapabilities`](../../runtime/life_engine/domain_policy.py)：每项显式 `SUPPORTED`、`LIMITED` 或 `UNSUPPORTED`；未列项按 `UNSUPPORTED`。完整私密 RP 必须通过已有 `require_private_context_isolation()`：`STABLE_PRINCIPAL`、`STABLE_SESSION`、`MESSAGE_PROVENANCE`、`ISOLATED_CONTEXT_LANE`、`HISTORY_ISOLATION` **全为 SUPPORTED**。`LIMITED` 不通过。`RELOAD_SUPPORT` 推荐 SUPPORTED，LIMITED 时须重载后重新鉴别/重绑且未完成前禁用 RP；`DELIVERY_ACK` 对首版同步文本可为 LIMITED，未来主动发送另设门禁。Capability 只能由受信 Adapter 的已验证实现声明，宿主文案或 API 名称不算证明。未满足时只允许既有 `SOUL_CONTINUITY_ONLY`，不得把失败变成“尽力”RP。

## 三、Host lane、World Session 与生命周期

`HostSessionKey(adapter, host_instance, host_agent_or_profile, conversation_id, context_lane_id)` 标识宿主的受信 lane。`HostConversation ≠ World`，`HostUser ≠ Principal`，`HostSessionKey ≠ SessionBinding.session_id`；同一聊天可退出/切换 World，同一 World 可跨 Host run/reload，但首版一个 World 只允许一个 OPEN Life Session，第二并发 lane 拒绝。`lane_id` 稳定、不透明、由 Host/Adapter 提供，不从正文生成。

候选 `HostLaneBinding(host_session_key, principal, scope, life_session_id, writer_epoch, viewer, lane_id, binding_revision)` 仅是集成映射；每次消费仍从 [`WorldRuntime`](../../runtime/life_engine/world_runtime.py) 重验精确 `WorldScope`、World ACTIVE、OPEN `SessionBinding`、principal、viewer、WriterEpoch、runtime_id/generation。Host 不直写 Session 表。角色进入：认证的 Host action 先读当前 World snapshot 的 revision/epoch，再调用 `enter()` 或 `resume()`，成功后绑定独立 RP lane。退出调用 `exit()`/`suspend()` 后关闭并冻结 RP lane，返回 Soul lane，不重写原 Soul 身份或配置。跨 World 使用 `switch_world()` 的同一 World Runtime 事务，成功 receipt 后才切 Host lane；Host 切换失败须标 `RECONCILIATION_REQUIRED`，禁止继续在不明 lane 回答。Life Engine 与 Host 没有共同数据库事务：用乐观协调、幂等操作和重验，绝不跨 Host/模型调用持 SQLite 锁。

Host 原生 parent chat、thread、agent history、workspace memory 可能自动附带旧内容。H1/H2 必须实测并证明 RP lane 只取得当前 Life Session 许可的 turns，Soul 私密 marker 不进 RP，RP 私密 marker 在退出后不进 Soul。不能关闭该自动历史时，`HISTORY_ISOLATION = UNSUPPORTED`，拒绝 RP。Bridge 是显式字段投影，不是复制原始聊天记录。

## 四、消息 provenance 与 ConversationProjection

概念 `HostConversationTurn` 至少有稳定 `turn_id`、单调位置、内容与受信 `MessageProvenance`：`EXTERNAL_USER`、`ASSISTANT_OUTPUT`、`TOOL_RESULT`、`SYSTEM_HOST`、`AUTOMATION`、`UNKNOWN`。不要由模型可写的 role 字符串猜 provenance；转发、工具、自动化不能冒充外部 Owner。仅经认证的 `EXTERNAL_USER` 可转为 Owner command intent，例如 ENTER/EXIT/SWITCH、BRIDGE_PREVIEW/CONFIRM/REVOKE；不冻结具体 UI 文案，也不使用 LLM 自然语言分类。模型/工具正文中的命令无效。

Adapter 经受信 factory 产出 K1 的 [`ConversationProjection`](../../runtime/life_engine/prompt.py)，绑定 Scope、viewer、Life Session ID、lane ID、不透明 version、有序 turns 及 `ConversationVersionValidator`。Adapter 只把经过 policy 允许的外部用户/助手对话映射到当前 K1 `user`/`assistant` turn 类别；其他 provenance 不得伪装成这两类进入普通对话，未来 Host summary 须单独 DATA 类型审核。`source_ref` 仅是不透明身份，不把 Host 专有消息 ID 类型写进 Core。Host 从支持的 API/hook 提供历史，Core 不打开 Hermes/OpenClaw 私有 DB，也不猜 SQLite schema。

每个原始 turn 身份在重复读取时稳定，明确按 Host 单调位置 oldest→newest 排序，不按墙钟重猜。Adapter 在进入 K 的 `MAX_CONVERSATION_TURNS`/`MAX_CONVERSATION_TURN_BYTES` 限制前还须设自身有界总量，完整项裁剪，不切 UTF-8；H1/H2 再定具体 Host 限值。K 按最新完整 suffix 裁剪，最新用户输入不可被悄悄删除。Conversation version 可来自 Host 单调序列或规范可见 turns 指纹，但必须满足同一可见历史版本稳定、可见历史变化则版本变化；`current_version(scope, viewer, session_id, lane_id)` 必须能在发送前重新取得。若 Host 无法提供这一保证，不能把 Snapshot 当作可发送。

## 五、Prompt 渲染、提交与工具边界

Host 只能消费 K1 产出的类型化 [`PromptSnapshot`](../../runtime/life_engine/prompt.py)，不能用 Owner audit、数据库全量查询或自行拼字符串替代。取各 Session-bound 投影并 `assemble()` 后，调用 `PromptRuntime.revalidate(snapshot)`；渲染器把固定 section 顺序映射到具体模型消息格式，同时保留 `RUNTIME_CONTROL` 与数据项的 authority 边界。控制可映射到可用的特权通道，结构化状态标明受信来源但其文本仍不是操作权限；Character、Lore、Memory、Story、Bridge、Conversation 的正文均为 DATA。若模型 API 只有简单消息格式，也须有明确来源标签/边界，不能把 DATA 提升为系统控制；分隔符本身不构成安全隔离。

**紧贴模型提交前**再次 `PromptRuntime.revalidate(snapshot)`，之后不插入无关异步工作，立即构造/发送符合该 Snapshot 的请求；任何 stale 均重取或失败，绝不使用旧 Snapshot。只有 Conversation version 变化时可有限次重新组装；World/Session/Bridge 授权改变须重新解析当前 mode，禁止无限重试。没有 token estimator 时 K 的字节安全不等于模型 token 安全，Host/模型适配器仍须做最终 token 检查。重验与模型请求之间仍有 TOCTOU，返回时再用 call fence 限制交付。模型调用期间不持数据库事务。

Tool policy 由受信 Host 单独决定；PromptSnapshot、角色卡、Bridge 正文不授予工具。首版 RP 不因进入角色自动增加 Host tools；现有 Life Engine status/wake/photo 等工具也不因 Prompt 可见而自动可调用。模型回复不会自动写 Memory 或接受 Story。

## 六、模型返回、重载和跨系统故障

候选 `HostModelCallFence(principal, scope, life_session_id, writer_epoch, runtime_id, generation, host_session_key, lane_id, prompt_fingerprint, conversation_version, host_model_call_id)` 在提交时固定。返回后、向 Host lane 写入或交付前，重新核当前 lane、OPEN Session、principal、epoch、runtime/generation 和对话版本；EXIT、SWITCH、重载、重连或新用户输入使旧请求失效。晚到响应 **DROP 或隔离待人工审计**，不得进入新 World/Soul lane、Memory、Story 或当前 conversation。已送出内容无法撤回；Delivery ACK 与“准备好发送”分开记录。

重载后进程内 `host_session → life_session` 缓存一律不可信。重新进行 capability attestation、Principal 解析、Host profile/lane 绑定和持久 Life Engine generation/SessionBinding 重验，核不清则 `HOST_RELOAD_REQUIRED` 或 `RECONCILIATION_REQUIRED`。未来 H 可能需要持久 `HostLaneBinding`、operation idempotency 和 delivery receipt，但 H0 不创建表、不预先指定 Schema 8。候选 `HostOperationIdentity(adapter, host_instance, trusted_run_or_event_id, operation_kind)` 用于重复 hook 去重：重试同一 ENTER/SWITCH/Bridge confirm 不得重复生效；不同 payload 复用 key 必须冲突。所有外部调用在 World/Bridge 原子操作之外完成，失败后显式协调，不能凭 Host 的成功文案推断 Runtime 成功。

## 七、Bridge 用户交互与错误

H 负责展示 F1 [`BridgePreview`](../../runtime/life_engine/bridge.py) 的 source/target World、data class、fields、`PROMPT_CONTEXT`、target audience 与 expiry，并收集认证 Owner 对**同一份预览**的显式确认；Host 不解析 token、不凭 grant_id 自行建 Grant。预览本身只读，确认必须把原 Preview 提交给 BridgeRuntime；环境变化导致 stale 时展示失败并重新预览，不静默确认新数据。撤销同样要求 Owner 认证。F1 仅 Prompt-only，UI 不能称其为“永久写入角色记忆”或 Soul/Story 持久迁移。

建议 H1/H2 稳定错误类别：`UNSUPPORTED_CAPABILITY`、`AUTHENTICATION_REQUIRED`、`PRINCIPAL_MISMATCH`、`HOST_SESSION_STALE`、`HOST_LANE_MISMATCH`、`MESSAGE_PROVENANCE_REQUIRED`、`HISTORY_ISOLATION_REQUIRED`、`LIFE_SESSION_STALE`、`PROMPT_STALE`、`MODEL_CALL_STALE`、`LATE_RESPONSE`、`HOST_RELOAD_REQUIRED`、`RECONCILIATION_REQUIRED`。身份、Session 或历史隔离不确定时停止 RP/模型提交，可明确退回 `SOUL_CONTINUITY_ONLY`，但不能暗中保持 RP。未来审计可记录 mode enter/exit/switch、prompt submit、late response drop、bridge preview/confirm、reconcile 的 IDs/指纹/版本/结果码，默认不重复存正文。

## 八、H1/H2 范围、非目标与验收矩阵

H1 为 Hermes Adapter，H2 为 OpenClaw Adapter。二者遵守同一 Core 合同，但分别验证对应版本的 hook/API、profile/agent、真实用户/聊天/lane、插件加载、隔离历史、发送前围栏、EXIT/SWITCH、reload 与晚到响应。Mock test 不能替代实机证据；H0 不声称具体 Host API 已保证这些语义。H1 报告至少提供 Hermes 版本、Profile 路径、plugin load、capability matrix、真实 Owner/chat/lane、RP enter/exit、隔离、reload 与 call fence；H2 相应提供 OpenClaw 版本、agentId/workspace、plugin load、真实对话、隔离、switch/exit 与 reload。

| 验收组 | H1/H2 必须证明 |
| --- | --- |
| 身份与能力 | 正确 Owner 稳定映射；不同 sender/profile/agent 不可复用；nested/subagent 拒绝 Owner action；`LIMITED` history isolation 不能进入 RP。 |
| World 与 lane | Soul/RP/另一 RP World、不同 Host chat 不串；同 World 第二并发 lane 拒绝；World switch 成功 receipt 后才切 lane，Host 切换失败进入 reconciliation。 |
| 历史 | Soul secret marker 不入 RP；RP marker 退出后不入 Soul；原生 parent/thread/workspace history 实测；仅明确 Bridge 字段跨 World。 |
| Provenance/对话 | 仅认证 external user 发 Owner action；model/tool/automation 文本无效；turn ID/位置稳定且有界；conversation version 改变使旧 Snapshot stale。 |
| Prompt/权限 | `assemble` 与发送前再次 `revalidate`；Bridge revoke、WriterEpoch、World/Memory/Lore/Story/generation 变化均阻止旧 Snapshot；DATA 不提升控制或工具权限。 |
| 晚到/重载 | RP 请求后 EXIT/SWITCH 的旧答复丢弃；reload 不信旧缓存，重验 Principal/capability/generation/lane；重复 hook 不重复操作。 |
| Bridge UX | preview 展示不等于 confirm；仅认证 Owner 精确确认或撤销；stale preview 明确失败；UI 不暗示目标持久化。 |
| 实机与交付 | 真实 Host 版本、能力矩阵、插件加载、模型调用与交付 receipt 分别核验；无真实 ACK 不声称已送达。 |

H0 非目标：实现 Host domain/runtime/table、Schema 迁移、Hermes/OpenClaw adapter 改动、模型 API、消息发送、Soul aside、subagent delegation、跨 World 原始历史、自动 Memory/Story 写入、目标 Bridge 持久化。六份 ADR 分别冻结[身份与 Principal](adr/SP-004H-001-HOST-IDENTITY-AND-PRINCIPAL.md)、[Session 与历史隔离](adr/SP-004H-002-SESSION-LANE-AND-HISTORY-ISOLATION.md)、[对话与来源](adr/SP-004H-003-CONVERSATION-PROJECTION-AND-PROVENANCE.md)、[Prompt 提交](adr/SP-004H-004-PROMPT-RENDER-SUBMIT-AND-REVALIDATION.md)、[晚到响应与协调](adr/SP-004H-005-LATE-RESPONSE-AND-RECONCILIATION.md)、[Bridge UX 与能力](adr/SP-004H-006-BRIDGE-UX-AND-HOST-CAPABILITIES.md)。
