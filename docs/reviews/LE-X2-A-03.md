# LE-X2-A-03：Origin 调查与固定版本待独审包

这是限定范围的作者静态复核和诊断交付，**不是独立审核批准**。当前状态只见 [STATUS](../STATUS.md)。用户操作入口是 [五步诊断卡](../trials/X2-A-ORIGIN-DIAGNOSTIC.md)。关联 [Issue #63](https://github.com/y19870785/life-engine/issues/63)、[PR #64](https://github.com/y19870785/life-engine/pull/64)、[Draft PR #65](https://github.com/y19870785/life-engine/pull/65)。

## 快照与变更边界

- 审查 Base：`baa59729babf9ac56a17e02c682de2e3086e3575`。
- 审查 Head：`e00778b300bfc84fc14b4ca982a23b7bc7ef6cc4`，版本 `X2-A-L1.1`。
- 2026-10-25 实时查询：#65 OPEN / Draft，Head、Base 与上述一致；`reviews=[]`、行内 review comments 为空。#64 唯一 OWNER Review 为 COMMENTED，且明确只审文档、非本机代码独审，不能挪作 #65 的批准。
- 本诊断分支 `fix/x2-browser-closure` 从上述 Head 分出；本次只提交文档和文本证据，运行时、UI、Core、测试、CI 配置均无修改，没有安全放宽或空代码修复提交。文档 PR 以 `feat/x2-a-offline-l1` 为 Base，保留 #65 Draft。
- 全 19 路径 diff 的 SHA256：`1ebf5745aed923d2b084f736bf4a3b2044727bc555752fa10da1adc138947b4e`；三 Core diff：`e258f36cd481f7b01fc12bd902660bdc0833b778718c826233bf9a001eff3834`。命令为 `git diff --no-ext-diff --no-color --binary BASE HEAD [-- 三路径]`，不混用旧 C2 投影 diff 的 hash。
- [16 个审查文件的 Git 内容/本地字节绑定](../validation/LE-X2-A-03/source-binding.json)。本检出包 SHA256 为 `61ee20c2bd66aa0c05112783940da16c482b18a54510b4e3ee567e4f471171cb`；各文件 LF 归一化后与固定 Head 相等。#65 原检出记录的 `5cb54308…` 是另一份本地字节快照，不能用新目录打开旧摘要 fixture 并称兼容。本文档不进入应用包摘要。

## Origin 证据与分类

沿用 LE-X2-A-02 的实际 Chrome 观测（本轮未重放浏览器操作）：页面 `http://127.0.0.1:9262/`；点击“新建扮演”；Chrome `Network.requestWillBeSentExtraInfo` 中 Host=`127.0.0.1:9262`、Origin=`http://127.0.0.1:11434`、Referer=`http://127.0.0.1:9262/`；页面显示 `ORIGIN_DENIED · 阶段 http`，故事数仍 0。浏览器网络事件只选取这三个头字段，未导出凭据。服务端未回显实收头；不将浏览器事件冒充服务端原始抓包。

上一轮已明确遇到两类工具限制：扩展页面访问被策略拒绝；原生控制随后因无法可靠确定当前 URL 而要求停止。本轮未再调用该工具，没有改用其他 UI 自动化、CDP 或进程启动规避同一限制，也没有读取已有 Profile、扩展、历史、Cookie 或密码。没有发起新的系统代理/全局浏览器变更。先前启动参数、代理和监听观察均只能是环境线索，不能成为归因结论。

| 对照 | 真实执行情况 | 结论边界 |
| --- | --- | --- |
| 原 Chrome，固定 Head，新合成 fixture | LE-X2-A-02 已执行：加载成功，新建被拒绝；本轮不重跑 | 错误 Origin 症状成立，整条浏览器闭环未通过 |
| 全新 Chrome 临时 Profile | NOT_EXECUTED；已交付用户手动命令 | 不能声称已隔离或已解决 |
| Edge InPrivate | NOT_EXECUTED；已交付五步手动入口 | 不能声称 Edge 可用；InPrivate 也不保证无代理/策略 |
| 独立浏览器测试实例 | NOT_EXECUTED；不绕过工具停止限制 | 无浏览器新证据 |
| 真实 loopback HTTP 对照 | 本轮执行，见下文 | 只证明本源接受、错误源拒绝，不替代浏览器 |
| 人工完整点击验收 | NOT_EXECUTED | 不宣称 USER_TRIAL_READY |

**当前分类 D：根因未明。** A 类“浏览器环境干扰”有待隔离对照支持；B 类前端错误没有静态证据支持；C 类服务兼容问题未证明。11434 只是异常 Origin 的端口，不能据此指认 Ollama、扩展、代理或任何服务。

### 前端与服务静态定位

- `examples/x2/app.js:9-19` 的 `call(path, body)` 使用 `fetch(path, options)`；所有调用点是 `/api/...` 相对路径，没有绝对 URL、11434、重定向配置或手工 Origin 头。POST 只设置 Authorization、Content-Type、X-X2-CSRF。页面从本源加载 `/app.js`；`history.replaceState(null, '', '/')` 仅移除片段，不改变 origin。
- `examples/x2/index.html` 不含 iframe、base、外部脚本或表单提交；`style.css` 无网络引用；`fixture.json` 是离线合成说明。没有 Service Worker 注册代码。这排除仓库自带 SW，**不能排除已有环境的 SW/注入或策略干扰**，没有读取浏览器存储来验证后者。
- `tools/x2_web.py:54-64,155-160` 将预期 Origin 构造成当前随机端口的 `http://127.0.0.1:<port>`，以 `get_all` 精确单值比较；预期值不是 Referer 或客户端可选参数。Host、Bearer、Origin、CSRF 都需通过，之后才路由到控制器。
- HTTP handler 只返回 200/403/409/404/405/500，没有 3xx 或 Location，没有代理/跨域路由；无 CORS。CSP 的 connect-src 为 self。未知端口的 Origin 被拒绝符合设计。
- 缺少隔离浏览器目标请求的同组 URL/Host/Origin/Referer/状态/发起者对照，故本轮没有可证明的最小代码修复。**保留原校验，不添加 11434 白名单，不改监听方式。**

### 本轮 HTTP 因果对照（不是浏览器）

Python 3.12.10、固定 Head、本检出包、新 fixture，随机端口 `2365`。使用同一个已完成 bootstrap 的测试客户端，只改变 Origin，Referer 保持该 X2 本源。负例 403 / ORIGIN_DENIED，拒绝后 sessions=0、没有 Access-Control-Allow-Origin；随后本源 Origin 的 `/api/new` 为 200 / roleplay。[最小结果](../validation/LE-X2-A-03/http-origin-probe.json)。测试结束已关闭服务和 Controller，fixture 保留。

复现命令：在检出目录将下面代码通过 PowerShell here-string 管道输入 `py -3.12 -B -X utf8 -`；它只开合成 fixture，不操作浏览器，也不输出口令：

```python
import sys, threading
from pathlib import Path
root = Path.cwd()
sys.path[:0] = [str(root/'tests'), str(root/'tools'), str(root/'runtime')]
from test_x2_web import Client
from x2_runtime import Controller
from x2_web import make_server
c = Controller(); server = make_server(c)
worker = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .05})
worker.start()
try:
    client = Client(server.launch_url); client.bootstrap()
    status, result, headers = client.send('POST', '/api/new', {},
        {'Origin': 'http://127.0.0.1:11434', 'Referer': client.origin+'/'})
    assert (status, result['code'], len(c.state['sessions'])) == (403, 'ORIGIN_DENIED', 0)
    assert 'Access-Control-Allow-Origin' not in headers
    assert client.send('POST', '/api/new', {})[0] == 200
    print('WRONG_ORIGIN_DENIED_AND_SAME_ORIGIN_ACCEPTED')
finally:
    server.shutdown(); worker.join(5); server.server_close(); c.close()
```

## 限定代码作者复核

审查的是上面固定 Head，不重新审计全仓。下列是作者判断及对应测试索引，**不是独立批准，也不是穷尽安全证明**。

| 检查项 | 固定实现与证据 | 尚需独审确认 |
| --- | --- | --- |
| 三 Core 最小投影 | `domain.py` 仅加 ROLEPLAY_RECALL；`memory_runtime.py` 新来源形状、同事务验源、通用变更入口防脱壳；`roleplay_recall.py` 177 行确定性摘要。无 Schema/Migration/Prompt 改动 | 与 #64 审定投影逐项签认；通用 owner API 与 UI 权限区别 |
| 来源与跨 World | `execute_pending(finish)` 只用服务端 ledger 中的 Memory ID，逐项核 scope、actor、source、audience、canon、reality、binding；Core 核同 Owner/Soul、ROLEPLAY 源与 Timeline、SOUL 目标，回忆仅 Soul audience | 源成员校验与源归档后读语义；同一 OS 用户可写 fixture 不在对抗边界 |
| 候选/接受 | `record_recall` 默认 accept=False；HTTP 接受无 Memory ID/World 外来参数，用当前候选和 CAS revision。Core 通用库可由授权 Owner 显式调用 accept=True，不代表页面自动接受 | 不混淆底层 Owner API 的可信输入与浏览器输入；没有正文事实真伪保证 |
| 虚构边界 | ROLEPLAY_RECALL 固定 FICTIONAL_SHARED_EXPERIENCE、shared_experience、TEXT subjects；普通 Session 只见 accepted；原 RP 用户/模型记录不直接进入 Soul 查询 | 摘录允许包含所选原文片段；不能宣传为绝无原文，也不能称自然模型能力 |
| 持久与新进程 | SQLite 持久层；启动新 runtime 关闭旧 lease，重开 Soul Session；测试 `test_http_process_close_reopen_full_loop` 用真实退出与新 Popen、旧 token 拒绝 | 浏览器跨进程仍 NOT_EXECUTED，不能用此测试代替 |
| 重试与未知结果 | turn/finish/accept 的 request+payload fingerprint、Core 唯一 receipt；accept 提交后实际 RST 再试不重复。recover 仅恢复已提交完整 pair/候选/接受索引，不补半轮、不自动接受；new/end 未知结果停写 | pending 和控制索引写入窗口；见下列已知恢复限制 |
| HTTP 边界 | 127.0.0.1:0、随机 token/CSRF、单值 Host/Origin/Bearer、正文 8192 上限、字段白名单、无 CORS、固定静态路由、CSP、textContent、无 eval/innerHTML；错误响应不输出请求头 | 重复头/非常规方法等完整攻击面需审核；当前测试不是协议模糊测试 |
| 路径/包 | fixture ID 32 位小写十六进制；每层拒绝 symlink/reparse（含 Windows junction）；生命周期锁；注册表固定 synthetic-host、agent；release 文件/控制索引/包摘要绑定 | 存在校验与打开间的 TOCTOU 窗口；不抵抗同一 OS 用户恶意换路径，不能宣称对抗级沙箱 |
| 初始化/离线 | 只在 fixture 调 durable.create_install；导入探针 SHA、argv、manifest、解释器、最小环境固定；子进程禁网络/再派生，主 CLI 禁 connect/DNS/外部 bind；无 provider 导入 | `adapter='hermes'` 是合成注册信息，不能冒充真实 Hermes 接入。直接 Controller 类不自动安装 CLI 的网络审计钩子 |
| 导出/诊断 | `diagnostic_report` 验证固定字段后仅导出模式、计数、固定诊断、反馈枚举、初始化布尔、0 模型和 no send；错误固定 code/stage；不含口令/路径/对话/查询 | x2.json pending 可能含合成原文，不是脱敏导出，不能让用户上传 fixture 或全控制文件 |
| 纯选择闭包 | x2_selection 无 Host/provider import；确定性摘录 6×180 bytes，NFKC 词面选择，仅从已授权可见 recall 输入取最多 6 条 | 不是语义检索；字段结构由调用方提供，纯函数自身不是权限门 |

### 已知缺口，不隐藏为“已通过”

- **R1 浏览器阻塞**：独立 Profile/Edge 及完整 UI 闭环均未执行；这是体验准入阻塞。
- **R2 真正独审缺失**：同一作者的复核不独立；没有另一位审核者对固定 Base/Head/diff/测试作结论。保留待审，不委派或伪造 Review。审核者应按上表逐项确认或给出发现；任何代码修复会使此代码 Head 绑定失效，需重测、重新独审。
- **R3 刷新/断连恢复限制**：URL 片段清除后 token 仅在 JS 内存，刷新需重贴终端完整地址。pending request Map 也仅在页面内存；网络结果未知时应停服、同 fixture 重开核实，不刷新后把操作当全新意图重复提交。服务端同身份重放测试通过，不等于浏览器能自动恢复相同身份。
- **R4 状态机限制**：空故事停机重开变 interrupted 且没有完整轮次，UI 无法生成候选/结束，需要保留原 fixture 另建；结束前未接受的候选没有后续补认入口。均非此次 Origin 根因；本轮不扩功能或改状态机。
- **R5 非记忆操作**：`new` 没有客户端 request identity，但已有未结束故事会阻止再次创建；`end` 已结束时无新写入。反馈没有幂等 key，断连重试可能重复枚举反馈计数；不会新增回忆。不能宣传所有 POST 都 exactly-once。
- **R6 字节绑定/临时目录**：同 SHA 换行差异影响包摘要；临时目录会被系统清理。回退须保留原包与整个 fixture，不在新包尝试迁移/覆盖，不让旧 main 打开。

没有发现应当通过放宽既有安全断言才能处理的变化；本轮不改这些断言。独立审核者仍应核实上述判断，而非把“作者未见问题”作为批准。

## 验证账本

本轮定向 **52 项 / 127.262 秒 / OK / 无跳过 / exit 0**。完整 [执行账本](../validation/LE-X2-A-03/execution.json)、[日志](../validation/LE-X2-A-03/targeted.log)、[原 Head CI 实时查询](../validation/LE-X2-A-03/ci-baseline.json) 分别保存。完整命令为：

```powershell
py -3.12 -B -X utf8 -m unittest discover -s tests -p 'test_x2_*.py' -v
```

另实跑诊断卡的绝对路径启动命令：从其他 cwd 启动独立包，正常输出版本/离线模式/新 fixture 和随机地址；通过认证的 `/api/stop` 正常停服并退出 0。没有将启动口令写入附件。这是 CLI 冒烟，不是浏览器验收。

补充限制：读取旧 C2 临时投影并追加绑定的命令被自动审批拒绝（返回 blocked by policy，无更具体原因），未执行、未重试。本轮不宣称重新逐字验证了旧 C2 临时文件；固定 Git diff 和 16 文件摘要已独立保存，三 Core 的语义检查如上表，最终独立签认仍待完成。

此命令覆盖 5 个 X2 模块：来源与跨 Owner/Soul/Timeline、候选与接受/防现实升级/Bridge、路径与 junction、未知控制对象拒绝、真实 HTTP Host/Origin/Bearer/CSRF、RST、进程崩溃四窗口、新进程召回、离线审计哨兵。既有全量 736 项 / 783.855 秒 / OK(skipped=3) 是 #65 原交付记录，包含提交前 EOF 空行清理的已说明边界；**本轮未重复本地全量**，不能写成本轮新跑。

2026-10-25 实时核对 [CI 40056006236](https://github.com/y19870785/life-engine/actions/runs/40056006236)：`headSha=e00778b300bfc84fc14b4ca982a23b7bc7ef6cc4`、pull_request、completed/success；Ubuntu 3.11/3.12、Windows 3.11/3.12 均 SUCCESS。本轮无代码修改，不手动重复 CI、不把旧 Head 当新代码通过；文档 PR 的自动 CI 如触发应在 PR Checks 单列，不改变浏览器/独审门禁。

## 后续最小闭环

先收用户手动 Edge 对照的固定结果。成功则同环境按试用卡做完整跨进程点击并取得独立审查；失败则按五步卡的允许字段进一步区分 A/B/C/D。没有这些证据，不宣称根因已修复，不提交猜测性的兼容改动，不合并 PR。
