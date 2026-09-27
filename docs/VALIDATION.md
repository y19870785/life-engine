# v0.3 验证记录

## 当前 canonical validation（2026-09-26）

固定 canonical main：`8e2db9ae50b1ac3c46bb1953851d14442c58f085`。合并 H0 后的 [main push CI #36088249987](https://github.com/y19870785/life-engine/actions/runs/36088249987) 在 Ubuntu / Windows × Python 3.11 / 3.12 四矩阵全绿。此处不推断本次 CI 的测试数量；下方 217 项是 SP-004B1 时点的**历史**记录。

当前 `DATA_SCHEMA = 7`，World Schema Signature 为 `SP-004F-bridge-runtime-v1`，Prompt template 为 `SP-004K-prompt-v1`。World、Memory、Lore、Story、Bridge、Prompt Core Runtime 与 H0 Host Integration Contract 已进入 main；真实 Host Private RP 尚未通过能力门禁。自动 CI 和模拟宿主测试不等于真实渠道送达。

### Hermes Host Capability Audit

官方 final-output commit 能力仍阻塞 H1。CAP1 已判定需要 upstream，CAP2 提案已完成，CAP3 在 [PR #120170](https://github.com/NousResearch/hermes-agent/pull/120170) 获得 in-scope 方向反馈，官方实现仍待完成。独立的 compatibility fork 实机验证：attempt #1 因 recovery durability **FAIL**；R2 修复 recovery 后 rerun 又因 stale session incarnation / A→B→A writer fence **FAIL**，fork 路线已停止。以上是 **Hermes fork** 的 Host 能力实验，绝非 Life Engine main CI 结果，也不构成生产安全认证。

### OpenClaw Host Capability Audit

本机 2026.9.5 的 CAP0 结果：`HOST_CAPABILITY_INSUFFICIENT`。对 2026.9.6 做了相关边界的只读比对；CAP1 结果：`UPSTREAM_CHANGE_TOO_DEEP`。已有结构化身份、run/session ID、`lifecycleRevision`、transcript writer fencing 与多个 Hook，但缺统一的 fail-closed final-output commit / replay / delivery / stream 授权。宿主源码审计与正式 Life Engine Host 沙箱验收须分开记录。

## SP-004B1 时点自动验证（历史）

基线：`d89b362701e614415354c38302a102f593a0a0a7`（SP-004B1 合并提交）。[GitHub Actions 运行记录](https://github.com/y19870785/life-engine/actions/runs/35748952847) 已完成且通过：Ubuntu / Python 3.11、Ubuntu / Python 3.12、Windows / Python 3.11、Windows / Python 3.12。当时完整 `unittest` 共 217 项；Windows 为 216 项通过、1 项既有平台跳过。

这些自动测试覆盖代码合同与模拟宿主，不等于真实 Hermes / OpenClaw Gateway、聊天渠道、GPU 出图或发送回执闭环验收；也不表示新的 World Memory 已自动接入宿主每轮聊天。

## 2026-09-13 历史验证

测试环境：Linux，Python 3.12.14，Node.js 24.19.0。验证日期：2026-09-13。

执行：python -m unittest discover -s tests -q。

50 项测试通过。原有 31 项覆盖角色状态/联系策略、SQLite 并发领取、模拟隔离、ComfyUI 假 HTTP 服务流程、照片复用/未知失败不重排、旧安装保护和 v0.1 迁移。新增 19 项覆盖永久入口、升级备份、恢复原子切换、代码回退与原生适配器。

永久安装验证使用真实临时文件系统与独立 Python 子进程：安装后删除解压目录，改变 HERMES_HOME，重新运行状态与维护入口仍可读取已保存记忆。重复安装保留手工修改过的 agent.json 与数据库字节；不同宿主即使内部角色名相同，也使用不同实例与数据库。

升级验证将有变化的新代码复制为独立版本；确认切换版本后配置与数据库内容不变。构造语法损坏的新代码，导入检查拒绝激活；回退到原代码后，保留新代码运行期间写入的记忆。

备份验证包含保持 WAL 连接打开时已提交的新记录与实际图片文件。恢复验证保留原数据代次、重写所复制照片的有效路径并暂停主动联系；损坏备份与模拟注册指针写入失败都不会先删除当前可用数据。未知数据库 schema 会阻止升级。

Hermes 原生桥接器使用模拟 PluginContext 与当前 Profile 上下文，实际调用独立 Python 引擎，验证状态补入、主人匹配和跨 Profile 拒绝。OpenClaw 桥接器由 Node 实际加载，使用最小 SDK/宿主接口替身调用真实 Python 引擎，验证 agentId/workspace 双重匹配、工具调用和主人入站标记。它们是适配器契约测试，不等价于在真实 Hermes/OpenClaw Gateway 中测试。

OpenClaw 图片暂存验证只接受本实例生成目录中的图片，复制到当前 workspace 后内容一致；其他文件和冲突文件被拒绝。没有为此扩大宿主全局文件访问权限。

另执行安装 CLI 的非交互预览/应用/维护入口检查。未访问用户的本地宿主、未启用其定时任务、未发送真实微信消息、未调用真实 GPU。没有实测 Windows/macOS 系统服务、容器重建、真实断电或磁盘硬件故障；这些需要在最终运行环境验证，持续保存仍依赖持久磁盘/卷和可用备份。
