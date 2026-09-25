# ADR SP-004H-004 — Prompt Render, Submit and Revalidation

状态：H0 架构冻结候选；参见[主合同](../SP-004H-HOST-INTEGRATION.md)。

## 决策

Host 使用 K1 授权输入和 `PromptRuntime.assemble()` 取得结构化 `PromptSnapshot`。`HostPromptRenderer` 只映射 typed sections 到当前模型格式，不承担权限。`RUNTIME_CONTROL` 可用宿主特权通道；结构化状态保留来源和数据语义；Character/Lore/Memory/Story/Bridge/Conversation 正文均按 DATA 渲染，Bridge 永不提升为控制或工具权限。只有简单消息格式时，保留明确标签/边界，但不得把分隔符称为安全门禁。工具授权由受信 Host policy 独立决定，RP 首版不自动增加工具。

组装完成已由 K1 末尾重验；Host 渲染前检查 Snapshot，并在**紧贴模型提交前再次** `PromptRuntime.revalidate(snapshot)`。重验后不做无关异步工作，立即按同一 Snapshot 构造并发送；不可改 Section 后继续复用 fingerprint/token。Stale 只允许有限次重取：单纯 Conversation 变化可重新组装，World/Session/Bridge 授权变化必须重新解析 mode；重验失败不能使用旧快照。模型调用期间不持 SQLite 锁。无 token estimator 时 Host 对目标模型做最终 token 检查，不把字节预算冒充 token-safe。

模型返回后仍须 HostModelCallFence 再验；模型文本不自动成为 Memory、Story 或 Owner 操作。`PromptSnapshot` 是瞬时派生结果，Host 不能当真源或授予工具。H0 不冻结 OpenAI/Hermes/OpenClaw 消息字段或调用模型。

## 理由与后果

assemble 与发送间可发生 EXIT、SWITCH、Bridge revoke、Story/Memory/Lore/Conversation 更新；预先合法不等于发送时合法。渲染器保留 authority 是必要条件，真正的数据授权仍由 Runtime 和 Host 原生隔离提供。
