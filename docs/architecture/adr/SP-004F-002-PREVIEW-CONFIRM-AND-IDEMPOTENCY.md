# ADR SP-004F-002 — 精确预览、确认、幂等与 CAS

状态：**F0 架构候选 / 待独立审核**。关联[主文档](../SP-004F-CONTROLLED-WORLD-BRIDGE.md)及[授权 ADR](SP-004F-001-BRIDGE-GRANT-AUTHORITY.md)。

## 决策

预览是只读、不可变的数据结构，不移动信息、不创建目标 Memory/Story。`BridgePreview(mode=GRANT|USE)` 必须展示完整双 Scope、DataClass、字段、目标 audience、Purpose、来源 reality/canon/lineage、逐项完整内容或其安全可显示摘要、是否持久、过期和精确版本。GRANT 预览用于建立/扩权/续期；USE 预览用于一次持久目标操作或未来要求逐次确认的高敏感 prompt 用途。未经确认的预览不成为 grant 或目标写入。

Preview 的规范 fingerprint 覆盖 mode、proposal/grant ID 与 revision、source selection/query、source scope/version、target scope 与所需 Session fence、Purpose、audience、字段、逐项内容/身份、预算及持久操作种类。HMAC `BridgePreviewToken` 绑定 fingerprint、runtime/generation 和有效性条件；不是认证凭据。Token 可在进程重启后失效；不能把旧 token 当可跨 generation 传递的许可。人工确认期间不开 SQLite transaction 或管理锁。

`confirm(preview_token)` 只确认**预览过的确切项**。它须重新验证 Owner 身份、当前 grant 或待创建 proposal、grant revision/撤销/过期、source Runtime 授权与版本、source 删除控制、target World/Session fence、purpose/audience、预算和 token。任一项改变返回 `PREVIEW_STALE`，不重新抓最新内容后静默提交。GRANT_ONLY 模式允许已确认的 prompt-only grant 在其范围内多次只读消费，但每次都重验来源和 target Session；持久目标写入必须 PER_USE 精确确认。Revoke 应立即生效，不用再等待预览确认。

Grant mutation 在持久事务内比较独立 `BridgeGrantRevision`，竞争单胜者。`BridgeIdempotencyIdentity(producer, source, slot)` 与规范 proposal fingerprint 绑定 create/modify/revoke/confirm/目标写入请求：同键同指纹返回原 receipt，异指纹 `IDEMPOTENCY_CONFLICT`；replay 先于 CAS 冲突。持久目标操作还须把稳定操作身份传入目标 Memory/Story Runtime，防止重试重复写入。Bridge 与目标 Runtime 若不能安全形成单事务，F1 必须设计意图/回执与宕机恢复，并说明何时审计“requested/completed”；不以空泛“原子”承诺掩盖跨边界故障。

## 理由与后果

`confirm(grant_id)` 会让用户确认旧画面、系统写入新来源数据。两阶段乐观校验把用户意图与精确来源版本绑定，也允许 UI 等待而不持锁。F0 只冻结接口与不变式；Preview token、审计表和故障恢复实现归 F1。
