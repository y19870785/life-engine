# W0/W1：角色体验基线

日期：2026-10-14。本文是当前能力与证据索引，不是长期自主执行授权。

## 固定对象与来源

| 对象 | 本次观察／实现 Base | 含义 |
| --- | --- | --- |
| canonical main | `1758f3e8e82cd5cc5b385f545fee1df45742bdd6`（#55） | 本批启动时主线观察值，操作前须重新核验 |
| #56 | `5bcc4c484178d712e59cf3fb9032aa6473b48cfe` | 原生角色卡，Draft |
| #57 | `bc1e32aefdbbaaf54a90789c660e6ef26f72a97f` | 普通文本跨会话，Draft |
| #58 | `8bd2313a69cb87d9053d0b9641253d78f7aafa57` | Host 工具权限交集，Draft |
| #59 | `1d1ec6b7681684cbc44458e94344c261c5a2011b` | 统一入口，Draft；本批实现 Base |

依赖顺序为 main → #56 → #57 → #58 → #59。本分支继承这条未合并链；累计代码通过不替代每个 PR 的独立审核、Ready 授权、合并与 exact main CI。当前分支新增 Head 由提交记录确定，不将 Base 写成新 Head。

## 能力与阶段边界

- Core World、Memory、Lore、Story、Prompt、Bridge 和 Living 已有实现；Core 完成不代表真实 Host 交付完成。
- SP-006S0 与 M1-P0 协议文档已完成。M1-A 存储设计与隔离原语探针已有记录，结果仍为 [E0_SYNTHETIC_PARTIAL / M1-A_PRIMITIVE_GATE_PENDING](M1-A-PRIMITIVE-ADMISSION-EVIDENCE.md)。正式 M1 writer/verdict、M1.x、M2 不由 W0/W1 解锁。
- X1 已进入 #55 主线，是隔离合成体验；#56—#59 为独立命名 Profile 的 CLI / Chat Completions 试用，复用 Core World/Memory/Story，不等于正式 Soul Continuity。
- V2 只投影最近至多 12 个完整记录，总预算 48,000 UTF-8 字节；单条用户原话与回复各限 12,000 字节。USER_CLAIMED 的枚举值为 `user_claimed_fact`，只证明用户曾说过；模型剧情保持 FICTIONAL/CANDIDATE。
- 结构化纠正/遗忘、工具轮经历和超窗口检索均为 EXPECTED_GAP。原生卡片/世界书组装尚未收敛到正式 Core Prompt/Lore。
- Living Real Delivery 仍 DEFERRED，Full Private RP 仍 FROZEN_EXTERNAL_BLOCKER；本批 REAL_SEND = NO，不取得 SENT/ACK。

## 本批合同与协作

run ID：`w0w1-20261014-01`。用户已批准 W0-REVIEW_COMPLETE 与 W1 有界执行；Ready/Merge、W2—W4、schema/workflow 和正式 Soul 实施不在范围内。主协调维护唯一动作记录；A 单写仓库、B 独立审核、C 单写测试 Host。新增 Head 必须经 B 审核和主协调派发后才能部署。

W0 修正状态入口与历史标记，不重写历史验证原件。W1 先建立支持范围内基线，只有明确缺陷才修改产品实现。新隔离 Profile 不复制主身份、历史、任务或凭据；使用 Host 已有合法认证途径。真实模型工具集合为空；失败、重试在内的 provider 请求累计最多 12 次，由 C 持久计数。计数不可确认即停止，禁止渠道发送或生产 Gateway/cron 操作。

## 场景与证据层级

| 场景 | W1 判定与证据 |
| --- | --- |
| A 选定开场 | 原卡选择与实际请求一致；已有 native/import 测试及 T1 |
| B 新 CLI 会话 | 同 World、不同 SessionBinding、原话/候选来源、开场不重播；合成独立进程与 T2 分开 |
| C 不同角色/World | 隔离，拒绝交叉 Profile/Card 读取 |
| D 纠正虚构经历 | 只验证最新原话及来源；旧候选仍可能影响模型，结构化撤销 EXPECTED_GAP |
| E 遗忘 | 完整交互/派生失效未实现，EXPECTED_GAP；停用不表示删除 |
| F 工具轮 | T0/T1 合成消息保守拒绝；T2 不执行工具 |
| G 重复/失败/恢复 | 不重复写入、不投影 PENDING、旧 lease 拒绝；只在合成 fixture 注入故障 |
| H 超出窗口/字节预算 | 老记录仍持久存储，但不保证被召回；保持完整条目，不扩容 |

T0 是本地合成；T1 是真实 Hermes 插件调度与合成请求、不调用模型；T2 是真实 CLI 模型观察。每层单独结论，机器结构通过不等于模型体验完全合格。新增测试与运行状态见 [W1 验证记录](../validation/W1-HERMES-TEXT-BASELINE.md)。没有证据时写 NOT_EXECUTED/PENDING，不提前签 PASS。

既有指南中的实机观察属于其原固定对象的历史证据，不能自动移用到本批。结束时 C 记录退出、受控停用和漂移核验，保留世界与失败现场；主协调汇总代码、审核、CI、Host 与体验结果。

## 初批历史收口（2026-10-16，w0w1-20261014-01）

W0-REVIEW_COMPLETE；W1 EVIDENCE_PARTIAL。T0 合成与 V1 受限真实 dispatcher 获得证据，V2 辅助工具仍有 Host 接线阻断、两次尝试失败，T2 BLOCKED / NOT_EXECUTED；provider 请求 0。固定对象、清理和根因推断见 [验证记录](../validation/W1-HERMES-TEXT-BASELINE.md)。保留失败现场和当前代码，以 Draft 交付供后续修复；本批不继续改 helper 或扩大执行范围。

## 路径薄任务收口（2026-10-16，w1-path-20261016-01）

用户另行授权的路径薄任务 codeHead 为 d1df0f4。本地复现与独立测试已证明同文件解释器别名及 Windows 短路径修复；唯一真实 T1 越过原阻断、完成 World/SessionDB/V2 激活至 pre_llm_call，但 Host 自动依赖准备被拒后 exit 1，无 COMMITTED 或新会话投影。结论 PATH_FIX_VALIDATED、T1_NOT_PASSED / HOST_DEPENDENCY_GAP，W1 仍为 EVIDENCE_PARTIAL。raw report=PENDING 不代表仍运行；退出清理、保留现场与解释边界见 [验证记录](../validation/W1-HERMES-TEXT-BASELINE.md)。

T1 预算 1/1、provider 0；T2 BLOCKED。新最终 Head CI 待一次 push 后独立核验，旧失败记录不覆盖。本轮不再改 helper、不启动 Host 自动修复、不扩依赖权限；后续依赖接线工作需单独界定任务。#60 保持 Draft，Ready/Merge、W2—W4、正式 M1 未解锁。

## 无模型诊断收口（2026-10-17，w1-diag-20261016-01）

另行授权的诊断 codeHead da8beac 已取得 DIAGNOSTIC_LOCATION_CONFIRMED：用户行持久化中的显示去重分类导入 Host bootstrap，准备 uv venv 时被拒。request middleware 与 UID 标记已返回，persist_user 未返回；无用户行持久化完成、COMMITTED 或跨会话成功证据。完整 T1 仍 T1_FAILED / HOST_DEPENDENCY_GAP，W1 EVIDENCE_PARTIAL，T2 BLOCKED。

唯一诊断预算 1/1、provider 0；四项清理均返回、V2 已停用，12 个预绑定源摘要无漂移，新 8 源仅退出后观察。详细固定对象、调用链和现场边界见 [验证记录](../validation/W1-HERMES-TEXT-BASELINE.md)。本轮只定位，不修 Host 或依赖绑定，不重试；新最终 Head 的 CI 单独核验。后续绑定方案需另行界定任务，既有发布和阶段权限不变。
