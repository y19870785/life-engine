# SP-004K-003 — Prompt 预算与确定性裁剪

状态：**架构候选 / 待独立审核**。主合同见[Prompt Runtime 架构](../SP-004K-PROMPT-RUNTIME.md)。

## 决策

`PromptBudget` 独立于 Lore 激活预算。K1 固定总 UTF-8 字节与分节上限、必需控制/身份/Story 预留；token 上限通过可选 `PromptTokenEstimator` 抽象提供，不绑定任何模型 tokenizer。没有估算器时只能声明字节预算模式，记 `TOKEN_ESTIMATE_UNAVAILABLE`，H 在提交目标模型前做最终 token 门禁。

Item 是裁剪最小单位，字节统计包含标签、封装与正文；不切半条 Memory、Lore Entry、对话 turn、Story 结构项或多字节字符。固定策略：控制与必需身份、默认纳入的 Story 项为 `NONE`，超预算 `BUDGET_REQUIRED` 硬失败；Lore、Memory、可选角色示例使用稳定 `PREFIX`，遇到首个装不下的 item 即停止，不跳到较短后项；近期对话使用完整 turn 的 `SUFFIX`，优先保留最新交互。Memory 维持授权查询顺序，不在 K 重排；Lore 维持激活顺序。K 不用 LLM 选择、摘要或估算相关性。

可选内容被裁剪时 Snapshot 明示 `budget_exhausted` 并给固定诊断，例如 `LORE_TRUNCATED`、`MEMORY_TRUNCATED`、`CONVERSATION_TRUNCATED`、`CHARACTER_EXAMPLES_TRUNCATED`。空授权结果正常。必需项超限、预算参数非法或来源错配不能降级为空。相同输入、预算和估算器必须得到完全相同的包含项、字节、诊断和 fingerprint，不能受时间、随机数或集合迭代影响。

## 取舍与结果

稳定前缀可能留下少量空间，但不会因后来短项偶然插入而改变语义顺序。对话使用后缀是为了保留最近完整交互，不把最新用户问题裁掉而留旧历史。K1 应分别测试小预算、边界相等、UTF-8、必需项溢出和四平台确定性；不能把字节限制宣传为模型 token 安全。

## K1 实现状态

K1 候选固定总上限 1,048,576 UTF-8 字节、每 Section 物理上限 524,288 字节、每 Item 65,536 字节；规范 JSON 编码包含标签、来源与封装。Lore/Memory 用完整项稳定前缀，对话保留最新完整后缀；必需项或最新 turn 装不下时硬失败。无 token 估算器时给出诊断，不宣称 token 安全。状态：**IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**；原决策不变。
