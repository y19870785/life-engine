# SP-004E-001 — 重启后的会话恢复与写入围栏

## 状态

已实施候选；PENDING_INDEPENDENT_REVIEW。未授权转 Ready 或合并。

## 背景

OPEN Session 表示原运行代次授予的写权限，不能证明创建它的进程仍存活。数据库重开后原样恢复 OPEN 会产生陈旧写入风险。普通工作连接加入又不能每次都关闭有效会话。

## 决策

默认创建 `SQLiteWorldRepository(path)` 是新运行代次启动。一个 `BEGIN IMMEDIATE` 中先验证整个数据库，再关闭遗留 OPEN Session，给每个受影响 World 的 revision 和 writer_epoch 各加 1；Roleplay 变为 SUSPENDED，Soul 保持 ACTIVE；最后发布 `meta.world_runtime_id` 并提交。

World、Timeline、CharacterInstance、DefinitionRef、状态和关系数据不删除、不换身份。关闭的 Session 保存原 epoch 和 Principal。无 OPEN Session 的世界不变化；再次执行 recovery 返回 0，不重复推进围栏。正常 EXIT 后重启保留 SUSPENDED/CLOSED 和原 epoch，下一次 RESUME 再加 1。

每次事务在数据库锁内核对运行代次。旧 Repository 返回 `RecoveryRequired`，即使旧进程还活着也不能继续提交。可信协调方通过 `runtime_id=repository.runtime_id` 创建同代次工作仓储；缺失、过期标识拒绝加入。

显式 `recover_open_sessions()` 用于停止接收写入后的维护恢复；它保持同一运行代次，但关闭会话并推进 World 围栏。同一次恢复里的全部世界一起成功或回滚。

## 影响

恢复后 Roleplay 用户必须显式 RESUME，获得新的 Session ID 和 epoch。Soul 可重新 ENTER 绑定，保持独立生命周期。构造时的恢复错误不会提交一部分会话变化。

本方案没有进程存活探测、租约定时器或自动宿主集成。新建 Repository 默认代表启动，不能被当作连接池取连接；未来宿主需要明确区分启动协调方和工作连接。运行代次不是认证凭据，Principal 认证仍由可信适配层负责。

## 验证

`test_crash_recovery_is_idempotent_and_fences_old_repository`、`test_soul_crash_keeps_active_and_rebinds`、`test_epoch_nine_survives_restart_then_resume_is_ten` 和 `test_v3_restart_resume_preserves_all_values` 覆盖崩溃、正常退出、旧进程、Soul、幂等和身份保留。两个独立连接的竞争测试显式使用同一 runtime_id。

相关：[整体架构](../SP-004E-WORLD-SQLITE-PERSISTENCE.md)。
