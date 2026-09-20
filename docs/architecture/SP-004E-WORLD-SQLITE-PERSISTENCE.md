# SP-004E — 世界运行时 SQLite 持久化

状态：PENDING_INDEPENDENT_REVIEW。实施范围仅限 SP-004E；不转 Ready、不合并。

授权基线：`399b084a8a5dfd76eb2aa3d0aac9ebbaafd35260`。

## Schema 所有权

`DATA_SCHEMA = 3` 指 **SP-004E canonical Schema 3**。

**Schema 版本号相同不代表 Schema 兼容。**

数据库必须同时通过 `meta.schema_version`、`meta.world_schema = SP-004E-world-runtime-v1`、实际表/列/约束/索引/触发器结构比较、`quick_check`、`foreign_key_check` 与领域对象重建检查。结构比较以当前 SQLite 编译的预期建表语句为参照，只规范化空白，不忽略索引谓词、约束或额外结构。拒绝未知扩展和旧 PR #3 结构，不猜测、不修复。

## 存储边界

数据仍位于当前 generation 的 `agents/<agent_id>/life.db`，没有第二个数据库或部署体系。`Store` 继续负责生活业务；`SQLiteWorldRepository` 实现已有 `WorldRepository`。`WorldRuntime` 生命周期业务没有增加 SQLite 分支。

新建文件由 `Store` 一次事务创建完整 Schema 3。既有文件先验证，禁止 `CREATE TABLE IF NOT EXISTS` 掩盖缺表。SQLiteWorldRepository 只打开已有文件，不能自动初始化或迁移。

| 表 | 持久合同 |
| --- | --- |
| souls | Soul、owner、唯一 Soul World 注册信息 |
| character_definitions | definition_id/version 联合主键、owner、name、traits、provenance |
| worlds | World ID、owner、Soul、kind/status、revision、writer_epoch、provenance |
| world_timelines | Timeline ID、唯一 World 引用、revision、logical_tick、provenance |
| character_instances | 实例 ID、World/Timeline、固定 DefinitionRef、state、relationships、provenance、position |
| session_bindings | 全局 Session ID、Principal/owner、World/Timeline/实例、epoch、OPEN/CLOSED、position |

原 `meta/days/contacts/observations/memories/loops/photos` 表不重建、不删行。SessionBinding 领域模型目前没有 provenance 字段，因此不凭空增加来源语义。

## 序列化与约束

核心身份与并发信息保存在可查询列中。附属 Values 和 Provenance 使用 UTF-8、稳定键排序的 JSON，禁止 pickle、eval 或 repr。Values 保留 tuple 中的原顺序；时间统一写为 UTC ISO 8601，读取恢复 aware datetime。DomainId 使用带 kind 的规范 UUID4 字符串，重建时再次校验。

快照按持久 `position` 排序，保留 CharacterInstance 和 SessionBinding tuple 顺序，包括最后一次会话身份。单 World 读取按索引取该 World 的子对象，不扫描其他世界历史。启动和健康检查才执行全库领域验证。

数据库使用主键、NOT NULL、复合外键、唯一约束及枚举/非负计数检查。World 的 owner 必须属于其 Soul，Session owner 必须属于其 World，实例必须引用已登记的 Definition 版本。`one_open_session_per_world` 是 `status='open'` 的部分唯一索引。触发器禁止替换实例的 DefinitionRef 或重新开放 CLOSED Session。

按 World、CharacterInstance、Session ID 和 Definition/version 的查询均有主键、联合唯一索引或显式索引支持。完整 Session 历史保留，未来另行设计保留期限和归档，本阶段不清理。

## 事务与 CAS

每次 `transaction()` 创建连接、启用 `PRAGMA foreign_keys=ON`、执行 `BEGIN IMMEDIATE`，成功 commit，任何异常 rollback，最终 close。没有跨线程共享的全局连接；同线程嵌套事务拒绝，结束后的事务对象拒绝使用。

`save_world` 在共同身份/历史检查后执行 `UPDATE worlds ... WHERE world_id=? AND revision=?`，检查影响行数必须为 1，否则 `RevisionConflict`。Python 预检查不替代 SQL 条件。Switch 的两次保存共用一个数据库事务，写 A 后写 B 失败不会留下半完成结果。

锁等待默认 5 秒，可在大于 0、不超过 60 秒范围内配置；超时返回 `StorageBusy`。文件或 SQL 基础设施错误返回 `PersistenceFailure`，损坏数据返回 `StorageCorrupt`，结构或版本不匹配返回 `SchemaMismatch`，运行代次过期返回 `RecoveryRequired`。

## 启动和恢复

```python
repository = SQLiteWorldRepository(path)
runtime = WorldRuntime(repository)
# 同一运行代次内的第二个连接显式加入，而不是再次执行启动。
worker_repository = SQLiteWorldRepository(path, runtime_id=repository.runtime_id)
```

默认构造代表一次明确的运行启动，原子关闭旧 OPEN Session、推进受影响 World revision/epoch 并发布新的运行代次。Roleplay 转为 SUSPENDED，Soul 保持 ACTIVE。已有 CLOSED 历史与没有 OPEN Session 的 World 完全保留。每次事务比较运行代次，旧 Repository 也被阻断。

`runtime_id` 是可信调用方传递的代次标识，不是用户认证凭据，也不提供分布式进程存活检测。未来宿主必须由单一启动协调方创建新代次；连接池/工作进程只显式加入该代次。详情见[重启恢复 ADR](adr/SP-004E-001-RESTART-SESSION-RECOVERY.md)。

## 部署、备份与回退

升级器持有 management 及所有实例锁，先为全部实例建立并验证 `before-schema-3-migration` 备份，再复制到新 generation 迁移。所有实例及新 release 验证通过才一次切换 registry 的 release、generation、data_schema。失败副本保留用于诊断，旧 generation 和旧 release 不删除。

SQLite backup API 包含已提交 WAL；manifest、checksums 与照片资产沿用 durable 机制。Schema 2 备份保持标记 2，并经过原版 Schema 2 环境验证。Schema 3 restore 不接受 Schema 2 备份；不会隐式转换。

代码回退只允许相同 Schema；跨 Schema 使用升级记录中的旧 release、旧 generation、旧 registry 整组回退。详细操作及限制见[迁移 ADR](adr/SP-004E-002-SCHEMA-3-MIGRATION.md)。

## PR #3 持久化兼容性评估

只读研究 Head：`ab227f2179eeaa7ded662d612508a98ad5cdf04a`。未 cherry-pick，也未导入其数据库实现。

| 项目 | 结论 | 处理 |
| --- | --- | --- |
| Schema migration | ADAPT | 采纳副本迁移的经验；重新定义 World 结构、结构签名和整安装激活验收 |
| backup strategy | KEEP | 保留 main 已有 SQLite backup API、WAL、资产复制和 checksums，补充按实际 Schema 验证 |
| Windows SQLite cleanup | ADAPT | PR #3 已使用显式 closing；在本任务涉及的既有 SQLite 测试中适配相同资源所有权原则 |
| RoleplaySession tables | REPLACE | card_id/整数 session 模型没有 World/Timeline/固定实例/revision/epoch，不能沿用 |
| card storage | MIGRATE | 将可复用的导入语义投影为已版本化 Definition；不迁移 PR #3 数据库，也不持久化完整 IR/头像 |
| memory isolation | REPLACE | 不引入其 memories scope/card_id/session_id 改表；现有生活 memories 原样保留，未来 Memory Runtime 单独设计 |
| host integration | REPLACE | 本阶段不采用其自动角色命令、Prompt 或宿主钩子；后续宿主集成需另行授权 |

PR #3 的 Schema 3 会重建 memories 并增加 roleplay_cards、roleplay_sessions 等表，其版本识别主要依赖数字。SP-004E 不接收这一结构，即使 meta 写着 3 也会拒绝。

## 验收与限制

[质量门禁](../planning/SP-004E-QUALITY-GATES.md)列出合同复用、竞争、故障注入、真实旧安装升级、备份恢复和跨平台证据。

本阶段不接入 Engine、Hermes、OpenClaw，不启动 Story/Memory/Lore 或完整 Bridge。没有读取真实角色卡目录。CharacterDefinition 恢复不依赖原 PNG/JSON，全部测试使用原创合成数据。

严格结构验证意味着手工修改结构的数据库会被拒绝。跨 Schema 回退会回到升级前业务状态，升级后的写入保留在新 generation，不能自动向 Schema 2 转换。启动/健康检查扫描完整 World 数据，保留全部会话导致检查成本随历史增长；归档和大型性能优化留待后续阶段。
