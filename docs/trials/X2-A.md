# X2-A · 离线跨会话回忆试用卡

当前门禁只见 [STATUS](../STATUS.md)。这是实际代码入口，不需要安装 Hermes、插件、模型 SDK、第三方 Python 包或 Node 运行依赖。

## 启动与亲手验证

在本 PR 的独立检出目录使用 Python 3.11+（本机正式验证 3.12）。不要在仍有未提交候选的原工作树启动另一份版本。

```powershell
py -3.12 -I -S -B -X utf8 tools/experience_x2.py start --new --offline
```

终端输出 `X2-A-L1.1`、随机 fixture ID、`http://127.0.0.1:<随机端口>/#<本次口令>`。复制**整个地址**到浏览器。片段口令载入后从地址栏移除，不写文件、access log 或导出；保留终端以便重新打开。不要将完整地址贴到 GitHub。刷新后若认证失败，需要再次粘贴终端完整地址。

1. 点击“新建扮演”，输入合成情节：`我们在蓝灯书店找到地图，约定明天去灯塔。`，点击“记录一轮”。页面显示真实保存的用户记录及明确标注的固定离线回放。每故事最多 4 轮，每条最多 1200 UTF-8 bytes，超限拒绝，不截断。
2. 点击“生成候选回忆”。审阅正文、`roleplay_recall`、源 World/Timeline、引用和 `fictional_shared_experience`。此时查询“蓝灯书店”应无已接受回忆，错误原因是 `NO_ACCEPTED_RECALL`，不表示数据丢失。
3. 点击“明确接受当前候选”，再点击“结束扮演”。接受会创建 Core 后继；不会原地把 RP 原文变成 Soul 现实事实。页面可见 predecessor 与候选/接受状态。
4. 点击“停止本次服务”或在运行终端 Ctrl+C。复制页面给出的重开命令，在相同版本目录执行：

```powershell
py -3.12 -I -S -B -X utf8 tools/experience_x2.py start --fixture <32位fixture-ID> --offline
```

5. 打开**新输出**的地址，查询“蓝灯书店”。应见已接受回忆、源 RP World/Timeline 与“这不是现实事实”的明确边界。查询“购买咖啡”应显示 `NO_LEXICAL_MATCH`；留空显示最近已接受回忆，最多 6 条。
6. 选择体验/原因并保存反馈，预览脱敏导出。它只包含计数、固定错误/模式、初始化隔离证据和枚举反馈，不含正文、个人路径、查询、提示或口令。可复制这段 JSON 反馈；不需要复制 store。

停止后也能在终端查看/复制诊断，不打开业务 DB，不推进 World 运行代次：

```powershell
py -3.12 -I -S -B -X utf8 tools/experience_x2.py status --fixture <fixture-ID> --offline
py -3.12 -I -S -B -X utf8 tools/experience_x2.py export --fixture <fixture-ID> --offline
```

`export` 向 stdout 输出 JSON，页面提供同样的可预览文本；不提供任意导出路径或自动上传。fixture 默认保留在系统临时目录下的 `life-engine-x2-l1/<ID>`，目录和 marker 组成受管索引；不接受任意路径。临时目录能跨进程重开，但不承诺抵抗系统临时文件清理。

## 怎样理解来源与失败

| 可观察项 | 含义与下一步 |
| --- | --- |
| `candidate` | 由当前故事实际记录 ID 派生，尚未显式接受，不可普通召回 |
| `roleplay_recall` / `fictional_shared_experience` | 记得共同扮演过的情节；没有把它升级为现实观察 |
| `source_world` / `source_timeline` / `source_reference` | 指向本 fixture 的真实 Core RP 来源；浏览器不能传入 Owner/World/来源或摘要来冒充它 |
| `predecessor` | 接受后继指向原候选；源回忆录没有被无声覆盖 |
| `NO_ACCEPTED_RECALL` | 当前 Soul Session 没有可见且已接受的回忆；先审阅候选 |
| `NO_LEXICAL_MATCH` | 已有可见回忆，但本查询未提供词面命中；可试原词或留空，不能据此宣称语义能力 |
| `ORIGIN_DENIED` | 当前浏览器发来的 Origin 与页面本源不一致；保留拒绝，使用不改写请求头的干净浏览器/配置 |
| `AUTH_DENIED` / `CSRF_DENIED` / `HOST_DENIED` | 地址口令、启动会话或本源目标不对；从终端打开当前完整地址，不放宽校验 |
| `INCOMPLETE_TURN` | 中断时只有用户记录成功。新 Core 运行代次已关闭旧 session，不能用旧 lease 补写 MODEL。保留故障 fixture，导出控制诊断，另建全新 fixture；不生成半轮回忆 |
| `interrupted` | 完整轮次已提交，但进程关闭了旧 session。可审阅并生成现有轮次候选、接受、结束；不能在旧 session 追加新轮次 |
| `RECOVERY_REQUIRED` | 无法唯一证明操作已提交，或 World 多步建立/结束的结果不明。停止写入，不猜测、不更换 source/request 身份；保留并反馈 |
| `REVISION_CONFLICT` | 显示的审阅版本已过期；不自动接受。重新查看候选后再决定 |
| `FIXTURE_VERSION_MISMATCH` / `PACKAGE_CHANGED` | 包/协议与 fixture 不符；拒绝自动迁移，保留数据 |
| `FIXTURE_BUSY` | 另一进程持有同 fixture 生命周期锁；先停止它 |
| `SESSION_LIMIT_REACHED` / `FIXTURE_LIMIT_REACHED` | 4 轮/故事或 7 故事上限；另建 fixture，不清游标/重置旧实例 |

浏览器实测发现：本机 Chrome 的 X2 POST 请求实际携带 `Origin: http://127.0.0.1:11434`，而页面本源是 X2 随机端口。服务返回 `ORIGIN_DENIED`，因此该配置下**没有**完成浏览器点击闭环。没有修改全局浏览器设置或放宽本源校验；内置浏览器在本会话不可用。试用需使用不重写 Origin 的浏览器配置。无此干扰的真实 HTTP 子进程闭环与浏览器完整交互是不同证据，后者不能被前者冒充。

## 本轮实现与权限闭包

基线 `baa59729babf9ac56a17e02c682de2e3086e3575`。仅三个 Core 文件采用 #64 的固定最小投影；`roleplay_recall.py` 只归一化行尾，语义保持审定版本。纯选择器从 C2 按 AST 函数/常量闭包抽取到 `tools/x2_selection.py`，没有 import provider 包。Core 原安全测试文件未修改。

源复核绑定：C2 manifest SHA256 `045ed49ac08ead503df47133ae669810766abcce2ce666bb5ed693ac669abc02`；审定三文件投影 diff SHA256 `0e5ebf19072dea44bf7be3b65f5ed568e886c3c89a8475584e2cdd8ad44c3077`。本片三个 Core 文件归一化行尾后与投影一致，所有抽取函数 AST 与 C2 一致；原工作树 187 个候选源码摘要漂移为 0。应用包摘要（四工具、三静态资源/fixture 与全部既有 runtime）为 `5cb54308a8777c9cd8ee4fb1a743092083d06b3758169a77e16fdbb0ba234287`，不含本文档与测试。

薄控制器顺序是：`create_owner_memory(USER_REPORT/USER_CLAIMED)` → `create_session_candidate(MODEL/FICTIONAL/CANDIDATE)` → 按已存 ID 核当前生命周期/身份/受众/原 session 来源 → 固定摘录 → `record_recall(accept=False)` → 用户单独 `accept_memory` → 结束 → 新进程新 Soul Session 的 `query(limit=100)` → 纯词面选择。RP 原文和 MODEL 候选都不直接进入 Soul 召回，Owner 历史仅用于受控摘录/回执核验。

每 fixture 最多 7 故事、4 轮/故事、8 RP 记录/故事、14 个 Soul 原始行；不采用完整扫描、追加扫描、flush 游标或正式 Prompt Runtime。来源控制只读 Core 自有 `memory_idempotency` 表的固定 Scope/producer/source/slot 唯一回执，再经 `get_memory` 校验当前生命周期；不写该表、不创建第二事实库。

初始化唯一子进程是 `durable.create_install` 所需的已审导入探针。工具层校验脚本 SHA256、完整 argv、Python、Schema8、release manifest 和文件摘要，改以 `-I -S -B -X utf8`、最小系统/临时环境执行；子进程禁网络/派生执行。只在 fixture 内创建 synthetic-host 和 bridge 参考文件，不连接 Host。控制元数据按固定字段集合/有界计数/枚举验证，未知对象拒绝打开与导出。CLI 拒绝 socket.connect、DNS 查询和非 `127.0.0.1` bind；HTTP server 避免反向 DNS。

HTTP 只绑定 127.0.0.1 随机端口；256-bit 随机 bearer、独立 CSRF、精确 Host/Origin、固定路由/字段、JSON/字节上限、禁 CORS、CSP、自有静态文件、textContent 输出。错误响应有界消费请求体，避免 Windows 未读 body 导致 RST 吞掉失败原因。仅单线程串行处理，socket 有 3 秒超时；这是本地试验服务，没有抗同 OS 用户恶意控制或多用户 DoS 的安全承诺。

跨进程恢复不会复活旧 writer lease。已提交完整 pair/候选/接受只补索引，不重写正文、不自动接受；半轮和未知事实停写。外围 journal 为重试冻结合成输入、时间和身份，**可能暂存合成原文**，不是保密日志；不提供生产数据导入或删除。新建 World/结束操作先持久 pending，结果不明时保全失败 fixture，不换 ID 重做。

## 验证记录

准入：#64 Head `b7a9b24fe77c05e539f67b5779158f5882a08c61` 的 Ubuntu/Windows × Python3.11/3.12 四矩阵均成功，[运行 40051582728](https://github.com/y19870785/life-engine/actions/runs/40051582728)。OWNER 最新 Review 是 `COMMENTED`，没有将它冒充独审批准；本轮实施权来自用户明确离线 L1 授权。

定向测试第一轮：50 项，124.364 秒，OK，无跳过；日志 SHA256 `892c0240fa84fd88779f877580a5703f9c5781448e02089553b06761e5a0ffb7`。之后新增真实 HTTP accept 提交后 RST 断连/同身份重试测试，最终 HTTP 模块 5 项、12.176 秒、OK；应用包摘要已更新到上述最终版本。早期全量运行因必要修复主动停止，不计 PASS；冻结版本最终定向测试 **52 项、132.883 秒、OK、无跳过**；日志 SHA256 `2bdb92ace7bb5f6643ed9063a9de9adcfca05f44f463367fbc2fe2233eee730d`；包含未知控制对象拒绝及真实 HTTP RST 用例。最终全量：**736 项、783.855 秒、OK（skipped=3）**，退出码 0；日志 SHA256 `97da003ba0c37a71309593873962719327ce3742868b614ef3f267cfb54e0d65`。本片 52 项无跳过；全量跳过来自既有测试。正式环境 Python3.12.10 / Windows；Node22.23.2 只供既有测试使用，X2 不依赖它。代码与测试 16 文件冻结清单 SHA256 `48617907451cbcc441e36732719bfb16ee1f0be4d6264c25b87089c579d96a7a`。测试命令：

```powershell
py -3.12 -B -X utf8 -m unittest discover -s tests -p 'test_x2_*.py' -v
$env:PYTHONUTF8='1'
py -3.12 -B -m unittest discover -s tests -q
```

新增测试分五文件，覆盖 Core 通用伪造/跨 Soul/Owner/Bridge/脱壳拒绝、候选与接受、实际 HTTP、跨进程重开与旧 token 失效、双进程锁、路径/版本/注册表/Windows junction、固定查询闭包、有界限量和反馈脱敏。故障测试在独立子进程 `os._exit(73)` 强制退出四个提交窗口，另测 MODEL pair 已提交但索引未存、World 建立未知结果，以及 accept 提交后实际 HTTP RST 断连/同身份重试无重复、日志无路径堆栈；合成 production sentinel 的读取通过审计钩子拒绝，文件也保持不变。

没有真实模型、Host、消息或人类持续体验证据。独审应重点核对 Core 写门、恢复 receipt 与 controller 源成员证明、fixture 再打开、HTTP 和包绑定；“作者自检/测试成功”不等于独立批准。

## 回退与已知限制

停止页面服务或 Ctrl+C → 保留整个 fixture → 停用本包。不删除/重置、迁移、flush、覆盖或自动回滚数据。旧 main 不认识 `ROLEPLAY_RECALL`，**不能**把 `git checkout main` 后打开此 fixture 当作回退。只有相同包摘要/协议的已知版本能重开；升级包会拒绝旧 fixture，首片不提供兼容迁移。需要旧版试用时另建全新 fixture，并明确它不是原实例恢复。

这是跨会话记忆链路试验，不是自然聊天产品：回复固定、摘录确定性、检索词面，不能证明人设、语义泛化、关系成长或真实小雪提升。接受后不能在本 UI 编辑/删除；不实现模型、媒体、语音、任务、外网、任意角色卡、生产导入或多用户。任何真实模型试用仍需独立批准准确 endpoint/model/凭据引用/token 与费用硬限，本轮预算为零真实模型调用。

提交前仅清理 `x2_selection.py` 与新 Core 测试文件的多余 EOF 空行，AST 完全相等，无行为/断言变化；上述本地全量对应清理前的代码字节快照。清理后的 16 文件清单 SHA256 为 `9ef4de08a9ba8f0a150a2aa4bc1d97b00f176fcc37ced529b7cdf71436795a9d`，应用包摘要见前文；最终提交字节由精确 Head 四矩阵进一步核对，远端结果记录在 PR Conversation，不预填 PASS。
