# 开发周报：2026-10-12—2026-10-18

统计时区：Asia/Shanghai；窗口为 10 月 12 日 00:00 至 10 月 18 日结束，事实截至代码链收口。审计范围为前一主线 `5cd993c1d9d286e3d903e36be54d3650446b5deb` 到 `baa59729babf9ac56a17e02c682de2e3086e3575`，结合源分支、PR 和原始验证记录；不是按 PR 创建日期统计。

## 本周结论

本周把体验目标从隔离合成样机推进为具备原生卡片、普通文本连续性、工具许可与统一导入流程的 Hermes 角色试用代码，并完成积压 PR 的主线合并。**代码交付已闭环，真实角色体验验证尚未闭环。** 完整 T1 仍因 Host 依赖准备受阻，T2 未执行；不能说“角色已经在真实 Hermes 中稳定长期生活”。

## 时间线与交付

| 日期 | 代码和验证进展 | 用户得到什么 / 限制 |
| --- | --- | --- |
| 10-12 | [#55](https://github.com/y19870785/life-engine/pull/55) 合入 main `1758f3e8e82cd5cc5b385f545fee1df45742bdd6` | X1 在独立临时实例演示记忆、虚拟日常与跨会话事实包；不接模型、网络或真实 Host |
| 10-13 | #56—#59 创建并开展独立审查；修改发生在源分支，尚不等于当天进入 main | 原生卡片 → V2 文本连续性 → 工具权限交集 → 故事/开场及统一导入，形成依赖链 |
| 10-14—10-16 | W0 统一体验基线；W1 进行受限 dispatcher / 合成请求验证；路径薄任务修复解释器同文件别名与 Windows 短路径 | 部分调度和路径证据有效；实际 T1 越过前一阻断后暴露依赖准备缺口，未获 COMMITTED/投影证据 |
| 10-17 | [#60](https://github.com/y19870785/life-engine/pull/60) 合入 #59 分支 `2dc434995de65bcd85cc1041abdc21504e819946`；无模型诊断结果归档/收口 | 定位到 persist_user 内 Host bootstrap / uv venv 准备被拒；不是 middleware 或用户消息已保存的证据 |
| 10-18 | #56、#57、必要修复 #61、#58、#59 按序 Squash Merge；每一步核实际 parent/tree 和 exact main CI | 原生卡片、连续性、权限交集和导入代码进入 main；测试 ready 半写竞态经确定性复现后修复；三份文档入口校准 |

周窗口内 main 有 6 个提交，合并 PR 为 #55—#61 共 7 个，其中 #60 通过 #59 进入 main，不重复计为第 7 个 main 提交。`git diff --shortstat 5cd993c… baa5972…` 为 40 个文件、5137 行新增、13 行删除；这是净差异而非工作量、质量或用户体验分数。周前 #51—#54 的治理、M1-A 设计和探针是本周输入，不冒充本周新交付。

## 从代码看到的能力变化

- [X1 样机](../../examples/experience_x1.py)让“记录→持久化→新会话事实包”可以离线观察；`MODEL_NOT_CONNECTED` 保持显式。
- [原生卡运行时](../../runtime/life_engine/hermes_card_runtime.py)和 [Hook](../../runtime/life_engine/hermes_card_native_hook.py)接入原卡请求内容；支持的世界书行为是明确子集，不复制整个 SillyTavern Runtime。
- [连续性模块](../../runtime/life_engine/character_continuity.py)复用 World、Memory、Story；用户原话按 `user_claimed_fact` 记录，只证明用户说过，模型文本保持 FICTIONAL / CANDIDATE。最多投影最近 12 个完整记录、合计 48000 UTF-8 字节，每条用户/回复各限 12000 字节；工具中间消息轮仍保守跳过。
- [统一导入](../../runtime/life_engine/character_onboarding.py)及 [Profile 配置](../../runtime/life_engine/hermes_profile_setup.py)加入故事/开场选择、兼容逐项确认、摘要重核、目标绑定、备份及分阶段回执；失败保留现场，恢复不覆盖发生漂移的配置。
- [W1 helper](../../tools/hermes_text_baseline_probe.py)增加阶段、拒绝栈和清理诊断，但不是通用 Host 沙箱。拒绝子进程并不证明 Host 导入没有其他文件副作用。

## 验证结果与未解决问题

最终 main `baa59729…` 的 [push/main CI39138679747](https://github.com/y19870785/life-engine/actions/runs/39138679747) 四矩阵成功，各 684 tests、0 失败，Ubuntu skip 3 / Windows skip 2。各 PR 的实际 SHA、CI 和 #57 原失败→#61 新 main 修复关系见 [项目状态](../PROJECT-STATUS.md)。完整测试数量增加证明覆盖面有变化，不能替代场景验收。

本周保留三类不同失败：

1. **确定性代码/测试同步缺陷**：#57 main CI 读取尚未写完的 ready JSON。#61 先让实际 worker 停在半写窗口复现，再同目录临时文件完整写入/关闭、原子发布，并加入并发读取回归。未修改数据库同步、竞争次数、CAS 或既有时限。
2. **累计 CI 超时**：旧 #59 的 [38992484652](https://github.com/y19870785/life-engine/actions/runs/38992484652) Windows 3.11 因 45 分钟限额取消，多个模块普遍慢，末尾 P07 栈不是已证实死锁。新 Head 和新 main 在原限额下通过，底层慢因仍未知。
3. **真实 Host 缺口**：W1 `T1_FAILED / HOST_DEPENDENCY_GAP`，显示去重分类导入触发 bootstrap 依赖准备；本批 provider 请求 0，T2 `BLOCKED / NOT_EXECUTED`。历史其他 Profile 的成功观察不移用。详见 [原始 W1 记录](../validation/W1-HERMES-TEXT-BASELINE.md)。

10-18 的后续静态准入还发现真实 venv 的 .pth/editable 映射回指共享环境，以及官方开关未覆盖的更早恢复写入边界。该次未启动 Host、未改代码、未用 T1 或 provider，结论为 `STATIC_ISOLATION_NOT_PROVEN`；这是静态缺口，不是另一轮真实 T1 失败。详见 [当前状态](../PROJECT-STATUS.md)及[已知问题](../KNOWN-ISSUES.md)。

M1-A 的 `E0_SYNTHETIC_PARTIAL / M1-A_PRIMITIVE_GATE_PENDING` 没有因角色代码或 #61 升级。当前同身份绕过和整体回滚反例仍在；正式 Soul writer/verdict、断电和管理域不回滚未证明。

## 开发方式的得失

主协调规划/记录、A 单写代码、B 固定对象独立审核、C 按需真实 Host 验证的分工，提高了错误定位、授权可见性和恢复能力。收益最清楚的证据是：发现真实 main 失败后没有沿用 PR 绿灯，能独立交付 #61，保留原失败并在新 main 验证。

代价也很明确：依赖 PR 长时间不合并，Squash 后下游产生历史冲突；同一事实散落多份 CURRENT 文档；Windows 完整 CI 串行放大等待；中断后人工对账与频繁“继续”增加协调负担。独立 Agent 也并非天然独立，仍需固定 checkout、证据和明确写入权。完整分析、具体改进和衡量指标见 [开发方式复盘](../planning/DEVELOPMENT-WORKFLOW-REVIEW-2026-10.md)。

## 下一周应聚焦什么

先让角色普通文本链取得可复现的真实 Host 证据：依赖/恢复写入隔离方案 → 本地实现与反例 → 另行授权无模型 T1 → 再评审小预算 T2。期间用少量工程任务降低 CI、PR 堆叠和文档维护成本，不扩展媒体、语音、渠道或工具轮长期记忆。正式 Soul 主线的原语证明按原 Gate 单独准备，不用角色旁线绕开。任务顺序、交付物和停止条件见 [近期计划](../planning/NEXT-DEVELOPMENT-PLAN-2026-10.md)。

这是一份复盘与规划；后续实施、真实环境访问和预算另按具体任务批准，不产生自动开始下一阶段的权限。
