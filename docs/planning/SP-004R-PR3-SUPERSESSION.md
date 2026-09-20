# SP-004R — PR #3 正式替代与历史拆分记录

## 一、记录身份与授权边界

本文是 PR #3 的 canonical supersession record，当前状态为 **PENDING_INDEPENDENT_REVIEW**，随本次文档 PR 接受独立审核。

- 历史 PR：[PR #3](https://github.com/y19870785/life-engine/pull/3)，标题：新增双层身份角色扮演、世界书与隔离记忆。
- 固定 Head：`ab227f2179eeaa7ded662d612508a98ad5cdf04a`。
- 原 Base：`81ee02b561ac90641c3632f750ffd86a48310cf7`。
- 当前 canonical main：`780c7a54635e7347b914751ce0c79e350800be0b`。
- 本轮核对状态：**OPEN / DRAFT / NOT MERGED**；变更文件数：**32**。
- 实施授权仅限 SP-004R；转 Ready、合并、关闭 PR #3 均未授权。

**本文档不意味着 PR #3 已关闭。** 关闭必须等待独立审核后单独授权。PR #3 不再是等待解决冲突后合并的候选，而是历史实现来源、兼容性研究材料和后续能力拆分来源。以后只能作为 read-only reference；不得因为“PR #3 里已经写过”就 cherry-pick，必须重新适配 canonical domain model。

核对依据为固定提交的文件内容及相对原 Base 的差异，并与当前代码和阶段文档比较；没有运行历史宿主探针、读取真实角色卡或复制历史二进制资产。

当前依据：[总体架构](../architecture/SP-004-PERSISTENT-WORLD-RUNTIME.md)、[A 领域模型](../architecture/SP-004A-WORLD-DOMAIN-MODEL.md)、[G 导入 IR](../architecture/SP-004G-CHARACTER-IMPORT-IR.md)、[D 运行合同](../architecture/SP-004D-WORLD-INSTANCE-RUNTIME.md)、[E 持久化](../architecture/SP-004E-WORLD-SQLITE-PERSISTENCE.md)、[实施计划](SP-004-IMPLEMENTATION-PLAN.md)。相关 ADR：[定义与实例](../architecture/adr/SP-004A-003-CHARACTER-DEFINITION-INSTANCE.md)、[真实性与正史](../architecture/adr/SP-004A-002-REALITY-AND-CANON.md)、[重启恢复](../architecture/adr/SP-004E-001-RESTART-SESSION-RECOVERY.md)、[迁移与回退](../architecture/adr/SP-004E-002-SCHEMA-3-MIGRATION.md)。

## 二、32 文件逐项审计

主分类唯一：SUPERSEDED 表示主职责已正式替代；ADAPT_LATER 表示能力需要但须重建；HISTORICAL_EVIDENCE 表示仅保留证据；DROP 表示不再采用。主分类不是对文件全部子能力的完成声明；混合文件的未完成部分单独列明。B/J/C/F/K/H/L 和 GOV-CI/GOV-DOC 均是实施计划中的 **PROPOSED** 归属，不是启动授权。

表内历史文件链接全部固定到上述 Head。

| PR #3 文件 | 主分类 | 已替代位置 / 后续目标 | 可吸收内容 | 禁止吸收内容 | 说明 |
| --- | --- | --- | --- | --- | --- |
| [`.github/workflows/tests.yml`][p01] | ADAPT_LATER | GOV-CI | Windows/Linux 与 Python 矩阵、Node 合同测试组织经验 | 直接复制旧 workflow 或宣称当前 CI 已通过 | CI、TEST；旧角色断言须重建 |
| [`README.md`][p02] | ADAPT_LATER | GOV-DOC、H | 用户价值与角色切换体验的表达意图 | v0.4 能力声明、旧命令和架构直接发布 | DOCUMENTATION；当前生活功能介绍已有，World 产品体验尚未接入 |
| [`docs/KNOWN-ISSUES.md`][p03] | HISTORICAL_EVIDENCE | E 已处理连接；J/K/H 重验限制 | 多聊天污染、预算与模型误述风险 | 将历史限制或修复记录当当前验收 | DOCUMENTATION；区分已解决存储问题和未解决宿主问题 |
| [`docs/OPERATIONS.md`][p04] | SUPERSEDED | E 迁移 ADR；H 承接重连 | 副本迁移、安装备份与重载经验 | 旧 Schema 3 运维及隐式跨 Schema restore | MIGRATION、BACKUP；refresh/connect 角色接入仍待 H |
| [`docs/ROLEPLAY-VALIDATION.md`][p05] | HISTORICAL_EVIDENCE | H 验收设计 | 实际 Hermes 隔离探针与原 SOUL 不变验证 | 当作当前 World 或在线 Gateway 通过证明 | TEST、HERMES、OPENCLAW |
| [`docs/ROLEPLAY.md`][p06] | ADAPT_LATER | H/K、GOV-DOC | 角色模式说明、退出与身份问答场景 | 自动元记忆、卡片即运行身份 | DOCUMENTATION、HOST；须以新 UX 重写 |
| [`docs/SOURCES.md`][p07] | HISTORICAL_EVIDENCE | J/H 的来源复核 | 历史规格、宿主 API 来源索引 | 把旧日期接口当当前接口承诺 | DOCUMENTATION；实施时重新查证 |
| [`docs/demo/render_probe.py`][p08] | HISTORICAL_EVIDENCE | H 脱敏验收展示参考 | 转录渲染与 HTML 转义方法 | 把渲染断言当独立集成验证 | DEMO、TEST；不执行或迁入 Runtime |
| [`docs/demo/roleplay-hermes.html`][p09] | HISTORICAL_EVIDENCE | H 历史展示 | 四阶段对话与程序状态并列展示 | 作为当前产品页面或实机宿主 UI | DEMO；保留固定 Head，不复制 |
| [`docs/demo/roleplay-hermes.json`][p10] | HISTORICAL_EVIDENCE | H 历史探针证据 | 转录、程序结果与模型回答对照 | 原始身份片段直接再发布、当前验收背书 | DEMO、HERMES；未来派生材料先脱敏另审 |
| [`docs/demo/roleplay-hermes.png`][p11] | HISTORICAL_EVIDENCE | H 历史截图 | 旧转录展示的可视证据 | 二进制复制进 main 或冒充 Gateway 截图 | DEMO；已核对固定提交的同一图片 |
| [`examples/roleplay/starmap.card.json`][p12] | HISTORICAL_EVIDENCE | G 测试意图；L 资产 | 原创 V2 卡、内嵌书与递归触发场景 | 旧 card_id 存储与外部卡依赖恢复 | CHARACTER_IMPORT、TEST；后续另造合成 fixture |
| [`examples/roleplay/starmap.world.json`][p13] | HISTORICAL_EVIDENCE | J | 独立书字典条目、顺序与 depth 样例 | 将书当持久 World | WORLD_BOOK、TEST；保留参考，不宣称执行已支持 |
| [`runtime/life_engine/__init__.py`][p14] | DROP | 当前发布版本管理 | 无需吸收旧版本号 | 单独复用 0.3 → 0.4 的版本递增 | 仅历史发布标记，无独立运行能力 |
| [`runtime/life_engine/bridges.py`][p15] | ADAPT_LATER | H/K | 作用域、原生命令、Hook、来源检查与晚到响应场景 | 整实例活动角色、Prompt 降级充当权限 | HOST、HERMES、OPENCLAW；两宿主消息记录能力不对称 |
| [`runtime/life_engine/cli.py`][p16] | ADAPT_LATER | H | Windows 路径及结构化参数错误意图 | 整数 session/card 作为新运行入口 | HOST、SESSION；命令必须绑定可信 Principal 和 World |
| [`runtime/life_engine/config.py`][p17] | ADAPT_LATER | J/K/H | 扫描、递归、上下文预算可配置且有界 | 将全局 roleplay 配置当世界权限 | LORE、PROMPT；配置版本不等于数据库版本 |
| [`runtime/life_engine/deploy_cli.py`][p18] | ADAPT_LATER | H | refresh/connect、插件刷新与重载流程 | 假设更新文件会自动改变宿主已加载插件 | HOST；按新运行代次和能力声明重建 |
| [`runtime/life_engine/durable.py`][p19] | SUPERSEDED | E；K/H 承接表现与 Hook | 副本迁移、缺库拒绝、备份与连接经验 | 旧 schema 识别、旧角色 context、隐式旧库恢复 | SCHEMA、MIGRATION、BACKUP；存储替代不代表宿主完成 |
| [`runtime/life_engine/engine.py`][p20] | ADAPT_LATER | H/B | 角色期间避免现实通知与记录污染的意图 | 用全局 active role 判断全部行为 | HOST、MEMORY；现有生活 Engine 不自动创建 World |
| [`runtime/life_engine/photos.py`][p21] | ADAPT_LATER | H/F | 工具执行前检查模式与权限 | 旧 require_soul 全局状态充当新授权 | HOST；现实照片能力须明确权限，不由 Prompt 授予 |
| [`runtime/life_engine/rp_cards.py`][p22] | SUPERSEDED | G；原包/头像归 L | 格式边界、CRC、大小限制、恶意输入测试意图 | 浅白名单替代保真 IR、卡片充当运行根 | CHARACTER_IMPORT；G 不等于完整原包/头像仓库 |
| [`runtime/life_engine/rp_commands.py`][p23] | ADAPT_LATER | H/K/F | 命令与中文退出、路径解析、切换失败场景 | 无授权 aside、删卡级联删经历、全局角色路由 | HOST、PROMPT；aside 当前只返回上下文，并非独立模型调用 |
| [`runtime/life_engine/rp_lore.py`][p24] | ADAPT_LATER | J | 有界字面触发、确定顺序、递归终止、预算测试 | card 绑定、字节预算冒充词元预算 | LORE、WORLD_BOOK；高价值参考，不能直接复制执行器 |
| [`runtime/life_engine/rp_prompt.py`][p25] | ADAPT_LATER | K/H/F | 元身份表达、不可信数据标记、裁剪场景 | Prompt 权限边界、未授权 Soul 记忆、同卡共享记忆 | PROMPT、MEMORY；depth 只改插件摘录窗口 |
| [`runtime/life_engine/rp_schema.py`][p26] | DROP | E canonical schema | 失败场景与不兼容反例 | 整套旧 Schema 3、仅凭版本号放行、删卡级联 | SCHEMA；数字同为 3 不代表兼容 |
| [`runtime/life_engine/rp_sessions.py`][p27] | SUPERSEDED | D/E；记忆 B、跨域 F、资产 L | 事务、历史保留与晚到写入的测试意图 | RoleplaySession 根、自动 Soul 元记忆、旧归属模型 | SESSION、MEMORY；Memory 和共同体验并未随替代完成 |
| [`runtime/life_engine/store.py`][p28] | SUPERSEDED | E；B/H 承接记忆与工具隔离 | 缺库拒绝、约束与明确连接关闭经验 | 自动接受旧 Schema 3、角色逻辑继续塞入 Store | SCHEMA、MEMORY；当前 Store 保持生活业务职责 |
| [`tests/manual_hermes_probe.py`][p29] | HISTORICAL_EVIDENCE | H | 隔离数据目录、真实 Hook/模型与 SOUL 哈希核对 | 直接运行读取真实配置、把旧 session 断言当新验收 | TEST、HERMES；本次不执行，不产生模型调用 |
| [`tests/test_durable.py`][p30] | ADAPT_LATER | E 已吸收清理；H 重建宿主测试 | closing、忽略 .git、中文编码与 Node 合同意图 | 旧 session/Prompt 断言原样复用 | TEST、HOST；混合文件不能整体标记完成 |
| [`tests/test_photos_migration.py`][p31] | SUPERSEDED | E 对应显式 closing | 确定性释放 SQLite 连接 | sleep、gc.collect 或吞掉清理错误 | TEST、MIGRATION；小范围资源管理经验已吸收 |
| [`tests/test_roleplay.py`][p32] | ADAPT_LATER | G/D/E 覆盖部分；B/J/K/F/H/L 重建其余 | 解析、原子性、隔离、预算和宿主回归意图 | 用旧测试通过背书新领域、复活旧模型 | TEST；见下文逐组拆分 |

统计：SUPERSEDED **6**；ADAPT_LATER **14**；HISTORICAL_EVIDENCE **10**；DROP **2**；合计 **32**。次级标签只辅助检索，不改变唯一主分类。

## 三、已经替代的运行基础

### Character Card 与定义/实例

旧解析器支持 JSON V1/V2/V3、PNG chara/ccv3 与 CRC/大小边界，但主要投影为浅层字段并交给卡片表；书的规范化混在导入路径中。当前 [import_cards.py](../../runtime/life_engine/import_cards.py) 与 [import_ir.py](../../runtime/life_engine/import_ir.py) 提供保真 IR、诊断、来源指纹和受信 Principal 的 Definition 投影。G 正式替代导入核心，LoreIR 保留并不执行 Lore。

Character Card ≠ CharacterInstance：卡片导入为 CharacterDefinition，进入 World 时创建 CharacterInstance；同一定义可以有多个实例。E 保存固定定义版本，无需原角色卡仍存在。原 PNG、头像提取/仓库、完整 IR 导入历史并未因此完成，归 L。旧 `card_id == runtime character` 语义淘汰。

### RoleplaySession 与会话持久化

旧 RoleplaySession 是 card/session 归属根，整实例最多一个活动会话；同卡记忆跨会话共享。当前 [WorldRuntime](../../runtime/life_engine/world_runtime.py) 通过 WorldRepository 统一管理 World、WorldTimeline、CharacterInstance 和 SessionBinding；[SQLiteWorldRepository](../../runtime/life_engine/world_sqlite_repository.py) 持久化完整身份、固定 DefinitionRef 和 CLOSED 历史。

数据库事务、revision CAS、writer_epoch 与 runtime_id 重启围栏取代旧可选 expected_session 防护；每个 World 最多一个 OPEN，而不是每个 Profile 一个角色。重启使旧 OPEN 写权限失效，Roleplay 可恢复，Soul 保持独立生命周期；恢复不改变 World/Timeline/Instance 身份。双 World 切换是单事务。这不等于持久消息、World Memory、Story 或宿主消息幂等均已完成。

### Schema、迁移与备份

当前 [world_schema.py](../../runtime/life_engine/world_schema.py) 的 `DATA_SCHEMA = 3`、`SIGNATURE = SP-004E-world-runtime-v1` 才是 canonical Schema 3。**Schema 版本号相同不代表 Schema 兼容；数字同为 3 不代表兼容。** 旧卡片、条目、session/message 与 persona memory 表不可直接合并，旧迁移遇到版本 3 就返回的识别方式不可沿用。

E 使用既有 durable 安装体系的 Copy → Migrate → Validate → Atomic Activate；迁移前备份、多实例整安装激活、保留旧 generation、结构/索引/外键检查和失败保护已经正式替代旧方案。SQLite backup API 与 committed WAL 保护是既有部署基础，不应全记为 PR #3 首创。旧副本迁移和缺库保护的经验已适配，不能重复搬迁实现。

Windows cleanup 的关键经验是显式关闭连接：SQLite connection 上下文管理只管理事务，不保证关闭。E 已在相关 durable/photos 测试等位置采用确定性关闭；本次只是比对，不重跑历史平台测试。旧 Schema 2 备份隐式转换为角色 Schema 3 的流程不被继承；当前跨 Schema 恢复需显式路径，普通 rollback_code 禁止跨 Schema，整组回退同时恢复 release/generation/registry。

## 四、剩余能力与迁移矩阵

只有进入 canonical main 的能力才算完成。现有生活 Hermes/OpenClaw Bridge 不等于基于 SessionBinding 的角色 World 集成。

| PR #3 能力 | 当前 canonical 状态 | 后续工作包 | 处理方式 |
| --- | --- | --- | --- |
| 卡片解析与 Definition 投影 | G 已合并 | G | 已完成 |
| 原包、头像与导入历史仓库 | G/E 不保存完整资产历史 | L | 重新实现 |
| World/实例/会话生命周期 | D/E 替代旧根与持久化 | D/E | 已完成 |
| Schema 2 → canonical 3、备份、回退与连接管理 | E 已合并 | E | 已完成 |
| PR #3 旧 Schema 3 直接兼容 | 明确拒绝 | 无 | 放弃 |
| 确有历史库时的只读映射提案 | 无通用迁移器，不是关闭前提 | L | 重新实现 |
| World Book 版本、绑定和激活 | G 仅保留 LoreIR | J/L | 重新实现 |
| Lore Retrieval、递归、循环终止和 budget | 无执行器 | J | 重新实现 |
| Character Prompt assembly 与身份表现 | 无 canonical Prompt Runtime | K | 重新实现 |
| Roleplay/World/Timeline/Instance Memory | 无 World Memory 服务 | B | 重新实现 |
| Story state、accepted events、关系推进 | Values 不是 Story 引擎 | C | 重新实现 |
| fictional_shared_experience | 只有类型/策略合同，无完整 Bridge | F | 重新实现 |
| 自动退出摘要写 Soul、无范围 aside | 不符合显式授权边界 | 无 | 放弃 |
| /rp、模型角色状态切换与角色模式 UX | World API 已有，宿主产品入口未接入 | H/K | 重新实现 |
| Hermes pre/post Hook 与晚到响应 | 旧验证仅供参考 | H | 重新实现 |
| OpenClaw 命令/工具/上下文 Bridge | 无新 World 角色接入 | H | 重新实现 |
| Host context isolation、宿主历史污染控制 | 无实机新模型验收 | H/K | 重新实现 |
| Host reload/reconnect、跨聊天路由 | 未交付新会话合同 | H | 重新实现 |
| 现实工具、照片、静默与通知隔离 | 不能用旧全局活动模式证明权限 | H/F/B | 重新实现 |
| 实机宿主探针方法 | 需新身份/权限与历史隔离断言 | H | 重新实现 |
| 历史转录、截图与旧验收结论 | 固定 Head 保留，不代表当前能力 | H 历史索引 | 仅保留参考 |
| Windows/Linux CI 矩阵 | 当前 main 无该 workflow | GOV-CI | 重新实现 |
| README/运维/角色使用说明 | 新产品入口未完成，旧说明过时 | GOV-DOC/H | 重新实现 |
| 旧版本号、card 删除级联经历 | 不再采用 | 无 | 放弃 |

### Lore / World Book

旧 rp_lore 是高价值只读参考：字面关键词、大小写、常驻/禁用、优先级和稳定排序，已选条目去重，只有预算内条目参与后续递归。实现限制包括最多 1000 条、扫描窗口上限 64、递归上限 8，预算按 UTF-8 JSON 字节估算而非模型词元；regex/secondary 条件被拒绝。未来 J 应重新定义格式兼容、递归与 budget 合同，而不是照搬这些数值。

World Book ≠ World：前者是外部知识/Lore 格式；后者是持久身份、timeline、state、instances、sessions 及未来 memory/story 的隔离边界。书关联 Definition/World 的明确版本，不执行脚本、不自动获得工具权限。

### Prompt、Memory 与共同体验

旧 rp_prompt 从活动卡、同卡最近 8 条记忆和消息摘录组装文本，内部约 23000 字节上限；depth 插入插件摘录窗口，不是修改宿主原始消息数组。元身份、裁剪和不可信文本标记可以成为 K 的测试意图，但不能充当权限控制。K 应只消费授权快照，H 隔离宿主历史，模型口吻切换与程序写权限分别验证。

旧 rp_sessions 的 remember/finish 自动写 Soul roleplay_meta，结束摘要取最近条目；旧 aside 可读取 Soul 记忆。这些实现淘汰。B 应以 World/Timeline/Instance、audience/scope、RealityStatus/CanonStatus 控制写入、检索、缓存和导出，不能用同卡最近记忆替代 Story 真源。

“虚构共同体验”思想分类为 **ADAPT_LATER**：未来 F 通过 Controlled World Bridge 的 default deny、grant、preview、显式确认和 lineage 产生 `RealityStatus.FICTIONAL_SHARED_EXPERIENCE`；不是 EXIT 的自动副作用。Soul ↔ Roleplay 两向都受控，不伪造历史 grant。

### 宿主、UX 与实机证据

旧 Hermes 有原生命令、工具与 pre/post Hook，进程内 turn/session 对照用于晚到写入；Profile 与 CLI 条件并不等于新 Principal/World 鉴权。OpenClaw 有 agentId/workspace、命令授权与来源条件，助手消息记录与 Hermes 不对称，命令名冲突、多聊天隔离与重连仍须验收。UTF-8、Windows 路径、结构化错误、事件去重可以吸收测试意图。模型被要求“不要串角色”不是 host history isolation。

H 必须重新验证运行代次、SessionBinding、Prompt lane、宿主历史、模型角色状态、真实 UX、reload/reconnect 和能力不足时拒绝/降级。不得启动真实 Hermes/OpenClaw 连接作为本次文档任务的一部分。

历史验证文档记录 2026-09-15 的 Hermes v0.21.2 隔离探针：真实插件/Hook/AIAgent，临时 Life Engine 与会话数据，原 SOUL/config 哈希不变；不是在线 Gateway 验收。OpenClaw 是 Node 合同验证，不能升级为实机证明。manual_hermes_probe 会涉及真实配置与可选模型调用，因此本次不执行。

JSON/HTML/PNG 具有长期历史证据价值，全部 HISTORICAL_EVIDENCE，留在固定 Head；图片是转录渲染，不能冒充宿主原生界面。已比对图片 Git blob `90582d821d9b8e0979abcfa24d09ea2c41a28502`。这些材料含身份片段及工具/模型信息，不复制二进制或原转录到 main；未来若发布脱敏派生材料，须单独审核并保留来源。render_probe 的展示断言不是独立模型验证。

### CI 与 README

旧 workflow 在 push/pull_request 运行 ubuntu-latest/windows-latest × Python 3.11/3.12，并配置 Node 24；unittest discover 包含角色测试，没有独立角色任务。GOV-CI 可参考矩阵思路，但需按实施时支持范围、权限和当前 G/D/E 测试重建。本次未添加 workflow，也未宣称 GitHub Actions 通过。历史文档中的本地平台通过数不是当前 CI 状态。

当前 README 已有生活引擎的用户价值说明；旧角色预览的使用叙事可供 GOV-DOC/H 参考，但 v0.4 命令、自动元记忆与截图不能直接合入。README 等用户文档残留的旧能力/问题说明应按当前发布事实另行校准，本次不扩大修改范围。

## 五、旧测试意图的拆分

以下覆盖 test_roleplay.py 的全部 19 个测试函数，按相邻意图合并展示；“覆盖”指相应合同已由当前实现验证，不表示复制了旧断言或本轮重新运行。

| 旧测试函数 | 已替代的意图 | 待重建或淘汰 |
| --- | --- | --- |
| test_json_versions_and_png_avatar_roundtrip；test_corrupt_png_and_invalid_cards_do_not_write | G 格式/恶意输入与诊断；E 事务不留半写入 | 原包/头像资产往返归 L |
| test_lore_recursion_case_depth_and_budget；test_disabled_nonrecursive_and_priority | G 仅保留数据 | J 激活、递归、顺序、预算；K 消费位置 |
| test_enter_switch_exit_and_meta_memory_isolation | D/E 生命周期及持久身份 | B/K/F 重建记忆/上下文/跨域；自动 meta 淘汰 |
| test_switch_unknown_is_atomic_exit_idempotent | D/E 切换失败原子性 | 旧幂等 EXIT 不照搬；当前 CLOSED 绑定拒绝合同不同 |
| test_foreign_keys_scope_checks_and_active_uniqueness；test_parallel_enter_claims_once | E 外键及每 World OPEN 唯一、独立连接竞争 | B 的 memory 外键/scope 另验；不保留整实例单角色限制 |
| test_life_silent_photo_blocked_and_loops_protected | 无新角色宿主权限验收 | H/F/B 重建工具与生活隔离 |
| test_import_book_and_delete_cascade | G 导入数据保留 | J/L 书资产；删卡级联删经历淘汰 |
| test_memory_disabled_and_aside | 无完整 B/F | B 禁用行为；F 授权；K/H 上下文；无授权 aside 淘汰 |
| test_stale_session_cannot_write_soul_or_next_persona | D/E revision/epoch/runtime 围栏 | B/H 将记忆/晚到响应对接新绑定 |
| test_depth_placement_and_repeated_event_deduplication | 会话唯一不等于消息去重 | J/K 位置；H 消息去重；C 接受事件去重 |
| test_prompt_has_hard_bound_with_large_card | G 输入有界不是 Prompt 预算 | K 预算与恶意内容裁剪 |
| test_invalid_tool_arguments_return_json_error | 无新 World CLI | H 结构化错误 |
| test_upgrade_copies_schema2_and_preserves_original；test_failed_migration_keeps_registry_and_source；test_missing_database_is_not_recreated | E 更严格的副本迁移、失败保护和缺库拒绝 | 旧 Schema 2 restore 隐式迁移断言淘汰 |
| test_hook_exit_and_roleplay_context_do_not_leak_soul | 无新宿主闭环 | H/K/B 实际历史与权限隔离 |

另两个测试文件的 closing/.git 处理已由 E 吸收；test_durable 的中文编码、Hook 参数、Node 上下文验证归 H，test_photos_migration 的连接释放不必再搬一次。旧测试通过不能证明新模型完成。

## 六、明确淘汰的架构与路线校准

以下设计不得作为未来架构：RoleplaySession aggregate root、card_id 运行身份、host conversation 充当 World identity、记忆直接归旧 session root、PR #3 Schema 3、角色事件自动写 Soul memory、Prompt 充当权限边界，以及删模板级联删经历。

[实施计划](SP-004-IMPLEMENTATION-PLAN.md) 已将 SP-004/A/G/D/E 按实际合并历史记为 DONE；E 唯一含义是 SQLite World Runtime Persistence。未来候选主线为 **B World Memory → J Lore/World Book → C Story Runtime → F Controlled Bridge → K Prompt Runtime → H Host Integration**；L 单独承接资产与历史映射，GOV-CI/GOV-DOC 是独立治理候选。所有未来编号、拆包与顺序均为 **PROPOSED**，等待独立审核，不由 Codex 宣布最终顺序。

## 七、PR #3 后续关闭条件

关闭前必须逐项满足：

1. 32 文件全部具有唯一主分类，无重复和遗漏。
2. 所有剩余能力均有未来归属或明确放弃，无能力仅存在于 PR #3 而没有记录。
3. canonical main 不依赖 PR #3；不存在计划中的 cherry-pick 或整包合并。
4. 本替代记录已经合并。
5. 路线图校准已经合并。
6. 独立审核完成，并另行明确授权关闭。

本轮形成了前三项的审计依据；后面合并与授权条件仍未满足。达到这些条件后可以安全关闭，但目前不得关闭。关闭不删除历史 Head；建议保留远端 `feat/metacognitive-roleplay` 至少到后续 Lore / Memory / Host Integration 完成，再另行评估，SP-004R 不删除分支。

## 八、建议关闭说明（仅准备，未发布）

以下文本等待独立审核决定，本轮不向 PR #3 发布评论或状态更新：

```text
PR #3 已被后续 canonical 架构分阶段替代。

角色卡导入已由 SP-004G 替代；
World / CharacterInstance / SessionBinding Runtime 已由 SP-004D 替代；
持久化、重启恢复与 canonical Schema 3 已由 SP-004E 替代。

PR #3 中仍有价值的 Lore、Prompt、Memory、Hermes/OpenClaw 宿主集成与实机验收经验，已经记录到 SP-004R supersession 清单，并将基于当前 canonical World 架构重新实现。

因此本 PR 不再作为可合并实现，关闭仅表示其开发分支被后续架构取代，不删除其历史 Head，也不否定其中的验证与设计参考价值。
```

## 九、本轮质量边界

仅修改 Markdown；核对 32 文件清单、唯一分类、相对链接、固定历史文件引用、diff、基线与 PR 状态。DATA_SCHEMA 仍为 3，World Schema Signature 仍为 `SP-004E-world-runtime-v1`。未修改可执行代码，因此未重复运行 Runtime 全量测试。没有新的 Windows/WSL 运行验收或 GitHub Actions 通过声明。

独立审核状态：**PENDING_INDEPENDENT_REVIEW**。

[p01]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/.github/workflows/tests.yml
[p02]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/README.md
[p03]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/docs/KNOWN-ISSUES.md
[p04]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/docs/OPERATIONS.md
[p05]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/docs/ROLEPLAY-VALIDATION.md
[p06]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/docs/ROLEPLAY.md
[p07]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/docs/SOURCES.md
[p08]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/docs/demo/render_probe.py
[p09]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/docs/demo/roleplay-hermes.html
[p10]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/docs/demo/roleplay-hermes.json
[p11]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/docs/demo/roleplay-hermes.png
[p12]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/examples/roleplay/starmap.card.json
[p13]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/examples/roleplay/starmap.world.json
[p14]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/__init__.py
[p15]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/bridges.py
[p16]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/cli.py
[p17]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/config.py
[p18]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/deploy_cli.py
[p19]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/durable.py
[p20]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/engine.py
[p21]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/photos.py
[p22]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_cards.py
[p23]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_commands.py
[p24]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_lore.py
[p25]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_prompt.py
[p26]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_schema.py
[p27]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/rp_sessions.py
[p28]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/runtime/life_engine/store.py
[p29]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/tests/manual_hermes_probe.py
[p30]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/tests/test_durable.py
[p31]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/tests/test_photos_migration.py
[p32]: https://github.com/y19870785/life-engine/blob/ab227f2179eeaa7ded662d612508a98ad5cdf04a/tests/test_roleplay.py
