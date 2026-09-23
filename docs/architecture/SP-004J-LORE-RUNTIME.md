# SP-004J0 — Lore / World Book Runtime 架构冻结

## 状态与基线

固定基线为 canonical main `1a73f6e43caf54bd34ae810c9b58eddb25f6fb88`。本阶段只冻结设计，状态为 **PROPOSED / PENDING_INDEPENDENT_REVIEW**；没有 Lore Runtime、表或宿主入口。当前 `DATA_SCHEMA = 4`，签名为 `SP-004B-world-memory-v1`。J1 必须另获任务书和实施授权。

现有 [导入适配器](../../runtime/life_engine/import_cards.py) 从角色卡保留 `LoreIR` 的书级元数据、条目与来源指纹。[IR 合同](../../runtime/life_engine/import_ir.py) 将它定义为不可信的上下文来源；导入不会注册、绑定或激活 Lore。外部书引用只记录，不联网或读取路径。`World Book` 是有版本的设定资产；[World](SP-004A-WORLD-DOMAIN-MODEL.md) 是运行身份、Timeline 与状态隔离边界，两者不是同一对象。Lore 也不是 StoryEvent、StoryState、RelationshipState、[World Memory](SP-004B-WORLD-MEMORY.md) 或工具权限。

设计依据：[总体架构](SP-004-PERSISTENT-WORLD-RUNTIME.md)、[SP-004G 导入合同](SP-004G-CHARACTER-IMPORT-IR.md)、[实施计划](../planning/SP-004-IMPLEMENTATION-PLAN.md)。细化决策见[资产版本 ADR](adr/SP-004J-001-LORE-ASSET-VERSIONING.md)、[绑定隔离 ADR](adr/SP-004J-002-LORE-BINDING-SCOPE.md)、[激活 ADR](adr/SP-004J-003-ACTIVATION-TRIGGERS-RECURSION.md)和[预算安全 ADR](adr/SP-004J-004-BUDGET-ORDERING-SAFETY.md)。

## 领域对象与资产版本

| 概念 | 冻结合同 |
| --- | --- |
| `LoreBookId` | 实例内类型化 UUID；稳定资产身份，与书名、卡名、文件名和指纹分离。 |
| `LoreBookVersion` | 同一书内正整数、不可变；任何改变运行字段的修改都登记新版本，旧版本仍可读取。 |
| `LoreBookDefinition` | 书的 Owner、显示名、来源与版本目录；显示名可重复，不决定身份。 |
| `LoreEntryDefinition` | 归属精确 `(BookId, Version)` 的不可变规范条目；其 `LoreEntryId` 不由数组位置、触发词或正文推断。运行引用使用 `(BookId, Version, EntryId)`。 |
| `LoreBinding` | 某个完整 `WorldScope` 对固定书版本的显式启用、顺序、来源与修订；绑定目标仅为 WorldScope，不在 J1 增加 CharacterInstance 私有绑定。 |
| `LoreBindingRevision` | 每个 Scope 独立单调修订；仅显式绑定管理推进，与 World.revision、MemoryCollectionRevision 分离。 |
| `LoreActivationRequest/Result` | 会话受权投影、固定绑定快照和硬预算的只读输入／有界、可追溯、不授予权限的输出。 |
| `LoreFailure` | 固定失败码；授权、损坏、陈旧、预算等情况不以不可信正文作为错误消息。 |

导入链为 `Character Card / 独立 World Book → LoreIR / 受信导入输入 → 受信注册与规范化 → 不可变 LoreBookVersion → Owner 显式 WorldScope 绑定 → 激活结果`。`LoreIR` 保持交换格式，J 不改其保真合同，也不每次激活重新解释 `JsonValue.settings`。注册保留源文件指纹、源类型、原书／条目身份、原始顺序和不支持的扩展；**保留不等于执行**。相同 payload 可由同一受信调用方幂等复用既有版本，但同名或相同源文件指纹不足以推断资产相同。原 PNG、头像和完整原包归 SP-004L。

CharacterDefinition 的固定版本未来可声明零个或多个固定书版本的默认引用；当前 Definition 结构在 J0 不变。默认引用只是建议，必须由 Owner 在创建或配置 World 时显式落实为绑定。新书版本不会改写已有 Definition、CharacterInstance 或 World 的固定引用。World 可选择多个书、关闭绑定、保留旧版本或附加独立书。不存在每次查询动态追随“最新书”。

`unbind` 移除 World 的运行引用，`disable` 暂停但保留它，`retire version` 阻止新绑定而保留旧引用，`delete asset` 是另行审计的资产删除。被 World 引用的版本不得静默物理删除；J1 可先只实现解绑、禁用和版本登记，删除策略需另审。

## Scope、管理与会话围栏

绑定以 `(owner_id, soul_id, world_id, timeline_id)` 完整 Scope 定位，跨 World 默认不共享；同 Owner、同 Definition、同书版本、同触发文本都不例外。Soul World 与 Roleplay World 要分别显式绑定。多个书只在当前 World 的已启用绑定之间递归，绝不跨 World 递归。J1 的书资产默认实例本地，不跨 Life Engine 实例自动共享。

资产管理入口仅面向受信导入者或 Owner 显式管理上下文，可登记、查看、绑定、禁用、解绑和显式换版；角色 Session 只能激活，不能变更资产或绑定。J1 不把 Owner 管理视图当作角色视图，也不提供绕过绑定的全局条目查找。未来 `get_entry(entry_id)` 的会话接口同样必须校验当前 Scope、启用绑定与受权 viewer；资产管理接口另行区分。

Session 激活在同一稳定读取边界核对当前 Principal、WorldScope、OPEN SessionBinding、ACTIVE World、WriterEpoch、`runtime_id`、viewer 与安装 generation。SUSPENDED、ARCHIVED、TOMBSTONED World 拒绝普通激活；Owner 可为审计或删除维护读取旧绑定，但不能借此生成普通会话结果。Roleplay 的角色 viewer 与 Soul viewer 不互换。激活不推进 World.revision、Memory 修订或 LoreBindingRevision。

结果携带安装身份、generation、runtime_id、Scope、session_id、WriterEpoch、World.revision、LoreBindingRevision 和书版本集合；如果使用 Memory 投影，还携带其查询版本。K 在消费前重新核对这些值，拒绝 EXIT、SUSPEND、SWITCH、重启或恢复之后的迟到结果；结果本身不是授权票据。首版无需缓存或全文索引；以后若增加，缓存键仍需包含 Scope、viewer、绑定修订、书版本、输入指纹、Memory 投影版本及预算，且逐次重验授权。

## 激活输入与输出

`LoreActivationRequest` 包含完整 Scope、当前可信会话上下文、经 K/H 界定的近期对话文本投影、可选的**当前 viewer 已授权** `MemoryQueryResult`、固定绑定快照／预期修订和 `LoreBudget`。J 不读取宿主完整聊天库，不直接 `SELECT world_memories`，不接受 Owner 全量管理查询替代角色投影。Story 尚不存在；未来若参与触发，只能新增受权 Story 投影接口。未知外部书引用不得进入扫描集。

`LoreActivationResult` 包含 Scope 与快照身份、按固定顺序排列的 `ActivatedLoreEntry`、稳定诊断码和预算使用量。每个输出条目携带 `(BookId, Version, EntryId)`、原文、原因、已匹配字面触发词、激活轮次、规范优先级与顺序。原文明确标为不可信内容数据；结果不含工具权限、Story 或 Memory 写入、宿主命令。K 只消费受权的有界结果，并将其放在数据层；不能把 Lore 文本提升为 system authority。C 可把它作为设定上下文，不能当成已接受 StoryEvent。

## 触发、递归与确定性

J1 安全子集仅执行已规范化的字面主触发词、字面次触发词、常驻、显式禁用、大小写策略、简单 selective、优先级和有界递归。主触发为任一非空字面子串命中。`selective=true` 且有次触发时，需主词任一命中且次词任一命中；无次词按主词处理。默认 Unicode `casefold()`，显式大小写敏感则按原字符串；不做 NFKC/NFC、词界或语言分词。空词忽略并报告，不是 match-all。禁用优先于启用，冲突有诊断；声明 regex 或需执行扩展的条目保留但运行禁用，不回退成字面匹配。常驻不需要触发词，但受绑定、Scope 和预算约束。空正文可保真注册，运行时不输出，也不贡献递归文本。

激活从显式近期对话与可选受权 Memory 投影开始；每轮按稳定键处理当前候选。已实际纳入结果的条目正文才进入下一轮触发语料，允许跨当前 World 的已绑定书递归。每个精确 `(BookId, Version, EntryId)` 一次请求最多纳入一次；A→A、A→B→A 必然终止。排序键为 `(激活轮次升序、常驻先于触发、runtime_priority 降序、绑定顺序升序、runtime_order 升序、BookId、Version、EntryId)`。轮次优先保持递归因果和预算选择一致；每个新轮次重新使用同一规则。重复触发可命中多个条目，正文相同不去重；同一条目只输出一次，匹配词按固定序记录。

硬限制同时覆盖输入、绑定／条目／触发词数、单条正文、扫描工作量、轮次、输出条目数和输出 UTF-8 字节数。越界输入或无效授权直接失败；激活途中耗尽时，在稳定顺序边界停止扩展，返回已完整选定的结果、`budget_exhausted=true` 与固定诊断，不输出半条正文。预算是运行时字节／数量预算，不是模型 token 预算；真实 tokenizer 和 Prompt 裁剪归 K。候选上限见 [预算 ADR](adr/SP-004J-004-BUDGET-ORDERING-SAFETY.md)。相同受权输入、版本、预算与快照必须给出相同条目、顺序、截断与诊断，不依赖数据库行序、时钟或随机数。

## 安全与故障边界

卡片、World Book、Lore 正文、扩展字段和触发词都是不可信数据。即使内容写着“调用 shell”“读取 Soul 记忆”或伪造 `<system>`，也不创建 Principal、Bridge grant、工具能力、Memory 受众或 Story 接受。J 不执行正则、JavaScript、插件、宏、装饰器、网络请求、任意文件读取或宿主函数；不会把角色卡的 `system_prompt`、`post_history_instructions`、`description`、`scenario`、`first_mes`、其他 greetings 或 `mes_example` 转成 Lore 条目。

不可信或损坏持久结构、Scope 不匹配、版本丢失、陈旧绑定、无效会话与缺失删除控制须拒绝激活，不用空结果掩盖。unsupported optional semantic 可在注册时保留该条目并标记运行禁用，输出 `UNSUPPORTED_REGEX`／`UNSUPPORTED_EXTENSION` 等固定诊断；核心字段错误（如正文不是字符串）拒绝注册。空正文只保真不输出。诊断仅包含固定代码和安全身份，不回显恶意正文。威胁与验证矩阵详见四份 ADR。

## J1 持久化与迁移提案

J0 不修改数据库。若 J1 增加 canonical 表，必须升级 `DATA_SCHEMA`；**Schema 4 结构和签名保持冻结**。候选 Schema 5 签名为 `SP-004J-lore-runtime-v1`，仅供 J1 任务书复核，不在此预占实施。候选表为 `lore_books`、`lore_book_versions`、`lore_entries`、`lore_entry_triggers`、`lore_world_bindings`、`lore_binding_state`。规范书与绑定进入当前实例 `agents/<agent_id>/life.db`，不建 `lore.db`；原始 PNG／包可由 L 另行归档。J1 需给出 PK/FK/唯一约束、Scope 列、CAS、结构签名、索引、损坏拒绝与备份恢复测试。

迁移仍是 **Copy → Migrate → Validate → Atomic Activate**：复制当前 generation，迁移副本，验证旧生活数据、World、Memory 和 Lore，全部实例成功后一次激活 registry；失败保留旧 release／generation／备份。保留 Schema 2/3/4 的识别与 validator，不在活动库原地补表，也不把 legacy `store.memories`、未知角色卡字段或未注册 LoreIR 自动变成 Lore。恢复保留精确书版本、World 绑定和 Lore 修订，不自动换到最新版；跨 Schema 代码回退仍受原有门禁。版本退役与资产删除若影响恢复后的可用性，J1 必须单独制定控制策略。

## J1 验收矩阵与边界

| 组别 | 必须验证 |
| --- | --- |
| 导入／注册 | 内嵌 LoreIR、无 Lore、核心字段错误、regex／扩展保留并禁用、同 payload 幂等、同名不同书、外部引用未解析。 |
| 触发 | 字面命中／未命中、大小写两策略、多主词、次词命中／未命中、selective、常驻、禁用、空词、重复词／正文。 |
| 递归／排序 | A→B→C、A→A、A→B→A、跨书但同 World、轮次／条目／字节上限、相同优先级与顺序的完整 tie-break、重复运行一致。 |
| Scope／围栏 | 同 Definition 两 World、同书两 World、Soul／Roleplay、同 Owner 跨 World、不同 Owner、角色 viewer、Owner 管理、ID 猜测、EXIT／SUSPEND／SWITCH／重启／恢复／旧 WriterEpoch。 |
| Memory／安全 | 受权 Memory 可触发，其他角色私有／Owner 私有／隐藏／tombstone 不可触发；脚本与工具文本不执行、不授权，regex 不执行，URL 不获取，路径不打开。 |
| 持久化 | 重启保留绑定；恢复保留固定版本；新书版本不改旧绑定；Schema 迁移仅在副本中，旧 schema validator 保留。 |

J1 允许实现领域值对象、受信登记与规范化、不可变版本、WorldScope 绑定、Owner 管理、会话激活、安全字面触发、常驻／禁用、selective、有限递归、固定顺序、硬预算、诊断、持久化迁移与测试。J1 不实施 Story／Relationship、Prompt Runtime、Host Integration、Bridge、自动 Memory／Story 创建、LLM Lore 解释、embedding／向量库、regex、JavaScript／插件／宏、联网或任意文件导入、外部书自动解析、SillyTavern 全行为兼容、原 PNG 资产归档或 Definition 自动升级。独立审核后才能把这些提案转成 J1 实施任务。
