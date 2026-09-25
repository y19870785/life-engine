# ADR SP-004H-006 — Bridge UX and Host Capabilities

状态：H0 架构冻结候选；参见[主合同](../SP-004H-HOST-INTEGRATION.md)。

## 决策

启动/重载握手使用既有 [`HostCapabilities`](../../../runtime/life_engine/domain_policy.py)；每项显式 `SUPPORTED`、`LIMITED`、`UNSUPPORTED`，未列为 UNSUPPORTED。完整 RP 必须 `STABLE_PRINCIPAL`、`STABLE_SESSION`、`MESSAGE_PROVENANCE`、`ISOLATED_CONTEXT_LANE`、`HISTORY_ISOLATION` 全部 SUPPORTED。`RELOAD_SUPPORT` 推荐 SUPPORTED；LIMITED 要在恢复重绑前禁用 RP。首版同步文本 `DELIVERY_ACK` 可 LIMITED，主动消息另设门禁。能力来自受信 Adapter 的实际验证，不来自模型或 Host prose。缺少私密隔离时只能 `SOUL_CONTINUITY_ONLY`，不能靠 prompt 文案隔离历史。

Host 负责给认证 Owner 显示 F1 `BridgePreview` 的 source/target World、data class、fields、PROMPT_CONTEXT、target audience、expiry；预览不授权。用户显式确认的是同一份 Preview，Adapter 将原对象/不透明 token 交 BridgeRuntime，不能仅传 grant_id、解析 token、悄悄重抓新源数据。确认 stale 时明确失败并重新预览；撤销同样需认证 Owner。模型、角色或工具文本不能 grant/revoke。F1 只有 Prompt-only Bridge，UI 不能承诺写入目标 Memory/Story 或“永久记住”。

真实 Host 版本、plugin load、用户认证、lane 与原生历史隔离必须在 H1 Hermes、H2 OpenClaw 分别实测；现有 [`bridges.py`](../../../runtime/life_engine/bridges.py) 连续状态插件及其 hook 不等于 H Roleplay 支持。H0 不改现有插件或 F1 Bridge Runtime。

## 理由与后果

Bridge 的显式授权会被糟糕 Host UI 误导为自动共享；能力的模糊声明也会把私密数据放进未隔离历史。强制精确预览与能力硬门禁能把这些错误在模型看到数据前拒绝。
