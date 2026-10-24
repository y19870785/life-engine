# X2-A 候选差异复核与复用裁定

当前门禁只见 [STATUS](../STATUS.md)。这是对 PR #64 的定向补充，不重复全仓审计。依据 OWNER 在 `f4bf7b5804c06eb0c50867d42b88f2fcaf79baa6` 上于 2026-10-24 00:58:42（Asia/Shanghai）提交的 [COMMENTED Review](https://github.com/y19870785/life-engine/pull/64#pullrequestreview-5631726989)：方向认可，但未 APPROVE；候选完整 diff、隔离编排和模型配置仍需补齐。本报告不把该 Review 改写成实施授权。

## 复核对象与结论

固定 main 仍为 `baa59729babf9ac56a17e02c682de2e3086e3575`。本次新冻结对象 C2 的完整清单 SHA256 为 `045ed49ac08ead503df47133ae669810766abcce2ce666bb5ed693ac669abc02`；不是上次 L 快照。187 个源码/fixture 文件中 43 个有语义差异，其中 37 个属于回忆录/provider 及相关测试，另 6 个是角色卡/共享用户身份旁线。完整相关 diff 与逐文件摘要见[证据台账](../validation/LE-RESET-01-X2-A-REVIEW-EVIDENCE.md)。

**裁定：可以提出一个明确、缩小后的离线 L1 实施合同；不批准整包复用 Hermes provider。** 可复用的是 Core 回忆录来源与生命周期约束，以及经过输入过滤的纯选择函数。Hermes wrapper、RecallService 生命周期、安装器、自动迁移和正式 Prompt 变更均不进入 X2-A。三个 Core 文件的临时最小投影已有 92 项回归和跨进程路径证明；X2 Web 层还不存在，相关安全性仍必须由后续实现和独立审核证明。

本轮只读候选代码，没有修候选以获得通过。相关生产差异逐函数检查；测试按完整新增文件的 fixture、调用、断言及错误路径核对，并记录所有测试方法和辅助断言。没有把 AST 枚举或通过一次全量写成通用安全认证。源代码作者的旧私有复审记录不代替这次固定对象证据；本报告也不冒充另一位外部独立复核者的批准。

## 完整差异覆盖与复用分类

| C2 文件/差异组 | 实际变化与审查重点 | X2-A 裁定 |
| --- | --- | --- |
| `domain.py`（仅新增 ROLEPLAY_RECALL） | 新来源枚举，不复用 BRIDGE；JSON 中的新值不是新表/迁移，但旧代码不认识该值 | **拟复用这四行增量**；不改 Schema/签名 |
| `memory_runtime.py` 来源校验及专用创建 | `validate_record` 收紧目标 Soul/SHARED_EXPERIENCE/Soul-only audience/TEXT subject；`validate_recall_write` 在同事务验同 Owner/Soul 的 RP 来源并堵通用 create/supersede/受众扩张/脱壳；既有回忆生命周期不因源归档而失效 | **拟复用必要安全闭包**，不能只抽 `create_roleplay_recall` 而遗漏泛入口写门 |
| `memory_runtime.py` 完整扫描与追加证明；`memory_repository.py` 两个失败码 | Owner 单事务 EOF、行/字节/协作时间预算；追加审计验证 revision/前驱/创建序列，合法编辑明确拒绝 | 有本地价值，但 **首片不采用**；有限 fixture 维护可信事件 ID，逐 ID 读取，不需要完整扫描/flush cursor |
| `roleplay_recall.py` 全文件 | RecallSource 上限、来源与虚构 reality、候选默认值、accept 幂等和后继/可见性复查 | **拟复用完整固定文件**；源码前置条件和残余边界见下文 |
| `prompt_runtime.py` 回忆录控制段/item kind | 改变正式 Prompt 派生内容；TEMPLATE_VERSION 未变 | **不进入 X2-A**；另用明确标识的试验上下文数据包，不签发伪 PromptSnapshot |
| `recall_service.py` 初始化/布局/轮次/迁移/flush/render | 会构建 install、选角色键、保存 state/cursor、默认接受回忆录；不是无副作用查询器 | **不整体复用，不从 HTTP 调它**；五个实测不匹配见下表 |
| 同文件纯函数与常量 | `_excerpt`、`_select_highlights`、query 校验、Unicode/引号/编号/词面选择；不执行网络或 Host | **可按冻结函数闭包抽取**到薄工具层；不得 import `integrations.hermes_memory` 包触发其 `__init__` |
| `integrations/hermes_memory/__init__.py`、plugin.yaml | Host SDK import/替身、文件/环境配置、available/prefetch/sync_turn/session callbacks；普通异常隔离 | **排除**；配置完整不代表路径隔离或 Host durability proof；不得用吞异常的空串充当 X2 未命中 |
| `tools/hermes_memory_install.py` | 缓存三文件 full digest、stage/xb/冲突保护；Profile 配置/插件/备份写入、可用性初始化 | **排除**；新缓存/参数修复已存在，不再沿用上次“未修”标签；仍不是完整安装事务或祖先路径认证 |
| `tools/hermes_memory_flush.py` / manage.py | 显式目标、固定错误码、候选查看/接受、CAS、同 basename 仅角色键 | **排除 CLI 入口**；只参考其失败分类、CAS与后继校验；HTTP 不接受 root/profile/Owner 参数 |
| `tools/roleplay_recall_eval.py` + 冻结语料 | 完成阶段/required IDs 检查、防空集 PASS、来源 hash、质量与安全分开；临时 store | 作为 **离线质量参照**，不把它变成新 X2 实现的端到端验收 |
| `examples/cosplay_recall_trial.py` | 临时根/marker、World 初始化、退出/接受/重开；示例含任意 temp path 和 reset 删除 | **参考 Core 顺序**，不原样暴露给 Web，不提供 reset/任意路径/删除 API；示例 truncate、随机 accept identity 不作为新编排策略 |
| 24 个相关测试文件/fixture | 完整覆盖来源/通用写门、拒绝不写、完整扫描/追加、游标/重试/生命周期、配置/参数/缓存、词面/Unicode/摘要、管理接受、评测完整性；未改既有安全测试 | 全部在 C2 完整 diff 中可读；本轮 C2 全量结果单列，X2 抽取后仍需自身全量和新增安全场景 |
| 另 6 个旁线文件 | character_onboarding、hermes_card_hook/native_hook/runtime、test_hermes_card_native、test_user_identity：脚本块/compat ack/8MiB、全局用户身份回退及测试 | **全部排除**；尤其 `Path.home()` 用户身份读取不允许进入隔离 X2。完整字节摘要单列，未以旁线测试冒充回忆录证据 |

所有相关 Runtime/工具/示例 diff 及测试的全文都作为 Markdown 审查证据提交；不以 hash 代替远端可读代码。六个旁线不属于要复用的候选闭包，只发布分类与摘要，不夹带其个人身份测试文本。

## 本轮合成实测：为什么不能整包复用

这五项只操作本轮新建临时 store，没有读真实 Profile、密钥或聊天。它们是调用契约不匹配，不能全部冠以“权限漏洞”。探针全文和结果见证据页。

| ID | 调用及实际结果 | 对 X2 的约束 |
| --- | --- | --- |
| P01 | 对不存在的合成 root 调 `RecallService.available()`，返回 True，之后 state.json 已存在 | “状态/可用”不能直接指向用户给的路径；创建只能经受管 new fixture 动作 |
| P02 | `remember_turn('assistant',...)` 的 RP Memory 为 `MODEL / accepted / fictional` | 没升格成现实事实，但与 X2“模型输出保持候选”的要求不同；新编排走 `create_session_candidate`，不走此函数 |
| P03 | 不传 accept 参数的 `flush_recall()` 返回 accepted Soul 回忆 | 不可把 session_end 自动接受挂到 Web；结束只创建候选，用户另行接受 |
| P04 | 两个不同绝对 Profile 路径、同 basename、同 store，取得相同 RP scope | 这是当前角色键语义，不是完整路径身份认证；X2 用启动器签发的 fixture/Session映射，禁浏览器传 Profile |
| P05 | 直接把合成 version=999 布局交 `_migrate`，写成 version=2，未来字段丢失 | X2 未知 fixture 版本直接拒绝，不调用 provider 自动兼容迁移 |

静态补充：`RecallService.ensure` 的 sys.path 与已缓存模块不能认证 runtime 来源；服务与 CLI 未提供整条祖先目录的抗链接/替换证明；state.json/flush.json 与 Memory 不在同一事务；sync_turn 的两次写入也不是原子 pair。已有幂等/重试测试约束部分失败，不等于无限崩溃、并发或恶意同 OS 身份安全。X2 不通过放宽这些函数的含义来“解决”隔离。

## 可复用安全闭包与实际路径证明

对 main 仅投影以下三文件，**没有**带入 scans、两个新失败码、正式 Prompt、Hermes wrapper/安装器/角色卡修改：

1. domain 新来源值。
2. memory_runtime 的 `validate_record` 回忆录分支、`recall_source_identity`、`validate_recall_write`、`create_roleplay_recall`、 `_mutate` 同事务校验调用及 WC import。
3. roleplay_recall 完整文件。

临时投影本轮跑过 **92 tests / OK / 0 skipped**，涵盖 RoleplayRecallTests、既有 Memory、删除恢复、Bridge、Prompt 回归；原拒绝断言和原文件未改。另跑的真实 Core 新进程路径得到：模型 RP 记录仍 candidate，Soul 接受前 0 条，显式接受生成后继，新进程 Session 查询 1 条，来源 roleplay_recall、reality fictional_shared_experience。完整投影 diff 与探针可在远端复验。

因此可以确认**已有 Core API 能支撑拟议消费链**；不能确认尚不存在的 X2 HTTP/UI 或模型 adapter 已安全。投影是审查用临时对象，不是产品实施提交，不给正式 M1 writer/Host/Schema 授权。

## 必须由 L1 编排补齐的边界

- Core 信任入口提供的 Principal/Owner；它不认证浏览器。浏览器只能给合成正文、服务端颁发的当前会话 ID、用户接受意图，不能指定 source/provenance/canon/World/路径。
- `record_recall` 确认同 Soul 的 RP 来源存在，不证明 highlights 与 RP 记录逐条相符。控制器必须从该 session 的持久 ID 清单读取且重验记录，确定性摘录，不接受浏览器或模型自报摘要来源。
- 字节截断与 max_name 有不同上限，非受信输入应先按 UTF-8 预算拒绝；首片使用固定合成名称。选出的模型原文仍是虚构候选材料，不作为现实证据。
- 不使用 append-only flush 链：它要求所有 RP 原记录 accepted，candidate/accept 历史会被拒；X2 保留模型 candidate，改用有界、服务端维护的 ID 清单而非放宽扫描断言。
- 接受是用户对“保存这段扮演回忆”的确认，不是承认剧情现实发生。取消/隐藏/拒绝内容不进入重建；旧回执不能冒充当前可见性。
- 源级删除与未来写入粒度仍未解决；X2-A 不提供局部遗忘、批量导出或源改名重放。普通重开不宣称强 Soul Continuity。
- 回退不能把旧 main 直接对含新 SourceType 的 fixture 启动；先停写保全，兼容未知则拒绝。具体可执行合同见[L1提案](../planning/LE-RESET-01-X2-A-L1-IMPLEMENTATION-PROPOSAL.md)。
- 初始化并非无子进程：durable.create_install会运行固定release导入探针，并在fixture下生成bridge参考文件；不调用Host connect。L1必须给该唯一子进程加固定argv/包/最小环境约束并验证真实导入位置，不能把本轮Core合成通过当成已验证隔离启动器。

## 下一门

建议用户只批准上述最小 Core 闭包与 L1 工具层、合成测试和试用卡的实施；不批准复制整个 dirty 目录。实现必须再经固定 Head 独立审核及验收，继续 Draft、不自动 merge。真实模型配置与预算另见[独立模型合同](../planning/LE-RESET-01-X2-A-MODEL-TRIAL-CONTRACT.md)，未填目标或缺硬限证明时保持关闭。该合同不继承本机另一份 Hermes 三会话/五请求的专项许可。
