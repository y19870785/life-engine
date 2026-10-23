# LE-RESET-01：阶段自治与安全边界提案

本轮实际权限与状态只见 [STATUS](../STATUS.md)。Issue #63 授权审计、离线验证及仅文档 Draft PR，不授权下面的开发、模型或 Host 操作。本文是未来阶段合同模板，不从“想自主开发”推导生产权限。

## 权限分级

| 级别 | 未来合同可以一次性授权的动作 | 必须保持的停止门 |
| --- | --- | --- |
| L0 调查/文档 | 读仓库及公开 PR/CI、分析、离线既有测试、独立文档分支、push/Draft PR | 不读密钥、不探生产数据；不改 Runtime/Workflow/Schema；不 merge。此轮仅此范围 |
| L1 隔离体验实施 | 指定目录内代码/测试/试用卡；全新合成 fixture；本地 loopback UI；构建版本包；合同内自主修复并提交 Draft | 需要下一次明确实施许可；不导入真实聊天、不读 Host Home/生产 store、不调用模型、不调度发送；不放宽安全断言 |
| L2 真实模型试用 | 指定模型/端点/凭据引用/合成数据/硬请求和费用上限的有限调用 | 单独批准，实际请求前持久计数；未知结果计入、无自动重试；不因模型可用获得 Host 或工具权限 |
| L3 真实隔离 Host | 精确版本、Profile/环境/数据根、允许回调与预算下安装/探测/回退 | 单独批准，依赖闭包/进程/网络范围固定；Default Home 保护；未知目标、共享状态或包漂移即停 |
| L4 渠道/生产/迁移 | 本提案不默认预授权 | 真实发送、定时任务、Gateway 重启、生产写入、迁移、权限扩大、密钥访问/外传及 merge 都需用户针对动作明确授权 |

生产秘密外传不属于建议开放能力；模型最小凭据引用也不能变成“随便查找可用 key”。同样，后续若获只读 Host 许可，应先证明只读方式不会创建 SQLite WAL/SHM 等副作用，不能仅因命令名字叫 status 就推断零写入。

## 一份阶段合同，应减少用户介入但保留真实控制

下次批准时一次冻结下列字段；缺失的动作默认为未授权，不要求用户对已批准范围内的每个局部修复再回复“继续”：

```text
authorization_id / revision / human approval reference:
effective_at / expires_at / revocation:
goal / user trial / allowed scenario IDs:
canonical Base / allowed paths / source manifest:
allowed actions (edit, offline test, package, push, Draft):
forbidden actions and protected roots:
fixture identity / model or Host contract references:
budget (time, requests, retries, repair loops, cost):
acceptance / reviewer / evidence bindings:
stop / resume / handover record:
```

生命周期为 proposed→approved→active→review required→closed/revoked/expired；暂停或额度不足不自动延期。用户撤销立即停止依赖动作、保全证据；恢复先查批准版本/剩余额度/实际远端状态，不把旧批准复制成新授权。阶段结束、scope/架构变化、碰生产、重复同因两轮不收敛、预算耗尽均停在准确失败或待审状态。

同一时间仅一个切片写代码。可以连续自主调查→实现→局部测试→全量→打包→作者自检→合同许可的独立复核→修复→Draft；独立复核者要读固定快照，不能替作者改代码后自审。多 Agent/委派仅在用户或适用规则明确允许时使用；本轮没有启动子代理。没有独立复核时就写待复核，不用作者换一个提示词冒充。

## 门禁按风险分配

| 必须保留的门 | 可简化的流程（待合同批准） | 原因 |
| --- | --- | --- |
| World/audience、FICTIONAL 来源、candidate、删除控制、generation/epoch、未知交付不重发 | 相同阶段内的有界修复无需逐次询问“继续” | 安全语义与操作节奏是两回事 |
| Schema/迁移/正式 M1 writer 与 Host/模型/发送分权 | 一份任务书列明数个紧邻小步骤，统一证据账本 | 不让规划文件数量变成进度；也不从路线图推权 |
| 固定 Base/Head/diff/测试/包/反馈版本 | 只维护 STATUS 和当前切片试用卡；引用原证据，不全文重复 CURRENT | 减少状态漂移；不重写历史失败 |
| 独立复核、Draft/Ready/Merge、exact main CI 各自门 | 风险相近的文档事实核对可集中一次完成 | 审核适用性必须绑定实际变化；不能在此取消四矩阵或全量测试 |
| 真实调用预算与隔离目标 | 同因失败最多两轮自动修复，超界交付阻塞 | 防止陷入无限 helper/allowlist 修补 |

不在此实现 docs-only CI 优化、定时续跑、自动通知或自动合并。现有要求全量测试的提交仍执行；以后的 CI 性能优化需独立提案、实际模块计时和覆盖不缩水证明。

## 审核绑定、基线竞争与恢复

审核记录至少绑定 Base、Head、`git diff --name-status`、树/关键文件摘要、命令/环境/退出码、CI event/attempt/SHA，以及体验包 manifest。Head 或相关依赖改变，受影响结论失效并重审；只改说明文字也要说明旧代码证据为何仍适用。PR CI 不等于 exact canonical-main push CI；模型观察绑定安装包版本，不由 main 绿自动继承。

提交/推送前复查 scope 和真实远端 main。若 Base 移动，先记录变化并评估相关性，必要时重建文档分支或重审；不能凭旧 Base 通过就修改生产。将来即使获 merge 许可，也要按当次批准 Head 和服务端竞争机制执行；无法保证 Base 条件就停在人工门。**本轮永不尝试 merge、Ready 或启用 Auto Merge。**

中断恢复先读账本和远端：同一动作 intent/receipt、PR URL、Head、CI、包摘要、剩余请求数；不重复创建 PR、重复模型请求或重新安装。缺回执写 UNKNOWN 后只读核验；recovery 只恢复事实，不授予执行权。未知外部调用结果不重发。

## 每 1–2 周的交付与反馈

开工时固定一个体验问题与可操作试用；周期中完成必要工程与验证；交付时给一条入口、已验证/未观察边界和上一版回退方式；用户试几天后把一处好/坏反馈转成下轮冻结用例。没有反馈时可修当前阻断，但不默认扩张到下一子系统。

周报告只列：版本及入口、用户现在能做的一件事、实际证据、仍不能证明的事项、一个下一步。遇到安全/授权阻塞，说明阻止哪个具体动作和所需最小决定，不能把范围内工作提前交还用户。Issue #63 最终停在审计完成待复核，独立复核与实施批准属于下一门。
