# SP-004A — World Domain Model & Core Contracts

Status: IMPLEMENTED_CANDIDATE / PENDING_INDEPENDENT_REVIEW

Implementation Authorization: AUTHORIZED — LIMITED TO SP-004A

Merge Authorization: NOT AUTHORIZED. PR #3 Merge Authorization: NOT AUTHORIZED.

Baseline: `f040a8241e3b6ebc34f4025c6f5211829a0d040c`。日期：2026-09-16。Owner: Codex；Independent Reviewer: ChatGPT / 小雪。

前置依据：[SP-004 RFC](SP-004-PERSISTENT-WORLD-RUNTIME.md)、[Gap Analysis](SP-004-GAP-ANALYSIS.md)、[实施计划](../planning/SP-004-IMPLEMENTATION-PLAN.md)、[基线检查](../planning/SP-004-QUALITY-GATES.md)。SP-004 文档保留原提交时的状态文字；其合并授权不等于本实现候选已通过独立审核。

## Scope and Entry Points

新增三个纯 Python 模块，不改变任何既有生产入口：

- [domain.py](../../runtime/life_engine/domain.py)：不可变领域值、身份、归属、来源、世界和角色引用。
- [domain_lifecycle.py](../../runtime/life_engine/domain_lifecycle.py)：纯状态转换、绑定与写入前置条件。
- [domain_policy.py](../../runtime/life_engine/domain_policy.py)：宿主能力及桥接许可的纯资格判断。

沿用当前 release 收集器只收集包内 `*.py` 的扁平结构，无需改变部署逻辑或包版本。使用 `from life_engine.domain import World` 等显式导入；不在包初始化时创建对象、连接数据库或开启运行器。

本阶段没有 repository 实现、数据库写入、事件日志、Story Engine、WorldMemory 服务、Importer 重构、桥接传输、调度器或宿主部署。`create_world` 名称表示对 CREATE 命令的纯求值，只有显式调用才返回内存对象，不自动登记或激活世界。

## Canonical Model

| Concept | 本阶段合同 | 真正的持久化/服务责任 |
| --- | --- | --- |
| Owner / Principal | Owner 是资源所有者；Principal 是上游已认证主体的值声明，二者有不同 ID | 未来 Adapter 鉴权，不能把用户填写的对象视为凭据 |
| Soul | owner、soul ID 与默认 soul_world_id；不复制或改写 SOUL 文件 | 后续目录/存储维护唯一性与身份引用 |
| World / WorldKind | Soul 与 Roleplay 共用 World，含 ownership、provenance、status、revision、epoch | 无生产 World 创建/注册 |
| WorldScope | owner/soul/world/timeline 完整引用，禁止缺少 ID 的默认范围 | 后续持久层按 scope 检索，不能全库回退 |
| WorldTimeline | scoped revision、logical_tick、provenance | 不推进时间、不建分支 |
| WorldState | scope、projection revision、provenance、不可变 Values | 不写库、不接受或归并剧情 |
| CharacterDefinition | DefinitionRef（ID + 固定版本）、名称、traits、provenance | 不定义外部卡片或最终 IR 全部字段 |
| CharacterInstance | 独立 ID、world/timeline scope、固定 DefinitionRef、provenance、独立 state/relationships | 只是最小状态样本，不是关系/故事引擎 |
| SessionBinding | session/principal/scope/character/epoch/status | 无会话注册中心、lease 或多人协作服务 |

`Values` 是严格的 tuple-of-string-pairs；可共享不可变空值，但没有共享的 mutable dict/list。更完整的角色与关系结构留给 D/C，不通过无边界的 `dict[str, Any]` 把外部格式塞入核心。

WorldScope、DefinitionRef、Values、Owner/Principal ID、Grant/Event ID、CloseReason 是为明确归属、版本、不可变性及未来来源引用而增加的最小 Value Object；没有把它们扩展成新服务。

## Stable IDs and Versions

DomainId 为带 kind 的 UUID4：`world:<uuid>` 等。所有七项必需身份，以及 principal/event/grant，均有独立类型标签。构造和字段校验拒绝错误 kind、非 UUID4、路径、卡名；字符串 parse/format 提供最小的稳定往返合同。

ID 生成不接收显示名、宿主路径或外部文件 ID。旧 card_id 与新 ID 的映射属于后续迁移；名称相同不表示身份相同。未来存储仍必须检查全局唯一性和引用存在性，本阶段随机生成与值校验不能替代唯一索引。

Revision、WriterEpoch、DefinitionVersion 是三个不同的不可变数值类型，拒绝 bool、负值、字符串混用。DefinitionVersion 从 1 开始；版本升级构造新定义值，不修改旧实例的引用。`validate_definition` 同时校验 definition ID、version 与 owner。

没有定稿完整 JSON/数据库 Schema，也没有承诺 dataclasses.asdict 的输出为永久 wire format。后续 IR/持久层应带自己的 schema version 并显式映射这些值。

## SoulWorld Decision

采用 **SoulWorld IS-A World**，详见 [ADR-001](adr/SP-004A-001-SOUL-WORLD-AS-WORLD.md)。

CREATE 必须匹配 Soul 预留的默认 world ID，Roleplay 不得占用它。Soul World 不允许普通 SUSPEND/EXIT/ARCHIVE/DELETE 生命周期命令；关闭它的宿主 Session 仅失效该代绑定，World 保持 ACTIVE。Roleplay 最后参与 Session 退出使 World 进入 SUSPENDED，保留 ID 与数据。账户删除、灾难恢复等操作不属于这个合同。

统一 World 不代表共用记忆或相同 reality。WorldKind 不能将模拟状态提升为现实事实；Soul 内可以存在 simulated life state、用户陈述和虚构体验。

## Reality and Canon

详见 [ADR-002](adr/SP-004A-002-REALITY-AND-CANON.md)。

| 信息 | RealityStatus | CanonStatus |
| --- | --- | --- |
| 经可信观测的数据 | OBSERVED_REAL_WORLD_FACT | 仍需明确接受流程；默认 CANDIDATE |
| 用户称“我去了上海” | USER_CLAIMED | CANDIDATE 或显式 ACCEPTED，不变成观测事实 |
| Agent 推断用户出行 | AGENT_INFERRED | 默认 CANDIDATE |
| 模拟生活日程 | SIMULATED_LIFE_STATE | 是否接受与真假分类分开 |
| 已确认的角色事件 | FICTIONAL | ACCEPTED |
| 模型刚生成“发生地震” | FICTIONAL | CANDIDATE |
| 一起玩过虚构故事 | FICTIONAL_SHARED_EXPERIENCE | 明确接受后可为 ACCEPTED，仍非现实剧情事实 |
| 无来源旧数据 | UNKNOWN / LEGACY_UNREVIEWED | UNREVIEWED 可显式保留 |

候选事件属于 CanonStatus 轴，不伪造为一种 RealityStatus。Provenance 默认 CANDIDATE，构造 World/State/Definition 不自动接受。示例中显式构造 ACCEPTED 仅表示调用方提供了该状态；本阶段没有 canon 接受权限服务，不能将直接构造 dataclass 当作认证或批准过程。

合同拒绝 USER_REPORT/MODEL/SIMULATION 声称 OBSERVED_REAL_WORLD_FACT；可信 OBSERVATION 和保留观测来源的 BRIDGE 可以表达该状态，但标签本身不验证外部事实，未来桥接仍须查原始 lineage 和 grant。没有“is_real”布尔值或模型自动推广路径。

## Provenance

Provenance 强制 source_type、非空 source_id、带时区 created_at、actor/principal、reality_status 与 canon_status。可携带 source_world_id、source_timeline_id、source_session_id、source_event_id；timeline 必须带 world，session/event 必须带 world+timeline。

World、WorldTimeline、WorldState、CharacterDefinition、CharacterInstance 均携带 provenance，且与资源 owner 一致。Source ID 可指向外部内容/宿主事件用于溯源，不能替代领域 ID。跨 World 的来源引用可以表示未来桥接，但不自动授权读取；外键存在性、Bridge 来源链、签名和撤销检查属于后续服务。

这些字段能解释信息来自哪个渠道、主体和世界，以及如何分类；它们不是“真实性证明”。后续若改变状态，必须生成对应来源记录，不能复用旧 provenance 假装没有发生变化。

## Lifecycle: Command / State / Event

WorldCommand、WorldStatus、WorldEvent 三个独立枚举。

| Command | 前态 | 后态 / Event |
| --- | --- | --- |
| CREATE | 无既有对象，显式 create_world | CREATED / WORLD_CREATED |
| ENTER | CREATED | ACTIVE / WORLD_ENTERED |
| SUSPEND | ACTIVE | SUSPENDED / WORLD_SUSPENDED |
| RESUME | SUSPENDED | ACTIVE / WORLD_RESUMED |
| EXIT | ACTIVE，单 writer/最后参与者合同 | SUSPENDED / WORLD_EXITED |
| ARCHIVE | CREATED / SUSPENDED | ARCHIVED / WORLD_ARCHIVED |
| UNARCHIVE | ARCHIVED | SUSPENDED / WORLD_UNARCHIVED |
| DELETE | ARCHIVED | TOMBSTONED / WORLD_TOMBSTONED |

非法状态/命令组合拒绝，TOMBSTONED 无出边；没有物理删除。Transition 仅返回新 World 值与事件种类，不建立事件系统。重复命令不会假装成功；幂等命令记录将由后续 Runtime 负责。

所有转换都需要匹配 owner、expected_revision 和 writer_epoch。每次成功转换推进 revision 与 epoch。输入对象保持不变；调用方必须原子保存返回值，本阶段无 I/O。

## Revision / Writer Epoch / SessionBinding

写入前置检查要求当前 ACTIVE World、开放 Binding、同一 principal、完整 scope、正确角色引用、当前 revision 与 epoch。WorldState.revision 是投影自身版本；本阶段 validate_write 的 expected_revision 对应 World 聚合版本，不假定它与投影版本同增。

epoch 为保守的 World 级 fence，跨挂起、退出、恢复和源世界切换失效。Timeline 保留独立 ID，但本阶段没有并行 timeline writer。后续若引入多个 writer，需新 ADR 与持久 CAS，不能直接复用本阶段单 writer 假设。

`close_session(..., reason=SWITCH)` 仅关闭源绑定并挂起源 Roleplay World；不激活目标，也不宣称跨世界原子切换已实现。恢复后使用新 session ID 绑定原 world/timeline/character。旧 Binding 即使还是旧 OPEN 副本，只要对照最新 World，也因 epoch 失配被拒绝。

重要限制：这些纯函数必须收到**最新可信快照**。若调用者同时提交旧 World 与旧 Binding，它们无法发现外部已发生的新提交。认证主体、会话唯一性、最新状态读取及原子 compare-and-swap 是 SP-004B/H 的责任；本阶段不是分布式锁或 lease manager。

## Bridge Policy Contract

BridgePolicy 明确 grant ID、principal、source/target WorldScope、字段集合、data class、purpose、audience、expiry、grant_revision、revoked。BridgeRequest 与它逐项匹配；字段/受众只允许子集，拒绝 wildcard。缺 grant、方向相反、跨 owner、过期、撤销或版本不匹配都不允许共享。

`evaluate_bridge` 只返回显式 ALLOW/DENY 资格值，不查询记忆、不转移载荷、不生成派生记忆、不改变 reality/canon。两个方向分别建许可；同 Soul 不提供隐式授权。本阶段仅支持同 owner 的显式跨世界许可，跨 owner 分享不在范围内。

调用者须从受信任存储提供当前 grant/revision/时间。函数不负责签发、用户同意、持久撤销、源目标 ACL、lineage 重放与内容变换；后续 F 在这些条件满足后才能执行传输。反向或传递权限不能由当前 ALLOW 推导。BridgeDecision 禁止隐式 bool 转换，避免把 DENY 枚举当成真值。

## Host Capability Contract

Capability 覆盖 stable_principal、stable_session、isolated_context_lane、message_provenance、reload_support、delivery_ack、history_isolation。每项为 SUPPORTED / LIMITED / UNSUPPORTED，缺省 UNSUPPORTED。

`require_private_context_isolation` 要求稳定主体、稳定会话、消息来源、独立 context lane 和历史隔离均明确 SUPPORTED。LIMITED 不算满足，枚举不能隐式转 bool。契约不会探测宿主或读取其配置，也不会用 Prompt 文案假装能力存在。能力报告的真实性与运行时变化仍需 H 验证。

## PR #3 → New Domain Model Compatibility Assessment

只读检查对象：[PR #3](https://github.com/y19870785/life-engine/pull/3)，head `ab227f2179eeaa7ded662d612508a98ad5cdf04a`。仍为 Implementation Candidate / Migration Source，不是本分支 baseline。

| 代码/能力 | 建议 | 后续映射与限制 |
| --- | --- | --- |
| PNG/JSON/V2/V3 解析及原始卡存储 | KEEP / ADAPT | G 生成 Versioned IR，再映射 CharacterDefinition；不把 V3 JSON 直接放进核心模型 |
| World Book / 递归预算 | KEEP / ADAPT | Lore IR，不是 World、Story 或 canon 来源证明 |
| card_id 及卡名 | MIGRATE | 显式映射 DefinitionRef + CharacterInstance；不能继续作为记忆最终隔离键 |
| 单活动 RoleplaySession | ADAPT / REPLACE | SessionBinding + World/Timeline scope + 必须携带 epoch/revision；恢复复用世界而非重建 |
| persona/Soul memory、roleplay_meta | KEEP 数据 / MIGRATE 语义 | 保留原文来源，旧 meta 标虚构体验与未审核；不捏造历史 grant |
| 可选 expected_session / 晚到响应防护 | ADAPT | 后续 writer 必须执行最新 snapshot 的 revision/epoch 验证 |
| Hermes/OpenClaw 桥接 | KEEP / ADAPT | 转换认证主体及 capabilities；Domain 不依赖 Profile 路径/SDK |
| Prompt 组装 | ADAPT | 未来仅呈现已授权世界投影，不写 canon、不颁发桥接权限 |
| schema 3 | MIGRATE（后续授权） | 保持候选迁移来源；本阶段生产 schema 仍为 2 |

产品目标保留：未来用户可直接导入兼容 SillyTavern V3 的卡片。路径是 V3 → Import Adapter → Versioned Internal IR → CharacterDefinition → World → CharacterInstance → Runtime。SP-004A 只固定定义/实例及引用边界，不实现这条完整链，也不声称已完成 V3 importer 重构。

## Tests, Decisions and Limits

[test_domain.py](../../tests/test_domain.py) 包含无数据库验收示例：同一个 Soul 下的 Soul World、Roleplay A/B，同一 Definition 的两个实例具有不同状态/关系/世界/时间线；退出 A 后恢复并重新绑定仍为原 World。测试不代表剧情已持久化。

ADR 采用 [最小规范](adr/README.md)，决策标记 Implemented candidate / Pending independent review。除三项必需 ADR 外，补充 [fencing 与信任边界 ADR](adr/SP-004A-004-PURE-CONTRACT-FENCING.md)，避免把纯校验误当部署完成。

检查结果见 [SP-004A Quality Gates](../planning/SP-004A-QUALITY-GATES.md)。剩余问题：最新快照/CAS、多人 writer、授权签发与撤销、完整 IR、关系类型和存储编码均留给后续授权阶段。本阶段无范围偏离；不开始 D/G/E/B/C/F/H，不修改或合并 PR #3，不合并本 PR。
