# ADR-SP-004J-001 — Lore 资产与版本身份

状态：**PROPOSED / PENDING_INDEPENDENT_REVIEW**。固定基线 `1a73f6e43caf54bd34ae810c9b58eddb25f6fb88`；只冻结 J1 合同，不改现有 CharacterDefinition、Schema 或 Runtime。总览见[SP-004J0 主文档](../SP-004J-LORE-RUNTIME.md)。

## 决策

每个 Life Engine 实例内的 `LoreBookId` 是登记时生成的类型化 UUID，作为长期资产身份；`LoreBookVersion` 是该书正整数、不可变版本。显示名、角色名、文件名、`source_fingerprint` 都不是 BookId，允许同名不同书。J1 的受信登记接口必须明确选用“登记新书”或“在已有 BookId 下建新版”；不能凭同名、同卡、同指纹猜测。改变任何会影响激活的正文、触发、优先级、启停、默认策略或条目集合，都创建新版本，不更新已发布版本的字节。

`LoreEntryId` 是登记产生的类型化 UUID。规范条目的运行身份是 `(BookId, Version, EntryId)`，其 `BookId/Version` 必须与父版本一致。J1 可在显式新版映射中为未变更的逻辑条目保留 EntryId，但不得从数组下标、触发词、正文或源条目名称重建它；一旦身份映射有歧义，生成新 ID 并记录来源。即使两个条目的正文或触发词相同，也不能合并。版本中的原始顺序单独记录，不能充当身份。

受信注册从当前 [LoreIR](../../../runtime/life_engine/import_ir.py) 或未来独立书导入器接受有界、已校验输入，产生规范支持字段与保真附属字段。`LoreIR.source_fingerprint` 指原始文件字节；`CharacterImportIR.payload_fingerprint` 指规范 JSON 载荷。两者都可进入 provenance 或幂等登记键，不等于 LoreBookId，也不能授权激活。同一受信调用方对同一 payload、同一登记意图可返回已有精确版本；若选择为既有书建新版，即使 payload 来自同名文件也必须明确给出 BookId 与预期版本。源类型、原书／条目身份、原顺序、源指纹及不支持设置要保留，未知设置不可执行。

`CharacterDefinition` 的某一固定版本未来可声明固定 `(BookId, Version)` 默认引用，引用是元数据，**不是运行绑定**。现有 Definition 不在 J0 改动；J1 如需扩展持久 Definition 合同，须纳入 Schema 迁移设计。卡内 `character_book` 经受信登记后可形成该引用，但不能让“导入成功”直接启用 World Lore。新书版本不会改变已有 Definition 版本、CharacterInstance 的 DefinitionRef 或 World 的 LoreBinding。完整 Definition 升级与原包归档归 SP-004L。

## 注册错误与生命周期

核心字段格式错误（例如条目正文不是字符串）拒绝该书版本注册，保留可核查错误码，不写入半本书。可选语义超出安全子集时，保留原始数据和该条目，但设为运行禁用并给 `UNSUPPORTED_REGEX`／`UNSUPPORTED_EXTENSION` 等诊断；不得静默降级为字面匹配。显式 `disable` 压过 `enabled`，记录冲突诊断。空正文可登记保真，运行时不输出。

`unbind` 仅改变某 World 的引用；`disable` 保留绑定但不参与激活；`retire version` 不接受新绑定，已存在引用与审计仍可读取；`delete asset` 需单独审计和引用检查。被绑定的版本不得静默物理删除。J1 至少实现明确换版／解绑与旧版本保留，物理删除可后续单独设计。恢复旧备份时不得自动升级到最新书版本。

## J1 实现状态

**IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**。书与条目使用独立类型化 `DomainId`；新书和显式新版是两种不同登记意图。新版在同一事务以预期 `current_version` 条件更新，已发布版本、条目及触发词由数据库触发器阻止更新或删除。幂等指纹在生成 EntryId 前覆盖规范字段、来源线索、操作意图和来源位置；来源位置仅用于核对操作，不替代运行身份。J1 暂不实现退役、物理删除及自动跨版本 EntryId 映射，因此默认新版生成新 EntryId。恢复旧 Schema 5 备份可回退后来登记的 Lore 版本和绑定，不具有 Memory 删除控制的不可复活语义。

## 选择理由与验证

此模型让一个 Definition 在多个 World 中被独立使用，让用户明确固定旧设定版本，同时仍保留原卡的来源证据。J1 应测试：同名不同书、同书新版本、新版本不影响旧 World、重复 payload 幂等、源指纹相同但登记意图不同、源顺序改变产生可审计新版、重复正文的不同 EntryId、重启／恢复后精确版本不变。原 PNG／头像／完整包归 L，规范资产默认进入实例自己的 `life.db`，不建独立 `lore.db`。
