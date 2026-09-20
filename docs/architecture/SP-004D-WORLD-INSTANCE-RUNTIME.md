# SP-004D — 角色实例与世界会话运行基线

状态：IMPLEMENTED_CANDIDATE / PENDING_INDEPENDENT_REVIEW。

实施授权：仅限 SP-004D。合并授权：未授权。PR #3 合并授权：未授权。

基线：`f71d1b7f1718bc8be9916b1c09dde625aaa0d362`。

前置约束：[SP-004 架构](SP-004-PERSISTENT-WORLD-RUNTIME.md)、[SP-004A 领域模型](SP-004A-WORLD-DOMAIN-MODEL.md)、[SP-004G 导入 IR](SP-004G-CHARACTER-IMPORT-IR.md)。验证结果见 [SP-004D 质量门禁](../planning/SP-004D-QUALITY-GATES.md)。

## 范围与模块

本阶段把 CharacterDefinition 接到世界、实例和会话的内存应用操作。角色卡是定义来源，World/Timeline 才是运行隔离边界。没有把旧 RoleplaySession 或 card_id 重新作为领域根。

| 模块 | 职责 |
| --- | --- |
| [world_repository.py](../../runtime/life_engine/world_repository.py) | WorldSnapshot、结构化失败代码、WorldTransaction/WorldRepository 协议、内存事务实现 |
| [world_runtime.py](../../runtime/life_engine/world_runtime.py) | 显式登记、世界创建、实例化、进入/退出/暂停/恢复/切换、最小状态写入 |
| [test_world_runtime.py](../../tests/test_world_runtime.py) | 原创 V3 导入链、隔离、并发、回滚与策略验收 |

沿用扁平模块布局，既有 release_files 可收集新增模块。没有修改 SP-004A/G、生产入口、包版本、DATA_SCHEMA 或宿主。导入模块不会自动创建世界或启动调度。

## 聚合与身份

WorldSnapshot 是不可变聚合，包含一个 World、一个 WorldTimeline、CharacterInstance 元组和 SessionBinding 历史元组。它是仓储操作单位，不是数据库表设计。所有属性仍使用已有 SP-004A 值对象；不引入第二套身份、真假或生命周期系统。

本阶段沿用 SP-004A 的**每个世界最多一个开放会话**合同。因此 EXIT/SUSPEND 关闭的就是最后一个有效会话。不同世界可以各有自己的会话，epoch 和 revision 独立；没有全局“同 Soul 只能活动一个世界”的隐式限制。多人写入、并行时间线与分支不在本阶段。

新增身份默认使用 DomainId.new 生成 UUID4。可显式提供正确类型的 ID 以支持可信调用者分配身份，仓储拒绝重复世界、时间线、实例和会话 ID。卡名、文件名、宿主会话文本都不参与 ID 计算。

Soul 需要显式 register_soul；Definition 需要显式 register_definition。登记不是宿主认证，也不自动创建 Soul World。仓储按 DefinitionRef 保存不可变版本，同一个定义 ID 的不同版本必须属于同一 owner；同 ID/版本禁止覆盖。

## 创建与实例化

create_roleplay_world 要求仓储已有 Soul，且主体 owner 匹配。它显式创建 ROLEPLAY World 和唯一 Timeline，状态 CREATED、revision=0、writer_epoch=0，没有会话。失败时不发布任何对象。

instantiate 要求世界为 ROLEPLAY 且处于 CREATED 或 SUSPENDED，校验 expected_revision、timeline、已登记 DefinitionRef 与 owner。它创建独立 CharacterInstance，固定引用版本，推进 World revision，但不激活世界、不推进 epoch。

同一个 X@1 可以实例化为 A 世界的 A 实例和 B 世界的 B 实例。Values 是不可变字符串元组，调用者不能修改共享字典。update_character 只替换调用者明确提供的最小状态/关系值，不推断关系、物品、故事或记忆；修改 A 不影响 B。

登记 X@2 不改变已存在的 X@1 实例。仓储保存时也禁止改写既有实例的 scope/DefinitionRef，或移除既有实例；本阶段没有实例升级和删除入口。

## 应用接口

所有生命周期写入显式携带 world_id、timeline_id、expected_revision、writer_epoch。会话操作还需 session_id；实例写入需 character_id。不从 session_id 反推目标世界，不接受调用方提供的旧 World 对象作为当前状态。

| 操作 | 前置状态及行为 | 修订号 / 写入代数 |
| --- | --- | --- |
| enter | CREATED → ACTIVE，校验实例并建立新绑定 | revision +1，epoch +1 |
| exit | ACTIVE → SUSPENDED，关闭当前 Roleplay 绑定，保留世界/时间线/实例 | 两者均 +1 |
| suspend | ACTIVE → SUSPENDED，同时关闭绑定，不保留仍可写的旧会话 | 两者均 +1 |
| resume | SUSPENDED → ACTIVE，使用原世界/时间线及上次会话的实例，新建 SessionBinding | 两者均 +1 |
| switch_world | 同一事务关闭源绑定，并 ENTER 或 RESUME 目标世界 | 两个世界分别按生命周期推进 |
| update_character | 当前 ACTIVE、同主体/世界/时间线/角色且绑定仍开放，替换状态值 | revision +1，epoch 不变 |

RESUME 不自动选择新定义或新实例；若指定与上次会话不同的实例则拒绝。会话 ID 不可复用，即使旧会话已关闭。重复 ENTER、重复 EXIT、同世界 SWITCH、活动世界再实例化都不会静默成功。

调用结果是完整不可变快照；应使用其中的新 revision/epoch 发起后续操作。WorldTimeline 的逻辑时间和修订号本阶段不推进，不构造故事时间引擎。

## 可信快照与围栏

每次应用操作都在仓储事务中读取最新 WorldSnapshot 和已存储 SessionBinding。用户提交的 session_id、epoch、revision 只是校验输入，不能覆盖仓储值。

revision 用于比较写入版本；epoch 用于失效旧会话。写入既校验请求 epoch 与最新世界一致，也校验仓储中的绑定 epoch 一致；把旧会话请求的 epoch 手动改成最新值仍然无法绕过。旧 revision 即使 epoch 正确也拒绝。

参数要求使用准确的 Revision / WriterEpoch 类型；显式传 None 不被视为省略围栏。实例化属于未活动世界的管理操作，使用最新 revision；活动会话的写入必须同时验证 epoch。

这些检查依赖可信主体声明：Principal 必须由未来适配器完成认证后传入，不是接受一个自填 owner_id 就证明身份。应用服务检查 owner 和会话的完整 principal；仓储接口供受信任应用使用，不是可直接暴露的授权 API。

## 仓储协议与原子边界

WorldRepository.transaction 返回 WorldTransaction 上下文；事务提供领域读取、显式新增及 save_world(snapshot, expected_revision)。同一事务必须满足：

1. 读取可信一致快照；并发操作按可串行化语义处理。
2. save_world 比较当前 revision，新的 World revision 必须恰好加一。
3. 唯一身份、引用存在、owner、固定定义版本和会话身份约束在提交前成立。
4. 正常退出时全部提交；任意异常（包括提交失败）不得部分可见。
5. 两个世界的切换必须处于同一个事务，不能分别提交。

InMemoryWorldRepository 使用 RLock 串行化完整事务，并在独立字典副本上修改；正常退出才发布副本。值对象不可变，浅拷贝不会共享可变领域状态。事务句柄关闭后拒绝使用，嵌套事务明确拒绝，避免内层提交被外层旧副本覆盖。

ENTER 的状态变化与绑定先在局部构造，再作为聚合保存。即便绑定冲突或提交失败，原 CREATED 世界仍完整保留。SWITCH 允许源保存先进入事务副本，但只有目标保存与提交成功后才一起可见；目标修订冲突或第二次保存失败均回滚源与目标。

未来 SQLiteWorldRepository 可以实现同一协议：在一个数据库事务内读取/校验、比较修订号、保证唯一性与引用、提交两个世界的变更。应用服务不依赖内存字典或 RLock；测试用协议代理注入保存/提交失败。未来实现必须运行同一套事务合同测试，不能只提供名称相同但分步提交的方法。本阶段没有实现数据库级 CAS、跨进程锁或最终表结构。

## 失败语义

WorldRuntimeError.code 使用 FailureCode，而不是解析错误消息字符串。

| 固定代码 | 含义 |
| --- | --- |
| WorldNotFound / SoulNotFound | 指定世界 / Soul 不存在 |
| DefinitionNotFound / CharacterInstanceNotFound | 固定版本定义 / 实例不存在 |
| SessionNotFound | 指定会话不存在 |
| OwnerMismatch | 所有者不一致 |
| WorldMismatch / TimelineMismatch | 跨世界 / 跨时间线引用 |
| InvalidLifecycleTransition | 当前状态或世界策略不允许操作 |
| RevisionConflict | 旧修订号或保存时未正确推进 |
| StaleWriterEpoch | 旧写入代数或旧会话围栏 |
| SessionAlreadyClosed | 试图再次关闭已关闭会话 |
| SessionBindingConflict | 重复绑定、会话身份冲突、角色切换或主体不一致 |
| IdentityConflict / DefinitionVersionConflict | 重复身份 / 改写已固定的版本引用 |
| InvalidArgument | 基础值对象类型或约束不合法 |
| TransactionClosed / NestedTransaction | 事务句柄已关闭 / 不支持嵌套事务 |

应用校验保留上述分类；未预期的后端异常不被伪装成校验成功。当前没有自动重试、幂等命令表或外部消息投递；调用者不可因超时自行假定已提交。

## Soul、现实与桥接边界

SoulWorld 仍使用同一 World 模型。测试通过可信仓储显式装入一个已有 Soul World，验证应用服务绑定、关闭和重新绑定；这不是新增 Soul 初始化或后台生活服务。

Soul World 关闭普通会话仍保持 ACTIVE，只推进 revision/epoch；再次 ENTER 重新绑定。Roleplay 的 SUSPEND 不适用于 Soul World。Roleplay 创建/退出不会修改 Soul 对象、默认世界状态或 Soul 记忆。

导入定义保持 IMPORT / UNKNOWN / UNREVIEWED。新 Roleplay World、Timeline、Instance 及最小状态更新的来源为 OWNER_COMMAND / FICTIONAL / UNREVIEWED，表示用户命令构造的虚构世界数据，不代表观测事实或已接受正史。生命周期活动状态与 CanonStatus 无关，不建立事件日志。

同 Soul 不隐含跨世界共享。应用流程没有桥接入口或许可副作用；缺 grant 的 BridgePolicy 判定仍为 DENY。状态、关系及导入定义引用不会自动复制到 Soul 世界；没有实现完整 Bridge、Memory、Story、Lore 或 Prompt 运行时。

## 自动化验收

[测试](../../tests/test_world_runtime.py) 从原创合成 V3 经 parse_bytes → CharacterImportIR → project_definition 开始，随后登记、创建 A/B 两世界、实例化、ENTER、EXIT、RESUME。它断言：

- World/Timeline/CharacterInstance ID 及 X@1 引用不变。
- Session ID 改变，epoch/revision 推进，旧会话无法继续写。
- B 使用同一 X@1，但状态、关系、世界、时间线与会话独立。
- 两个线程提交同一 revision 时恰好一个成功。
- 目标绑定失败、切换第二次保存失败、ENTER 提交失败不会留下半完成状态。

测试不读取真实角色卡目录，也不启用真实宿主。既有测试使用的临时 SQLite 文件不属于生产存储迁移。

## PR #3 拆分吸收评估

只读对象为 `ab227f2179eeaa7ded662d612508a98ad5cdf04a` 的 rp_sessions.py 及 SP-004 基线中的适配评估；本阶段未修改、拣选或合并该分支。

| 旧能力 | 处置 | 新模型路径 |
| --- | --- | --- |
| 进入/退出/切换事务思想 | KEEP / ADAPT | 保留整体提交与迟到响应防护；读取最新 WorldSnapshot 并使用双围栏 |
| RoleplaySession 作为活动角色根 | REPLACE | World 为根；CharacterInstance 固定定义版本；SessionBinding 只表示一次可撤销访问 |
| 同 card_id 恢复旧记忆 | MIGRATE（后续） | 需要显式旧数据到 World/Timeline/Instance 的映射，不凭卡名推断同一故事 |
| expected_session 检查 | ADAPT | session_id + 存储绑定 + expected_revision + writer_epoch，不接受旧快照自证 |
| finish 自动生成摘要和 roleplay_meta | KEEP 设计经验 / ADAPT（后续） | 本阶段不吸收写记忆行为；未来显式现实/虚构来源与桥接授权 |
| Hermes/OpenClaw 上下文接线与测试 | KEEP / ADAPT（后续） | 未来转换认证主体、宿主能力和绑定引用，不把宿主路径作为世界身份 |
| schema 3 与卡片级记忆隔离 | MIGRATE（后续） | 不引入现有生产 schema 2；先审核持久仓储和数据映射 |

继续建议按授权拆分吸收。PR #3 的旧会话 ID 最多映射到 SessionBinding；不能把每次会话结束当成世界删除，也不能擅自将同卡历史合成一个 World。

## 限制与后续待决问题

内存仓储在同进程内保留世界；重建应用服务并复用仓储可以恢复。**进程退出会丢失内存，尚无跨进程或重启持久恢复能力。**这不改变会话关闭不删除世界的领域语义，真正持久化留给后续 SP-004E 授权。

当前每世界一个 Timeline/一个开放会话。查询和唯一性检查使用内存遍历，关闭会话历史持续增长；未来持久仓储需索引、容量和保留策略。没有租约、分布式锁、失效通知、命令幂等或自动重试。来源记录只表达当前对象来源，不是可重放的故事事件历史。

本阶段无范围偏离；最小 Values 更新仅服务隔离与写入验收，没有关系推演。未启动后续阶段、数据库迁移或宿主上线；完成 Draft PR 后停止等待独立审核。
