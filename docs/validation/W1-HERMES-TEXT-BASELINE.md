# W1 普通文本体验基线验证

更新：2026-10-17；初批 run ID `w0w1-20261014-01`。范围与固定 Base 见 [W0/W1 基线](../planning/W0-W1-CHARACTER-BASELINE.md)。本文件只记录本批实际取得的结果，不覆盖历史验证原件。

## T0 本地合成

新增三项测试在 `tests/test_character_continuity.py`：独立 CLI 进程重新打开同一 World、重复提交与旧 lease 拒绝；13 轮记录对最近 12 条投影的边界；中文 UTF-8 字节预算下完整原话/剧情的保留。fixture 均为临时目录与原创合成内容，子进程运行本地 CLI，无网络、模型、真实 Host 或外部发送。

既有测试继续覆盖来源分类、开场不重播、不同 World 隔离、取消/截断/压缩拒绝、工具轮拒绝，以及 Memory/Story/journal 部分成功恢复。初次新测试误用 `user_claimed` 字符串，实际合同枚举为 `user_claimed_fact`；已校准测试，未改产品来源语义。

运行结果：Windows Python 3.12，以下两组共 **58 项通过，无跳过**；源码为本分支工作树（本批只改文档与测试，无 Runtime 变更），提交对象由包含本文的 Git 提交确定。

```powershell
py -3.12 -m unittest discover -s tests -p 'test_character*.py' -v
# Ran 27 tests in 25.750s / OK
py -3.12 -X utf8 -m unittest discover -s tests -p 'test_hermes*.py' -v
# Ran 31 tests in 1.411s / OK
```

连续性模块先单独通过 14 项（22.373s），已包含在上述 27 项中，不重复计数。Hermes 分组未加 UTF-8 的初跑有两项既有 `Path.read_text()` 测试受 Windows GBK 默认编码影响；显式 UTF-8 后通过，与仓库 CI 的 `PYTHONUTF8=1` 一致，没有修改测试条件或删除断言。此处不声称整个仓库或远端四矩阵已经通过。

## T1 辅助工具的本地准入检查

新增 `tools/hermes_text_baseline_probe.py`，仅由 C 在 B 审核固定提交后运行。**该辅助工具仍未在真实 Host 完成 V2 验证；路径修复后出现的依赖缺口及其直接运行时定位见文末薄任务和诊断结果。本地准入通过不等于功能 PASS。**工具校验整个 `runtime/**/*.py` 的路径与内容 SHA-256，要求全新测试目录，清理继承的凭据/代理环境；只使用真实 Host 的 UID 分配、SessionDB 和插件 dispatcher。生命周期完成参数与文本由工具合成，不代表真实模型 finalizer 或真实 CLI turn。

父进程和明确允许的 continuity CLI 子进程禁止 Python socket 网络动作；World 初始化还允许固定的 durable 导入探针，其命令正文、schema 8、冻结 Runtime 路径与摘要均须匹配，同样注入禁网与禁子进程的 guard；其他子进程拒绝。子进程仍执行冻结的真实 continuity CLI，额外加入禁网 audit hook；不是 mock Core 写回。父子进程都禁写 bytecode。此约束面向本批已审代码，不声称是可抵御任意原生扩展的 OS sandbox。

`py -3.12 -B -X utf8 -m unittest discover -s tests -p test_w1_text_baseline.py -v`：4 项通过（0.295s）。覆盖新目录拒绝、Runtime 路径/内容摘要、错误摘要无创建副作用、父子禁网/未知子进程拒绝/子进程不写 pycache。初次跨平台测试发现 Windows audit 参数为命令字符串，已按标准 `subprocess.list2cmdline` 精确匹配修复；Linux 仍精确匹配参数列表。此 4 项新增检查与前述 58 项分开，不将其当真实 Host T1 通过。

调用参数为 `--host-root <已核验Host源码> --root <不存在的隔离目录> --expected-runtime-sha256 <B核验的tree_digest值> --dependency-site <既有只读site-packages> --expected-dependency-sha256 <ruamel/yaml/__init__.py摘要>`。依赖路径显式引用，不从隔离 Profile 查询生产安装 facts；校验 Python 主次版本、marker 摘要与实际导入位置，不安装或复制依赖。输出 `report.json` 保留实际派发事件、固定 Runtime/Host 文件摘要、提交 trace、场景检查和退出状态；成功后卸载插件、停用 V2 并恢复安装前内容，保留合成数据。失败保留现场；不得自动重跑覆盖目录。模型请求为零。

本轮修复将依赖导入、安装、激活及 SessionDB 初始化纳入统一失败记录与清理。新增缺依赖、World 初始化失败、激活后 DB 初始化失败检查；使用真实安装/恢复及 World 初始化/停用验证回收，Host 导入用合成模块。六项本地检查通过，包含两种 setup 故障子场景；未知导入探针正文、路径、摘要及 schema 均拒绝。插件回退保留空目录，V2 配置停用而非删除，合成 World 与报告保留。

第三轮辅助修复的七项本地检查通过（含可选版本查询模拟原生捕获、未知 git 参数/cwd/调用来源拒绝）；这些检查不执行真实 Host 模型，也不将版本降级标为版本检查成功。

## 初批历史结论（w0w1-20261014-01）

本批结论：**W0-REVIEW_COMPLETE；W1 EVIDENCE_PARTIAL；T1 V2 FAILED；T2 BLOCKED / NOT_EXECUTED**。helper 准入是允许隔离执行的审核结论，不是 V2 功能通过。未修改产品 Runtime，也未修改最近 12 条/48,000 字节语义。

| 动作 | 固定对象 | 实际结果 |
| --- | --- | --- |
| host-t1-v1-002 | #59 `1d1ec6b7681684cbc44458e94344c261c5a2011b` | ENVIRONMENT_BLOCKED / exit 1；隔离 Profile 缺少安装 facts 引用，已安装 ruamel 未被加入导入路径 |
| host-t1-v1-003 | 同上，显式绑定既有依赖的已审启动 guard | SYNTHETIC_HOST_MIDDLEWARE_PASS / exit 0；真实 dispatcher 的卡片组装、工具拒绝、隔离、rollback/reinstall 等八项断言通过；不覆盖 V2 |
| host-t1-v2-001 | `d67d3f840c1723e3b15e37d467e910f1a3b9de7c` | T1_FAILED / exit 1；SessionDB 导入链的可选版本 git 查询被 T1_CHILD_DENIED 拒绝，卡片安装、World 初始化和 V2 激活前停止 |
| host-t1-v2-002 | `b18540606a9e0eb75aa347699e8df794e3ab32c8` | T1_FAILED / exit 1；已导入 Host 依赖并安装合成卡片，World create_install 内 durable.probe_release 子进程被 helper 白名单拒绝 |

V2 两次执行的 Runtime 路径/内容 SHA-256 均为 `489ce764f39b2a94ec06cfcf6413a77b4144cbb50b354705352acc3d5daba2d0`。001 helper SHA-256 为 `0CED46589A4E723C6281AAC98C01269EC37B9E3DCA0CD3B8EEF20F51081B46FE`；002 为 `3DD06A387A83A7FD691D0043C8A9476F57496D492167C7EC82D7318D5CEC429E`。Host 观察 HEAD `4e745c539893422cc5509b167350049702e948ee` 含既有本地修改，因此另核验六个生命周期文件实际字节，执行前后无漂移。解释器为 Host managed Python 3.14.7，使用隔离环境与既有只读依赖，没有新增依赖安装。

002 阻断发生在 helper 第 110 行的命令匹配失败分支，未到第 107 行 Runtime 路径/摘要失败分支。只读源码和路径核验支持以下**根因推断，尚未重跑验证**：durable 将基础解释器 resolve 为 `bin/python3.14`，helper 的 `sys.executable` 保持启动路径 `bin/python3`，字符串前缀未匹配。这是验证辅助工具与真实 Host 接线未收敛，不能据此判定产品连续性功能失败，更不能宣称 V2 通过。两次均无 dispatcher 事件、UID 持久化或跨会话投影证据。

版本查询仍不执行 git 子进程；002 实际仅记录 `git rev-parse HEAD` 被拒，metadata 为 UNAVAILABLE_QUERIES_DENIED。报告中的 expected_native_fallback 是预期说明，不是实测完整版本 API 返回 unknown/None；Host 身份以外部固定 SHA 和生命周期文件摘要核验为据。

001 清理 errors=[]，因插件未安装、V2 未激活，恢复/停用不适用；Host 导入创建的合成 Profile/SOUL 保留。002 清理 errors=[]，插件文件已 restore、目录为空，合成 config 恢复至安装前内容；V2 配置不存在且从未激活，不能把它当作激活后停用验证。部分 World control 数据、identity、release 及失败报告保留。退出后无测试进程，六个 Host 生命周期摘要未变。失败目录未覆盖或删除。

T2 凭据合法引用与实际 provider 请求持久硬上限尚未满足准入，状态 BLOCKED / NOT_EXECUTED。本批 provider 请求累计 **0/12**，渠道发送 **0**，无 SENT/ACK。W0 收口来自 B 于 2026-10-14 对累计 #59 代码准入及 c8e2397 文档校准的独立审核，不授予各 Draft 发布/合并资格。

本批按修复轮次边界收口，不再修改 helper 或继续 Host 重跑。下一轮提案仅为对齐真实 durable 初始化命令与解释器身份的薄验证：从真实调用捕获并核验参数，覆盖启动路径与 resolve 路径差异，避免测试 fixture 重复错误假设；经独立审核后再决定是否重试。该提案未在本批执行，T2、W2—W4、正式 M1 和合并均未解锁。结构化纠正/遗忘、工具轮经历和超窗口检索继续 EXPECTED_GAP。

## 路径身份薄任务结果（w1-path-20261016-01）

本轮在用户另行授权后执行；Base `f99963bdad61d100486dff9670923815370ebcbb`，固定 codeHead `d1df0f4c72df9e87a16cc46ef8b84ade6525e1d3`。上节初批失败原件与退出记录保留，不改写为通过。本轮结论：**PATH_FIX_VALIDATED；T1_NOT_PASSED / HOST_DEPENDENCY_GAP；W1 EVIDENCE_PARTIAL；T2 BLOCKED / NOT_EXECUTED**。本轮唯一无模型 T1 已用 **1/1**，不重试、不扩大依赖或子进程权限。

### 改前复现与代码验证

初批 CI run `38768822634` 的精确 Head f99963b 四矩阵均失败：Ubuntu 每项 680 测试/1 失败/2 跳过；Windows 每项 680 测试/3 失败/1 跳过。它们是测试失败，不是基础设施失败，未重跑覆盖。

A 在改前重现相同失败：Windows 通过真实 GetShortPathNameW 获得短目录名，源码帧和 Profile 的短/长路径指向同一对象，samefile=True，但原绝对路径字符串比较拒绝；重现版本查询和两个 setup 子场景三项失败。Linux 实际 durable 初始化输出 argv 首项 `/usr/bin/python3.12`，启动解释器为 `/usr/bin/python3`，samefile=True；在预定 DB 故障点前复现导入探针拒绝。C 另只读确认 Host 的 `bin/python3` 与 `bin/python3.14` 为同文件。上述 T0 复现不导入 Hermes，也不使用生产依赖。

修复仅涉及 helper 和测试：新根及版本源码/cwd 先拒绝链接，再规范化 Windows 短名称作完整路径比较；Python 子进程只接受与固定解释器 samefile 的绝对路径，随后使用固定规范化路径执行。不同 Profile、错误源码来源、未知解释器、executable 覆盖、脚本/schema/Runtime 摘要不匹配仍拒绝。Git 和网络零放行，未知子进程仍禁止。

A Windows 与 Linux 各运行 9 项测试，均为 8 通过/1 项另一平台专属跳过（4.388 秒/10.583 秒）。B 独立 archive 在 Windows Python 3.12 与 WSL 系统 Python 3.12 各运行 9 项，均为 8 通过/1 平台专属跳过（4.905 秒/17.629 秒）。Windows 真实 8.3 别名和 Linux 真实解释器 symlink 回归均在对应平台执行通过；setup 回归真实经过 durable 初始化，记录真实 argv，并以 reached-stage 标记证明到达指定 world_init/session_db 注入点。B 给出 HOST_T1_CODE_ADMISSION_PASS，仅准入一次隔离实测。

### 唯一 T1 的实际结果

Action `path-host-t1-001` 使用 B 的 d1df0f4 独立快照。helper SHA-256 为 `E30C404B0E0F85246D0B5AA4E0E5E63F44B19E3A65575A184E1382296CCFA17C`；Runtime 摘要仍为 `489ce764f39b2a94ec06cfcf6413a77b4144cbb50b354705352acc3d5daba2d0`。使用既有只读依赖、managed Python 3.14.7 和全新隔离根 `/home/hechao/life-engine-w1-path-20261016-01`，没有修改产品 Runtime 或 Host 源码。

本次越过此前路径阻断，实际完成 World 安装、SessionDB 建立、V2 激活，并记录唯一 `pre_llm_call`。随后 Host 自动尝试准备新数据根的依赖，子进程被 `T1_CHILD_DENIED` 拒绝；日志报告该根没有 committed 依赖环境，最终 **exit 1**。没有 COMMITTED 写回或跨会话投影证据。不能把前序步骤执行成功记作完整 T1 通过，也不能把环境缺口当成产品连续性断言失败。

原始 report 的 state 是 **PENDING**，保持原样：进程已退出且无残留进程，不能据此误判仍在运行。源码表明 helper 只捕获 Exception，而 Host bootstrap 可抛 SystemExit；这一解释由源码及日志支持，但未采到完整运行时调用链或 traceback，不能宣称已准确定位触发来源。该报告状态限制仍保留，判断结果必须同时核验退出码与原始日志。

Host 自动依赖准备**确曾尝试**，没有成功完成；不能将未手动调用 launcher/update/repair 写成没有副作用。隔离根中的 world、profiles、installs、cache、`.hermes-update-in-progress.lock` 和报告均保留，不删除或补修。cleanup.errors=[]，V2 enabled=false，插件目录无文件，无测试进程；六个 Host 生命周期文件执行前后摘要不变。锁文件残留不代表进程仍在运行。

本轮 provider 请求 **0**、渠道发送 **0**，无 SENT/ACK。T2 合法凭据引用和实际请求持久硬上限门禁仍未满足。依赖接线缺口不在本薄任务修复范围内，已到唯一 T1 预算边界；后续仅交付证据，未经新任务授权不继续执行。

本文收口提交只改文档，继承 d1df0f4 的 helper/tests/Runtime 字节。新最终 Head 的四矩阵 CI 在此记录写入时尚待一次正常 push 触发；旧 f99963b 的失败不能代表新 Head，代码准入和本地测试也不能代替远端结果。终态由 PR 与阶段报告另行记录，不为更新状态反复生成提交。Draft、Ready/Merge、W2—W4 和正式 M1 的边界不变。

## 无模型诊断结果（w1-diag-20261016-01）

本轮单独获准定位依赖准备入口，不修复 Host、不放行依赖子进程。Base 为 `a58c36312c51b4cfd63c503c7f0261feba6afa8d`，该历史 Head 的 CI run `38857002392` 四矩阵已通过（每项 682 tests / 0 fail）。诊断 codeHead 为 `da8beacdf5ee443958de41094fc11513ccba19e7`，helper SHA-256 `09DC43E0303C32C69919278C3219256AA7DC37CA915AE3A8AA7B6C363C6CD347`；Runtime 摘要仍为 `489ce764f39b2a94ec06cfcf6413a77b4144cbb50b354705352acc3d5daba2d0`。

诊断只增加阶段 enter/return、拒绝 Popen 当场结构化调用栈及外层退出栈。栈仅文件/函数/行号；不透明 argv、脚本和字符串退出信息仅保留类型、长度与摘要，不采集 locals、环境字典、源码行或异常消息。主体 BaseException 记失败后重新抛出；逐项清理继续执行并保留原主体异常优先级。SystemExit(0) 仍保留实际退出 0，但报告为失败，不能只凭退出码判断通过。原 Git/网络/未知子进程拒绝规则不变。

A 两平台各 10 项测试为 9 通过/1 另一平台专属跳过（Windows 12.608 秒、Linux 40.088 秒）；B 独立 archive 两平台同为 9 通过/1 跳过（14.966 秒、60.564 秒）。合成普通异常、SystemExit(7)/(0)、清理中的 SystemExit、拒绝点调用链及敏感参数不进入报告的检查均通过；路径及安全负例回归保留。B 仅准入一次无模型诊断。

### 实际定位与限制

唯一 action `diag-host-001` 已执行，2026-10-17 恢复时只读对账，预算 **1/1**；使用新根 `/home/hechao/life-engine-w1-diag-20261016-01` 和上述固定快照。结果为 **DIAGNOSTIC_LOCATION_CONFIRMED；T1_FAILED / HOST_DEPENDENCY_GAP；SystemExit(1) / exit 1**。原始 report 已准确记录 T1_FAILED，上一轮 PENDING 原件未改写。

`world_init`、`activate_v2`、`session_db`、插件发现、首会话建立、`pre_llm_call`、`request_first` 和 `uid_user` 均返回。`persist_user` 只有 enter，没有 return。UID 标记返回不代表用户行已写入数据库；没有 assistant 持久化、post_llm_call、COMMITTED 或跨会话投影成功证据。

外层实际异常栈为：`hermes_state_messages.append_message` → `_message_row_params` → `_display_dedupe_key` → `context_compressor.split_user_originated_turn` → `_is_real_user_turn` → `_is_synthetic_compression_user_turn` → 导入 `conversation_loop` / `process_bootstrap` → `hermes_bootstrap` 退出。拒绝当场栈补齐准备路径：bootstrap → `venv_sync.prepare_launch` → `_prepare_borrowed_launch` → `_sync_source_dependencies` → `pm.client.ensure_tools_for_sync` → runtime staging → environment 创建/运行 → helper 拒绝进程。

安全参数结构识别程序 `uv` 及固定标记 `venv`、`--no-project`、`--python`，其他参数仍为类型/长度/摘要，不猜测或还原其内容。现在有直接运行时证据证明触发点是**用户行持久化中的显示去重分类**，不是已经返回的 request middleware。Host 自动依赖准备确有尝试且被拒；未手动 update/repair、未完成依赖修复。诊断定位成功不等于连续性完成，也未证明任何合法既有依赖绑定方案。

### 退出与交付边界

`db_close`、`plugin_unload`、`disable_v2`、`restore_plugin` 四步均 return，cleanup.errors=[]。退出后 V2 enabled=false、插件无文件、任务进程为 0。预先绑定的 **12 个源文件**摘要执行前后相同；新涉及的 **8 个源文件只有退出后观察摘要**，不追认为执行前后一致。隔离 world/profiles/installs/cache/更新锁和报告均保留，不能描述为没有副作用。

provider 请求 **0**、渠道发送 **0**，无 SENT/ACK；T2 仍 BLOCKED。本轮不重放诊断，不修改 Host、依赖绑定或 Runtime。文档收口继承 da8beac 代码字节；新最终 Head 的 CI 在此记录写入时待一次 push 触发，不能沿用 a58c363 的历史通过替代。后续依赖绑定评估必须另行界定任务，#60 保持 Draft，Ready/Merge、W2—W4、正式 M1 不由此次定位解锁。
