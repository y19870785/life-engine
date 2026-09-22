# SP-004B-003 — 独立 Memory 修订、写入围栏与派生视图

## 状态

SP-004B0 架构冻结候选 / PENDING_INDEPENDENT_REVIEW；固定 Base `4372b557dc8e3cc498098b6fe26e13df51ce802e`。本文冻结逻辑原子性，不实现数据库接口、缓存或索引。

## 背景

当前 World.revision 管理整个 World 聚合，writer_epoch 与 runtime_id 失效旧会话/旧进程。若每条 Memory 都调用 save_world，会引入无必要的聚合冲突；若完全绕过 World 事务读取围栏，又会让 EXIT 与晚到 Memory 交错。必须分离内容并发域，同时保留共同的生命周期提交边界。

## 决策

### 一、版本职责与权威

| 版本 / 身份 | 比较对象及权威 | 何时改变 | 不承担什么 |
| --- | --- | --- | --- |
| World.revision | 已存储 World 聚合，现有 save_world CAS | 生命周期、实例最小状态等实际 World 修改 | 不因每条 Memory 内容写入而增加 |
| WriterEpoch | World 当前写入代次与已存储 SessionBinding | ENTER/EXIT/SUSPEND/RESUME/Switch/恢复等现有围栏动作 | 不是内容修订、幂等键或授权凭据 |
| runtime_id | 当前 life.db 的启动代次 | 可信协调方启动新运行代次 | 不是 Principal 认证，不能代替 Scope |
| MemoryCollectionRevision | 精确 owner/soul/world/timeline 集合的权威修订行 | 每个成功的可见 Memory 逻辑变更批次恰好 +1 | 不用 World revision 或时钟代替；不作为角色可见活动计数 |
| IndexGeneration | 集合内已完整发布的派生索引版本 | 完成重建并原子发布；附 indexed_memory_revision 和安全版本 | 不是内容真源，不推进 Memory revision |
| 安全控制版本 | 当前受众/授权、删除/撤销控制状态 | 权限、观看资格、删除或撤销变化 | 不可回滚为旧授权；不由请求方指定 |
| durable generation | 当前 registry 指向的数据代次 | 升级/restore/整组回退 | 防止还原后相同计数误命中旧缓存，不表示内容新旧 |

一个 WorldScope 一个 Memory collection；B1 保持现有单 Timeline，不创建 collection UUID。新集合从 0 开始。计数持久保存、非负且严格类型化。恢复旧备份可能回到旧数据计数，因此必须同时比较新的 durable generation/启动代次和不回溯安全版本，不能把计数当跨恢复永远递增的全局序列。

普通 create、批量 create、accept/reject/supersede、hide、audience 变化、删除等事务各推进受影响集合一次。无操作、拒绝、CAS 冲突、幂等重放不推进；单次重建索引不推进。派生摘要写成新 Memory 时推进。不同集合 revision 独立，SQLite 物理写锁仍可能串行，独立并发域不承诺 SQLite 并行 writer。

### 二、会话写入与 CAS 的原子边界

B1 的受信存储适配必须让 World/Timeline/Session/runtime_id 读取、Memory CAS、记录变更、依赖检查及幂等回执共享同一 life.db 事务。BEGIN IMMEDIATE 可延续 E，其他实现必须证明等价可串行化。不能先提交 World 围栏读取、再开独立事务写 Memory；不能在 Memory 事务内嵌套现有 WorldRepository.transaction。

逻辑步骤：

1. 认证调用方并绑定用途，确定完整 Scope，加载最新存储对象；拒绝外部传入旧快照作为权威。
2. 对会话写：World ACTIVE、Binding OPEN、完整 Principal/Scope/CharacterInstance 匹配、请求 epoch = Binding epoch = World epoch，runtime_id 为当前代次。
3. 验证来源、受众和接受政策；模型候选只能写自己有权的内容，禁止用维护标志绕过。
4. 核对幂等身份和载荷；若是已提交同一操作，仅在当前仍具备合法权限/围栏时返回最小回执，不重复写入。
5. 用请求 expected_memory_revision 比较权威 collection 修订，并在数据库条件写入中从 m 变为 m+1；影响对象不是 World 行。比较失败返回 Memory 修订冲突；不能先在 Python 比较再无条件覆盖。
6. 同事务写入所有新记录、替代/控制链接、幂等回执及必要失效标记。任何失败全部 rollback；提交后才发布成功与派生索引可用状态。

World 状态参与可写性检查，但普通 Memory append 不要求或增加 World expected_revision；若某种复合业务同时修改实例状态，必须同时满足两个 CAS 且同事务提交，不通过 Memory 接口隐式调用 update_character。当前 validate_write 的参数和行为不改；B1 实现专门的 Memory 校验适配复用其不变式，不假装当前函数已支持 Memory。

竞争例：A/B 都拿 m=5，A 提交变 6；B 即使等到 SQLite 锁，仍须以 5 做条件比较并失败。若 Memory 先取得事务并提交，随后 EXIT 关闭绑定，写入在线性顺序上有效；若 EXIT 先提交，Memory 检查旧绑定失败。内存快照中旧 OPEN 不构成证据。

Owner 删除/接受/维护是独立受权命令，检查 Owner 管理权与 Scope、collection revision、当前运行及安全状态，不需要伪造活动 Character Session，也不自动 RESUME。reindex 是只读真源/写派生物的维护任务，不推进剧情。来自过期会话的结果不得改标 Owner 命令重新提交。

### 三、幂等与提交不确定性

幂等身份至少为 Scope + 受信生产者/操作主体 + 来源消息/模型响应或事件身份 + 明确操作槽位。一次来源允许多条选择时槽位区分它们；来源 identity 由可信适配器提供，不采信模型自填。自动 Story 派生还需 event ID 和派生器版本，未来 C 开放时定义。

保存规范载荷指纹和结果回执。指纹包括内容、Scope、subject、audience、provenance、操作类型及目标/替代引用；不包括可变化的传输重试次数或 expected_memory_revision。相同键同载荷只返回原结果，相同键不同载荷拒绝为幂等冲突，不能覆盖旧记录。正文相同但来源不同不是重复判据。

会话 ID/epoch 属于请求围栏，不因重放而换成当前会话；原来源会话仍保留在 provenance 中。旧会话即使持有成功 key 也不能绕过校验取正文。调用方在 commit 后失联可用同一身份/键重试；如果原会话已关闭，可由 Owner 管理用途核对回执，不自动在新会话补写。即便原记录已删除，回执最多报告非正文结果，不能复活内容。

崩溃前未提交：记录、计数、回执都不存在，可重试。提交后崩溃：三者全部存在。并发同 key 由事务和唯一性约束保证唯一；CAS 冲突或 StorageBusy 不自动换 key。锁超时是存储忙，不伪装成 CAS 冲突；损坏/SchemaMismatch 也不伪装 Memory 不存在。

restore 与普通进程重启不同：旧备份可能不含之后的幂等回执。旧会话重放必须因新代次拒绝，删除控制域还要阻断已删来源/操作重新生成记录；不能宣称只恢复数据库回执就能对所有外部历史永久去重。未来 H 的重连对账必须显式处理恢复时点，不自动重放无法核实来源的旧消息。

### 四、查询一致性、分页与返回时检查

授权在候选生成前完成；在一致读快照中取 collection revision、安全版本及授权集合，随后才排名。B1 最低查询采用有界的同域真源扫描/文本匹配与确定性排序，最终以稳定 memory_id 打破并列，不能依赖随机 SQL 顺序。

普通结果包含授权投影、reality/canon、必要来源与不透明游标，不向角色暴露原始全集合修订或未授权计数。分页游标绑定 Scope/Principal/观看身份/用途/过滤/排序及版本；篡改或版本失效须重新查询，不继续拼接不同版本。Owner 一致导出可以在受控内部读取版本信息。

返回前核对当前安全控制版本、会话有效性、durable/runtime 代次与 Memory revision；变化则丢弃结果并有界重试或返回需刷新。由此不将权限撤销前读出的结果在撤销后当作当前结果输出；已交付外部的字节无法撤回。分页和流式每批都执行检查，完整导出需要固定快照/版本，不能混合更新前后正文。

### 五、派生索引与缓存

Memory canonical record/控制状态才是真源。FTS、keyword、summary index、embedding/vector 都可重建，丢失不等于 Memory 丢失。索引条目保留 Scope、audience、源 ID/version 及安全版本；构造、候选生成、排名统计都在授权分区内，不能全库检索后过滤。

重建从已验证版本 m 读取 canonical 数据，在不可见位置生成 g+1；发布前比较当前 m 和安全版本。发生修改或撤销则丢弃/重建，不发布旧索引。查询只使用 indexed_memory_revision 与当前所需修订一致且安全版本有效的完整索引；否则走相同授权的 canonical 查询或明确不可用，不把过期索引当正确结果。源隐藏/删除/撤销须同步阻断使用，异步物理清理不能成为泄漏窗口。

逻辑 cache namespace 至少包含：

```text
安装身份 + durable generation + runtime_id
+ owner_id + soul_id + world_id + timeline_id
+ principal_id + 单一观看身份 + 用途
+ audience 授权摘要 + 政策/撤销/删除安全版本
+ MemoryCollectionRevision + IndexGeneration
+ 规范 query + limit + 排序 + 过滤 + 返回字段 + 分页游标
```

以上由可信服务生成，不接受模型提供缓存键。命中不能省略授权；负缓存也受同一 namespace 和版本规则约束。不要将原始查询文本/内容哈希写入公开日志。B1 可以完全不实现缓存，不为证明架构而引入缓存系统。

重启默认丢弃进程缓存和未完成索引；已发布索引须重新验证版本。新 runtime_id 在所有工作仓储显式加入，不要因创建一个 Memory Repository 而触发第二次 World recovery。持久 Memory revision、幂等和正文不随重启重置，旧 Session 继续遵守 E 的围栏。

## 备选方案

| 方案 | 判断 |
| --- | --- |
| 每条 Memory 推进 World.revision | 拒绝；把独立内容变化绑到聚合 CAS，徒增冲突 |
| 用 WriterEpoch 作为 Memory revision | 拒绝；一轮会话内多次内容更新无法区分 |
| 每个角色独立集合，无统一 Scope 修订 | 不采用首版；共享受众和删除依赖难以一致查询 |
| 查询后异步过滤撤销 | 拒绝；产生实质泄漏窗口 |
| 用全库向量结果再裁剪 | 拒绝；候选、排名统计和缓存已经跨域 |

## 影响与拒绝项

集合级 Memory CAS 首版仍会让同 Timeline 高并发写入冲突，这是明确的保守选择；以后分片须新 ADR。数据库序列化简化与 World 生命周期的竞争证明，但不代表无锁或高吞吐。禁止事务外旧快照自证、后台任务伪装会话、索引升级 canon、重试改 key 和 restore 后计数碰撞复用缓存。

## 验证要求

未来 B1 至少覆盖两独立连接同 m 仅一成功、不同 Scope 不产生逻辑 CAS 冲突、Memory 写入不推进 World revision、退出前后两种串行顺序、重启旧 Repository 拒绝、同 key 同/异载荷、commit 前后故障、替代原子性、索引构建时删除、缓存命中时撤销、分页安全版本变化及 restore 后旧缓存拒绝。现有 [SQLite 测试](../../../tests/test_world_sqlite_repository.py) 只验证 World CAS，不能充当 Memory CAS 验收。

## 后续工作

B1 定义专门 Memory 事务协议与值类型；具体 SQL/索引布局需故障与竞争测试验证，不在 B0 固定 DDL。相关：[主架构](../SP-004B-WORLD-MEMORY.md)、[访问隔离](SP-004B-002-SCOPE-AUDIENCE-ISOLATION.md)、[恢复合同](SP-004B-004-SCHEMA-4-MIGRATION.md)。

## B1 实现状态

IMPLEMENTED / PENDING_INDEPENDENT_REVIEW。固定 Base 为 `4d628ca1b7b68609cd6fcf95e835c25ffa638c6b`。本节追加实施证据，不重写上述 B0 历史决策。

[SQLiteMemoryRepository](../../../runtime/life_engine/memory_sqlite_repository.py) 附着既有 runtime_id；独立集合 CAS、记录和幂等回执同事务。管理锁、实例锁、控制库与 life.db 按序持有，查询构造投影期间不能插入生命周期写入或删除。首版不实现派生索引或缓存；角色查询结果不含全集合 revision。验收见 [仓储测试](../../../tests/test_memory_sqlite_repository.py)。
