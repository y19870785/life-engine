# v0.3 验证记录

## SP-005A1 实施验证（待独立审核）

固定 Base：`9159c493ad435cf947ed8c0fef278e1f5fb9dc83`。本次实现 `DATA_SCHEMA = 8`、`SP-005A-living-runtime-v1`；Prompt Template 仍为 `SP-004K-prompt-v1`。原始 A0/R1 判据与具体测试的 48 项对应关系见 [实施映射](SP-005A1-VALIDATION.md)，部署边界与 copy migration/rollback 见 [操作说明](LIVING-RUNTIME.md)。

自动证据来自独立临时安装、Schema 7 canonical 原版发行包、进程 crash、两进程 tick/Scope 竞争、固定 DST fixture 和 fake delivery validator。未调用生产 Host、渠道、ComfyUI 或 TTS。Hermes/OpenClaw real Host validation 均保持 PENDING_REAL_HOST_VALIDATION；Full Private RP/H1/H2 继续 BLOCKED。

最终本地完整测试：Windows、Python 3.12.10、Node 22.23.2；`python -m unittest discover -s tests -v`，371 项，370 通过、1 项既有 Unix symlink 平台跳过，0 失败/错误，245.458 秒。新增 48 项 Living 测试及 3 项 Schema 8 migration/rollback 测试；48 项架构矩阵逐项映射，测试数量不等于矩阵编号数量。其后仅清理四个模块 EOF 空行，并核对 AST 未变。100 个相对链接检查通过，`git diff --check` 通过。远端 Ubuntu / Windows × Python 3.11 / 3.12 以本 PR exact Head 的 CI 记录为准；PR 描述和实施报告提供 run 关联。下方 H0 和 2026-09-26 数据是历史基线，不代表 A1 的 schema 或测试数量。


## SP-005H0 实施验证（2026-09-27，待独立审核）

固定 Base：`694b45a6f1cd10e28bef96a7e98261c1f85d66f6`。本阶段新增原生插件 `doctor`/`sandbox-probe`、durable 调用身份封套、文件化沙箱报告与交付证据链校验。报告不会签发真实 Host PASS，也不改变 Full Private RP 能力门禁。

审核修订后的顶层语义：`ok` 仅表示命令执行成功，`report_generated` 表示完整报告已生成；真实验证只看 `validation_result` 与 `validation_passed`，当前所有路径的 `validation_passed` 固定为 false。无 probe、模拟/unverified_capture 一致性通过、新进程本地探测通过，都仍为 PENDING_REAL_HOST_VALIDATION；probe 不一致或 generation drift 为 FAIL。生成 FAIL 报告不是命令异常，因此 ok=true、退出码 0；执行异常时 ok=false、report_generated=false、validation_result=FAIL、validation_passed=false，退出码 1。自动消费者不得使用 ok 或退出码判断 Sandbox 完成。

最终本地完整测试：Windows、Python 3.12.10、Node 22.23.2；执行 `python -m unittest discover -s tests -v`，320 项，319 通过、1 项既有 Unix symlink 测试平台跳过，0 失败/错误，耗时 198.235 秒。新增 12 项测试，并扩展既有两个原生插件合同测试。`git diff --check` 与三份更新文档相对链接检查通过。本机 Python 3.11 launcher 指向失效路径，未宣称本地 3.11 通过；其结果由 Draft PR 的独立 CI 矩阵提供。自动通过不等于真实 Host 或独立审核通过。

| 验证项 | 自动证据与边界 |
| --- | --- |
| Hermes | 模拟 PluginContext/get_hermes_home，实际加载生成的 Python 插件并调用独立 Python 引擎；错误 Profile 拒绝，status/doctor 身份一致，reload 更换插件代次且清空 hook 证据 |
| OpenClaw | Node 加载生成的 JS 插件，最小 SDK 替身；错误 agentId、缺少 workspace、调用后身份变更均拒绝；status/doctor、photo disabled、reload 重新验证 |
| stable instance / generation | 真实临时安装、新 Python 子进程读取同一 instance/data root；配置重建 generation 后旧 attestation 被拒绝，要求重验 |
| wake | 复用现有 contact opportunity、quiet hours、无联系理由和并发领取测试；补充 cooldown/daily budget 静默测试；插件 probe 仅 preview |
| photo | 自动验证关闭时为 DISABLED；既有假 ComfyUI 和本实例 media outbox 测试继续保留，未使用真实 GPU |
| delivery / receipt | 检查不能跳级、operation/target/message ID 必须一致；模型 evidence 不能登记 delivered；没有验证器时不能升级 SENT/ACKNOWLEDGED |
| Full Private RP | 一致性验证通过后，既有 require_private_context_isolation 仍拒绝缺失 capability；HISTORY_ISOLATION/final-output 门禁未弱化 |

真实 Hermes / OpenClaw Sandbox 均为 **PENDING_REAL_HOST_VALIDATION**。本轮只检查 Windows PATH 中的可执行命令位置，未发现 Hermes/OpenClaw；这不代表 WSL 或其它环境没有安装。没有选定独立测试 Profile/Agent、Session 或本人聊天目标，故未安装或更改生产插件、重启 Gateway、执行真实聊天/发送、读取生产聊天历史，也未探测 compatibility fork。实际 Host version、profile/config/Gateway/target evidence 为 **UNKNOWN**。测试中的版本和身份是模拟数据，不能当作实机记录。

真实 Host restart/upgrade：`NOT_EXECUTED — production host isolation unavailable`。新 Life Engine 子进程与模拟插件 reload 的通过结果只证明自动合同。OpenClaw 跨 Gateway/Profile 的唯一性尚未证明；当前没有渠道 receipt 验证器。操作方法、结构化输出与剩余实机检查见[沙箱指南](HOST-SANDBOX-TESTING.md)。

H0 当时数据版本为 `DATA_SCHEMA = 7`，Schema Signature 为 `SP-004F-bridge-runtime-v1`，Prompt Template 为 `SP-004K-prompt-v1`；没有 Schema 迁移、Host Core patch 或 H1/H2 实现。最终阶段结论由 ChatGPT / 小雪审核 Draft PR 与真实证据后决定。

## 历史 canonical validation（2026-09-26）

固定 canonical main：`8e2db9ae50b1ac3c46bb1953851d14442c58f085`。合并 H0 后的 [main push CI #36088249987](https://github.com/y19870785/life-engine/actions/runs/36088249987) 在 Ubuntu / Windows × Python 3.11 / 3.12 四矩阵全绿。此处不推断本次 CI 的测试数量；下方 217 项是 SP-004B1 时点的**历史**记录。

该历史基线 `DATA_SCHEMA = 7`，World Schema Signature 为 `SP-004F-bridge-runtime-v1`，Prompt template 为 `SP-004K-prompt-v1`。World、Memory、Lore、Story、Bridge、Prompt Core Runtime 与 H0 Host Integration Contract 已进入 main；真实 Host Private RP 尚未通过能力门禁。自动 CI 和模拟宿主测试不等于真实渠道送达。

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
