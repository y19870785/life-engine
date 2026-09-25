# ADR SP-004H-002 — Session Lane and History Isolation

状态：H0 架构冻结候选；参见[主合同](../SP-004H-HOST-INTEGRATION.md)。

## 决策

`HostSessionKey(adapter, host_instance, host_agent_or_profile, conversation_id, context_lane_id)` 是 Host lane 身份；`HostLaneBinding` 只映射它与 principal、完整 WorldScope、Life Session ID、WriterEpoch、viewer、lane ID 和映射版本。`SessionBinding` 的创建/关闭仍属于 [`WorldRuntime`](../../../runtime/life_engine/world_runtime.py)，Host 不写 Session SQL，映射本身不证明 Session 仍 OPEN。每次使用重验 World ACTIVE、Session/Scope/principal/viewer、epoch、runtime_id/generation。一个 World 首版只能有一个 OPEN Life Session；第二并发 Host lane 拒绝。同 Host chat 可以先 Soul、再 RP、再 Soul，但各 lane 历史物理或逻辑隔离。

进入/恢复先读可信 World snapshot 获取预期 revision/epoch，再调 `enter()`/`resume()`，成功后绑定 RP lane。退出/挂起调用 `exit()`/`suspend()`，冻结旧 lane。跨 World 用单次 `switch_world()`，收到成功 receipt 后切 Host lane；若 Host 切换失败，进入 `RECONCILIATION_REQUIRED` 而非继续在旧/新 lane 猜测。World 与 Host 无共同事务，重试靠受信 operation identity 与 reconciliation，不跨 Host 调用持数据库锁。

私密 RP 必须实测 Host 不自动带入 parent chat、Soul chat、其他角色、thread、agent/workspace history；退出后 RP 原始历史也不进入 Soul。不能关闭污染时 `HISTORY_ISOLATION = UNSUPPORTED`，Roleplay 拒绝；`LIMITED` 不够。跨 World 例外仅为显式 F1 `BridgeProjection` 的许可字段，不复制 raw history。H1/H2 要用双向秘密标记的真实宿主测试证明隔离。

## 理由与后果

单靠 prompt 中“忽略旧历史”无法阻止模型看到旧内容。Host lane 是集成映射、World Session 是 Runtime 真源，二者都要重验。未来若需持久 HostLaneBinding，另审 Schema 与故障恢复；H0 不建表。
