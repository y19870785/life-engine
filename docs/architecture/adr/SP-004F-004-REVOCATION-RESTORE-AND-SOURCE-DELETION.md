# ADR SP-004F-004 — 撤销、恢复与来源删除的不复活门禁

状态：**F0 架构候选 / 待独立审核**。关联[主文档](../SP-004F-CONTROLLED-WORLD-BRIDGE.md)与[Memory 恢复合同](../SP-004B-WORLD-MEMORY.md)。

## 决策

Grant revoke 与 expiry 均为硬围栏：新投影拒绝，已生成但未发送的投影及包含它的 PromptSnapshot 在发送前重验时 stale。Grant revision 变化也令旧结果 stale。已发送给外部模型的内容无法召回；撤销不承诺模型“忘记”。已经经过目标 Runtime 显式接受的目标 Memory/Story 不因 revoke 被静默删除，它们有自身真源和治理合同，Bridge lineage 仍需保留。

持久 grant 的撤销记录必须独立于可回滚的业务 generation，具安装/Grant 身份和单调控制序列。F1 在启动、备份恢复及新 generation 激活前须重放并验证当前撤销控制；旧备份中 ACTIVE grant 与更晚的撤销相冲突时，结果必须仍是撤销/不可用。控制域缺失、损坏或与业务状态无法核对则 fail closed，不能因为旧备份“校验通过”而放行。控制记录只存最小撤销身份/版本，不复制 Bridge 正文。具体控制 DB/文件、锁顺序、写入意图和故障收敛由 F1 审核；可借鉴 Memory deletion control，但不能未经分析直接复制其实现。F0 不创建账本或 Schema 表。

源 Memory 删除/隐藏/不可用时，新投影与尚未使用的旧投影失效。恢复删除前业务备份时，当前 Memory deletion control 仍须先重放，随后 Bridge 重验来源；不能让删除源重新获得可桥接资格。若目标已独立接受一条跨域 Memory，撤销或删源不等于自动物理删除目标记录；但 lineage 失效必须能阻断不再安全的派生使用并触发明确目标治理/复核。现有 Memory lineage 仅同 Scope，F1 若不能安全实现此目标依赖，就先不开放目标持久写入。Story 当前无物理事件删除，不能假装存在 Story 删除控制。

来源或目标 TOMBSTONED：新桥接一律拒绝。ARCHIVED：仅 Owner 审计历史，不发新投影/写目标。Prompt target ACTIVE 且 OPEN Session；Owner 持久目标操作可不依赖 Session，但仍遵守目标 Runtime 生命周期门禁。过期不依赖后台调度，任何消费均比较当前可信 aware 时间。

## 理由与后果

若撤销只在可恢复 `life.db` 中，T1 ACTIVE 备份、T2 revoke、T3 restore T1 会直接复活权限，这是安全错误。独立控制与 fail-closed 激活是 F1 的前置验收，不是可选优化。已向模型披露内容和已经成为目标真源的数据则是另一种不可自动回滚的后果，必须如实说明。

## F1 实现状态

**IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**。F1 独立 Bridge 控制身份、连续序列、哈希链和锚；撤销先同步外部拒绝意图，再更新业务 Grant。恢复或中断后由协调器重放到当前 generation；业务 ACTIVE 与控制 REVOKED 冲突时只可拒绝或协调为 REVOKED。来源 Memory 删除仍由原 Memory deletion control 加同条件 Runtime 重查负责，Bridge 不复制第二份来源删除账本。目标持久化尚未开放。
