# SP-004A — Quality Gates

Date: 2026-09-16. Status: PENDING_INDEPENDENT_REVIEW.

Implementation Authorization: AUTHORIZED — LIMITED TO SP-004A. Merge Authorization: NOT AUTHORIZED.

## Repository

fetch 后 main 为授权基线 `f040a8241e3b6ebc34f4025c6f5211829a0d040c`。新 worktree `D:/xiangmu/life-engine-sp004a`，分支 `feat/sp-004a-world-domain-model`；原工作区保持干净。已阅读 SP-004 的 RFC、Gap、计划和检查记录。

PR #3 只读检查 head `ab227f2179eeaa7ded662d612508a98ad5cdf04a`，OPEN / DRAFT；它仍是候选迁移来源，未修改、rebase、merge 或 close。没有从它 cherry-pick 代码。

## Tests

| Environment | Command | Result |
| --- | --- | --- |
| Windows Python 3.12 | py -3.12 -m unittest discover -s tests -p test_domain.py -q | 22 tests, OK, 0.004s |
| WSL Python 3.11 | python -m unittest discover -s tests -p test_domain.py -q | 22 tests, OK, 0.005s |
| Windows Python 3.12 | py -3.12 -m unittest discover -s tests -q | 72 tests, FAILED (errors=5, skipped=1), 20.474s |
| WSL Python 3.11 | python -m unittest discover -s tests -q | 72 tests, OK, 16.131s |

全量包含 main 既有 50 项及 SP-004A 新增 22 项。Windows 五项错误均是原有 SQLite tearDown WinError 32：backup_contains_committed_wal_and_assets、backup_restore_preserves_reference_to_actual_photo、restore_is_atomic_and_pauses_to_prevent_delivery_replay、unknown_database_schema_rejects_upgrade、migration_preserves_source_and_is_idempotent。唯一跳过项是原有 Unix 专用 symlink 测试。没有新增失败/skip，没有修改旧测试去掩盖失败。

后续补充了直接构造的 Binding 与 WorldKind 不一致时的防御校验，并在既有领域测试中加入拒绝断言；受影响的 22 项领域测试再次在 Windows（0.003s）与 WSL（0.005s）全部通过。没有新增测试数量或额外 skip。

WSL 使用已有 Python `/home/hechao/.hermes/hermes-agent/venv/bin/python`，只是解释器；未调用 Hermes 模型、在线 Gateway 或生产数据库。新领域测试不使用 SQLite，既有测试仅使用自身临时数据。

## Acceptance Demonstration

[test_acceptance_two_worlds_one_definition_and_reentry](../../tests/test_domain.py) 是最小可执行验收：

1. 同一 Owner/Soul 构造一个 Soul World 和 Roleplay A/B。
2. A/B 使用同一 DefinitionRef，实例 ID、world ID、timeline ID 不同。
3. A 在襄阳、与用户 trusted；B 在古墓、与用户 stranger；state/relationships 不相同且不可变。
4. 退出 A 得到 SUSPENDED，关闭 Session，不删除 World。
5. RESUME 后以新 session ID 绑定原世界/时间线/实例，并通过写入前置校验；旧 epoch 另有测试证明失效。

这只是内存对象演示，不宣称故事、关系或 World 已持久化。

## Package / Import and Documentation

在 Windows 与 WSL 执行所有包模块 import 和 compile 检查；检查 release_files 收集包含 domain.py、domain_lifecycle.py、domain_policy.py，生产 DATA_SCHEMA 仍为 2。

新模块只依赖标准库及彼此，不依赖 Hermes/OpenClaw、SQLite、Prompt 或宿主配置。没有改 `__init__.py`、CLI、Store、durable、bridges 或旧测试；扁平模块可由既有打包规则收集，无基础改动例外。

文档检查采用临时 Python 脚本：UTF-8、尾随空白、标题/围栏、表格列数、本地相对链接检查；7 份新文档、26 个本地链接通过，PR #3 URL 用 gh 实查。执行 git diff --check 和 staged diff --check，并核对允许的新增文件清单。未运行完整 Markdown/Mermaid 渲染器或 HTTP 爬虫。

本基线没有 GitHub Actions 工作流，本轮不新增以掩盖 Windows baseline failure 的 CI 配置。最终执行报告记录实际检查结果和 Draft PR；没有将 PR #3 的 CI 当作本分支 CI。

## Stop / Review Boundary

契约类型和纯校验不替代最新存储快照、认证、CAS、grant 签发/撤销、lineage、宿主隔离或传输服务。它们分别留给后续获授权阶段。

未执行数据库迁移、未部署宿主、未创建自动运行世界、未开启后台 scheduler。本 PR 必须 OPEN / DRAFT / NOT MERGED，未设置 auto-merge；完成后停止，不启动 D/G/E 或其他阶段。
