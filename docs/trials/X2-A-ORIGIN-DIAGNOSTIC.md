# X2 Origin 异常：五步手动诊断卡

适用于 `X2-A-L1.1`，代码固定在 `e00778b300bfc84fc14b4ca982a23b7bc7ef6cc4`。这次只排查离线页面；不安装软件，不登录账户，不调整系统代理，不读取已有 Profile、扩展或历史。当前准入裁定只见 [STATUS](../STATUS.md)，调查证据见 [复核包](../reviews/LE-X2-A-03.md)。

## 用户只需做这五步

1. **启动全新合成实例。** 本机已准备好的目录是 `$env:USERPROFILE\.codex\worktrees\x2-browser-repair\life-engine`；正式解释器为 Python 3.12（代码最低要求 3.11）。在任意 PowerShell 目录直接复制这一条命令即可，不用切换 Git 分支：

   ```powershell
   py -3.12 -I -S -B -X utf8 "$env:USERPROFILE\.codex\worktrees\x2-browser-repair\life-engine\tools\experience_x2.py" start --new --offline
   ```

   成功会输出 JSON：`version` 为 `X2-A-L1.1`、`fixture` 为 32 位小写十六进制 ID、`url` 为 `http://127.0.0.1:<随机端口>/#<本次口令>`、`mode` 为 `OFFLINE_REPLAY / MODEL_NOT_CONNECTED`。这些尖括号只是格式示例，不能原样输入。保留终端；**不要发送整行输出或完整地址**。若输出 `ok:false`，只反馈 `code` 和 `stage`，先不要继续。

2. **用 Edge InPrivate 对照。** 手动打开已安装的 Edge，按 `Ctrl+Shift+N` 新建 InPrivate 窗口，粘贴本次终端的完整 `url`。不要将 `127.0.0.1` 改成 `localhost`。核对页面版本、离线模式、fixture 与终端一致，再点击一次“新建扮演”。若没有 Edge，只反馈“Edge 未安装”，不用安装或登录。InPrivate 不保证排除所有企业策略或代理，成功/失败都是对照证据。

3. **先看页面固定结果。** 变成 `阶段 roleplay` 表示这一次写入成功；此时可以按 [完整试用卡](X2-A.md#启动与亲手验证) 继续“记录一轮 → 生成候选 → 未接受不能召回 → 明确接受 → 结束 → 停服 → 同 fixture 新进程重开 → 召回来源 → 反馈导出”。如果出现错误，只手抄固定码，例如 `ORIGIN_DENIED`、`AUTH_DENIED`、`CSRF_DENIED`。页面能打开不等于记忆闭环通过。

   仅在 `ORIGIN_DENIED` 或无法分类时：按 F12 打开开发者工具 → Network/网络，筛选 `/api/new`；若还没有记录，保持面板打开再点击一次“新建扮演”。只选目标 X2 端口的该请求，手抄 Request URL **去掉 `#` 及其后全部内容**、状态码和 Request Headers 中的 `Host`（HTTP/2 若显示 `:authority` 则抄它）、`Origin`、`Referer`；响应仅抄 `code`、`stage`。某字段未显示就填“未显示”，不猜值。可以只看脚本发起者是否为该 X2 的 `/app.js`；不需要查看其他请求。**不上传 HAR、不复制全部 Headers/“Copy as cURL”、不截图整个面板或终端，不发送 Authorization、CSRF、Cookie、口令片段或正文。** 刷新会移除原页面内存中的口令；若刷新后 `AUTH_DENIED`，重新粘贴终端完整地址，不将其归类为 Origin 问题。

4. **必要时手动做干净 Chrome 对照。** 如果 Edge 仍失败或不可用，先在终端 `Ctrl+C` 停止 X2，再用第 1 步命令创建另一个新 fixture。若已安装标准路径的 Chrome，可在另一 PowerShell 手动执行下面一条命令；它只新建临时 Profile，不修改日常 Chrome：

   ```powershell
   & "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" "--user-data-dir=$env:TEMP\le-x2-chrome-$([guid]::NewGuid().ToString('N'))" --no-first-run about:blank
   ```

   不导入数据、不登录、不安装扩展；若出现安全警告不要绕过，关闭并报告。将新 X2 地址粘贴到这个窗口，重复第 2～3 步。若路径不存在，只反馈“标准路径 Chrome 不可用”。不必再次操作原 Chrome，也不必改代理或浏览器设置。这一步是**用户手动对照入口**，不是已经执行通过的自动化证据。

5. **安全退出并反馈最小结果。** 关闭本次隔离窗口，在服务终端 `Ctrl+C`，等待命令提示符返回。所有 fixture 保留，不删除、不重置。只反馈：`浏览器及隔离方式 / 页面版本 / 端口 / fixture ID / 最后成功步骤 / 固定错误码`；必要时附第 3 步允许的几个字段。可以不提供截图。若要重开已完成或可恢复的实例，仍用原目录与原包，在第 1 步命令中把 `--new` 换成 `--fixture 实际32位ID`，使用新输出地址。不要另建实例后把它说成原记忆恢复。

## 结果怎样判断

| 最小反馈 | 能得出的结论与下一步 |
| --- | --- |
| Edge/干净 Chrome 成功，原 Chrome 曾失败 | 支持 A 类“原浏览器环境差异”；不能据此指认扩展、代理或 11434 上的某个服务。继续该隔离环境的完整试用，再做独立审核 |
| 多个环境均 Origin 异常，Host/Referer 正确 | 仍是 D 类；需将目标请求的最小字段与脚本发起者绑定分析，不放宽校验 |
| POST Request URL 本身跳到了其他端口/域，或发起者不是本 X2 脚本 | B 类或外部环境干扰的线索，尚非根因证明。提交允许字段，复核实际加载脚本与重定向链；不手改 Origin |
| Host/Origin 都与 X2 完全一致而仍被拒绝 | C 类候选；需进一步核对重复头、缺失头和服务端接收值后提出最小修复，不能直接宣布服务不兼容 |
| `AUTH_DENIED` | 确认是当前启动进程的完整地址；刷新后重新粘贴。不要公开口令 |
| `CSRF_DENIED` / `HOST_DENIED` | 重新打开当前完整地址，保持数字 loopback 主机名；只反馈固定码，不修改安全设置 |
| 无法连接 / 服务停止 | 确认终端是否仍运行，以及是否使用了旧端口；进程重开会换端口和口令 |
| `RECOVERY_REQUIRED` / `INCOMPLETE_TURN` | 停写保留 fixture。不要反复点击、换 request 身份、修改数据或迁移 |

`NO_ACCEPTED_RECALL` 是候选还未显式接受/没有可见已接受记录；`NO_LEXICAL_MATCH` 是词面未命中。它们与 HTTP 认证、Origin 和服务不可用不同。只输入原创合成情节；没有模型连接，也不证明真实小雪能力提升。

## 回退与保留

Ctrl+C 停服 → 保留原目录与整个 fixture → 停用本包。fixture 位于系统临时目录 `life-engine-x2-l1/<ID>`，可能被系统临时清理；不要为排障主动清理。包按原始字节摘要绑定，**同一 Git SHA 的不同换行检出也可能不能互开**。遇到 `FIXTURE_VERSION_MISMATCH` 应回到原目录/原包，不能自动迁移或覆盖。旧 main 没有本片入口和来源语义，不能拿它打开新 fixture；保留旧数据另建新 fixture 也不等于数据回退成功。
