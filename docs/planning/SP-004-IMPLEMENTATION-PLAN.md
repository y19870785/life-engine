# SP-004 — 实施历史与后续路线建议

本计划以 canonical main `780c7a54635e7347b914751ce0c79e350800be0b` 为核对基线，由 SP-004R 校准。

已合并阶段按事实标记 DONE；未来工作包及依赖顺序统一为 **PROPOSED / PENDING_INDEPENDENT_REVIEW**。负责人：Codex；独立审核：ChatGPT / 小雪。本次仅授权治理文档，不授权启动后续实现、转 Ready、合并或关闭 PR #3。

相关：[总体架构](../architecture/SP-004-PERSISTENT-WORLD-RUNTIME.md)、[差距校准](../architecture/SP-004-GAP-ANALYSIS.md)、[PR #3 正式替代记录](SP-004R-PR3-SUPERSESSION.md)。旧文档中的阶段授权/候选状态是当时的历史记录；完成事实以本表列出的已合并提交为准，不把阶段文档中的远期目标一并算作完成。

## 一、已完成阶段与真实历史

### World Memory 当前实施记录

SP-004B0 已合并于 `4d628ca1b7b68609cd6fcf95e835c25ffa638c6b`。以该提交为固定 Base 的 SP-004B1 当前为 **IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**，交付 World Memory 授权运行、同库持久化、独立 CAS、Schema 4 副本迁移与删除恢复门禁；详见 [World Memory 实现状态](../architecture/SP-004B-WORLD-MEMORY.md)。本记录不将 B1 标为 DONE，不启动后续 C/J/F/K/H/L，也不表示已完成真实宿主接入。下列 SP-004R 时点的阶段表与建议依赖仍作为历史路线记录。

### SP-004J0 当前设计记录

以 canonical main `1a73f6e43caf54bd34ae810c9b58eddb25f6fb88` 为固定 Base 的 SP-004J0 正在冻结 [Lore / World Book Runtime 架构](../architecture/SP-004J-LORE-RUNTIME.md)及四份 ADR；状态为 **PROPOSED / PENDING_INDEPENDENT_REVIEW**。J0 只交付设计，不表示 J1 已获实施授权或 Lore 激活能力已进入 main；当前 `DATA_SCHEMA = 4` 不变。上文 SP-004R 和 SP-004B1 的阶段用语保留各自成文时的历史状态，本段不重写其他阶段记录。

| 阶段 | 实际交付 | 状态 | 已合并提交 | 明确不包含 |
| --- | --- | --- | --- | --- |
| SP-004 | 持久 World Runtime 架构、领域边界与初始差距分析 | DONE | `f040a8241e3b6ebc34f4025c6f5211829a0d040c` | 不等于全部运行能力已实现 |
| [SP-004A](../architecture/SP-004A-WORLD-DOMAIN-MODEL.md) | World Domain Model；身份、所有权、生命周期纯合同、RealityStatus/CanonStatus、默认拒绝的 Bridge 策略与宿主能力声明 | DONE | `1ba30e32c42dfa3206e5ace93b25b8d522954e33` | 无完整 Bridge 服务或宿主认证实现 |
| [SP-004G](../architecture/SP-004G-CHARACTER-IMPORT-IR.md) | Character Card → CharacterImportIR → CharacterDefinition；有界解析、保真、诊断与来源指纹 | DONE | `f71d1b7f1718bc8be9916b1c09dde625aaa0d362` | LoreIR 保留不是 Lore 激活；没有完整资产仓库 |
| [SP-004D](../architecture/SP-004D-WORLD-INSTANCE-RUNTIME.md) | World 创建、CharacterInstance、SessionBinding、ENTER/EXIT/SUSPEND/RESUME、World Switch、Revision、WriterEpoch | DONE | `399b084a8a5dfd76eb2aa3d0aac9ebbaafd35260` | 最小 Values 更新不是 Story/Memory/关系推进引擎；纯领域状态不等于所有生命周期都有应用入口 |
| [SP-004E](../architecture/SP-004E-WORLD-SQLITE-PERSISTENCE.md) | canonical Schema 3、SQLiteWorldRepository、数据库 CAS、重启恢复、backup/restore、Schema 2 → 3 副本迁移、整组 Schema 回退 | DONE | `780c7a54635e7347b914751ce0c79e350800be0b` | 无 PR #3 数据库兼容、World Memory、Lore 或角色宿主接入 |

SP-004R 当前是替代记录与路线图校准候选，**不标记 DONE**。DONE 表示该阶段实际交付已进入 canonical main，不是对未来扩展的合并授权。

## 二、阶段编号纠偏

| 原计划描述 | 校准后的唯一含义或归属 |
| --- | --- |
| SP-004A 领域模型 | 保持已完成的领域合同含义，不扩大完成范围 |
| SP-004D 仅定义/实例 | 按实际历史记录为 World/CharacterInstance/SessionBinding Runtime；定义升级预览等未交付项另列 L |
| SP-004G 泛化到多种 IR | 已完成范围收敛为 CharacterImportIR 及保留的 LoreIR；Lore 执行归 J，Story 执行归 C |
| 原计划将 E 分配给记忆隔离 | 此分配撤销；SP-004E 唯一指 SQLite World Runtime Persistence；World Memory 候选改为 B |
| 原计划将 B 分配给持久 World Runtime | 核心运行/持久化已经由 D/E 完成，不再重复建设；B 拟重新定义为 World Memory |
| SP-004C、F、H | 保留 Story、Controlled Bridge、Host Integration 的方向，按当前依赖重新界定 |
| 新增 J、K、L | 分别承接 Lore/World Book、Prompt、导入资产与历史映射的剩余能力；全部只是建议 |

A、D、E、G 不再用于其他阶段。编号是工作包标识，不是按字母顺序执行的时间表。旧顺序失效，不能据它再次实施已经完成的持久化阶段。

## 三、未来工作包（PROPOSED）

以下每项均需独立任务书、范围、固定基线、实施授权和审核；这里没有自动执行队列。

| 工作包 | 目标与范围 | 前置合同与依赖 | 验收重点 | 数据与范围边界 |
| --- | --- | --- | --- | --- |
| SP-004B — World Memory / Roleplay Memory | world/timeline/CharacterInstance 归属；audience/scope；RealityStatus、CanonStatus；有权限的写入/检索/导出与缓存分区 | 已完成 A/G/D/E | 同一定义的两 World 不串读写；Soul 不被剧情污染；关闭记忆不产生旁路写入；越权 ID、检索/缓存/导出及重启测试 | 不以旧 card_id/session 根隔离；不自动生成 Soul 元记忆；新增表与迁移另审 |
| SP-004J — Lore / World Book Runtime | 书与条目的版本/来源；激活、递归、循环终止、优先级、预算、scope；Definition 与 World 对书版本的关联 | A/G/D/E；若扫描持久记忆则依赖 B 的授权读取；资产持久化与 L 明确接口 | 字面触发、禁用/常驻、大小写、递归、预算耗尽、确定顺序与世界隔离；不执行脚本，不因导入获得工具权限 | World Book 是知识格式，不是 World；明确字节预算与模型词元预算差别；不机械复制旧限制 |
| SP-004C — Story Runtime | Story state、accepted events、world events、未完成线索、关系推进、逻辑时钟与确定性投影；重启恢复 | A/D/E、B；使用 Lore 设定时对接 J | 同事件去重、接受/拒绝、重放一致、挂起不推进、修正来源可追溯、关系不跨 World | 最近几条记忆和模型摘要都不是故事真源；不因“提到”就自动变成已接受事件 |
| SP-004F — Controlled World Bridge | Soul ↔ Roleplay 默认拒绝；grant、字段/受众/目的、preview、显式确认、lineage、撤销；fictional_shared_experience | A 的策略合同、D/E 围栏、B 隔离；桥接 Story 时依赖 C 的接受语义 | 未授权正文不进入目标 Prompt；过期/撤销/重试/来源删除；确认后只写授权字段并保留真实性 | EXIT 不自动写 Soul Memory；不承诺收回外部模型已见内容 |
| SP-004K — Prompt Runtime | 从已授权 World/Memory/Story/Lore 快照组装 Character Prompt；定义/实例/会话引用与上下文预算、身份表现和错误降级 | D/E 快照；按启用能力对接 B/J/C；跨世界数据只接收 F 的授权结果 | 恶意卡片/世界书作为数据；固定版本、陈旧快照、预算裁剪、scope 隔离；程序状态与模型口吻分别验证 | Prompt 只是表现投影，不是权限边界；无授权的 Soul aside 不可用；不操作宿主原始历史 |
| SP-004H — Host Integration | Hermes/OpenClaw、可信 Principal、SessionBinding、运行代次协调、/rp 或等价体验；Prompt lane、宿主历史隔离、消息来源、重载/重连与实机验证 | D/E/K；启用 Memory/Lore/Story/Bridge 时满足各包验收；适配 A 的宿主能力声明 | 同 Profile 多聊天、跨宿主路由、原 SOUL 不变、旧消息与晚到响应、历史污染、能力不足拒绝/降级、真实接入报告 | 宿主聊天 ID 不等于 World ID；不把既有生活 Bridge 当成角色接入；上线、模型调用和真实渠道发送另行授权 |
| SP-004L — 导入资产与历史映射 | 原 PNG/头像/原包、完整 IR、导入历史、来源版本、Definition 升级预览；若确有旧数据，再提出映射提案 | A/G/E；影响实例时遵守 D 的版本固定，与 J 协商书资产持久化 | 资产/原包保留、同定义多实例不被升级改写、备份恢复、含歧义旧数据的人工决策 | 不承诺 PR #3 Schema 3 已可迁移；未知结构拒绝；不复活 card_id 运行身份或删除卡片级联删经历 |
| GOV-CI — 独立 CI 治理候选 | 根据当前 runtime 测试集评估 Windows/Linux、Python 与 Node 矩阵、工作流权限和发布门禁 | 独立治理任务书；实现版本以当时支持范围重新确认 | 实际 GitHub Actions 结果与本地测试分开记录；涵盖当前 G/D/E 测试，不复制旧角色断言 | 此处为候选标签，未分配正式阶段号；本任务不添加 workflow |
| GOV-DOC — 用户文档校准候选 | README 的价值说明、当前能力边界、已修复问题、未来角色体验与运维说明 | 以已合并事实更新；角色使用说明等待 H 实机验收 | 不把开发 API 写成可聊天功能，不把历史截图当线上证据；操作指令可核对 | 此处为候选标签，未分配正式阶段号；不复制旧 v0.4 发布声明 |

生命周期的 ARCHIVE/DELETE 应用入口、完整定义升级和历史数据迁移不能因为 A 中有类型、D 中有 World 就算完成。L 可形成范围提案；具体生命周期扩展需另立任务书，不隐含加入当前 D/E 或未来 Memory 实现。

## 四、依赖与建议顺序（PROPOSED）

已完成且不重复建设：**A → G → D → E**。这描述合并历史，不重写各阶段原先的设计依赖。

供独立审核的后续主线建议：

```text
B World Memory
→ J Lore / World Book
→ C Story Runtime
→ F Controlled World Bridge
→ K Prompt Runtime
→ H Host Integration
```

此顺序不是最终决定。它先建立读取隔离，再引入可执行知识与故事投影，然后实现授权跨域，最后消费这些结果构造 Prompt 并接入宿主。这样不会把“有角色口吻”误认为权限、状态或历史恢复已经正确。

表中的前置依赖与上面的建议顺序不同：J 的纯激活逻辑不必等待所有 Memory 功能；C 不使用 Lore 时不需要全部 J；K 可先定接口，未启用的能力必须缺省拒绝；F 无需为了普通世界内对话提前开放。是否并行、是否拆更小里程碑，以及 F/K 的交付先后，均等待独立审核，不由 Codex 定案。

L 在需要持久化书资产或旧数据映射前单独评估，不阻挡已有 Definition 恢复。GOV-CI/GOV-DOC 是可独立排期的治理候选，不冒充主线完成阶段。

## 五、迁移与历史数据治理

Schema 2 → canonical Schema 3 的部署迁移已由 E 完成，继续遵守其[迁移与回退 ADR](../architecture/adr/SP-004E-002-SCHEMA-3-MIGRATION.md)。禁止为了重用 PR #3 再执行它的旧迁移；数字同为 3 不代表结构兼容。

未来 B/J/C/F/L 只要改变持久数据，就需各自提交 Schema 所有权、副本迁移、验证、原子激活和回退方案；本计划不提前分配下一个 Schema 版本，不修改 DATA_SCHEMA。

若将来确有 PR #3 历史库需要救援，L 必须先只读盘点、保全备份和原包、生成显式旧 ID 映射与来源记录，对同卡多故事等歧义要求审核。旧摘要只能作为未审历史来源，不自动成为 accepted events、canon 或已授权的共同体验。当前不提供该迁移工具，也不把它设成关闭 PR #3 的前提。

运行生命周期恢复已实现；事件投影恢复、授权撤销后的派生数据清理、宿主历史隔离仍分别属于 C/F/H。代码回退与数据回退继续分开，不以旧备份覆盖后续新写入而不说明数据时点。

## 六、审核与发布门禁

每个未来工作包报告固定 Base/Head、文件范围、数据影响、测试和原始结果、回退限制及 Draft PR 状态。独立审核和实施/合并授权分别记录。

现有 A/G/D/E 证明世界身份与最小状态可以持久恢复；完整产品闭环还需 B/J/C/K/H 的检索、设定、故事和宿主体验验收。F 的跨域能力必须另过默认拒绝、预览、确认、撤销与 lineage 门禁。持久化成功不意味着完整角色模式已经可用。

## 七、范围与停止条件

本次 SP-004R 只交付文档、Commit、Push、Draft PR 和执行报告。PR #3 只作 read-only reference，任何后续引用都必须重新适配 canonical domain model；不得 cherry-pick、解决冲突后整包合并或把原测试通过当成新模型验收。

32 文件的唯一主分类、剩余能力矩阵、关闭条件与拟议说明统一记录在[替代清单](SP-004R-PR3-SUPERSESSION.md)。清单及本计划合并、独立审核并另获关闭授权之前，PR #3 保持 OPEN / DRAFT / NOT MERGED。后续关闭也保留远端分支至少到 Lore/Memory/Host Integration 完成。

本轮不启动 B/J/C/F/K/H/L，不修改 runtime、tests、Schema 或真实角色卡，不接入真实宿主；完成后停止等待独立审核。
