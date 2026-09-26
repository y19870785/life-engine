# SP-004 — 实施历史与后续路线建议

## 2026-09-26 当前状态快照

当前事实基线：canonical main `8e2db9ae50b1ac3c46bb1953851d14442c58f085`；`DATA_SCHEMA = 7`、World Schema Signature `SP-004F-bridge-runtime-v1`、Prompt template `SP-004K-prompt-v1`。下面大量章节是各阶段形成时的历史记录，含当时的 PROPOSED / PENDING 状态；**当前事实以本节为准**，后续路线以[2026-09 路线图](ROADMAP-2026-09.md)为准。

| 阶段 | 当前状态 | 已合并能力 |
| --- | --- | --- |
| SP-004A | DONE | World Domain Model |
| SP-004B | DONE | World Memory |
| SP-004C | DONE | Story Runtime |
| SP-004D | DONE | World Instance Runtime |
| SP-004E | DONE | World SQLite Persistence |
| SP-004F | DONE | Controlled World Bridge |
| SP-004G | DONE | Character Card Import IR |
| SP-004H0 | DONE | Host Integration Contract |
| SP-004H1 | BLOCKED | Hermes 官方 Host capability 尚缺；CAP3 in scope，官方实现待完成 |
| SP-004H2 | BLOCKED | OpenClaw CAP0/CAP1 审计未找到合格 final-output commit boundary |
| SP-004J | DONE | Lore Runtime |
| SP-004K | DONE | Prompt Runtime |

**SP-004 Core Runtime 主链已完成，但 SP-004H production Host Private RP 未完成；整个项目不能标为 DONE。** Soul Continuity / Living Agent 可进入[隔离 Host 沙箱](../HOST-SANDBOX-TESTING.md)，不能把沙箱验证或 Hermes Draft fork 当作 Full Private RP 解锁。

本计划以 canonical main `780c7a54635e7347b914751ce0c79e350800be0b` 为核对基线，由 SP-004R 校准。

已合并阶段按事实标记 DONE；未来工作包及依赖顺序统一为 **PROPOSED / PENDING_INDEPENDENT_REVIEW**。负责人：Codex；独立审核：ChatGPT / 小雪。本次仅授权治理文档，不授权启动后续实现、转 Ready、合并或关闭 PR #3。

相关：[总体架构](../architecture/SP-004-PERSISTENT-WORLD-RUNTIME.md)、[差距校准](../architecture/SP-004-GAP-ANALYSIS.md)、[PR #3 正式替代记录](SP-004R-PR3-SUPERSESSION.md)。旧文档中的阶段授权/候选状态是当时的历史记录；完成事实以本表列出的已合并提交为准，不把阶段文档中的远期目标一并算作完成。

## 一、已完成阶段与真实历史

### World Memory 当前实施记录

SP-004B0 已合并于 `4d628ca1b7b68609cd6fcf95e835c25ffa638c6b`。以该提交为固定 Base 的 SP-004B1 当前为 **IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**，交付 World Memory 授权运行、同库持久化、独立 CAS、Schema 4 副本迁移与删除恢复门禁；详见 [World Memory 实现状态](../architecture/SP-004B-WORLD-MEMORY.md)。本记录不将 B1 标为 DONE，不启动后续 C/J/F/K/H/L，也不表示已完成真实宿主接入。下列 SP-004R 时点的阶段表与建议依赖仍作为历史路线记录。

### SP-004J0 当前设计记录

以 canonical main `1a73f6e43caf54bd34ae810c9b58eddb25f6fb88` 为固定 Base 的 SP-004J0 正在冻结 [Lore / World Book Runtime 架构](../architecture/SP-004J-LORE-RUNTIME.md)及四份 ADR；状态为 **PROPOSED / PENDING_INDEPENDENT_REVIEW**。J0 只交付设计，不表示 J1 已获实施授权或 Lore 激活能力已进入 main；当前 `DATA_SCHEMA = 4` 不变。上文 SP-004R 和 SP-004B1 的阶段用语保留各自成文时的历史状态，本段不重写其他阶段记录。

### SP-004J1 当前实现记录

SP-004J0 已进入 canonical main `0fe1a416b70a90914581d7698a30cc066b4c1ba1`。以此为固定 Base 的 SP-004J1 已实现 Lore 受信注册、不可变书版本、WorldScope 显式绑定及 CAS、Session 围栏、确定性有界激活、Schema 5 与副本迁移、备份和恢复；详见 [J1 实现状态](../architecture/SP-004J-LORE-RUNTIME.md#j1-实现状态)。本分支状态为 **IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**，只有合并后才能记为 DONE。旧阶段表与 J0 设计记录保留成文时状态，不把 Story、Bridge、Prompt 或 Host Integration 误标为已完成。

### SP-004C0 当前设计记录

以 canonical main `0028faedc36e00c52b9328e15a43fa81c31f9475` 为固定 Base，SP-004C0 正在冻结[Story Runtime 架构](../architecture/SP-004C-STORY-RUNTIME.md)及四份 ADR；状态为 **PROPOSED / PENDING_INDEPENDENT_REVIEW**。本阶段只定义已接受事件真源、显式接受、独立 StoryRevision/StoryClock、确定性投影、前向修正、关系/线索与未来 Schema 6 候选，不实施 C1。当前 `DATA_SCHEMA = 5` 和 `SP-004J-lore-runtime-v1` 不变。上文 J1 的 PENDING 语句是该实施记录的历史状态，不在 C0 擅自改写；Story Runtime 尚未进入 canonical main。

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

## 八、当前 canonical 能力矩阵（2026-09 复盘）

本节原以 main `10b75a6f8fe6fd94b98e82a6e903cdcfcb8c6d1e` 为 C1 候选时点的事实基线；上文保留各历史任务成文时的状态与旧建议顺序。当前已合并事实见下方 K0 时点校准，完整依据见[中期复盘](SP-004-MIDTERM-REVIEW-2026-09.md)。

| 能力 | 阶段 | 当前状态 | canonical 提交 | 已实现 | 尚未实现 |
| --- | --- | --- | --- | --- | --- |
| Domain | SP-004A | DONE | `1ba30e32c42dfa3206e5ace93b25b8d522954e33` | Owner、Soul、World、Timeline、领域身份 | 完整 Bridge |
| Import | SP-004G | DONE | `f71d1b7f1718bc8be9916b1c09dde625aaa0d362` | CharacterImportIR、CharacterDefinition、LoreIR 保真 | 原包资产仓库 |
| World Runtime | SP-004D | DONE | `399b084a8a5dfd76eb2aa3d0aac9ebbaafd35260` | CharacterInstance、SessionBinding、生命周期和围栏 | Story 事件真源 |
| Persistence | SP-004E | DONE | `780c7a54635e7347b914751ce0c79e350800be0b` | 同库 SQLite、代次、迁移、备份恢复 | 宿主自动接线 |
| Memory | SP-004B | DONE | `d89b362701e614415354c38302a102f593a0a0a7` | WorldScope/Audience、CAS、幂等、删除恢复控制 | 自动提取与 Host 注入 |
| Lore | SP-004J | DONE | `0028faedc36e00c52b9328e15a43fa81c31f9475` | 固定版本、显式绑定、有界确定激活、Schema 5 | 完整 SillyTavern 执行 |
| Story（C1 候选时点） | SP-004C0/C1 | 架构 DONE；Runtime 当时候选 | `10b75a6f8fe6fd94b98e82a6e903cdcfcb8c6d1e`（C0） | 当时已冻结 accepted event、投影、时钟合同 | 当时 C1 未进入 main；无自动抽取 |
| Prompt | SP-004K | PROPOSED | — | — | Prompt 架构与运行时 |
| Bridge | SP-004F | PROPOSED | — | — | 受控跨 World 投影 |
| Host | SP-004H | PROPOSED | — | — | Hermes/OpenClaw 实机角色接入 |
| Assets | SP-004L | PROPOSED 旁线 | — | — | 原包、头像、历史与 Definition 升级 |

## 九、2026-09 中期路线调整（PROPOSED）

上文 `B → J → C → F → K → H` 是历史建议。C1 候选时点的建议主线为 **C1 → K0 → K1 → F0 → F1 → H0 → H1 → H2**，L 为旁线。C1 将世界中发生的事件确权；K 先消费 World、Definition、Instance、Story、Lore、Memory 与 Session 的授权投影，验证安全角色上下文；普通 Roleplay 不需要先开放 Soul Bridge。F 后续只桥接受授权的最小跨域投影，再由 K 消费；H 将宿主合同、Hermes 和 OpenClaw 适配分开。该顺序不构成后续阶段实施或合并授权。

## 十、SP-004K0 时点的当前 canonical 能力与路线

事实基线：canonical main `7f7c5c07d4cc821027cb083100335c8f4d139c44`。本节取代上方 C1 候选时点矩阵与建议顺序作为**当前**读法，不改写旧表的历史状态。

| 能力 | 阶段 | 当前状态 | 已合并提交 | 已实现 | 尚未实现 |
| --- | --- | --- | --- | --- | --- |
| Domain | A | DONE | `1ba30e32c42dfa3206e5ace93b25b8d522954e33` | Owner、Soul、World、Timeline 身份 | Bridge 服务 |
| Import | G | DONE | `f71d1b7f1718bc8be9916b1c09dde625aaa0d362` | CharacterImportIR、固定 Definition 投影、LoreIR | 原包资产仓库 |
| World Runtime | D | DONE | `399b084a8a5dfd76eb2aa3d0aac9ebbaafd35260` | CharacterInstance、SessionBinding、生命周期与围栏 | 宿主自动接线 |
| Persistence | E | DONE | `780c7a54635e7347b914751ce0c79e350800be0b` | 同库 SQLite、代次、迁移、备份恢复 | 自动宿主体验 |
| Memory | B | DONE | `d89b362701e614415354c38302a102f593a0a0a7` | 授权读写、Audience、删除恢复控制、Schema 4 | 自动提取与宿主注入 |
| Lore | J | DONE | `0028faedc36e00c52b9328e15a43fa81c31f9475` | 固定书版本、Scope 绑定、有界激活、Schema 5 | 完整 World Book 宿主执行 |
| Story | C0/C1 | **DONE** | `7f7c5c07d4cc821027cb083100335c8f4d139c44` | Accepted StoryEvent、独立修订/时钟、确定性 reducer/StoryState、关系/线索、前向修正、Schema 6 | 模型自动抽取与 Host 接入 |
| Prompt | K0/K1 | K0 架构候选；K1 未开始 | — | 本分支仅冻结[Prompt 合同](../architecture/SP-004K-PROMPT-RUNTIME.md) | Prompt Runtime 与模型提交 |
| Bridge | F0/F1 | PROPOSED | — | 默认拒绝策略合同 | 授权跨域投影服务 |
| Host | H0/H1/H2 | PROPOSED | — | 宿主能力声明 | Hermes/OpenClaw 真实适配 |
| Assets | L | 旁线 PROPOSED | — | G 的导入 IR 基础 | 原包、头像、升级与历史映射 |

旧路线 `B → J → C → F → K → H` 只作历史记录；**当前建议路线为 K0 → K1 → F0 → F1 → H0 → H1 → H2**，L 是旁线。K0 架构经独立审核、合并前不标 DONE；K1/F/H 各自需要新的实施授权。Prompt 仅消费各 Runtime 授权投影，不充当权限边界；Story 的 `world_facts` 与 `open_threads` 在首版默认不进入角色模型。

## 十一、SP-004K1 候选时点的当前记录

SP-004K0 已在 canonical main `dec8fd5797f67496c583f1112d379da954ab8f8b` 合并，状态 **DONE**；上节的 K0 候选措辞是成文时的历史状态。Prompt 能力矩阵的当前读法为：**K0 架构 DONE；K1 Runtime 候选 IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**。K1 候选交付会话绑定 Memory/Story/Lore 适配、只读组装、确定性预算、不可变快照及重验；不含模型 API、Bridge、Host 集成或 Schema 变更。K1 只有通过独立审核并合并才可标 DONE。当前建议顺序为 **K1 → F0 → F1 → H0 → H1 → H2**，L 保持旁线；本记录不授权自动启动后续阶段。

## 十二、SP-004F0 时点的 canonical 能力与路线

事实基线：canonical main `b1bb2fd07eae0699a108ad535ba6152c9a8de2f6`，其中 SP-004K1 已经 Squash Merge，**K0/K1 均 DONE**。上文 K1 候选状态是其成文时点的历史，不代表当前 main。`DATA_SCHEMA = 6`、签名 `SP-004C-story-runtime-v1`、Prompt 模板 `SP-004K-prompt-v1`。本 F0 分支只新增[受控 Bridge 架构](../architecture/SP-004F-CONTROLLED-WORLD-BRIDGE.md)及五份 ADR；Bridge Runtime 不存在。

| 能力 | 阶段 | 当前状态 | canonical 提交 | 已实现 | 尚未实现 |
| --- | --- | --- | --- | --- | --- |
| Domain / Import | A/G | DONE | 上方历史矩阵所列提交 | World/Timeline/CharacterDefinition 身份、角色卡导入 IR | L 原包资产与升级 |
| World / Persistence | D/E | DONE | 上方历史矩阵所列提交 | 实例、Session、生命周期、SQLite 代次/备份/恢复 | 宿主自动接线 |
| Memory | B | DONE | `d89b362701e614415354c38302a102f593a0a0a7` | Scope/Audience、CAS、删除恢复控制 | 自动提取、跨域写入 |
| Lore | J | DONE | `0028faedc36e00c52b9328e15a43fa81c31f9475` | 固定书版本、Scope 绑定、有界激活 | 完整外部 World Book 执行 |
| Story | C0/C1 | DONE | `7f7c5c07d4cc821027cb083100335c8f4d139c44` | Accepted Event 真源、确定性投影、Schema 6 | 自动事件抽取 |
| Prompt | K0/K1 | **DONE** | `b1bb2fd07eae0699a108ad535ba6152c9a8de2f6` | Session-bound 投影、类型化 Section、预算、快照重验 | 模型/宿主调用、Bridge Section 启用 |
| Bridge | F0/F1 | F0 架构候选；F1 未开始 | — | 现有纯 eligibility；本分支仅冻结 Grant/Preview/Projection 合同 | grant store、撤销控制、Runtime、Prompt 接线 |
| Host | H0/H1/H2 | NOT STARTED | — | HostCapabilities 声明 | Hermes/OpenClaw 真实接入 |
| Assets | L | 旁线 PROPOSED | — | G 的导入 IR 基础 | 原包、头像、历史与 Definition 升级 |

历史路线 `B → J → C → F → K → H` 和此前的 K1 候选顺序均保留。**当前建议主线：已完成 A → G → D → E → B → J → C → K；当前 F0 架构候选；后续 F1 → H0 → H1 → H2；L 为旁线。** F0 不授权 F1 实施，不把同 Owner 变成共享许可，也不把 Prompt 当 Bridge 授权边界。

## 十三、SP-004F1 实现候选时点的当前能力矩阵

F0 已随 canonical main `cd51d2d97ff4de18b681f4176e57d84f12ed679d` 合并，状态 **DONE**。上节 F0 候选表保留为历史。本 F1 分支以该 SHA 为固定 Base；以下候选能力尚未经过独立审核，不提前标 DONE。

| 能力 | 阶段 | 当前状态 | 已实现候选 | 未实现 |
| --- | --- | --- | --- | --- |
| Domain / Import / World / Persistence | A/G/D/E | DONE | 原有身份、会话、代次及恢复 | Host 自动接线 |
| Memory / Lore / Story | B/J/C | DONE | 各自授权与真源、Schema 4/5/6 | 跨域目标持久化 |
| Prompt | K0/K1 | DONE | Session-bound 快照、预算与重验 | 模型 API、Host renderer |
| Bridge 架构 | F0 | **DONE** | 默认拒绝、Grant/Preview/Projection 与撤销恢复合同 | — |
| Bridge Runtime | F1 | **IMPLEMENTED / PENDING_INDEPENDENT_REVIEW** | Prompt-only Soul↔Roleplay、创建/撤销 Grant、Schema 7、独立撤销控制、瞬时投影和 K 受信 BRIDGE_CONTEXT | 目标 Memory/Story 写入、Roleplay↔Roleplay、Host UI |
| Host | H0/H1/H2 | NOT STARTED | HostCapabilities 声明 | Hermes/OpenClaw 接入 |
| Assets | L | 旁线 PROPOSED | Import IR | 原包资产、升级与历史映射 |

当前路线：**DONE A → G → D → E → B → J → C → K → F0；CURRENT F1 候选；NEXT H0 → H1 → H2；SIDE L**。F1 只在独立审核、合并并通过 canonical main CI 后才能标 DONE。历史 `B → J → C → F → K → H` 不再是当前执行顺序。

## 十四、SP-004H0 当前 canonical 能力矩阵与路线

固定 canonical main `68c24b010ee464a66e0e853ab50f85b7e861e148`：SP-004F0/F1 **DONE**；上节 F1 候选描述保留为成文时点的历史。F1 已实现的是 **Prompt-only Soul↔Roleplay Bridge**：显式 Grant、受信 Session 来源、瞬时投影、K 的 DATA `BRIDGE_CONTEXT`、Schema 7 和非回滚撤销控制；**未**实现目标 Memory/Story 持久写入或 Host UI。当前 `DATA_SCHEMA = 7`，签名 `SP-004F-bridge-runtime-v1`，Prompt 模板 `SP-004K-prompt-v1`。

| Capability | Stage | Current status | Canonical commit | What is implemented | What is not implemented |
| --- | --- | --- | --- | --- | --- |
| Domain / Import | A/G | DONE | 上方历史矩阵所列提交 | Owner/Soul/World/Timeline 与有界卡片导入 | L 原始资产、升级 |
| World / Persistence | D/E | DONE | 上方历史矩阵所列提交 | CharacterInstance、SessionBinding、生命周期、SQLite 代次/备份/恢复 | 真实 Host lane 映射 |
| Memory / Lore / Story | B/J/C | DONE | 上方历史矩阵所列提交 | 各自真源、授权投影、Schema 4/5/6 | 模型自动提取/确权 |
| Prompt | K0/K1 | DONE | `b1bb2fd07eae0699a108ad535ba6152c9a8de2f6` | 类型化只读 Snapshot、预算与重验 | 模型消息格式及调用 |
| Bridge | F0/F1 | **DONE** | `68c24b010ee464a66e0e853ab50f85b7e861e148` | Prompt-only 双向 Soul↔RP、Grant/撤销/预览、Schema 7、受信 Bridge Section | 目标 Memory/Story 持久化、RP↔RP、Host UI |
| Host contract | H0 | **ARCHITECTURE CANDIDATE / PENDING_INDEPENDENT_REVIEW** | — | 本分支[Host Integration Contract](../architecture/SP-004H-HOST-INTEGRATION.md)及六份 ADR | Runtime/真实 Host 适配 |
| Hermes Adapter | H1 | NOT STARTED | — | — | 受信 Principal、真实 lane/历史隔离、提交/返回围栏 |
| OpenClaw Adapter | H2 | NOT STARTED | — | — | 同一合同的 OpenClaw 实机接入 |
| Assets | L | SIDE TRACK | — | 现有 G 导入 IR | 原包/头像/升级历史 |

**当前路线：DONE A → G → D → E → B → J → C → K → F；CURRENT H0 架构候选；NEXT H1 → H2；SIDE L。** H0 只冻结 Host 身份、能力、会话 lane、消息来源、Prompt 发送前重验、晚到响应与 Bridge 确认合同；既有 Hermes/OpenClaw continuity 插件不等于角色 Host 集成。旧路线及上方各时点候选文字作为历史记录保留，不再指导当前顺序。
