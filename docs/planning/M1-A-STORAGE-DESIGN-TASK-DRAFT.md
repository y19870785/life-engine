# M1-A — Continuity Storage / Admission 设计任务书草案

状态：`DRAFT / REVIEW_REQUIRED / NOT_EXECUTION_AUTHORIZATION`。日期：2026-10-09。

Roadmap Stage: Soul Continuity Mainline → M1 Soul Identity Core V1 → M1-A Schema / Storage Contract。
Why Now: M0 已冻结，M1-P0 给出了条件性持久化协议；在 Soul Identity 写入前必须选择并证明新增存储原语、旧版本准入和备份隔离路径。

## 1. 准入与本稿地位

本稿只供阶段目标与设计范围审核。规划编制时观察到的 canonical main 为 `25aa9aec7ceeb97d6fba99c913430c5296ec9e07`（PR #50 Squash commit），其 exact `push/main` CI #37703957820 四矩阵成功。这是历史观察，不自动成为正式执行 Base。

正式发布 M1-A 设计任务前，重新核验 main 与 M1-P0 独立收口结论，记录其被审合同版本、Base/Head、差异与结论；若尚无可追溯结论，补做独立 Gate 审核。只有用户批准本任务的确定版本与固定 Base 后，才开始设计执行。本稿本身不授权原语探针、故障注入代码、Schema/migration、Anchor/Record writer、active enrollment 或生产数据操作。

合同优先级：`SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md`、`M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md`、`M1-P0-IMPLEMENTATION-GATE.md`、`M1-P0-CRASH-RECOVERY-MATRIX.md`。阶段自主开发流程 R2 是拟议治理流程，生效条件见其 §10；本设计任务不靠流程提案取得产品权限。

## 2. 本次要回答的决定

设计应给出**单受信域**内的最小存储/准入方案，覆盖 Windows 与 Linux 目标环境，并精确描述可证明范围：

1. `D-business`、`D-registry`、`D-continuity-record`、`D-continuity-anchor` 的物理/逻辑边界、权限、备份与回滚策略。业务备份不能把 SoulRoot/退休 fence 回滚。无共同协调者的真实跨机器或 Host 迁移保留 `UNKNOWN`。
2. 一个 durable SoulRoot CAS 单位如何同时比较 root revision、source branch head、target `ABSENT` 和 Soul retirement fence；Genesis `expected SoulRoot=ABSENT` 只能有一个胜者。解释进程 crash、OS crash、断电以及平台/文件系统差异，不用 OS lock、先后两个写入或 registry 原子替换冒充 CAS。
3. immutable Record 如何在 Anchor 引用前 durable，引用后稳定寻址并受 GC 保护；Record hash、parent、`transition_id`、decision、目标 DataGeneration 与 protocol version 的完整性绑定。
4. 所有新旧 binary、管理 CLI、业务写入、Host permit 和 delivery 入口如何受可信 admission/version guard 约束；已运行旧进程怎样经 barrier/fence 停止越过新协议。列出无法改造或无法控制的入口并给 fail-closed 处理。
5. Schema 与 migration 的最小字段、版本变化和 legacy 数据的只读 `UNKNOWN` 路径。旧 `soul_id` 不自动升级为已证明的 continuation；ENROLL baseline 与 CREATE Genesis 保持区别。
6. Fork target 独立 Instance/branch Registry/Data binding。FORK 添加 target 不改变 source branch head、source registry/data pointer 或其运行权限；Soul 退役对所有 branch 生效。
7. 目标平台如何验证这些原语。列原始证据需求、可重复实验、故障模型、尚不能证明的保证和能力边界；不得将纯设计推断写成 PASS。

技术选型可以比较 SQLite、独立文件/日志或其他候选，但要给出首选及其证据计划。选型并不授权实施。如果候选都无法满足冻结合同，报告 `NO_SAFE_PROTOCOL_WITH_CURRENT_PRIMITIVES / STOP`；需要改变架构不变量时报告 `ARCHITECTURE_CHANGE_REQUIRED`，不通过降低故障模型继续。

## 3. 交付物

- **存储决策记录**：候选比较、选择理由、信任域与 rollback 边界、Windows/Linux 适用范围、平台假设和不可证明事项。
- **最小实体/Schema 合同**：SoulRoot、branch head、Record、Instance、DataGeneration 引用、protocol version 与 legacy 分类；不实现迁移。
- **入口和旧进程清单**：每个写/发入口的守卫、管理 barrier、停机/升级顺序、仍无法阻断的旧 binary 风险。
- **操作与故障顺序图**：CREATE、ENROLL、FORK、RETIRE 和普通 successor 的 prepare/CAS/activate 概念顺序；C01–C20、G01–G06、FK01–FK08 各项归属及待验证证据。
- **实施切片建议**：将允许的原语验证、存储实现、Schema/migration、M1-B read model、M1-C writer 和 M1-D transitions 分开，给每片最小范围、依赖与停止条件。规划切片不是自动授权。
- **证据台账**：下表每项填可复核来源、状态和阻断的后续动作；未取得证据填 `PENDING / NOT_PROVEN`。

| 要求 | 设计依据 | M1-A 存储原语 / admission 证明 | M1-C writer 证明 | M1-D transition 证明 | 当前状态与阻断动作 |
| --- | --- | --- | --- | --- | --- |
| SoulRoot 单次 durable 多条件 CAS | 待填 | 待验证 | 后续写路径验证 | 后续 transition 验证 | `PENDING / NOT_PROVEN` |
| immutable Record 引用保护 | 待填 | 待验证 | 后续写路径验证 | 按需 | `PENDING / NOT_PROVEN` |
| nonrollback Anchor / Soul retirement fence | 待填 | 待验证 | 后续写路径验证 | 后续退役验证 | `PENDING / NOT_PROVEN` |
| legacy/new binary admission 与旧进程围栏 | 待填 | 待验证 | 后续集成验证 | 后续 transition 验证 | `PENDING / NOT_PROVEN` |
| Fork target 独立数据绑定 | 待填 | 待验证 | 后续 activation 验证 | 后续 fork 验证 | `PENDING / NOT_PROVEN` |

M1-A 原有准入要求不可整体移到 M1-C/D：底层存储和 admission 保证要先取得各自证明；完整 writer 与 transition 的行为验证则在对应片完成。设计 PASS 只批准可供实施评审的方案，不提升任何 `PENDING` 为 PASS。

## 4. 审核与退出

ChatGPT 独立设计审核至少检查：与 M1-P0 合同逐项对应、选型的实际保证、平台差异、旧进程逃逸、备份回滚、Record GC、Fork source/target 和 retirement 的单 CAS、Schema 最小化，以及证据台账是否诚实。审核绑定设计文件的确切版本/内容 hash；若转成 PR，重新审核 Base/Head/diff。

设计草案退出为 `DESIGN_REVIEW_COMPLETE`，只表示选择、边界和证据计划被接受。**实施准入另需**：用户批准确切原语探针/存储验证范围和相应权限；验证取得 M1-A 要求的 durable CAS、Record/admission/备份/retirement 证据；Schema/migration 与产品写入再按独立范围授权。不得借“仅用合成 fixture”越过代码或测试授权。

设计阶段出现未解决的合同冲突或需要改变 World/Memory/Story/Living 真源、`Recovery != Authorization`、`UNKNOWN = FAIL_CLOSED` 等不变量，停止并交架构治理。即使设计通过，也不自动启动 M1-B/C/D/E、M1.x/M2、真实 Host、Provider 或 REAL_SEND。
