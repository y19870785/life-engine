# SP-004 — Quality Gates and Repository Evidence

日期：2026-09-16（Asia/Shanghai）。本记录对应纯文档任务，Implementation Authorization / Merge Authorization 均为 NOT AUTHORIZED。

## Repository Snapshot

| 检查 | 结果 |
| --- | --- |
| Repository | y19870785/life-engine |
| 开始时工作区 | `D:/xiangmu/life-engine`；git status --short 无输出，工作区干净 |
| 开始时分支 / HEAD | docs/readme-for-new-users / b79d2fe53a54df8ca394b1dff7ce5359ea54a102 |
| fetch 后 main | 81ee02b561ac90641c3632f750ffd86a48310cf7 |
| PR #3 | OPEN / DRAFT；head ab227f2179eeaa7ded662d612508a98ad5cdf04a；base main |
| 本任务分支 | docs/sp-004-persistent-world-runtime |
| 本任务 worktree | D:/xiangmu/life-engine-sp004，从 origin/main 创建 |
| PR #3 检查 worktree | D:/xiangmu/life-engine-roleplay，HEAD 与远端一致，工作区干净；只读检查与测试 |

开始执行了 git status、git branch --show-current、git rev-parse HEAD、git fetch origin；随后读取 PR 元数据和固定版本代码。未切换或覆盖原工作区的 README 分支，未修改 PR #3。

## Existing Relevant Tests

本轮实际执行全量现有测试，没有复用上一轮测试结果冒充本轮结果：

| 对象 / 环境 | 命令 | 结果 |
| --- | --- | --- |
| main 基线 / Windows Python 3.12 | py -3.12 -m unittest discover -s tests -q | 50 项；5 errors，1 skipped；退出码 1，25.058s |
| main 基线 / WSL Python 3.11 | python -m unittest discover -s tests -q | 50 项通过；退出码 0，24.945s |
| PR #3 固定 head / WSL Python 3.11 | python -m unittest discover -s tests -q | 69 项通过；退出码 0，30.958s |

WSL 实际解释器为本机已有的 `/home/hechao/.hermes/hermes-agent/venv/bin/python`；测试使用临时数据，没有调用 Hermes 模型、Gateway、私聊渠道或在线数据库。测试检查的是已有代码，不是本文尚未实现的 World/Story 模型。

Windows 五项错误均为 tearDown 时 SQLite 文件被占用（WinError 32）：

- test_backup_contains_committed_wal_and_assets
- test_backup_restore_preserves_reference_to_actual_photo
- test_restore_is_atomic_and_pauses_to_prevent_delivery_replay
- test_unknown_database_schema_rejects_upgrade
- test_migration_preserves_source_and_is_idempotent

唯一跳过项是 Unix 专用 symlink 测试。与 [main 的历史已知问题](../KNOWN-ISSUES.md) 对照，五项清理错误是既有问题；历史文档对跳过原因的 Node 描述不能用于本轮判断。本轮不修测试、不改运行代码，也不宣称全平台全绿。PR #3 中相应修复仍由 PR #3 自己管理。

## Documentation Checks

main 没有配置 Markdown lint 工作流。本轮使用临时 Python 文档检查器进行有限的格式/链接检查，不新增依赖或 CI 脚本：

- 四份新增文档 UTF-8 解码、结尾换行、无尾随空白或 tab、标题前空行与层级、代码围栏配对、Markdown 表格列数一致。
- 本地相对链接解析到实际文件；固定 SHA 的 GitHub blob 链接用 git cat-file 验证 commit:path 存在；PR #3 链接由 gh pr view 验证。
- 文档相互链接全部检查，不将“Git 对象存在”声称为外网 HTTP 渲染/可达性测试。
- git diff --check 与 staged diff --check；变更路径只允许 docs/architecture/SP-004-*.md 和 docs/planning/SP-004-*.md。
- 与 base 比较 runtime、tests、入口脚本和现有其他文件均无 diff；新文档没有 SQL 迁移或可执行实现。

这是轻量检查，不能替代完整 Markdown 渲染器、Mermaid 渲染器或独立架构审核。最终执行报告给出实际检查结果、提交 SHA 与 Draft PR URL，供 Reviewer 从 GitHub 复核。

实际轻量检查结果：4 份 Markdown、7 个本地相对链接、13 个不同的固定 commit:path 链接，全部通过。唯一非 blob 外部链接为 PR #3，已用 GitHub CLI 实查。未运行 HTTP 链接爬虫或完整 Markdown/Mermaid 渲染检查。

## Independent Review Checklist

Reviewer 应核对：RFC 的所有权矩阵是否闭合、World/Session/Character 是否分离、故事真源是否脱离 Prompt、Bridge 双向授权与撤销是否完整、旧 meta 是否保持虚构标签、迁移是否明确承认切换后回退限制，以及宿主能力不足是否实际降级而非只加提示。

GitHub 上应只有四份 SP-004 Markdown 文档变更；main 与 PR #3 不应被本任务改写。本任务 PR 必须 OPEN / DRAFT / NOT MERGED，未设置 auto-merge。独立审核状态保持 PENDING_INDEPENDENT_REVIEW，不由作者代签。
