# SP-004E-002 — Schema 3 副本迁移与整安装激活

## 状态

已实施候选；PENDING_INDEPENDENT_REVIEW。

## 背景

SQLite 事务无法覆盖数据库提交、文件复制、release 探针和 registry 替换的整个部署过程。直接改变活动库后再补救会让旧代码读到新结构。Schema 版本号相同不代表 Schema 兼容，尤其 PR #3 已使用过另一个 Schema 3。

## 决策

采用 Copy → Migrate → Validate → Atomic Activate，跨全部实例执行：

1. 新包升级器只接受已识别的 Schema 2 或 canonical Schema 3 registry。
2. 持有 management 锁，再按稳定顺序取得全部实例锁。
3. 验证所有旧数据及绑定；每个实例建立并验证 `before-schema-3-migration` 备份，不覆盖旧备份。
4. 安装新 release 并在独立 Python 进程核验 manifest 与 `durable.DATA_SCHEMA` 一致及 SQLite 模块可导入。
5. 通过 SQLite backup API 复制每个 Schema 2 generation 到唯一 `schema3-<UUID>`；迁移入口拒绝活动 generation。
6. 在副本内单事务创建 World 结构，逐表核验原业务数据未变，再写版本 3；执行 integrity_check、foreign_key_check、结构和领域校验。
7. 将真实存在的照片引用重定位到新 generation；保留其余设置和宿主绑定，同步文件。
8. 保存包含旧 registry 的独立回退记录；全部实例成功后，仅一次原子 registry 替换发布 release、generation、data_schema。

任何激活前错误均不改变旧 registry，不删除旧 release/generation。失败的新副本可保留用于诊断；重试使用新名称。已经激活 Schema 3 后再次 upgrade 不执行 2 → 3，也不改变数据 generation。

原子替换是激活提交点：进程在其之前终止，旧组合有效；在其之后终止，新组合有效，不存在部分实例激活。发生断电或文件系统错误后必须读取 registry 并运行健康检查判定提交状态；不能仅凭调用方未收到返回值认定尚未激活。沿用 durable 的文件同步与目录同步策略。

## 操作

旧安装必须从**新包**入口执行升级，旧安装内的 manage.py 仍绑定旧 release：

```text
python 新包/setup.py upgrade --root 安装目录
```

返回值 `schema_rollback` 是本安装的回退记录路径。升级后可使用活动管理器：

```text
python 安装目录/manage.py rollback-schema --checkpoint 回退记录路径
```

`rollback_code()` 只允许相同 data_schema。`rollback_schema()` 持有全部锁，验证旧 release 与旧数据可用、当前实例/generation 仍匹配升级记录，备份当前 Schema 3 状态，然后一次恢复旧 release + 旧 generation + registry data_schema 2。新 generation 保留。若之后执行过 restore/reconfigure/新增实例，旧回退记录失效并明确拒绝，不拼凑部分回退。

## 备份与恢复

备份 manifest 标记其真实 Schema。Schema 2 备份可由旧 runtime 验证，包含 committed WAL、checksums 和全部已存在资产。Schema 3 的默认 verify/restore 只接受 Schema 3；内部旧库检查显式传 `expected_schema=2`，不能绕过 restore 的边界。跨 Schema restore 不提供隐式转换。

恢复 Schema 3 使用新的 generation，完整保留 World 与 Session 历史；之后第一次启动 World Repository 仍执行 OPEN Session 围栏。生活主动联系沿用恢复后暂停策略。

## 影响

升级需要额外磁盘空间容纳旧 generation、迁移前备份和新 generation。代码回退与数据回退不再等价。整组 Schema 回退放弃新状态的活动身份，但新数据仍保留以供诊断或后续显式处理，不将新 World 数据反向转换为 Schema 2。

不接受数字相同但结构不同的 PR #3 数据库；不提供其自动迁移。检测不等于修复，坏库、缺表、未知版本、缺失活动数据库均停止使用。

## 验证

`test_schema3_migration.py` 从授权 Git 基线导出原版 runtime，在子进程创建真实 Schema 2 安装。测试覆盖原数据/照片/设置/Agent/Host 保留、多实例原子升级、第二实例故障、SQL 中断、registry 写入失败、旧 release 继续运行、WAL 备份、原版备份验证、重试幂等、完整回退和 Schema 3 World 历史恢复。

相关：[整体架构](../SP-004E-WORLD-SQLITE-PERSISTENCE.md)、[质量门禁](../../planning/SP-004E-QUALITY-GATES.md)。
