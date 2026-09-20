# SP-004E — 质量门禁

状态：PENDING_INDEPENDENT_REVIEW。仅实施 SP-004E，不转 Ready，不合并当前 PR 或 PR #3。

仓库：`y19870785/life-engine`。分支：`feat/sp-004e-world-sqlite-persistence`。
授权基线：`399b084a8a5dfd76eb2aa3d0aac9ebbaafd35260`。

相关：[持久化架构](../architecture/SP-004E-WORLD-SQLITE-PERSISTENCE.md)、[恢复 ADR](../architecture/adr/SP-004E-001-RESTART-SESSION-RECOVERY.md)、[迁移 ADR](../architecture/adr/SP-004E-002-SCHEMA-3-MIGRATION.md)。

## 实际执行结果

2026-09-20 本地执行；没有将本地结果表述为 GitHub CI。

| 门禁 | 结果 |
| --- | --- |
| Windows Python 3.12 全量 | 178 项，0 失败/错误，1 个既有 Unix 符号链接条件跳过 |
| WSL Ubuntu / Python 3.12.3 全量 | 178/178 通过，无跳过 |
| SQLite Repository | 39 项，包含 27 项共用 SP-004D 合同及 12 项持久化扩展 |
| SP-004D 内存实现 | 28 项；生命周期逻辑未新增 SQLite 分支 |
| Schema 迁移 | 11 项真实旧安装与故障注入测试 |
| durable 安装、升级、备份、恢复 | 包含在两平台完整测试集内 |
| 原创 V3 端到端 | V3 → IR → Definition → SQLite → ENTER → 更新 → EXIT → 重启 → RESUME → 更新通过 |
| SQLite 检查 | quick_check、foreign_key_check；副本迁移另执行 integrity_check |
| 发布导入 | 新 release 在独立子进程导入 SQLiteWorldRepository，并检查 manifest Schema 与 runtime 一致 |
| Python、文档、差异 | 语法/导入、相对链接与 git diff --check 检查 |
| GitHub Actions | 授权 main 没有工作流；本阶段不新增 CI，不宣称 GitHub CI 通过 |

Windows 测试为现有 Node 契约检查提供本地 Node 路径，因此唯一跳过来自既有 `test_install.py` 的 Unix 条件。没有新增 skip 或屏蔽失败。

执行命令：

```text
py -3.12 -m unittest discover -s tests -p test_world_sqlite_repository.py -q
py -3.12 -m unittest discover -s tests -p test_schema3_migration.py -q
py -3.12 -m unittest discover -s tests -q
wsl -d Ubuntu -- bash -lc 'cd /mnt/d/xiangmu/life-engine && python3 -m unittest discover -s tests -q'
py -3.12 -m compileall -q runtime tests
git diff --check
```

Windows 的默认 `python` 指向 3.10，初次探索暴露既有 `hashlib.file_digest` 版本要求；正式验收使用项目要求的 Python 3.11+，实际为 3.12。迁移 fixture 通过 `git archive` 从授权基线取原版 runtime，因此运行该测试需要 Git 和本地基线历史。

## 仓储验收映射

| 合同 | 测试证据 |
| --- | --- |
| Soul/Definition/World/Timeline/Instance/Session 全部往返，state/relationships 保留 | test_v3_restart_resume_preserves_all_values |
| X@2 登记后重启仍固定 X@1 | test_v3_restart_resume_preserves_all_values、共用 fixed Definition 测试 |
| 完整 Provenance、枚举、Principal、来源 ID、时区 | test_full_provenance_and_timezone_roundtrip |
| epoch 9 重启保持，下一次 RESUME 为 10 | test_epoch_nine_survives_restart_then_resume_is_ten |
| SQL CAS，两个独立 Repository/连接同 revision 仅一个成功 | test_independent_connections_database_cas |
| 同 World 竞争 ENTER 只有一个成功，直接 SQL 也受唯一索引保护 | test_independent_connections_open_race_and_index |
| A 写入后故障，重新连接 A/B 都未变 | test_switch_sql_rollback_survives_reopen |
| 第二次保存前后异常与提交前失败 | 共用 test_switch_second_save_failure_rolls_back_both_worlds、test_enter_commit_failure_rolls_back_world_and_binding |
| 实际 commit 方法抛出异常，回滚且释放连接 | test_real_commit_failure_closes_and_rolls_back |
| 锁超时不是 RevisionConflict，回滚后可用、Windows 文件可重命名 | test_busy_is_not_revision_conflict_and_connection_released |
| Roleplay 崩溃恢复、旧 Session 和旧 Repository 围栏、恢复幂等 | test_crash_recovery_is_idempotent_and_fences_old_repository |
| Soul 保持 ACTIVE 并可重新绑定 | test_soul_crash_keeps_active_and_rebinds |
| 固定 DefinitionRef 的数据库触发器、tuple 顺序稳定 | test_sql_definition_pin_trigger_and_snapshot_order |
| 缺表/缺列/缺索引/错误索引/伪版本/错误签名/坏 JSON/非法枚举/错误 ID kind/孤儿 Definition/外键损坏 | test_malformed_data_fail_closed_without_repair |

共用合同从 `test_world_runtime.py` 抽为测试混入类，内存与 SQLite 执行相同断言。纯内存“不访问数据库”测试留在内存具体类，不在 SQLite 测试中伪装跳过。共享 `validate_update` 防止固定引用与 CLOSED 历史检查分叉。

## Schema 与部署验收映射

| 合同 | 测试证据 |
| --- | --- |
| 全新 Schema 3 | 全部 SQLite fixture 与既有 create_install 测试 |
| 真实 Schema 2 安装升级、原业务行/配置/照片/Agent/Host 保留、旧 generation/备份/release 保留、重复升级幂等 | test_real_old_install_upgrade_preserves_data_assets_and_bindings |
| 两实例一起激活 | test_two_instances_activate_together |
| 第二实例失败 registry 字节不变，两个旧 release 业务操作仍可运行 | test_second_instance_failure_keeps_entire_registry_and_old_runtime |
| 迁移 SQL 中断，旧安装正常，重试成功 | test_migration_mid_sql_failure_preserves_active_and_retry |
| registry 激活失败，旧安装正常 | test_registry_activation_failure_preserves_old_install |
| 活动 generation 禁止直接迁移 | test_active_generation_migration_is_forbidden |
| code rollback 跨 Schema 拒绝，完整 Schema 回退恢复旧组合 | test_schema_rollback_blocks_code_only_and_restores_whole_tuple |
| 迁移前备份包括 committed WAL | test_pre_migration_backup_includes_committed_wal |
| Schema 2 备份由原版 Schema 2 runtime 验证 | test_real_old_install_upgrade_preserves_data_assets_and_bindings |
| unknown/PR #3 式 Schema 3 拒绝且原文件字节不变 | test_unknown_or_pr3_style_schema3_is_unchanged |
| Schema 3 World/Definition/Instance/CLOSED Session 历史 backup → 修改 → restore 恢复；Schema 2 备份不得直接 restore | test_schema3_backup_restore_world_and_reject_schema2_backup |
| 健康检查发现缺失 generation 或索引损坏 | test_health_reports_missing_generation_and_structural_damage |

## Windows SQLite 调查

使用授权基线原版 runtime/tests，在独立临时目录、Windows Python 3.12 子进程重跑以下五项，复现 **5 项 WinError 32 清理错误**：

- test_backup_contains_committed_wal_and_assets
- test_backup_restore_preserves_reference_to_actual_photo
- test_restore_is_atomic_and_pauses_to_prevent_delivery_replay
- test_unknown_database_schema_rejects_upgrade
- test_migration_preserves_source_and_is_idempotent

根因是测试的 `with sqlite3.connect(...)` 只管理事务、不关闭连接。生产 `Store.tx()` 与 durable backup 连接已有显式关闭；本阶段新增 Repository 也按事务显式关闭。对相关测试采用 `contextlib.closing(...)` 与原事务上下文组合，修改不影响业务断言。它属于本阶段连接所有权验收的直接关联修复，没有扩大到其他基础设施。

另排除测试复制包里的 `.git`，避免 Git 只读对象导致 WinError 5。没有使用 sleep、`gc.collect()`、吞掉 cleanup error 或修改真实数据库。

## 发布范围与待审事项

`DATA_SCHEMA`、Store 初始化、release/registry/backup manifest、db_check、upgrade、restore 和 rollback 边界统一为 canonical 3。没有借用 PR #3 数据库，也没有将旧 schema 3 当成兼容版本。PR #3 的 KEEP/ADAPT/MIGRATE/REPLACE 表见架构文档。

启动代次策略、严格结构拒绝策略和跨 Schema 整组回退属于独立审核重点。全部实施完成后仅创建 OPEN / DRAFT / NOT MERGED 的 PR，不启用自动合并。最终 Head SHA、远端状态和工作区 clean 结果由提交后的执行报告记录。
