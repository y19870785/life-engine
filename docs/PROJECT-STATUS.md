# 项目当前状态

状态观察日：2026-10-18（Asia/Shanghai）。本文是当前能力和证据的汇总入口；历史合同、原始验证记录及各阶段的授权条件继续各自有效。

代码验收基线：[`baa59729babf9ac56a17e02c682de2e3086e3575`](https://github.com/y19870785/life-engine/commit/baa59729babf9ac56a17e02c682de2e3086e3575)。它标识本次文档复盘所依据的代码，不永久代表最新 main；之后的文档提交也不需要倒填这个 SHA。

## 已经完成什么

| 能力 | 实现状态 | 能证明什么 | 不能证明什么 |
| --- | --- | --- | --- |
| World / Memory / Lore / Story / Prompt / Bridge、Living Core 与 Host Binding | 已有 Core 和本地实现 | 对应阶段的机械合同及模拟验证 | 当前真实 Host、模型、渠道的完整验收 |
| X1 跨会话记忆与虚拟日常样机（#55） | 已合并 | 隔离合成状态、来源和提示包；`MODEL_NOT_CONNECTED` | 真实模型体验、自动 Host 接入或正式 Soul Continuity |
| Hermes 原生角色卡（#56） | 已合并 | 独立 Profile 下的原卡提示、开场、示例对白与世界书兼容子集 | 完整 SillyTavern 宏、脚本、变量或全部世界书语义 |
| 角色连续性 V2（#57） | 已合并 | 普通文本轮的持久记录与受限跨会话投影；用户原话和模型候选剧情分源 | 工具轮经历、语义纠正/遗忘、超窗口召回及正式 Soul 身份证明 |
| 工具权限交集（#58） | 已合并 | 管理者许可与本轮 Host 提供 schema 的交集，以及调用前重核 | 所有主 Agent 能力都可用、媒体生成/发送或角色专用声线 |
| inspect → prepare → install / recover-config（#59） | 已合并 | 原卡故事展示、开场选择、兼容确认、新 Profile / World 与目标绑定恢复 | 真实 Host 依赖环境已完成隔离或完整角色体验已验收 |
| W0/W1 helper 与诊断（#60，经 #59 进入 main） | 已合并 | 路径别名/短路径修复、失败位置与清理记录 | 完整 T1、V2 COMMITTED 或 T2 模型观察通过 |
| ready 发布竞态修复（#61） | 已合并 | 完整 JSON 写好关闭后原子发布，确定性并发读取回归 | M1-A 不回滚原语、断电持久性，或旧 CI 超时根因已修复 |

角色指南：[统一导入](HERMES-CHARACTER-ONBOARDING.md)、[原生卡片](HERMES-CHARACTER-CARD-IMPORT.md)、[连续性 V2](HERMES-CHARACTER-CONTINUITY-V2.md)、[工具权限](HERMES-CHARACTER-CAPABILITIES.md)。

## 主线、体验和真实交付分别到哪里

| 轨道 | 当前结论 | 下一道证据门 |
| --- | --- | --- |
| Soul Continuity 正式主线 | `SP-006S0 = DONE`；M1-P0 协议文档已完成；M1-A 设计与探针已有交付，`E0_SYNTHETIC_PARTIAL / M1-A_PRIMITIVE_GATE_PENDING` | 真实 authority / admission / nonrollback 等原语证据；不能直接启动产品 writer/verdict |
| Hermes 角色体验验证 | `W1 EVIDENCE_PARTIAL`；完整 `T1_FAILED / HOST_DEPENDENCY_GAP`；`T2 BLOCKED` | 先明确并证明依赖环境与共享恢复写入的隔离，再独立授权 T1；T1 通过后才评审 T2 |
| Living Real Delivery | `DEFERRED`；当前链路 `SENT / ACK = NOT_ACQUIRED`，`ACK_VALIDATOR = HOST_GAP` | 专用 Host / transport / receipt 证据和独立任务 |
| Full Private RP | `FROZEN_EXTERNAL_BLOCKER` | 满足合同的官方 Host final-output commit 边界及独立验证 |

W1 的阻断发生在保存用户消息时：显示去重分类导入 `context_compressor → conversation_loop/process_bootstrap`，触发被拒的 uv venv 准备。request middleware 和 UID 分配返回，不代表用户行持久化、COMMITTED 或跨会话投影完成。早期固定 Profile 的历史成功观察不能覆盖本批失败。原始结论见 [W1 验证记录](validation/W1-HERMES-TEXT-BASELINE.md)。

2026-10-18 另一次只读静态准入核验（输入为 #60 合入后的 `2dc4349…`）发现：既有 venv 的 .pth/editable finder 在 helper 之前执行，并注册 63 个顶层映射回指共享生产环境；禁懒安装开关不能覆盖更早的更新恢复。该次结论是 `HOST_GAP / STATIC_ISOLATION_NOT_PROVEN`，Host/venv 启动、代码改动、T1 和 provider 均为 0；它没有制造新的运行失败，也没有重置前次已用预算。源码/依赖稳定性和整个运行期间的共享写入隔离仍需独立方案，见 [已知问题](KNOWN-ISSUES.md)。

`DATA_SCHEMA = 8`、`Schema Signature = SP-005A-living-runtime-v1`、`Prompt Template = SP-004K-prompt-v1` 保持不变。角色试用不激活正式 M1 Schema、Migration、Soul enrollment、writer/verdict、M1.x 或 M2。

## 合并与 CI 证据

| PR | 实际合并 SHA | exact push/main 结果 |
| --- | --- | --- |
| [#56](https://github.com/y19870785/life-engine/pull/56) | `2669a4a846c39acf93ebd10cefbefdcfc3c29dbc` | [39103961581](https://github.com/y19870785/life-engine/actions/runs/39103961581)：四矩阵成功，各 639 tests |
| [#57](https://github.com/y19870785/life-engine/pull/57) | `b1fbfc2694c45882c848b8dc1e978301615eb375` | [39107386322](https://github.com/y19870785/life-engine/actions/runs/39107386322)：Windows 3.11 ready JSON 竞态失败；其余三项成功；原失败保留 |
| [#61](https://github.com/y19870785/life-engine/pull/61) | `f5a6cbfc561de597b81a3ec14371989cf6da9479` | [39110579882](https://github.com/y19870785/life-engine/actions/runs/39110579882)：四矩阵成功，各 651 tests；#57 在新 main 修复 |
| [#58](https://github.com/y19870785/life-engine/pull/58) | `d4bcd7fc89fd30dc9e74519c553f1096cf046e62` | [39134857168](https://github.com/y19870785/life-engine/actions/runs/39134857168)：四矩阵成功，各 658 tests |
| [#59](https://github.com/y19870785/life-engine/pull/59) | `baa59729babf9ac56a17e02c682de2e3086e3575` | [39138679747](https://github.com/y19870785/life-engine/actions/runs/39138679747)：四矩阵成功，各 684 tests、0 失败；Ubuntu skip 3、Windows skip 2 |

矩阵为 Ubuntu / Windows × Python 3.11 / 3.12。tests 计数包含 skipped，不能改写为“684 项均执行通过”。#60 先合入 #59 源分支，其合并提交 `2dc434995de65bcd85cc1041abdc21504e819946` 不是单独的 main 提交。

上述五项在 2026-10-18 的代码收口时全部 MERGED，当时 open PR 为 0；随后文档 PR 的出现不推翻这条历史观察。最新 PR 和分支状态应读取 [GitHub PR](https://github.com/y19870785/life-engine/pulls) 与 [main](https://github.com/y19870785/life-engine/tree/main)。

旧 #59 source `2dc4349…` 的 [旧 PR CI38992484652](https://github.com/y19870785/life-engine/actions/runs/38992484652) 是 Windows 3.11 累计 45 分钟取消，底层慢因未确定。#60 `fa66fb4…` 的 [38940283429](https://github.com/y19870785/life-engine/actions/runs/38940283429) 四成功属于另一对象和运行。新对象成功不追认旧失败，也不把 ready 修复解释为旧超时根因。

## 怎么继续

- 本周进展与交付时间线：[周报](reports/WEEKLY-REVIEW-2026-10-18.md)。
- 分工、效率和改进：[开发方式复盘](planning/DEVELOPMENT-WORKFLOW-REVIEW-2026-10.md)。
- 近期建议、验收和停止点：[后续开发计划](planning/NEXT-DEVELOPMENT-PLAN-2026-10.md)。
- 长期阶段与既有合同：[长期路线](planning/LIFE-ENGINE-DEVELOPMENT-ROADMAP.md)、[Soul Continuity 计划](planning/SOUL-CONTINUITY-DEVELOPMENT-PLAN.md)。
- 全量文档的用途及历史边界：[文档索引](DOCUMENTATION-INDEX.md)。

本次用户授权复盘、规划和文档更新。后续计划是提案，不等于 Host、模型、渠道、正式 M1 或合并权限；不复用已经用尽的历史验证预算。
