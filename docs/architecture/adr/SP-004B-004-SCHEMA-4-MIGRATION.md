# SP-004B-004 — Schema 4 所有权、迁移与恢复安全

## 状态

SP-004B0 架构冻结候选 / PENDING_INDEPENDENT_REVIEW。固定 Base `4372b557dc8e3cc498098b6fe26e13df51ce802e`。

架构选择：未来 Memory persistence requires Schema 4。独立审核接受后才可称 ACCEPTED ARCHITECTURE DECISION；不等于实现完成或 B1 获实施授权。当前 DATA_SCHEMA before/after = 3，Signature 不变，Schema impact = NONE AT RUNTIME，Migration = NOT IMPLEMENTED。

## 背景

[world_schema.validate_schema](../../../runtime/life_engine/world_schema.py) 比较 sqlite_master 的规范化结构，包括列、约束、索引、触发器与额外对象，并检查版本/签名、完整性和外键。Schema 3 中偷偷加 Memory 表就会产生两个不同结构的“3”，破坏安装、备份、restore 与 rollback 的一致识别。

[SP-004E 迁移 ADR](SP-004E-002-SCHEMA-3-MIGRATION.md) 已证明 SQLite 单事务不足以覆盖数据库、release、文件系统和 registry 激活；B1 必须沿用同一 durable generation 体系，不能另起 Memory 数据库部署方案。

## 决策

### 一、冻结历史 Schema，明确未来版本

**Schema 3 frozen**：`DATA_SCHEMA = 3` 和 `SP-004E-world-runtime-v1` 的历史含义不变。本次不改 WORLD_DDL、常量、validator、Store、备份或迁移代码。

B1 引入持久 Memory 时必须使用 `DATA_SCHEMA = 4`，新 canonical 结构标识选定为 `SP-004B-world-memory-v1`；实现时 release/registry/backup/meta/validator/probe 必须一致，不能只改常量。Schema 4 的 `meta.world_schema` 使用新标识，验证历史 Schema 3 时仍要求旧标识；不能重解释旧值。Schema 4 包含已有业务与 World 持久结构加新的 Memory 结构，不是给旧 Schema 3 增加“可选表”。确切 DDL 必须由 B1 的实现/验证审查，不在 B0 伪造已经定稿的表定义。

所有 Memory 内容仍进入当前 generation 的 `agents/<agent_id>/life.db`，共用现有实例备份边界；无 world.db/memory.db。可评估逻辑表 world_memories、memory_audiences、memory_lineage、memory_collection_state 及操作/幂等控制记录，但名称不是本次 SQL 交付。

### 二、持久关系、唯一性与原数据保护

逻辑必须满足：Memory ID 全局不可复用；Scope 外键指向已登记 World/Timeline，并验证 Owner/Soul 一致；audience/subject 的实例引用必须同 Scope；同域 source memory 和 supersedes 有精确 ID/版本，不循环，单一后继；幂等 key 在 Scope/生产者/操作槽位内唯一；collection state 每 Scope 唯一。缺失/错误 kind/错误引用拒绝，不凭字符串关联。

定义引用不拥有 Memory 生命周期。删除卡片、替换定义或关闭会话不得级联删除世界经历。跨域 lineage 仅未来 F 可创建，不能借外键存在就授权查询；StoryEvent 引用要待 C 提供验证器，B1 不创建假事件表或接受任意 UUID。

原 Schema 3 `memories` 是生活业务表，没有 WorldScope。3 → 4 原样保留 meta/days/contacts/observations/memories/loops/photos 与全部 A/D/E 对象，不自动把 agent_id 推成 Owner/Soul/World，不自动建 Soul World，不让旧行进入新查询，也不双写。显式历史映射另审；它与 PR #3 旧 persona memory 表都不能作为 canonical MemoryRecord 来源捷径。

### 三、3 → 4 的整安装迁移

未来 B1 的唯一允许路径为 **Copy → Migrate → Validate → Atomic Activate**：

1. 新包识别 canonical Schema 3 的数字、签名与真实结构；未知结构、PR #3 式“3”、缺库、坏外键拒绝。Schema 4 已激活时识别并跳过重复迁移，不猜测未知未来版本。
2. 持有 management 锁，再按稳定顺序取得所有实例锁；停止/隔离现有工作进程，不能让只知旧路径的 writer 在激活后继续接收请求。
3. 对每实例创建不覆盖的 `before-schema-4-migration` 备份并验证 manifest/checksums/WAL/资产；保留可由 Schema 3 环境识别的原备份。
4. 安装并验证 Schema 4 release，包含新模块的 import probe；复制全部目标实例到唯一新 generation，禁止活动路径迁移。
5. 每副本事务中形成 Schema 4 结构，初始无新 Memory 时集合按既有 Scope 初始化为 0 或通过等价唯一初始化合同建立。逐项验证旧内容/身份/定义/Session/revision/epoch 保留；迁移不执行启动 recovery 冒充数据保留。
6. 核对新签名、完整结构、integrity/foreign_key、World 及 Memory 数据、设置/宿主绑定和资产引用；执行必要重定位与文件同步，确认安全控制域状态可用。
7. 保存旧 release/generation/registry 的整组回退点。全部实例及探针成功后，单次原子替换 registry 的 release、各 generation 和 data_schema；任一失败旧组合保持活动。
8. 新启动协调方发布运行代次并执行 E 的 OPEN Session 围栏。旧工作进程拒绝后续操作，新仓储才对新 generation 服务；保留所有旧 generation 和失败副本用于诊断，不自动删历史。

原子 registry 替换是激活提交点；崩溃后读取 registry/health 判定状态，不能根据响应超时假定尚未提交。重试使用新副本，不破坏旧数据。不得把所有实例逐个激活，造成同一 registry 混合 Schema。

B1 必须扩展当前只识别 2/3 的路径并保持显式兼容策略；Schema 2 安装先用既有 E 路径升级到 3，再走独立验证的 3 → 4，不在 B0 承诺未测试的直接 2 → 4。PR #3 的另一种 Schema 3 明确拒绝；历史救援归 L，不自动兼容。

### 四、备份与普通恢复

Schema 4 backup 完整包含 Memory 正文、来源、受众、lineage、集合修订、幂等和 tombstone；派生索引可重建，但 manifest 需明确其是否在备份中，不能把索引当唯一正文。SQLite backup API 保留 committed WAL，所有连接显式关闭，资产/checksum 和已有照片引用不丢。

Schema 4 默认 restore 仅接收经过验证的 Schema 4 备份；Schema 3 备份需显式副本迁移路径，不直接当 4 激活。恢复是复制到新 generation，版本/Scope/引用校验后再原子激活；须先完成下面的删除/撤销协调。清除旧 cache namespace，索引重新核验/重建，幂等记录与正文同快照恢复，OPEN Session 在新代次启动时失效。生活主动联系仍沿用暂停策略。

Owner 备份权限是管理权限，不是对任何角色授予全库读取；备份、旧 generation、失败副本和日志均是私有数据，不提供给匿名诊断或模型工具。

### 五、删除/撤销与备份时间回溯

冻结的最低安全承诺：**T2 已确认删除/撤销的记录，恢复 T1 备份后不得自动重新进入任何 Memory 查询、导出、摘要或 Prompt。** 只在被回滚数据库里保留 tombstone 无法保证这一点。

采用不随业务 generation 回滚的最小安全控制记录，位于同一 durable 安装管理域，不另建 Memory 内容库。记录安装身份、单调控制序号、Scope、目标 memory/source/grant 引用、被禁止重放的来源/幂等操作身份、动作及受信操作身份；不保存正文/原 prompt。B1 必须为 Memory 删除建立这项恢复门禁；Bridge 撤销动作与来源验证留给 F，B1 不伪造 grant 服务。具体文件/表布局和耐久协议在 B1 实现审查，逻辑提交语义如下：

- 删除先验证 Owner/Scope/expected memory revision，再持有管理与实例协调锁记录并同步删除意图；所有 Memory 读写都必须能观察该控制域，不能只持有绕过协调锁的裸 SQL 连接。
- 删除意图一经持久化就立即拒绝相关正文及依赖派生物被读取，即使后续内容库事务失败；恢复任务幂等完成 tombstone、集合 revision 和派生失效后标记完成。未完成意图不是“删除成功”，但绝不恢复可见。
- 首版对存在未完成删除意图的受影响集合暂停普通读写，由管理协调方收敛，避免其间 CAS 继续推进造成不明确结果。恢复任务按持久操作身份检查是否已经应用，已应用不重复加 revision；未应用才以当前受控集合版本完成一次事务。
- 普通 create/supersede 的 CAS 仍是同库事务；删除这类跨管理域操作按先拒绝再收敛的协议处理，不能声称跨文件 ACID。锁顺序为 management → instance → 数据库，禁止反向嵌套死锁。
- restore 激活前，把控制域当前水位与备份水位对账，重放更新的删除/撤销；安全控制记录不能被备份旧版本覆盖。新 generation 保存已应用水位，返回服务前确认没有未应用控制动作。
- 控制域缺失、损坏、水位无法证明连续、安装身份不匹配或灾难恢复只剩旧备份时，进入隔离维护状态；可保全字节，不得对角色/普通导出服务，不按“没有撤销”处理。恢复完整控制记录后才可激活。
- 源 Memory 删除及未来 grant 撤销沿 lineage 阻断派生摘要/副本；来源被 tombstone 不等于可以删除其所有后继判断依据。尚未清理的依赖由读路径检查控制状态拒绝，异步清理不提供可见性窗口。
- 恢复到创建前时，旧数据库可能连原 Memory ID/幂等回执也没有；因此写入路径还必须检查控制域里的来源/操作身份，拒绝通过同一来源重放生成新 ID 来绕过删除。无法辨认来源的自动重放拒绝；不靠正文相似度猜测已删数据。

这种控制记录防止应用恢复复活，不等于物理强删除。B1 不承诺已导出备份、旧 release/generation、操作系统快照、日志副本和外部模型中的字节全部消失；物理擦除/备份保留策略需独立管理授权与证据。删除界面不得写“永久抹除所有副本”。没有完整控制域的旧备份不能单独恢复为安全在线系统，这是选择的可用性代价。

### 六、回退边界

同 Schema 代码回退仍需兼容当前安全控制协议；不得回退到忽略删除控制记录的版本。跨 Schema 必须显式恢复旧 release + 旧 generation + registry schema 整组，先保存新状态和恢复时点说明，不能让旧代码读 Schema 4。

Schema 4 已有 Memory 写入后回退 3 不承诺无损：新 Memory 留在保留的新 generation，旧代码看不到它们，禁止偷偷降级到旧生活 memories。若安全控制域存在旧 release 无法执行的删除/撤销约束，普通整组回退必须拒绝；仅可保全为隔离离线副本，待具备同等门禁的明确恢复流程。不得为了可回退而绕过隐私约束。

### 七、Windows 与失败处理

沿用 E 的连接所有权：事务创建连接、commit/rollback、finally close；SQLite 上下文不代替 close。迁移/backup/health/验证连接全部显式释放，rename/replace 发生前关闭句柄；不能 skip、sleep、gc.collect 或吞 cleanup error。

锁/磁盘/探针/校验/registry 失败保持旧 active 组合；可保留失败副本诊断但不暴露正文。规范 JSON、aware UTC、类型化 ID 往返和结构拒绝继续适用；检测不是修复，不对未知库执行自动补表。

## 备选方案与明确拒绝

拒绝 Schema 3 原地扩展、另建独立 memory.db、直接采用 PR #3 表、活动库原地迁移、先激活部分实例、Schema 3 备份隐式按 4 打开，以及把回滚数据库里的 tombstone 当不可回溯删除账本。

仅提示“恢复可能复活已删 Memory”虽然较简单，但不满足本设计的默认读取安全目标，因此不作为普通在线恢复策略。保留严格隔离、拒绝缺控制域的激活，以明确的可用性代价换取不静默复活。

## 影响

未来 B1 除 Memory 表外，还必须验证删除控制与 durable 管理器的协调；没有这项门禁不能宣称支持安全 Memory delete/restore。新增控制域不是 B0 实现，不改变当前 Schema 3 恢复行为。它不要求先完成 Story 或 Bridge，但 F 上线前必须接入同一撤销水位合同。

## 验证要求

未来必须覆盖：真实 Schema 3 fixture 原数据不变、全新 4、多实例第二个失败、数据库提交后 registry 失败、重复 upgrade、旧签名与未知结构拒绝、WAL/资产备份、普通跨版本恢复拒绝、整组回退边界、连接释放；以及 T1 backup → T2 delete → T1 restore 不复活、删除意图持久后崩溃、控制域丢失/损坏/过期、源删除后摘要不可读、旧索引/缓存水位拒绝。B0 不声称这些未来测试已存在。

## 后续工作

B1 在独立任务授权后落实 Schema 4 结构、校验、迁移与上述最低恢复门禁。物理 DDL、控制记录编码和错误码需实现测试，但不能改变本 ADR 的版本、激活与不复活语义。相关：[主架构](../SP-004B-WORLD-MEMORY.md)、[并发与视图](SP-004B-003-REVISION-QUERY-CACHE.md)、[E 恢复围栏](SP-004E-001-RESTART-SESSION-RECOVERY.md)。
