# SP-004D — 质量门禁

状态：PENDING_INDEPENDENT_REVIEW。实施授权：仅限 SP-004D。合并授权：未授权。

基线：`f71d1b7f1718bc8be9916b1c09dde625aaa0d362`。分支：`feat/sp-004d-world-instance-runtime`。

相关文档：[角色实例与世界会话运行基线](../architecture/SP-004D-WORLD-INSTANCE-RUNTIME.md)。

## 自动化测试

| 门禁 | 实际结果 |
| --- | --- |
| Windows 新增领域运行测试 | 28/28 PASS |
| WSL/Linux 完整测试集 | 128/128 PASS，包含 100 项既有测试与 28 项新增测试 |
| Windows 完整测试集 | 128 项，5 个既有 SQLite 清理错误、1 个既有跳过；新增测试全部通过 |
| Python 导入与发布包 | world_runtime、world_repository 可导入，既有 release_files 收集两个新模块 |
| 数据结构 | DATA_SCHEMA == 2；既有生产文件无修改 |
| 文档与差异 | 本任务文档相对链接检查、Python 语法检查及 git diff --check |
| 私有语料 | 未读取、扫描、复制或上传；只使用原创合成 V3 数据 |

测试命令：

```text
python -m unittest discover -s tests -p test_world_runtime.py -v
python -m unittest discover -s tests
git diff --check
```

完整测试已在 Windows Python 3.12 和 WSL Python 3.11 环境执行。日志留在本地临时目录，不提交。Windows 的五个错误与既有基线一致，均为临时 SQLite 文件清理时的 WinError 32：

- test_backup_contains_committed_wal_and_assets
- test_backup_restore_preserves_reference_to_actual_photo
- test_restore_is_atomic_and_pauses_to_prevent_delivery_replay
- test_unknown_database_schema_rejects_upgrade
- test_migration_preserves_source_and_is_idempotent

没有新增跳过、删除旧测试、降低断言或修订无关 SQLite 行为。既有一个跳过为平台符号链接条件。

## 关键验收证据

| 验收项 | 测试 |
| --- | --- |
| 原创 V3 → IR → Definition → World → Instance → ENTER → EXIT → RESUME | test_import_world_exit_resume_acceptance |
| 世界、时间线和实例 ID 保留，新会话 ID 与 epoch/revision 推进 | test_import_world_exit_resume_acceptance |
| 同一定义跨世界状态、关系与 epoch 独立 | test_multiworld_values_and_epochs_are_independent |
| X@2 登记不改写 X@1，仓储也拒绝改写固定引用 | test_definition_version_is_pinned_and_cannot_be_overwritten、test_repository_preserves_pinned_references_and_closed_history |
| 退出/恢复后旧请求或旧绑定不能继续写入 | test_old_epoch_rejected_after_exit_and_resume |
| 同一修订号并发提交恰好一个成功 | test_concurrent_compare_and_swap_has_one_winner |
| 绑定失败后世界保持 CREATED | test_enter_binding_failure_leaves_created_world |
| 切换目标修订冲突或第二次保存失败，两个世界均回滚 | test_switch_invalid_target_rolls_back_source、test_switch_second_save_failure_rolls_back_both_worlds |
| 提交失败不留下 ACTIVE 世界或开放绑定 | test_enter_commit_failure_rolls_back_world_and_binding |
| 世界、时间线、owner 与完整 principal 校验 | test_cross_world_character_cannot_bind、test_cross_timeline_cannot_bind_or_write、test_owner_and_principal_boundaries |
| Soul World 关闭会话保持 ACTIVE 并可重新绑定 | test_soul_world_close_keeps_active_and_can_rebind |
| 现实/正史标记不提升、桥接仍拒绝、Soul 不变 | test_reality_canon_bridge_and_soul_unchanged |
| 重建应用服务后使用同一仓储恢复 | test_new_application_reuses_existing_repository_and_original_ids |
| 不访问数据库、网络或宿主进程 | test_no_database_network_or_host_process |

## 仓储与持久化边界

内存事务持锁、复制后写入、成功才发布；失败注入通过协议代理完成。当前结果证明进程内原子性，不声称数据库级 CAS、分布式锁或进程重启后持久恢复。

没有生产 World 表、迁移或持久事件执行器。原子存储、索引、容量及恢复责任留给后续获授权的仓储实现。

## 发布与范围检查

仅新增两个模块、一个测试模块、两个文档。新增普通注释、docstring、文档与 PR 说明使用中文，固定技术标识保留原样。

PR #3 只读检查提交为 `ab227f2179eeaa7ded662d612508a98ad5cdf04a`，要求 OPEN / DRAFT / NOT MERGED；未修改、变基或合并。当前任务 PR 必须 OPEN / DRAFT / NOT MERGED，不启用自动合并。

本阶段无范围偏离。最小 Values 替换不构成关系引擎；未实现 Story、Memory、Lore、Prompt 或完整 Bridge 运行时，未部署 Hermes/OpenClaw，也未启动 SP-004E。提交、远端状态和工作区结果由最终执行报告记录，完成后停止等待独立审核。
