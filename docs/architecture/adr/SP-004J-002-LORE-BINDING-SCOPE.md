# ADR-SP-004J-002 — Lore 绑定、Scope 与观看身份

状态：**PROPOSED / PENDING_INDEPENDENT_REVIEW**。固定基线 `1a73f6e43caf54bd34ae810c9b58eddb25f6fb88`；总览见[SP-004J0 主文档](../SP-004J-LORE-RUNTIME.md)。

## 决策

J1 唯一运行绑定目标为完整 `WorldScope(owner_id, soul_id, world_id, timeline_id)`。`LoreBinding` 固定 `(Scope, BookId, BookVersion)`、启用状态、显式绑定顺序、来源和管理动作；同一 Scope 内同一精确版本只允许一个有效绑定。若需以新版替换旧版，Owner 显式执行 CAS 换版。CharacterDefinition 的默认书引用只是未来可供 Owner 选择的元数据，CharacterInstance 不拥有独立绑定；同一 Definition 的两个 World 各有独立绑定和修订。当前 World 模型只有一个 Timeline；Scope 仍包含 Timeline，以防未来把两个 Timeline 的候选混在一起。

每个 Scope 有独立 `LoreBindingRevision`，初始值、CAS 和递增由 J1 持久仓储定义。Owner 显式 bind、unbind、enable、disable、rebind 才推进它；普通激活是只读操作，不推进它、World.revision 或 MemoryCollectionRevision。绑定修改同时校验 Owner、World/Timeline 存在、书版本所属实例与 Owner、预期修订及精确 Scope。角色 Session 不得调用管理入口，不得让模型调整书版本或安全策略。受信导入权限不自动授予 World 管理权限。

Soul 与 Roleplay 默认完全分隔：相同 Owner、书版本、Definition、卡片来源或触发词都不建立跨 World 激活。显式在两个 World 各绑定同一规范资产是两次独立的 Owner 选择，查询和结果仍分别按 WorldScope 隔离。未来 F 如果允许跨 World 共享，必须有目标 World 明确绑定或经审计的派生资产，J 自身不桥接。跨书递归只在当前 Scope 的已启用绑定集合内运行。

## 会话校验与迟到结果

会话激活读取存储内最新 WorldSnapshot 与 SessionBinding，校验 Principal、Scope、World ACTIVE、Session OPEN、session viewer 对应当前 CharacterInstance 或 Soul、WriterEpoch、`runtime_id` 和当前 generation。Owner 管理上下文只用于显式管理或审计，不得拿 Owner 全量视图生成角色激活结果。SUSPENDED、ARCHIVED、TOMBSTONED World 禁止普通激活；Owner 可为解绑／删除及审计读取绑定，但不生成普通结果。直接按 EntryId 取会话条目也须检查当前绑定和 Scope，不能做全局 ID 探针。

## J1 实现状态

**IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**。每个 WorldScope 的 `lore_binding_state` 从零开始，由数据库 CAS 管理。`lore_world_bindings` 对完整 Scope 与 BookId 唯一；同书同时只能绑定一个版本，换版必须显式 `rebind`。管理操作在 `BEGIN IMMEDIATE` 中核对 Owner、Scope 和版本并写审计、幂等与修订；普通激活在稳定只读事务内先核对会话围栏，再读取该 Scope 的绑定。Owner 可查看其资产；Session 没有直接条目探测或资产列举入口。Definition 默认书引用未实施。

结果绑定安装身份、generation、runtime_id、完整 Scope、session_id、WriterEpoch、World.revision、LoreBindingRevision、书版本集合，以及可选 Memory 查询版本。未来 K 在把结果加入 Prompt 前重验这些值；EXIT、SUSPEND、SWITCH、重启和恢复使旧结果失效。会话身份检查应与取绑定和结果构造处于一致读取边界。结果的版本标签是陈旧检测材料，不是无需再校验的授权票据。

## Memory 与缓存

J 不直接查询 `world_memories`。可选 Memory 文本必须来自当前 viewer 的已授权 `MemoryQueryResult` 或等价投影；Owner 私有、其他角色私有、隐藏和 tombstone 内容不能进入角色语料。J1 默认无缓存；以后缓存须按 Scope、viewer、绑定修订、书版本、输入指纹、Memory 投影版本与预算分区，每次返回前仍验证当前授权。即使资产管理者能看整本书，也不能把管理视图转换成角色绕过 World 绑定的激活入口。

## 验证

J1 至少测试同 Definition 两 World、同书两 World、Soul/Roleplay、同 Owner 跨 World、不同 Owner、当前角色 viewer、Owner 管理、猜测 EntryId、旧 Session epoch、EXIT/SUSPEND/SWITCH、重启／恢复 generation 变更及旧绑定修订。任何失败不得返回其他 Scope 的书名或正文。
