# LE-RESET-01：仓库审计与开发复盘

任务来源：[Issue #63](https://github.com/y19870785/life-engine/issues/63)。执行边界与当前裁定只见 [STATUS](../STATUS.md)。本文是固定对象的事实审计，不是生产接入记录或独立安全认证；可复核原件、版本、测试结果和完整 PR 快照见[基线](../validation/LE-RESET-01-BASELINE.md)。

## 1. 结论：缺的是一条被用户反复使用的消费链

已经做成的是一个有价值的持久世界与权限内核，以及若干受限接入；尚未证明的是“小雪在你每天使用的入口上持续表现出这些能力”。主要断点在 **聊天输入 → 可靠记录 → 选择/汇总 → 下一会话上下文 → 模型表达 → 用户反馈**。过去常把前半段工程完成当作阶段出口，后半段又依赖被延期的 Host、投影或用户手工接线。这个判断来自下面的调用路径和真实验证记录，不来自 PR 数量。

| 发现 | 证据与反例 | 对体验的影响 | 下一步 |
| --- | --- | --- | --- |
| F01：能力存在于不同层，日常聊天没有统一消费 | `cli.py:78` 调 Engine/Store；`durable.py:762` 的 context 是 legacy 状态；`bridges.py:155,294` 消费它。全仓非测试搜索没有 `PromptRuntime(...)` 构造调用；正式组装仍是 Core API | World Memory、Story、Lore、Living 做得再多，也不会自动变成下一句回答的依据 | X2 只接一条可观测的 Memory 消费链；正式 Prompt P1 另审 |
| F02：X1 是机械样机 | `experience_x1.py:179–247`：固定合成输入、JSON 事实包、`MODEL_NOT_CONNECTED`；本轮 8 个独立 CLI 调用均成功 | 用户仍要复制提示或读 JSON，不能每日和样机聊天 | 复用其隔离初始化与重开路径，补真正聊天入口；无模型时明确是回放模式 |
| F03：角色 V2 有实现，真实链卡在 Host 接线 | `hermes_card_native_hook.py:101,262,284` → `hermes_turn_proof.py:31` → `character_continuity.py:223,239`。W1 记录定位到 `persist_user` 的显示去重分类导入 bootstrap，准备依赖的子进程被拒 | 角色卡加载/提示组装不等于一轮被保存，更不等于跨会话成功 | W1 保留为独立依赖接线问题；不让它阻塞无 Host 的 X2 |
| F04：最新体验候选没有进入 main/统一交付 | main 只有 #59 卡片线；本机另有 64 个 modified/untracked 条目，包括 provider、回忆录、测试、试用卡；见 L 快照。历史包 `69c76569` 与当前补丁不同 | 远端、开发目录和安装副本可能是三种能力；用户无法凭“修好了”知道哪一版生效 | 每个体验包绑定 commit/逐文件 hash、安装对象和反馈版本；不得直接打包全部 dirty 文件 |
| F05：检索质量仍有限 | L 快照本轮评测：9/10 检索项 MET；`paraphrase` 实际返回空；摘要 3/3 固定片段保留；65 次安全检查 PASS | 换一种自然说法就可能“不记得”；安全通过不会修复漏召回 | 保留真实失败语料，先收集自然问法，再做可比较改进；不硬编码同义词刷分 |
| F06：用户无法区分没记下与没检索到 | L `provider.prefetch:120` 异常返回空串，`recall_status:134` 返回 None；只有固定 `unavailable_reason`。汇总依赖会话边界 | 聊天继续正常，看起来却像从未开发过记忆；故障被感知成性格失忆 | 可见记录/接受/检索/注入阶段与固定错误原因，正文默认不写诊断 |
| F07：高层目标尚不是 Runtime 的现成能力 | Living 的计划活动不代表自主研究；Story 关系边不等于关系学习；仓库没有完整 TTS/多 Agent 受控协商产品链 | “有自己的世界”“有判断”“长期学习”被用户理解为行为，交付却主要是状态容器 | 分别立体验场景，不把状态名改成能力名 |
| F08：治理保障真实，但成本投向失衡 | M1-A P05 同身份直写/P06 整体回滚负例真实存在；身份强证明需保留。与此同时历史规划把 M1.x 放在 M2 前，旧体验计划又把 X2 定义为底座收口 | 强身份工程很难成为 1–2 周可感知增量；用户在等待底座期间没有日常闭环 | 两轨分配预算，X2 使用明确可丢弃实例且不声称正式 Soul continuation |

代码路径均指固定 main，标 L 的指[本机冻结候选及摘录](../validation/LE-RESET-01-BASELINE.md#本机候选证据)。每项能力的测试路径、证据层级、入口及阻塞见[矩阵](LE-RESET-01-CAPABILITY-EVIDENCE-MATRIX.md)，代码链接固定到审计 SHA，不能用漂移行号替代。

## 2. 审计范围与边界

枚举 main 全树 306 个 tracked 文件；runtime 77 个 Python 模块共 16,443 行，tests 60 个 Python 文件共 14,167 行；另有 tools、examples、integrations 和部署入口。逐子系统追踪公开入口、存储、投影、Host 注册与实际消费方；静态解析 Python、核对测试场景和真实验证报告；本轮执行干净 main 全量与 X1 CLI、本机冻结候选质量评测。**没有把这些工作描述为 16,443 行逐行安全审查**，也没有探测生产 Host、密钥、数据库或当前安装副本。

文档审计覆盖 README、START-HERE、OPERATIONS、ROADMAP-2026-09、长期路线、SP-004 中期复盘、SP-006S0 架构/实施/矩阵、Soul Continuity 计划、M1-P0 协议/故障矩阵/门禁、M1-A 设计/证据、X0/X1、Host Sandbox、KNOWN-ISSUES、VALIDATION、Host ADR 与 HLV/W1 记录。额外读取 #62 的规划/流程复盘和本机 STATUS/provider/召回/遗忘设计，避免复述已存在的“优先体验”口号。文件和符号索引在基线；历史材料不因新提案被抹去。

## 3. 实际调用路径

| 子系统 | 入口 → 实际处理 → 消费边界 | 裁定 |
| --- | --- | --- |
| setup / CLI | `setup.py` → `life_engine.setup.main:201` / `deploy_cli.main:57` → install 的 preview/apply/rollback；durable release/registry → `cli.main:78` | 是部署与生活状态管理，不是交互聊天应用；本轮只读代码，不执行安装 |
| legacy 生活层 | `bridges.py` Hermes `pre_llm_call` / OpenClaw `before_prompt_build` → durable context → Engine/Store；observe/remember/loop 另走工具 | 和 World Memory 是不同真源；模型是否主动调记忆工具并不可靠 |
| World / Memory | WorldRuntime 的 Scope/Session/WriterEpoch → SQLite repository → MemoryRuntime candidate/accept/query/supersede/delete → 授权投影 | 能稳定保存、拒绝错 World/过时代次；没有自动聊天提取或语义理解 |
| Story / Lore | Story accept_event → reducer/projection；Lore 固定 book version/binding → activate | 世界事实与设定不等于模型所有输出；不能靠接受 Memory 自动确权剧情 |
| Prompt / Bridge | `PromptRuntime.assemble:280/revalidate:325` 消费受信派生投影；Bridge grant→bounded project→revalidate | 有预算、一致性和拒绝保障；Bridge prompt-only，不可写目标 Memory；当前 Host 没有统一消费正式 Prompt Runtime |
| Living / recovery | tick→opportunity→prepare_intent→begin_attempt→record_delivery；Facade 绑定 capability/一次性 permit；recovery 只查提交 | 新生活内核与 legacy 并存；计划/模拟活动不证明现实经历；恢复不授权重发 |
| Dedicated Hermes/Discord | adapter register_platform → 私有 `deliver_authorized_real_contact` → ownership→provider transport | generic send、图片、语音等均拒绝；真实 inventory/target/session 尚无当前闭环证明 |
| 卡片 V1/V2 / 工具 | onboarding prepare/install → 原生 hook/assemble；owner permission ∩ 实际工具 schema；V2 verify_pair→journal→Memory/Story→最近窗口 | 仅特定 CLI 普通文本；工具轮拒写是设计边界，不可说工具结果已被长期记住 |
| 本机回忆录/provider（L） | `sync_turn`→RP World；session_end→有来源虚构回忆录→Soul；prefetch→词面筛选→带边界 render | 比“没有任何真实记忆接入”更新，但仍是未提交候选；不能推断已接入小雪微信/当前 Profile |
| ComfyUI | `photos.photo:108` → graph token 替换 → `/prompt` → `/history` → download/outbox | 有本地 HTTP fixture 测试；默认关闭，真实 GPU、形象质量与渠道投递未由本轮证明 |

## 4. 真实证据究竟到哪里

1. 2026-09-30 报告保留一次历史受控 Discord 文字发送的引用；本批新发 0，SENT/ACK UNKNOWN，不能证明自然主动跟进。
2. HLV1–3 有限定真实隔离 Host 的只读、生命周期、authority、fake dry-run 记录。HLV3 使用真实 Gateway 但 fake transport；CI 中另用 `CI_SYNTHETIC`。两者都不是现实 provider 发送。
3. HLV4 A1/A2-R1 是 local/synthetic 实现证据；adapter 的 generic route 明确拒绝，不是插件加载后自动可用的发送机器人。
4. W1 最终记录取得导入栈，未完成 persist_user、assistant 持久化、COMMITTED 与跨会话投影；provider 调用 0。#60 已合并到 #59 分支再入 main，旧文档写 Draft 的时点不能覆盖远端。
5. 本机 2026-10-19 provider 文档记载 dongxue 两次真实模型回答和跨会话计数，这是 **HOST_RECORD / 历史文档证据**。本轮没有重演、没有读取原始私有日志或安装清单；不能验证当前部署、自然度持续性，尤其不能将 dongxue 等同于用户日常小雪。
6. 微信/OpenClaw 的真实会话、渠道、语音/图片和连续数天用户观察，在本轮可读材料中没有当前版本闭环证据；裁定为未证明，而不是“肯定从未发生”。上游最新 Host 版本本轮未源码重审，历史 blocker 不写成对所有最新版本的永久断言。

补充历史成功证据不能遗漏：[PR #57](https://github.com/y19870785/life-engine/pull/57)记载早期固定 Profile 的双新 CLI 会话观察到同 World、历史读取和两轮 COMMITTED；这与后来 W1 在另一接线环境失败可以同时成立。[PR #58](https://github.com/y19870785/life-engine/pull/58)记载历史独立 Profile 观察到工具 schema 交集 22 项、可见技能 119 项，但明确不证明 ComfyUI 生成、声线、发送或当前 Host 可用。两项都属于历史报告证据，本轮没有读取私有运行原件，不能将其扩大成持续体验通过。

## 5. 历史路线为何没有收敛到体验

| 阶段 | 获得的资产 | 延续的体验债 |
| --- | --- | --- |
| #1–22：Domain/World/Memory/Lore/Story/Prompt/Bridge | 可隔离、持久、带来源的内核；按架构拆分 #3 有合理价值 | 09 月中期复盘已经指出“尚不是可聊天产品”；之后 Prompt 完成仍缺 Host consumer |
| #23–39：Sandbox/Living/Binding/HLV | 拒绝错误身份、旧 lease、迟到/重复执行的能力；真实 fake dry-run | 关键交付仍是验证与权限层，普通用户感知不到内部 permit |
| #40–54：发送 authority 与 Soul Continuity | 本地 provider transport、架构、协议、原语反例 | 真发送延期；强身份准入与用户记忆体验的依赖越来越深 |
| #55–61：X1、角色卡、普通文本连续性与工具 | 直接朝体验迈进；工具能力按实际 schema 相交 | X1 无模型、V2 Host 接线未过、工具轮不写记忆；仍缺一个稳定可试的完整入口 |
| #62 + 本机后续候选 | #62 已复盘 CI/依赖 PR/重复状态；本机又补了 provider 和多项可靠性 | #62 没有自动获得合并授权；本机补丁没有形成与 main/安装版本统一的发布与反馈链 |

这不是“所有架构都是浪费”。删除控制、Scope、generation、输出权限与未知发送不重试保护真实隐私和外部副作用。偏差是**以内部技术门作为主要用户里程碑**，又没有安排足够早的隔离聊天和持续反馈。治理的摩擦可由一次阶段授权、一个写入分支、一个证据入口减轻；安全语义不能靠少写几份文档解除。

## 6. 重复架构、闲置能力与覆盖空洞

- **重复但职责不同：**Store 简单记忆/loop、World Memory、V2 turn journal、provider flush cursor 并存。journal 解决多步骤恢复，cursor 解决消费进度，不能直接合表；真正应统一的是入口、版本与诊断，不是强行统一数据。
- **未消费而非已证明死代码：**PromptRuntime/LivingContextSnapshot 没有进入当前普通聊天链；这是消费缺口。静态无调用不证明外部用户从未调用，不能贸然删除。
- **覆盖较强：**World/audience/epoch 拒绝、不可变修正、删除恢复、CAS/幂等、快照重验、能力交集、普通轮 proof、未知交付保守处理。
- **覆盖空洞：**当前 Host 回调顺序/依赖闭包、真实 installed wrapper、自动会话结束可靠性、自然问法/长尾摘要、连续多天打扰度、工具轮经历、不同 Profile 对应同一 Soul 的产品含义、照片身份/语音质量。
- **本机已记录但本轮未重现实测的风险：**Unicode 符号形成强匹配、冻结缓存复用不核内容、来源级遗忘阻断未来同来源写入。其设计与源码摘录见基线，不能冒充新发现或已修复；它们影响新包准入，应逐项复核且单线修复。
- **可观测性缺失：**“记录了什么/何时接受/为什么没召回/到底注入了哪版”没有面向用户的一处解释。把 exception 吞掉可保会话，但需要另给无正文诊断；不能靠让宿主崩溃解决透明性。

## 7. 本提案相对旧规划的实质变化

旧 X2 是“可信底座最小收口”；本提案把 X2 定义成**可每日使用的隔离体验试验台**，明确不授予正式 continuation 身份。旧 #62 下一周期目标仍偏 H0/H1 依赖闭包任务书；本提案先用现有 Core 做端到端可观察消费，不把 W1 成功设为 X2 前置。旧本机连续小修以局部回归为出口；本提案改成一个版本包、一张试用卡、一周反馈，缺少用户体验证据就不扩下一类能力。

具体范围、每 1–2 周切片、失败回退与需要用户决定的事项见[新路线](../planning/LE-RESET-01-REVISED-ROADMAP.md)。独立复核仍待进行，本报告不替代其结论。
