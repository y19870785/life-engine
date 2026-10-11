# M1-A — Continuity Storage / Admission 设计任务书草案

状态：`PROPOSED_V1 / REVIEW_REQUIRED / DESIGN_ONLY`。日期：2026-10-11。

Roadmap Stage: Soul Continuity Mainline → M1 Soul Identity Core V1 → M1-A Schema / Storage Contract。
Why Now: M0 已冻结，M1-P0 给出了条件性持久化协议；在 Soul Identity 写入前必须选择并证明新增存储原语、旧版本准入和备份隔离路径。

## 1. 准入与本稿地位

本任务书的拟定设计 Base 为 `c26d6c5c4a721bedf7dde6c6575ee23277574dd6`（PR #52 Squash commit）。[exact `push/main` CI #38107717191](https://github.com/y19870785/life-engine/actions/runs/38107717191) 四矩阵成功，PR #52 已获独立 `M1-P0_DOC_DONE`。原 PR #50 Squash `25aa9aec7ceeb97d6fba99c913430c5296ec9e07` 与 PR #51 Squash `462eee14bdc4be32c163797bc528ea7c0bba7c22` 均为历史 Base，不自动替代当前 main。正式设计启动前仍须重新检查远端 main 未漂移。

2026-10-11 准入复核结果：独立内容终审曾发现上游 CREATE 首代 `0` 与 M1-P0 `G1` 冲突（F01）；PR #52 将首代校准为 `G0`，独立审核裁定 `F01_CLOSED`，并在合并后 exact main CI 全部成功后裁定 `M1-P0_DOC_DONE`。这是文档协议准入证据，不是目标平台存储原语证明。

正式发布 M1-A 设计任务前，重新核验 main 与 M1-P0 独立收口结论，记录其被审合同版本、Base/Head、差异与结论。用户先前的“授权”是准备任务书的历史依据；正式设计授权的来源必须是用户看到本确定版本、内容 hash 和固定 Base 后作出的明确批准，不能由本文件自行签发。拟议范围仅为只读源码/合同调查及 `docs/planning/` 下的设计文档，允许已批准范围内的修订和独立设计审核；不含原语探针、故障注入代码、Schema/migration、Anchor/Record writer、active enrollment、真实 Host 或生产数据操作。

合同优先级：`SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md`、`M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md`、`M1-P0-IMPLEMENTATION-GATE.md`、`M1-P0-CRASH-RECOVERY-MATRIX.md`。[阶段自主开发流程 R2](CODEX-STAGE-AUTONOMY-PLAN.md)已随 PR #51 完成独立收口，但流程本身不签发产品实施权限。

### 拟议的设计授权合同（待确切版本审定）

| 字段 | 拟议值 |
| --- | --- |
| Authorization ID / Version / Source | `M1-A-DESIGN-V1`；先前“授权”仅为任务准备依据；正式 Source 待用户对本确定版本及 SHA-256 的明确批准消息定位后填写，缺失时仍为 `PROPOSED` |
| State / Base | `PROPOSED`；固定设计 Base 为 `c26d6c5c4a721bedf7dde6c6575ee23277574dd6`；获批后为 `ACTIVE`，可由用户暂停/撤销，到期或出口后分别记 `PAUSED / REVOKED / EXPIRED / COMPLETED`；启动、恢复及每次远端变更前重验用户授权、main 和依赖证据 |
| Goal / Exit | 交付 §3 的设计材料，先取得独立 `DESIGN_REVIEW_COMPLETE`；之后才允许提交、推送、建立一个 Draft PR，对实际 Base/Head/diff 另作审核，exact Head CI 作为后续 PR Gate 证据；最终停在 `REVIEW_COMPLETE_AWAITING_HUMAN_GATE`，不要求 Ready/Merge，不宣称仓库任务 DONE |
| Actions | 只读源码/合同核验、编写 `docs/planning/` 设计文档、独立设计审核与同范围最多三轮修订；独立设计 PASS 后在隔离分支提交并推送设计文档、创建一个 Draft PR；Ready、Merge 和 CI rerun 均不在本拟议授权内 |
| Scope / Migration | 不改 Runtime、Schema、tests、workflow；不运行原语探针；仅分析合成/隔离数据方案，不接触真实 Host、生产数据或真实发送 |
| Acceptance | §2 全部决策、§3 全部交付物、可追溯 C01–C20/G01–G06/FK01–FK08 归属；不具证据的保证一律 `PENDING / NOT_PROVEN` |
| Limits / Recovery | 一份设计主文档、一个 Draft PR、最多三轮独立审核修订；CI 重试额度 0；单次 CI 等待最多 60 分钟、独立审核等待最多 30 分钟，超时记 `PENDING` 并停止新变更动作；无后台自动运行；累计轮次跨会话保存，超出后停止；拟议不设额外 token/费用上限，仍受系统限额约束，须由用户明确批准 |
| Delegation / Review | 本合同不启用实施或审核子 Agent，也不启用 R2 §7 阶段自主循环；ChatGPT 设计审核仅向用户已授权的独立审核会话交接确切文档，跨聊天发送权限若不成立则先取得授权 |
| Exceptions | M1-P0 独立收口缺失、main 外部漂移、候选与冻结语义不相容、无可行验证路径、必须降低保证或需扩大动作时停止并交用户/ChatGPT 决策；纯实验实证缺失应诚实列 `PENDING / NOT_PROVEN` 并给验证方案，不误判为设计失败 |

本表是供审批的具体边界。只有用户确认其确定版本（含内容 hash、固定 Base 和资源限额）后，状态才可从 `PROPOSED` 进入 `ACTIVE`。设计交付物在已批准范围内的三轮修订、commit/push 和复审无需逐轮批准；授权合同的范围、验收、权限或资源上限扩大则需新版本和用户授权。暂停、撤销、到期后不再发起新变更动作；只读对账已在途动作，恢复时重新核验授权和远端状态，不靠修改状态文件自解锁。若将来启用阶段自主循环，须先另行完成 R2 §7 协调保护准入；本合同不授权实现该工具。

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
