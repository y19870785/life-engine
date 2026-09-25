# ADR SP-004H-003 — Conversation Projection and Provenance

状态：H0 架构冻结候选；参见[主合同](../SP-004H-HOST-INTEGRATION.md)。

## 决策

Adapter 为原始 `HostConversationTurn` 保留稳定 turn ID、Host 单调位置、内容和强类型 `MessageProvenance`：`EXTERNAL_USER`、`ASSISTANT_OUTPUT`、`TOOL_RESULT`、`SYSTEM_HOST`、`AUTOMATION`、`UNKNOWN`。模型/工具可写的 role 文本不可信。仅受信认证 external user 允许产生 Owner command；其他 kind 不得冒充 K1 普通 user turn 或授权动作。首版仅经 policy 许可的用户/助手 turns 映射至 K1 的 `ConversationTurn(user|assistant)`，其文本永远为 DATA。未来 Host summary 需单独来源类别，不能假扮原始 user turn。

经受信 Host factory 生成的 `ConversationProjection` 绑定一个完整 WorldScope、viewer、Life Session、lane ID、按 oldest→newest 的完整 turns、不透明 version 和 `ConversationVersionValidator`。版本必须对同一可见历史稳定、历史变更则变化；validator 的 `current_version(scope, viewer, session_id, lane_id)` 在组装及模型发送前可重验。不能提供可信版本/validator 就不能把快照标为可发送。Host adapter 自己有最大 turn 数、单 turn 与总 UTF-8 字节限额，具体 Host 数值 H1/H2 再定，并须服从 K1 的更高层限额；不按墙钟猜顺序、不切半条或截坏 UTF-8，最新用户 turn 不能被静默丢弃。

Core 仅消费适配结果，不读取宿主私有数据库或把 Telegram/WeChat 等专有 ID 类型塞入领域。两个 Host chats 不共享 Projection，除非未来有显式同 lane 合同；首版默认分离。

## 理由与后果

“role=user” 不足以区分用户、转发、工具和自动化；没有可信版本就无法发现 assemble 后的新消息。H1/H2 必须验证宿主 hook 实际提供稳定身份和隔离历史，而非凭 API 文案宣称满足。
