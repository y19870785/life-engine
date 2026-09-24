# SP-004K-004 — 观看身份、用途与子系统边界

状态：**架构候选 / 待独立审核**。主合同见[Prompt Runtime 架构](../SP-004K-PROMPT-RUNTIME.md)。

## 决策

`PromptPurpose` 首版限 `ROLEPLAY_RESPONSE` 和 `SOUL_RESPONSE`；用途不是管理员开关。每份 Prompt 只属于一个完整 WorldScope、一个 OPEN Session、一个 viewer。Roleplay viewer 是当前 CharacterInstance；Soul viewer 是 Soul，不造假角色实例。Memory、Lore、Story 与对话的 Scope/viewer/Session 绑定必须吻合，Owner 查询/审计不可降格为角色结果。角色固定 DefinitionRef 不能跟随最新版本。

Story 的 Session 投影仍是**内部世界状态**，不是“角色已知事实”。首版 Roleplay 默认仅使用当前角色的结构化 state 和涉及该角色的关系；`world_facts` 与 `open_threads` 默认不进入模型。Soul 同样不因其身份而读取 Owner 全量 Story。这一保守选择防止全知角色及秘密线索泄漏；未来可通过明确可见性策略或经 Memory/Lore 授权投影开放。Story、Lore、Memory 有冲突时 K 分节保留来源，不自动判断真伪或改写任何子系统。

近期对话由 H 提供携带同 Session lane/Scope/viewer 的 `ConversationProjection`；K 不读取 Hermes/OpenClaw 历史或猜测消息来源。K 输出结构化 Snapshot，H 负责 Host 特定 role 渲染、实际能力判断和模型调用。`HostCapabilities` 中 `ISOLATED_CONTEXT_LANE`、`HISTORY_ISOLATION` 等必须真实受支持；Prompt 文案不能制造历史隔离。F 尚未实现，K1 的 Bridge 输入禁用；未来只接 F 授权的 BridgeProjection，正文仍是数据，不直接查询另一 World。K 不签发权限、工具许可、Bridge grant，也不写 Memory 或 Story。

## 取舍与结果

不把所有 Story world facts/open threads 默认注入会使首版角色上下文更窄，但当前 Story 没有 viewer 级可见性，这是可审计的安全边界。不提供跨 World Prompt、Soul aside 或多 viewer 拼接；这些需要独立的 F/H 合同。K1 必须测试跨 Scope/身份/Session 的硬拒绝、Owner 数据拒绝及默认 Story 可见性。

## K1 实现状态

K1 候选只允许 `ROLEPLAY_RESPONSE` 与 `SOUL_RESPONSE`，按当前 SessionBinding 核对观看身份。Soul 不造角色实例；Roleplay 只使用固定 DefinitionRef。Story 内部 `world_facts` 与 `open_threads` 均未进入模型 Section；Owner 审计结果、跨 World 与 Bridge 输入均不受理。状态：**IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**；原决策不变。
