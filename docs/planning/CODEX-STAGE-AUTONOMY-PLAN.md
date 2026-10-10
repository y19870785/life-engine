# Life Engine 阶段自主开发方案

日期：2026-10-09。版本：R2。状态：`DRAFT / RE_REVIEW_REQUIRED`。

R1 独立审核：ChatGPT《调整开发规划》，2026-10-09，消息 `d327d361-7d0b-5453-b835-485335b3f55d`，结论 `CHANGES_REQUIRED`。R2 按 F01–F07 修订，尚未获复审 PASS。

Roadmap Stage: Soul Continuity Mainline / 阶段内开发流程调整。
Why Now: 用户已决定采用 ChatGPT 编制阶段任务书与阶段审核、Codex 在阶段内拆分任务、实现、独立代码审核、修复与验证的模式，需要将授权范围和恢复流程具体化。

## 1. 本轮决定与适用边界

用户已同意采用上述模式并要求开始规划。本文件落实该方向，不将其解释为 M1-A–E 全部实施、自动合并、Schema 激活、真实 Host 或发送授权。当前仅交付规划草案；未启动 Goal、后台调度或实施 Agent。

本方案获审定并填妥具体阶段授权后，阶段内部不再逐个请求已有授权范围内的编码、测试、修复和只读核验许可。现有文件中“每片独立授权”“ChatGPT 逐 PR 审核”“失败 CI 当次授权”等规则，需要在治理 PR 中显式列出替代条款和适用阶段，不能让新旧流程同时宣称生效。未被明确替代的架构、安全与授权规则继续有效。

## 2. 当前证据与历史区分

本轮只读远端核验：

- canonical main 观察值：`25aa9aec7ceeb97d6fba99c913430c5296ec9e07`，PR #50 的 Squash commit。
- PR #48、#49、#50 均显示 MERGED。main 规划记载 `SP-006S0 = DONE`；M1-P0 为持久化协议冻结，M1-A–E 尚未授权。
- exact SHA 的 `push/main` CI：<https://github.com/y19870785/life-engine/actions/runs/37703957820>，completed/success；Ubuntu/Windows × Python 3.11/3.12 四项成功。
- 本次没有执行 M1-P0 全量独立终审，不将“已合并 + CI 成功”替代独立 DONE 裁定。试运行准入时应读取已有独立结论；若无，则补齐一次。
- 本地工作分支为 `docs/soul-continuity-plan-v2`，HEAD `70289ea`，属于旧规划分支。本草案参考远端 main 合同；正式治理 PR 与实施必须从届时重新核验的 main 建立独立分支，不能从该旧分支直接续做。

上述 SHA 是本次观察快照，不是以后每个切片永久固定的 Base。

权威合同入口（以该远端 SHA 的内容为准）：

- `docs/architecture/SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md`
- `docs/architecture/M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md`
- `docs/planning/M1-P0-IMPLEMENTATION-GATE.md`
- `docs/planning/M1-P0-CRASH-RECOVERY-MATRIX.md`
- `docs/planning/SP-006S0-IMPLEMENTATION-PLAN.md`

## 3. 分工与评审独立性

| 角色 | 职责 | 不得自行决定 |
| --- | --- | --- |
| 用户 + ChatGPT | 阶段目标、范围、合同与阶段最终评审；用户授予执行权限 | ChatGPT 的审核 PASS 不替代用户未授予的权限 |
| Codex 主协调 Agent | 读取阶段合同、生成子任务、组织实施/审核、收集证据、决定已授权范围内的下一步 | 扩大阶段、改变成功定义、跳过 Gate |
| 实施 Agent | 在隔离工作区实现一个切片、测试、回应发现 | 把自检标为独立审核 |
| 独立审核 Agent | 从单独上下文读取冻结合同、确切 diff 与原始证据，提出可复现问题 | 修改产品代码后继续充当同一修改的独立审核者 |
| 验证步骤 / CI | 检查确切提交、文件范围、行为、矩阵和合并结果 | 以 CI 绿替代架构或产品结论 |

阶段启动合同应明确允许使用实施与审核子 Agent。首轮串行处理一个实施切片，不同时写多条主线。审核上下文从冻结合同和代码开始，实施摘要只作辅助；同一模型的独立上下文仍可能共享盲点，关键不变量须有正负例和故障证据。

审核使用独立 checkout，固定到被审提交；实施工作区的未提交文件不作为被审对象。记录审核者身份/聊天或 Agent ID、checkout、合同版本、Base、Head、完整 diff/文件集合、CI 的 SHA/event/run/attempt 和原始发现。实施者不能编辑或覆盖审核者原始报告；修复回应单独追加。协调者不得自行豁免阻断项，问题关闭须由独立审核者确认。审核者参与修复后，受影响修改须换另一位未参与实施的审核者复核。规划阶段尚无 commit 时，审核绑定完整文件内容的 SHA-256；未来治理 PR 仍须审核实际 diff。

## 4. 阶段授权合同

每个阶段只签发一份稳定合同，至少填写以下字段：

| 字段 | 内容 |
| --- | --- |
| Authorization ID / Version / Source | 唯一授权标识、不可静默修改的版本、用户原始授权消息及其明确批准的合同摘要/内容 hash |
| Authorization State | PROPOSED / ACTIVE / PAUSED / REVOKED / EXPIRED / COMPLETED；生效条件、适用切片、终止条件 |
| Stage / Goal | 阶段编号、可观察成果、明确终点 |
| Baseline / Contracts | 启动 Base SHA、架构文件版本、依赖 Gate 证据 |
| Scope | 可改模块/路径、允许新增的内部子任务、禁止范围 |
| Acceptance | 固定行为场景、负例、CI、平台与证据要求 |
| Delegation | 是否允许子 Agent；实施/审核工作区与角色约束 |
| Actions | 分别列明本地编辑、测试、commit、push、Draft、Ready、Squash Merge、CI rerun 的权限 |
| Migration | 是否仅允许合成 fixture，是否允许迁移代码，是否允许实际数据激活 |
| Limits | 总预算、最大修复轮次、CI 重试规则、外部等待上限 |
| Exceptions | 必须交还用户/ChatGPT 决策的条件 |
| Exit | 可合并交付、已合并且验证，或阶段独立验收；三者不可混用 |

建议同一切片最多三轮审核修复；仍有阻断问题则输出分歧与证据。具体 token/费用预算由阶段合同填写，本草案不代填。失败 CI 不自动当作基础设施抖动；区分产品失败与设施失败，并只按已授权重试范围操作。

只有原始用户授权及其条件可使权限生效，修改状态文件不能创造权限。Actions 空白或含糊时默认 DENIED；总资源上限须在启动合同中明确，用户也可明确选择不设额外 token 上限，系统限制始终有效。范围、验收、权限扩大或预算增加须新版本与用户授权；纯记录更新不改变授权。用户暂停、撤销或授权到期后不再发起新变更动作；记录已在途动作并只读核验结果，不假装远端动作可被撤回。恢复必须验证授权仍有效。因停止条件暂停的执行不能由协调者改状态自行解锁。

自主推进采用一次性有界授权：内部任务编制、实施、测试、审核、缺陷修复、已批准外部聊天的复审交接，以及具体 CI 重试额度，可以一起列入 Actions。获批范围内无需每轮重复问用户。普通可修复问题自动回到 FIXING；只有超范围、不可满足合同、超过累计轮次/资源限制或需人类取舍才进入 NEEDS_DECISION。阶段内独立 Gate 可以由指定审核者据证据裁定，无须用户重复批准同一已授权动作；阶段外权限不能据此继承。

## 5. 阶段内循环

1. 准入：重新核验远端状态、阶段授权和依赖证据；锁定本切片 Base、范围、验收。
2. 拆解：生成一个可验收子任务。新子任务必须属于既有范围，保持 M1-A → B → C → D → E 顺序；不能发明新架构阶段。
3. 实施：隔离分支/工作区，写代码与适当测试，保留原始结果。
4. 独立审核：记录 reviewer、Base、Head、文件集合、问题、证据和结论。合同违规、未解释行为差异、必需证据缺失均阻断。
5. 修复：逐条处理问题；新 Head 必须重新取得适用审核，不能沿用旧 Head 的 PASS。验收条目不可为使测试通过而删除或降级。
6. PR Gate：若已授权，创建 Draft 并核验 exact Head CI。Ready 前确认最新 Base/Head、diff 与审核适用性。
7. 合并：仅在本阶段明确允许时执行固定获审 Head 的 Squash Merge。Auto Merge、force-push、绕过保护规则均禁止。GitHub required review 不能由一份本地 Agent 报告冒充。合并前必须满足下文的 Base 竞争控制。
8. 合并后：由未参与该修改实施的独立审核者，核对实际 PR/Head/Squash 对象、Squash 唯一 parent 等于获审 Base、完整 Git tree 等于从获审 Base 应用获审 diff 的预期 tree、无额外文件，以及 exact Squash SHA 的 `push/main` 四矩阵。协调者可采集证据，不能把自己的合并报告判为独立 PASS。失败则阶段标为验证失败并停止下一切片，不自动 revert 或跳过。
9. 下一步：只有该切片完成、下一切片已在阶段授权内且依赖满足，才自动继续。阶段出口汇总后交 ChatGPT/用户最终验收，不进入 M1.x/M2。

建议状态记录：`PLANNED → IMPLEMENTING → REVIEWING ↔ FIXING → REVIEW_COMPLETE → POST_MERGE_VERIFY → SLICE_DONE`。首轮 REVIEW_COMPLETE 后进入 `REVIEW_COMPLETE_AWAITING_HUMAN_GATE`，GitHub PR 仍为 Draft，`Ready=DENIED / Merge=DENIED`。后续有条件式合并授权时才允许自动执行平台 Ready/合并步骤。异常记 `NEEDS_DECISION`；阶段区分 `STAGE_ACCEPTANCE_PENDING` 与 `STAGE_DONE`。记录状态不冒充 Goal 工具状态或生命周期控制。

Base 变化时核验提交来源。自身上一切片的已验证合并允许成为下一切片的新 Base；其他来源导致本切片固定 Base 漂移时停止，重新裁定兼容性，不悄悄 rebase 或抹掉审核溯源。

合同版本、Base、Head、完整 diff/文件集合或 CI 对象任一变化，原审核都需重新裁定适用性，并保留新结论；不能只比较 Head。main 在合并后又出现其他提交时，不将先前 CI 当作新 main 的证明，停止自动续片并裁定。

### 合并竞争控制

`--match-head-commit` 只约束 Head，不是 Base 的原子锁。自动合并必须先证明目标分支写入已被服务端保护机制或覆盖全部写入者的受控独占窗口约束，且实际合并时 Base 等于获审 Base；本地互斥不约束其他用户/服务。阶段合同应记录机制、覆盖范围、旁路权限与核验证据。不能证明这些条件时，自动合并默认不可用，降级至人工关口；只读轮询 main 不能填补此缺口。未来若选择 merge queue 等机制，须另审其合并方式和实际 Base，不默认与固定 Base + Squash 合同兼容。

即使已有预防措施，也要做第 8 步事后检测：出现 parent/tree 不符则记 `POST_MERGE_MISMATCH`，阻断续片并通知用户；不得事后补批、自动回滚或把已发生的竞态称为已预防。当前尚未调查或配置远端写入保护，不声称自动合并已可安全启用。

## 6. 首轮试运行：M1-A 准入与存储合同

不把 M1-A–E 一次全部交给自动循环。M1-P0 明确 `NEW_PRIMITIVE_REQUIRED = YES`：非回滚 durable SoulRoot CAS、稳定可寻址 immutable Record、legacy admission guard 及独立 fork target binding 均需要实际证明。当前下一步先形成 M1-A 的准入与存储决策材料。

### 第一步：M1-A 任务书与技术方案（设计交付）

在本流程草案审定后，按既有 M1-A 定义准备：

- Windows/Linux 存储选择及 durability 依据；区分进程 crash、OS crash、断电保证及尚不可验证的部分。
- SoulRoot Genesis single-winner CAS、Fork source/target 双条件和 Soul-level retirement fence 的可实现性分析。
- Record 引用保护/GC、非回滚域与业务备份的边界。
- 所有旧/新 binary 入口的 admission/fencing 清单，含已运行旧进程失效路径。
- Schema/Migration 和独立 target Registry/Data binding 的最小合同。
- 将 C01–C20、G01–G06、FK01–FK08 分配到 M1-A 与后续 M1-C/D 的证据表；不能将后续 writer 证明提前声称为已完成。

退出：可以供 ChatGPT 审核的明确技术选择、最小实施范围、证据方案与停止条件。仍不可创建“空表”、Anchor prototype、active enrollment 或写生产数据。技术选择不能满足冻结语义时报告 `NO_SAFE_PROTOCOL_WITH_CURRENT_PRIMITIVES / STOP`；需要改变冻结合同则报告 `ARCHITECTURE_CHANGE_REQUIRED`。

### 第二步：获批后的 M1-A 实施试运行

仅在存储合同与具体实施权限获批后，启动 Goal 和实施/独立审核循环。仅使用隔离合成数据；允许范围按任务书冻结，不操作真实 Host/生产数据。

建议首轮授权至 `REVIEW_COMPLETE_AWAITING_HUMAN_GATE`：允许 commit/push/Draft 和审核修复，GitHub PR 保持 Draft，`Ready=DENIED / Merge=DENIED`。首轮验收重点是闭环是否能可靠交付、能否发现错误及正确停在边界，而非追求一次跑完整个 M1。

### 设计出口与原语证明分离

技术方案 PASS 只接受技术选择、合同和证据计划，不证明 durable CAS、旧 binary fencing 或断电保证已成立。设计报告逐项列出：要求、设计依据、存储原语验证、M1-C writer 验证、M1-D transition 验证、证据位置、状态与阻断的动作。没有证据填 `PENDING / NOT_PROVEN`。

| 层次 | 必须保留的准入责任 |
| --- | --- |
| 设计依据 | 明确平台/文件系统/故障模型与技术保证，不能以普通进程 kill 证明断电持久性 |
| M1-A 存储原语 / admission | durable SoulRoot 多条件 CAS、immutable Record 引用保护、备份不回滚 Anchor、旧 binary/已运行进程 fence 与 target binding；M1-A 原有门槛不得延期给 M1-C/D |
| M1-C writer | 全协议写入顺序、lost ACK、幂等恢复、故障矩阵和新进程证据，不替代底层存储保证 |
| M1-D transition | 各 transition、并发/退役/复制等完整行为证据，不追溯抹平早期准入缺口 |

任何探针、原型、故障注入代码、Schema/迁移代码必须逐项列入另获批的实施范围；“合成 fixture”只限定数据，不是写代码的授权。若准入证据必须通过受控原语验证取得，先提交明确的验证范围和激活禁令供授权，不自行把验证藏进设计任务。证据未满足时不能开放 active write；如需调整既有 Gate，单独治理，不能靠任务拆分绕过。

### 第三步：扩大到阶段内条件式合并

试运行通过后，由用户明确授予后续指定切片的 Ready/Squash Merge 与合并后验证权限。保留独立技术 Gate，自动化其证据采集和执行；不能把“省去逐次询问”解释为取消 Schema 或存储评审。

M1-B/C/D/E 按原顺序推进，各片具体范围必须先进入阶段合同。M1-D 每种 transition 保留独立审核。M1 出口不等于 M1.x Proof PASS；M1.x、M2、真实 Host/发送始终需要新阶段合同。

## 7. 持久状态与运行恢复

首轮只增加必要的阶段任务书、运行记录和审核证据，不先建设通用编排平台。建议运行记录包含 stage/task ID、合同版本、Base/Head、PR、审核发现、CI run/attempt、合并 SHA、预算/修复轮次与下一动作。

启动 Goal 前先落地阶段合同。Goal 负责跨轮次继续推进；外部 CI 等待如需要另行使用明确授权的跟踪安排。此草案不创建后台自动化，不承诺桌面关闭/离线后仍运行。

恢复时先核对远端和本地事实，再读取运行记录：PR 已合并就只恢复合并后核验；push/merge 结果未知就先查询，不能重复执行；审核对象改变则原审核失效；禁止由聊天摘要直接恢复授权。实现单个主协调者写运行记录，避免多个 Agent 竞争推进。

阶段自主运行启用前，须有最小协调保护并经过验证（本草案不声称已经实现）：

1. 对同一仓库/阶段持 OS 级排他锁，记录 run ID、进程身份及启动标识。接管前证明旧协调者及其仍可执行写动作的子进程/Agent 已停止；时间戳过期不算证明。多机不能用本地锁声称全局唯一，未有受控单写入口则停止。
2. 运行记录在同一文件系统以临时文件写入、刷盘及原子替换保存，保留可校验的序号/上一版本。损坏或保存失败时停止变更并只读对账；不能猜出“最新”记录。原子性/持久性按实际平台验证，不能只因使用 rename 就宣布满足。
3. 每次 push、建 PR、merge、CI rerun 前记录 action ID、授权版本、仓库、branch/PR、预期 Base/Head、run/attempt、前置状态与 INTENT；完成后记录 CONFIRMED 或 UNKNOWN。恢复先查询远端；UNKNOWN 时等待或停止，不重新发起。服务没有幂等键时 action ID 仅用于对账，不能承诺 exactly-once。
4. 已发起调用、修复轮次、CI 重试次数和资源消耗跨恢复累计；不能换聊天/重启清零。恢复证据不足时保守停止。
5. 最小验证覆盖双协调者竞争、记录写入中断、远端成功但回执丢失、授权被撤销、累计额度恢复。任何保护实现需纳入明确授权的开发工具范围，不借产品 M1-A 权限修改 workflow 或产品 Runtime。

开发编排恢复与产品恢复分离：运行记录不能签发或恢复产品 management decision、transition 权限或 execution authority。产品仍分别判定 `Persistence Fact / Identity Verdict / Operational State / Execution Authority`；完整已提交但未激活可以是 `COMMITTED / CONTINUATION或FORK / ACTIVATION_PENDING / DENIED`，不能一律归 UNKNOWN 或据恢复成功自动赋权。

## 8. 全阶段停止与安全边界

- 超出 Scope、需要新架构/Schema 语义、无法满足原语合同，或审核分歧不收敛。
- 需要真实 Host、Provider、Default Home、生产迁移、真实发送或跨机器 authority 才能继续。
- 原始证据缺失、外部 Base 漂移、GitHub 权限/保护规则阻断、预算到限。
- 不得删除失败测试、降低验收、伪造审核/ACK，或将 simulated/historical evidence 升格为当前真实验证。

`Soul != Model/Host`、`Recovery != Authorization`、`UNKNOWN = FAIL_CLOSED`、World/Memory/Story/Living 各自真源和 Full Private RP 冻结边界保持。

## 9. 落地顺序与评审清单

1. ChatGPT 审核本方案：重点评审角色独立性、阶段授权、Base 漂移、重复执行恢复、试运行范围与停止条件。
2. 治理 PR：从最新 main 落地本方案并明确更新 `SOUL-CONTINUITY-DEVELOPMENT-PLAN.md`、`LIFE-ENGINE-DEVELOPMENT-ROADMAP.md`、`M1-P0-IMPLEMENTATION-GATE.md` 中受影响的流程条款；保留旧规则的历史属性与技术合同。发布/合并权限按具体授权执行。
3. 补齐或引用 M1-P0 独立收口证据，编制 M1-A 技术方案与阶段任务书。
4. 审定 M1-A 存储合同和试运行权限后，启动首轮阶段内自主循环。
5. 首轮结束评估审核漏项、返工轮次、人工介入原因及证据完整性，再决定后续切片是否开放条件式合并。

本次交付是一份可评审的流程与试运行规划，不改变任何 Runtime、tests、Schema、workflow、Host 或远端 PR 状态。

## 10. 治理过渡与确切生效点

本方案的治理 PR 自身沿用旧流程：Draft → ChatGPT 独立审核 → 用户授权 Ready → 轻量终审 → 用户授权 Squash Merge → exact main CI → 独立合并后核验。不能用本方案批准自身。只有治理 PR 完成独立收口后，新流程才对另有有效阶段授权的后续工作生效；“流程生效”和“某阶段获执行权限”是两个条件。

治理 PR 必须在最新 main 逐条核对并落实下表；其他同义入口如被发现，一并列出，不只修改摘要。旧规则保留为标明日期/版本的历史，不与 CURRENT 同时有效。

| 原文件 / 条款 | 替代规则 | 适用阶段 | 保留 Gate |
| --- | --- | --- | --- |
| `SOUL-CONTINUITY-DEVELOPMENT-PLAN.md`，开发与审核节奏：逐片授权、逐 PR ChatGPT 审核 | 有效阶段合同列明内部切片权限；指定独立 Agent 做片内审核，ChatGPT 做阶段验收 | 仅签发新合同的阶段 | 固定行为验收、独立审核、合并后 exact CI |
| 同节：失败/取消 CI 须当次授权 | 可预授权具体设施故障分类、次数与等待额度；产品失败修复后按批准测试计划验证，不用 rerun 掩盖 | 仅 Actions 明列的重试 | 无额度不重跑；失败证据保留；次数跨恢复累计 |
| `LIFE-ENGINE-DEVELOPMENT-ROADMAP.md` §18，逐次 Ready/Merge 授权 | 试运行仍人工关口；后续可依据有效合同和 §5 竞争控制条件式推进 | 明列 Ready/Merge 权限的后续切片 | 禁止 Auto Merge/force-push/绕保护；独立合并后核验 |
| `M1-P0-IMPLEMENTATION-GATE.md` §2，M1-A–E 每片独立授权 | 可由用户在同一阶段合同分别列明各片权限，满足依赖后自动推进 | 仅明确列入合同的切片，未列默认拒绝 | A→B→C→D→E 顺序；A 存储/Schema 评审；C 写路径权限；D 每 transition 独立审核 |
| `SP-006S0-IMPLEMENTATION-PLAN.md`，共同边界及 M1/M1.x/M2 准入 | 对明确采用本流程的阶段引用授权合同；阶段间仍单独授权 | 指定阶段内 | M1-P0 Gate、M1 出口、M1.x Proof Gate、M2 入口全部保持 |

架构方向、Schema 语义、Host/发送、Full Private RP、实际数据激活和跨阶段权限不被这张表放宽。治理发布前缺少互斥工具不妨碍审核流程设计，但正式启动自主执行前必须完成 §7 的保护实现/验证准入；该工具工作是独立有界任务，不暗中扩展 M1-A。

## 11. R1 审核意见处置

| Finding | R2 修订位置 | 验收方式 |
| --- | --- | --- |
| F01 | §4 授权 ID/版本/来源、生命周期、默认拒绝与撤销 | 检查空权限、改 Scope、恢复和撤销场景不能自动获权 |
| F02 | §3 独立 checkout 与原始报告归属 | 审核对象可复现；实施者不能关闭阻断项 |
| F03 | §5 审核绑定、Base 竞争控制与降级 | 仅锁 Head 不足时不能自动合并 |
| F04 | §5 第 8 步独立 parent/tree/CI 核验 | 合并异常或 main 漂移均阻断续片 |
| F05 | §7 互斥、原子记录、动作对账与累计额度 | 启用前通过列明的恢复故障场景；当前为计划非实现证据 |
| F06 | §6 四层证据归属与探针授权 | 设计 PASS 不提升原语证明，不延期 M1-A 门槛 |
| F07 | §10 原条款映射与生效点 | 治理 PR 旧流程自举；新流程与阶段授权分别生效 |

处置状态均为 `ADDRESSED_PENDING_INDEPENDENT_REVIEW`，不是协调者自行关闭。首轮内部状态已改为 `REVIEW_COMPLETE_AWAITING_HUMAN_GATE`。M1-P0 独立 DONE 证据仍待定位/核验，不因本流程修改而升级。
