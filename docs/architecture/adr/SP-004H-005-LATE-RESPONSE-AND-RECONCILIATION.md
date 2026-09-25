# ADR SP-004H-005 — Late Response and Reconciliation

状态：H0 架构冻结候选；参见[主合同](../SP-004H-HOST-INTEGRATION.md)。

## 决策

模型提交时冻结 `HostModelCallFence(principal, scope, life_session_id, writer_epoch, runtime_id, generation, host_session_key, lane_id, prompt_fingerprint, conversation_version, host_model_call_id)`。返回时、写入 lane 或交付前，再核当前 Host lane、World/Session OPEN、principal、epoch、runtime/generation 与 conversation version。EXIT/SWITCH 后旧 RP 输出不能流入新 World 或 Soul；旧响应 DROP 或隔离待审计，不写 Memory/Story/对话。已真实送达的输出无法撤回；`prepare` 或生成成功不等于 delivery ACK。

重载/重连后废弃内存 HostLaneBinding 缓存，重新 attest capabilities、解析 Principal/Host lane，并对照 Life Engine 持久 generation 和 SessionBinding 重绑。无法证实时 fail closed，返回 `HOST_RELOAD_REQUIRED`/`RECONCILIATION_REQUIRED`。Host 与 World Runtime 是两个故障域，不承诺分布式原子提交。`HostOperationIdentity(adapter, host_instance, trusted_run_or_event_id, operation_kind)` 用于重复 hook/重试去重；同 key 同输入返回先前结果，异输入冲突。Switch 的 World receipt 先成功，再改变 Host lane；后者失败则暂停模型提交并协调，不把两步伪装成原子操作。禁止跨 Host API/模型等待持 SQLite 事务。

未来审计可存 operation/call ID、Scope、fingerprint、版本、结果码和真实 delivery receipt，不默认存敏感正文。H0 不实现出站日志或 Host 持久表。

## 理由与后果

发送前重验只能缩小 TOCTOU，不能保证数秒后的模型结果仍属于当前 Session。返回围栏与恢复协调是防止晚到答案污染新 lane 的必要第二道门禁。
