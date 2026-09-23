# v0.3 已知问题与历史记录

本版本用于开发审阅和受控试用，尚未完成真实宿主验收。

当前 canonical main 的 GitHub Actions 在 Ubuntu / Windows、Python 3.11 / 3.12 四矩阵通过。下述 2026-09-13 Windows 结果和缺库复现是历史记录，不代表当前测试状态。

## 数据库缺失时静默初始化（历史问题，已修复）

2026-09-13 在 Windows / Python 3.12 临时安装中复现：写入记忆后移走
`life.db`，`doctor` 仍返回 `ok: true`，`status` 返回成功并创建空数据库。
`durable.state_check` 仅检查存在的数据库，后续 `Store` 自动初始化。
已有实例应在缺库时停止并要求恢复，首次安装才允许建库。

SP-004E 已修复此问题：当前 main 的 `state_check` 拒绝缺失活动数据库，健康检查返回失败；
首次安装仍可显式创建完整数据库。相关测试见
[SP-004E 质量门禁](planning/SP-004E-QUALITY-GATES.md)。

## 出图期间实例锁阻塞其他调用（OPEN）

代码检查发现 `durable.run` 在整个 photo 命令期间持有实例锁，包括网络等待；
其他命令取得锁的等待上限为 5 秒。长耗时出图可能使上下文注入和入站记录失败。
此并发场景尚未实际复现，应在调整锁范围时同时保护恢复和数据代次切换。

## Windows 测试结果（2026-09-13 历史记录）

2026-09-13 执行 `py -3.12 -m unittest discover -s tests -q`：
50 项测试，5 项错误，1 项跳过。

五项错误均发生于 tearDown 清理临时目录，报 SQLite 文件被占用（WinError 32）。
相关测试的 SQLite 连接需显式关闭；不能据此认定备份、恢复和迁移的业务断言失败。
OpenClaw 契约测试因测试进程 PATH 未发现 Node 而跳过。
历史 Linux 检查记录见 VALIDATION.md，与本轮 Windows 结果分别保留。

SP-004E 已将上述 SQLite 测试改为显式 `contextlib.closing` 释放连接，
保留事务上下文负责 commit/rollback；没有使用 sleep、GC、错误吞掉或新增跳过。
测试复制发布源码时排除 `.git`，避免 Windows 只读 Git 对象触发无关清理错误。
当前 canonical main 的四矩阵结果见 [验证记录](VALIDATION.md)；本节保留当时的故障证据。

## 真实环境验证（OPEN）

尚未验证真实 Hermes / OpenClaw Gateway、聊天渠道、GPU 出图及发送回执闭环；World Memory 也尚未自动接入真实宿主对话。
上传代码不代表已安装到本机 Agent，也不代表可宣称稳定发布。
