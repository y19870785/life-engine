# SP-004F0 — Controlled World Bridge 架构冻结

状态：**架构候选 / 待独立审核**。固定 canonical Base：`b1bb2fd07eae0699a108ad535ba6152c9a8de2f6`。本阶段只定义合同：`DATA_SCHEMA = 6`、签名 `SP-004C-story-runtime-v1`、Prompt 模板 `SP-004K-prompt-v1` 均不变。F1 Bridge Runtime、持久化、Prompt 接线与 Host UI 尚未实现。

本合同由五份 ADR 细化：[授权对象](adr/SP-004F-001-BRIDGE-GRANT-AUTHORITY.md)、[预览与确认](adr/SP-004F-002-PREVIEW-CONFIRM-AND-IDEMPOTENCY.md)、[投影与来源链](adr/SP-004F-003-BRIDGE-PROJECTION-AND-LINEAGE.md)、[撤销与恢复](adr/SP-004F-004-REVOCATION-RESTORE-AND-SOURCE-DELETION.md)、[Prompt 与目标写入](adr/SP-004F-005-PROMPT-AND-TARGET-PERSISTENCE-BOUNDARIES.md)。现有依据：[World Memory](SP-004B-WORLD-MEMORY.md)、[Story](SP-004C-STORY-RUNTIME.md)、[Prompt](SP-004K-PROMPT-RUNTIME.md)和[实施计划](../planning/SP-004-IMPLEMENTATION-PLAN.md)。

## 一、问题、当前事实与默认拒绝

Bridge 是受信 Owner 对精确源、目标、数据类别、字段、用途及目标受众授予的**有界跨 World 投影资格**，不是数据库同步、自动记忆或目标世界真源。没有当前有效 grant 一律拒绝；同 Owner、同 Soul、同 Definition、同 Principal 均不构成默认共享。一个请求、一个授权、一次经授权投影分别是 `BridgeRequest`、`BridgeGrant`、`BridgeProjection`，不能互相冒充。

当前 [`domain_policy.py`](../../runtime/life_engine/domain_policy.py) 已有 `BridgeRequest`、`BridgePolicy`、`BridgeDecision` 与纯 `evaluate_bridge()`：它能检查不同 World、同 Owner、字段/受众子集、授权修订、撤销和过期，但只做 **eligibility**；字符串标签不是未来强类型授权，调用方提供的 policy 不是可信 grant store。它没有持久化、预览、确认、撤销账本、投影或 Prompt 接线。F1 保留纯 eligibility kernel，在外围建立受信服务；持久 `BridgeGrant` 另建，不把审计、预览和恢复塞进 `domain_policy.py`。现有 `IdKind.GRANT` 可直接复用。

F1 首版建议仅开 `SOUL → ROLEPLAY` 与 `ROLEPLAY → SOUL`。架构允许将来明确增加 Roleplay↔Roleplay，但 F1 首版默认拒绝；同一 World 永不通过 Bridge。Source 与 target 各自绑定完整 `WorldScope(owner_id, soul_id, world_id, timeline_id)`，Timeline 不可省略或通配。F0 不启用任何方向。

## 二、授权对象、范围、字段与受众

`BridgeGrant` 使用稳定 `DomainId(IdKind.GRANT)`、受信 Owner Principal、source/target Scope、单一 `BridgeDataClass`、非空且无通配的最小 `allowed_fields`、单一 `BridgePurpose`、非空的**目标**受众、aware UTC `expires_at`、单调 `BridgeGrantRevision`、状态及审计来源。初次 revision 至少为 1；扩大、缩小、续期、撤销均推进 revision；旧预览/投影立即失效。持久状态可为 `ACTIVE/REVOKED`，`EXPIRED` 由当前可信时间达到 `expires_at` 导出，不靠定时作业改状态。Grant 不绑定某一次 Session，供 Prompt 使用的投影则必须绑定当前目标 Session。扩权与续期是新授权动作，不能静默原地放宽。

`BridgeRequest` 是一次期望操作，须写明受信 principal、完整双 Scope、data class、请求字段、purpose、目标 audience、source selection/query 与预算；它自身不是授权。未来强类型 `BridgeDataClass` 首版候选为 `MEMORY`、`STORY_PROJECTION`；`EXPLICIT_CONTEXT` 仅预留，不在 F1 首版启用。`LORE` 与 `CharacterDefinition` 不作为 Bridge 类别：Lore 应显式绑定书，Definition 已有固定版本身份。用途首版候选 `PROMPT_CONTEXT`、`PERSIST_TARGET_MEMORY`、`PERSIST_TARGET_STORY_CANDIDATE`，一 grant 只授一 purpose；后两种持久目的必须另行确认为实际 F1 功能。`PROMPT_CONTEXT` 不能被改用来写目标 Memory/Story。

字段使用有限 `BridgeFieldRegistry`，不是任意用户字符串。候选 `MEMORY` 字段为 `content`、`kind`、`subjects`、`reality_status`、`canon_status`、`source_reference`；`STORY_PROJECTION` 首版仅 `character_state` 与 `viewer_relationships`，不含 `world_facts`、`open_threads`、event log。请求字段必须是对应类别允许集合和 grant 集合的非空子集；`*`、`all`、`everything` 及未知字段均拒绝。每项字段都不能携带新的权限、工具命令或更大数据视图。

Grant audience 指**哪个 target viewer 可以消费**，建议使用类型化、精确目标的 `MemoryAudience(SOUL | CHARACTER_INSTANCE)` 或等价 BridgeAudience；不支持 `WORLD`、`USER`、`PRINCIPAL` 或通配目标作为首版 Prompt audience。target CharacterInstance 必须存在并属于 target Scope，Soul viewer 必须匹配 target soul。来源 Memory 的 audience 另行保留于 lineage，不能把来源实例 UUID 复制成目标受众，也不能因为 Owner 管理 grant 就让 Soul 模型取得 Owner 全量视图。

`OwnerBridgeContext` 承载受信 Principal 与两个 Scope，供 grant、revoke、preview 和持久操作确认；仅 Owner 可建立、扩大、续期或撤销 grant。`SessionBridgeContext` 承载 Principal、target Scope、OPEN Session、WriterEpoch、runtime_id、generation、精确 viewer 与 purpose，供目标模型消费。知道 grant_id 或掌握模型文本都不是凭据。未来 H 可将明确用户命令转交受信入口，但模型/角色文本不能创建 grant。

## 三、来源读取与生命周期

先验证 grant 与双 Scope，再通过**来源 Runtime** 取得具体授权投影，绝不先扫全库后过滤。Memory 的普通 Prompt 来源是 `SessionMemoryContext + MemoryQueryResult`，保留原 query/limit、viewer、记录顺序及不透明 version；必须再检 `LIVE`、`CanonStatus.ACCEPTED`、源 audience 与当前 source viewer。Owner 可在管理路径**明确选取具体 MemoryId** 作为独立授权模式，但要展示它属于 Owner 显式选择、保留原 audience/reality/canon，不能把 Owner 全量查询伪装成角色 Session 查询。隐藏、tombstone、删除控制阻断的来源不可投影。

Story 来源只能是精确 `SessionStoryContext` 的有界 `StoryProjection` 再经保守字段过滤：当前角色状态及涉及该 viewer 的关系。Owner `StoryState`、全事件日志、全部 world_facts 和 open_threads 不可直桥给角色。Story revision、projection version 和不透明 snapshot token 是来源版本，不能解码 token；Bridge 不把 accepted Story 变成目标 Story truth。

来源与目标 TOMBSTONED 一律拒绝新预览、投影和写入；ARCHIVED 仅 Owner 审计/读取旧操作，不发新投影或目标写入。CREATED、ACTIVE、SUSPENDED 来源可在对应 Runtime 原有读合同许可下使用；不能因为 Bridge 额外打开原 Runtime 拒绝的读取。Prompt 消费要求目标 ACTIVE、当前 OPEN Session；Owner 确认持久目标操作不需要伪造 Session，但目标 World 状态仍必须满足目标 Memory/Story Runtime 的写入合同。EXIT、SWITCH 不触发桥接。

## 四、预览、确认与幂等

`BridgePreview` 是只读、不可变的确切视图；mode 区分 `GRANT`（建立/扩权/续期将允许什么）与 `USE`（这次将共享/写入哪些完整 item）。它展示双 Scope、data class、字段、目的、目标 audience、源真实性/canon、lineage、是否持久化、过期与授权 revision。Preview 不移动数据、不写目标、不持数据库锁等待用户。`BridgePreviewToken` 用 HMAC 绑定规范预览内容、来源版本、grant revision、Scope、purpose、audience、精确 item fingerprint、runtime/generation 和按用途需要的目标 Session 围栏；它是防篡改绑定，不是登录凭据。

Grant 创建/扩权/续期须经 `GRANT` 预览和 Owner 确认；`PROMPT_CONTEXT` 的有效持久 grant 可以采用 `GRANT_ONLY`，在每次符合范围、来源 ACL 和目标 Session 的读取前不再弹窗，但每次仍重验。所有目标持久写入采用 `PER_USE`，必须先给 Owner `USE` 数据预览并确认**同一份内容**。未来可为更敏感的 prompt-only grant 要求 `PER_USE`。`confirm(preview_token)` 不接受仅传 grant_id 后重新抓“最新数据”；必须重验当前 grant、source auth/version、双 Scope、target eligibility、精确预览 fingerprint 及过期。任一变化报 `PREVIEW_STALE`，不得悄悄刷新内容后继续。

Grant mutation 用独立 BridgeGrantRevision 的事务内 CAS；同 revision 竞争单胜者。`BridgeIdempotencyIdentity(producer, source, slot)` 加规范 proposal fingerprint 用于 create/modify/revoke/confirm/持久提交：同 key 同内容返回原 receipt，异内容拒绝。重试 replay 优先于 CAS 旧 revision 错误；跨目标 Runtime 写入的 confirm 必须有稳定目标操作身份，避免网络重试两次写入。预览与人工确认之间不开长事务；确认时乐观重查，F1 要定义跨 Bridge 与目标 Runtime 提交故障时的可恢复 receipt/审计，而非假装两个服务天然单事务。

## 五、瞬时投影、来源链与语义保留

`BridgeProjection` 是不可变、瞬时、目标专属的授权数据，不作为 canonical 表、目标 MemoryRecord、StoryEvent 或 StoryState。至少含规范 projection fingerprint、grant_id/revision、双 Scope、data class、字段、purpose、target audience、完整有序 items、source versions、lineage、来源 reality/canon 语义、有效期及 HMAC projection token。每 item 带来源子系统、精确对象身份与版本；没有“所有角色通用 blob”。同 grant/source snapshot/request/budget 必须得到同 items、顺序与规范 fingerprint；当前墙钟、随机数和 HMAC secret 不参与 fingerprint。有效性另按当前时间判定；runtime/generation 重启替换也令旧投影 stale。Token 不是权限凭据。

`BridgeLineage` 至少记录 source World/Timeline、子系统、对象 ID、版本、来源 audience/reality/canon、grant ID/revision 与 projection fingerprint；目标持久记录必须能追溯原投影。`RealityStatus.FICTIONAL` 或 `FICTIONAL_SHARED_EXPERIENCE` 跨到 Soul 后仍是虚构语义，不会提升为真实观察；来源 `CanonStatus.ACCEPTED` 也不自动成为目标 Story 接受。目标受众是新的授权边界，不复制源受众的 UUID；源受众语义仍保留供审计。

`BridgeBudget` 独立于 PromptBudget，至少控制 item 数、单 item UTF-8 bytes 和总 bytes；数值 F1 再定。按来源授权顺序与明确字段序稳定选择，完整项装不下立即停止或报预算失败，不切半、不跳过大项补小项，不使用 LLM 筛选。Preview、Projection 与后续 K 可有不同预算，但 K 不能扩大 F 已授权字段或增加遗漏 item。

## 六、撤销、过期、源删除与恢复

Revoke 是即时硬围栏：新投影拒绝；未发送的旧投影及已装入旧 PromptSnapshot 在重验时 stale；过期同样拒绝。外部模型已见数据无法召回，不能宣传“撤销后模型忘记”。已显式接受为目标 Memory/Story 的记录不因 grant 撤销被静默删除；它归目标子系统治理，lineage 仍须留存，依赖来源失效时应进入目标记录的明确失效/复核流程，F1 不能在没有该合同前承诺安全持久写入。

**撤销不能随业务备份回滚。** 若 grant 持久化，F1 必须具备独立于可恢复 generation 的非回滚撤销控制记录，并在启动、备份恢复及候选 generation 激活前重放/核对；控制域缺失或损坏则 fail closed。旧备份中 ACTIVE grant 若已被撤销，恢复后仍不得可用。该控制域只存最小撤销身份/序列，不是第二套 Bridge 内容库；实现可借鉴 Memory deletion control，但须在 F1 审核故障原子性、安装身份和锁顺序。F0 不创建控制 DB。

来源 Memory 删除后，新桥接和未使用投影失效；恢复删除前的业务备份也不能使它重新成为来源，必须继续执行 Memory deletion control 并重验当前来源可用性。Story 首版无物理事件删除，不能借 Bridge 假设 Story 删除控制。已写入目标的来源依赖记录不自动消失，需目标 Memory/Story 自身的 lineage 失效和治理政策；F1 若无法安全实现，应延后持久目标写入，不放松来源删除合同。

## 七、Prompt、Memory、Story 与 Host 的边界

最小路径是 `BridgeProjection → PromptBridgeProjection → K → BRIDGE_CONTEXT`，**仅** `PROMPT_CONTEXT`、target Scope/viewer/Session/purpose/audience/版本全部相符时可用。当前 [`prompt.py`](../../runtime/life_engine/prompt.py) 虽有 `BRIDGE_CONTEXT` Enum，却在 `PromptSection` 中明确拒绝；F0 不修改它。未来 F1/K 扩展必须给 Bridge 独立 `bridge_bytes`，按固定 item 顺序 `PREFIX` 完整项裁剪，建议 Section 位于 **STORY → LORE → MEMORY → BRIDGE → CONVERSATION**。Bridge 文本始终 `UNTRUSTED_CONTENT_DATA`，不可生成 `RUNTIME_CONTROL`。K 在 assemble 及 Host 发送前 revalidate 中检查当前 grant/撤销、来源版本、目标 Session/epoch/runtime/generation、purpose、audience 与过期；F 不直接修改 PromptSnapshot。

持久目标 Memory 路径是 `BridgeProjection → 显式 Owner 确认 → target Memory candidate/create → MemoryRuntime 接受语义`，不是复制 source DB row。自动来源首选 `CANDIDATE`，不因源 ACCEPTED 而自动接受；确实由 Owner 明确接受也须经过目标 Runtime 的独立管理门禁。当前 [`memory_runtime.py`](../../runtime/life_engine/memory_runtime.py) 明确拒绝 `SourceType.BRIDGE` 为 `INVALID_SOURCE`，且现有 lineage 只允许同 Scope；F1 需独立审核可信 Bridge 来源与跨 Scope lineage 扩展，不能直接构造或 SQL 插入目标 Memory。

持久目标 Story 路径是 `BridgeProjection → StoryEventProposal → 目标 Scope 的受信 explicit accept → Accepted StoryEvent`。当前 `StoryEventSourceReference` 只有 STORY_EVENT/MEMORY/LORE_ENTRY/EXTERNAL_MESSAGE 身份，未来 Bridge lineage 必须另设计明确源 Scope/投影引用；不能用任意 external_message 假装授权。Bridge 不读写完整 StoryState、event log，不直接 `INSERT story_events`，不因来源被接受就直接确权目标。H 负责未来自然语言意图、预览展示、用户确认、真实 HostCapabilities 和模型提交；F 不读宿主聊天库、不主动发送消息、不调用 LLM。

## 八、候选持久层、审计、错误与验收

若 F1 实施持久 grant，很可能需要**另行批准的 Schema 迁移**：只在新 generation 副本建立 grant/revision、审计与幂等业务状态，独立控制域记录不回滚撤销；支持 restart、backup、restore、精确校验、多实例原子激活与同 Schema 代码回退。F0 不锁定 Schema 编号、不建表、不实施迁移。Bridge repository 只管理 grant、audit、idempotency 与控制状态；不复制目标 Memory/Story 正文，也不持久化 BridgeProjection。`BridgeOperationAudit` 至少记 operation_id、grant_id、actor、action、双 Scope、revision、可选 projection fingerprint、时间及结果 ID；不存完整聊天或敏感正文。Prompt-only 的“已消费”审计应在未来 H 真正发送时产生，不能让只读 assemble/revalidate 偷写状态。

建议固定错误类别：`INVALID_ARGUMENT`、`AUTHORIZATION_DENIED`、`SOURCE_SCOPE_MISMATCH`、`TARGET_SCOPE_MISMATCH`、`AUDIENCE_DENIED`、`GRANT_NOT_FOUND`、`GRANT_REVOKED`、`GRANT_EXPIRED`、`GRANT_REVISION_CONFLICT`、`FIELD_DENIED`、`PURPOSE_DENIED`、`DATA_CLASS_DENIED`、`SOURCE_STALE`、`TARGET_STALE`、`PREVIEW_STALE`、`PROJECTION_STALE`、`SOURCE_NOT_AVAILABLE`、`TARGET_NOT_AVAILABLE`、`BUDGET_INPUT`、`STORAGE_CORRUPT`、`STORAGE_BUSY`、`SCHEMA_MISMATCH`、`RECOVERY_REQUIRED`。Session 外部接口对猜测来源/授权不提供存在性 oracle，诊断不回显来源正文。

F1 验收矩阵必须至少覆盖下列合同；测试使用合成数据和受信 Runtime，不借 Host/LLM 假装通过：

| 组别 | 必须证明 |
| --- | --- |
| 默认拒绝与方向 | 无/错误 grant、revoked、expired 均 DENY；Soul↔Roleplay 明确授权才可用；Roleplay↔Roleplay 首版及同 World 默认拒绝；EXIT/SWITCH 不自动桥。 |
| Scope 与 audience | 错 source/target World、Timeline、Owner、viewer、已删除 target CharacterInstance 均拒绝；Owner 管理身份不等于 Soul/角色 viewer。 |
| DataClass、字段、purpose | 请求只取有限 registry 的授权子集；未知/额外/通配字段或受众拒绝；PROMPT_CONTEXT 不可用于目标持久写入。 |
| 来源与语义 | Session Memory ACL、LIVE/ACCEPTED、删除控制有效；Owner 选具体 ID 与角色查询分路径；Story 只含角色状态/相关关系；虚构现实状态跨域保留、canon 不升级。 |
| 预览与确认 | 展示确切 items/版本/目的/目标；preview 只读；source、grant、audience、expiry、target Session 改变后 stale；confirm 只提交预览指纹，不能悄悄重抓。 |
| 幂等、CAS 与并发 | 同 key 同 proposal 返回原 receipt，异 proposal 冲突；同 revision 双写单胜者；并发 confirm/重试只触发一次目标操作。 |
| 投影与预算 | 相同授权输入得同有序 items/fingerprint；item 完整，预算耗尽不跳过；token 非凭据；恶意来源文本不产生 grant/工具权限。 |
| 撤销、过期与 Prompt | revoke 后新投影拒绝，旧投影和未发模型的 PromptSnapshot stale；BRIDGE_CONTEXT 只能是 DATA、独立预算、target Scope/viewer/purpose 一致。 |
| 备份恢复与删源 | ACTIVE 备份后 revoke 再恢复仍 revoked；源 Memory 删除后恢复旧数据 generation 不重新可桥；控制域损坏 fail closed。 |
| 目标写入 | Memory 只经 MemoryRuntime、Story 只经 proposal/accept；无直接 SQL copy；来源删/撤销不静默删除已接受目标数据，但 lineage 失效按目标治理合同处理。 |
| 生命周期与平台 | TOMBSTONED/ARCHIVED 拒绝新桥；Prompt Session OPEN、epoch/runtime/generation 围栏；Windows/Linux 重启/备份/迁移/连接清理不回归。 |

F0 不新增测试，既有全量回归和四矩阵 CI 只证明现有代码未回归，**不证明 Bridge 已实现**。

## 九、F1 边界与非目标

F1 候选可独立设计 `bridge.py`、`bridge_runtime.py`、`bridge_sqlite_repository.py`、`bridge_schema.py` 及必要的 K/Memory/Story 受信适配，但必须另立任务书，审查撤销控制、来源删除和目标持久语义后才实施。F0 不改 Runtime、Schema、Tests、Workflow、README，也不启用 K 的 Bridge Section。非目标包括自动跨 World 复制、EXIT/SWITCH 自动回写、Soul aside、LLM 选材或授权、Hermes/OpenClaw、Host UI、外部网络获取、World 数据库同步及已发模型内容的“撤回”。
