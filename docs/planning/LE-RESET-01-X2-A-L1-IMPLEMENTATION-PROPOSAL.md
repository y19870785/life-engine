# X2-A 首轮 L1 代码实施提案

这是待用户明确批准的具体范围，当前门禁只见 [STATUS](../STATUS.md)。本轮只提交提案、候选审查和临时合成证明，**没有实施 X2 Web 产品**。本文件细化旧 X2 方案；不再把“复用 provider”当作未定范围，事实依据见[候选复核](../reviews/LE-RESET-01-X2-A-CANDIDATE-REVIEW.md)。

## 1. 建议批准的结果与范围

建议授权 ID `X2-A-L1-01`、从用户批准之时起 14 天、单一实施分支。从实时重新核验的 canonical main 开始，只采用证据页指定 C2/三文件投影中的固定增量；main 变化必须先核相关性，不能默默换 dirty 快照。模型、Host、渠道、Schema、正式 Prompt 和 merge 均不在该授权内。

目标：一个单命令启动的离线试验页，用户能输入合成扮演文本，明确结束并接受一条候选回忆，关闭后在同一 fixture 的新会话按词面检索，查看来源/失败阶段和脱敏反馈。离线响应固定标注 `OFFLINE_REPLAY / MODEL_NOT_CONNECTED`，不冒充自然聊天或当前小雪。

| 允许写入的精确路径 | 本片允许的变化 |
| --- | --- |
| `runtime/life_engine/domain.py` | 仅 ROLEPLAY_RECALL 枚举值与来源注释 |
| `runtime/life_engine/memory_runtime.py` | 仅投影中的回忆录形状/来源/通用写门、专用创建及必需 import；不带完整扫描/追加扫描，不改 query/删除/恢复语义 |
| `runtime/life_engine/roleplay_recall.py` | 新增已审完整 helper；若为安全或幂等修复需改变已审内容，必须记录新 diff 和重审，不自动扩至别的子系统 |
| `tools/experience_x2.py` | `start --new --offline`、受管 fixture 重开、状态/导出/停止；无任意路径/子命令/生产设置 |
| `tools/x2_runtime.py` | World/Session/Memory 薄控制器、当前事件/候选 ID 清单、幂等及明确失败阶段 |
| `tools/x2_selection.py` | 从 C2 抽取有界纯选择函数闭包及常量；只依赖标准库与已批准 Core，不导入 provider 包/wrapper |
| `tools/x2_web.py` | 标准库 loopback HTTP、会话认证/Origin/CSRF、长度/方法/字段校验；无通用执行路由 |
| `examples/x2/index.html`、`app.js`、`style.css`、`fixture.json` | 本地静态 UI 与原创合成种子；无 CDN、外部脚本、生产 Persona 或日志 |
| `tests/test_x2_recall_core.py`、`test_x2_runtime.py`、`test_x2_web.py`、`test_x2_process.py`、`test_x2_selection.py` | 新行为和真实子进程/HTTP 安全边界；从现有候选测试迁移必要场景而不修改既有拒绝断言 |
| `docs/trials/X2-A.md`、`docs/STATUS.md`、本片直接入口说明 | 一张用户试用卡、版本/已测/未观察及停止方法 |

这是产品代码的最小**安全闭包**，不是只允许添加 UI。ROLEPLAY_RECALL 是一种明确受控的新来源语义；若不批准前三文件，就只能交原 main 同 World 记忆样机，不能宣称“退出扮演后 Soul 回忆”。不采用降级样机偷换目标。

拟定正式启动命令为 `py -3.12 -I -S -B -X utf8 tools/experience_x2.py start --new --offline`；入口显式插入已固定包的runtime路径，不依赖当前目录、用户site或PYTHONPATH。这仍是待实施命令，当前不可运行。

明确排除：Hermes wrapper/plugin/安装/配置/flush/manage、`memory_repository.py` 新失败码、完整/追加扫描、`prompt_runtime.py`、角色卡/用户身份回退、生产数据导入、局部遗忘/源重命名/旧布局迁移、TTS/ComfyUI、联网研究、多 Agent、调度/自动化、密钥读取、真实模型请求、Ready/Merge。若要新增依赖、Schema/迁移、放宽安全测试或跨目录，停止该部分并重新定范围。

## 2. 源码上已验证的 Core 调用链，和仍需实施的薄层

下面的 Core 名称真实存在于 main/C2 投影；HTTP/UI/控制器名字是待实施接口，不是已经跑通的产品。临时路径证明仅跑 Core。

| 阶段 | 拟采用的实际 Core/API 顺序 | 权威与持久边界 |
| --- | --- | --- |
| 创建 fixture | 启动器创建唯一新 temp 根→durable.create_install（指向该根的合成 host）→WorldRuntime.register_soul/definition→create_roleplay_world/instantiate→受控建立 Soul World | 仿照 X1/回忆录 fixture 初始化；Owner/Principal/World 由服务端产生，不是浏览器参数；这只是合成身份，不签发正式 continuation |
| 新 RP 会话 | WorldRuntime.snapshot→enter/resume→SessionBinding→SessionMemoryContext | 保持 writer_epoch/revision，旧会话拒绝；进程重开按实际 World 状态进入，不冒用旧 lease |
| 用户输入 | controller 校验合成输入→MemoryRuntime.create_owner_memory(USER_REPORT/USER_CLAIMED，RP scope，固定受众) | 用户说过≠现实已观察；请求 ID 与操作 identity 持久绑定；超限拒绝而非静默截断 |
| 离线/模型候选回复 | L1 仅回放→create_session_candidate(MODEL/FICTIONAL/CANDIDATE，当前 Session 来源) | 没有工具/文件/网络；L2 不在此授权；不复用 provider 的 accepted MODEL 写法 |
| 结束扮演 | 服务端持久 ID 清单→get_memory(owner,history=True)→逐条核当前生命周期、来源与 scope→有界确定性摘录→RecallSource→record_recall(accept=False) | highlights 来自本 session 实际记录而非客户端自报。仅完整轮次生成候选；不依赖 append-only scan，也不把候选先接受以迎合 scanner |
| 接受 | 当前候选 ID/内容摘要/集合 revision→用户单独点击→accept_memory(Owner, expected_revision, stable identity)→读回后继并核 source/reality/predecessor | CAS 冲突展示需重新查看，不自动刷新 revision；禁止默许接受、重复结束变接受或重放隐藏/已拒绝结果 |
| 结束/重开与召回 | exit/open Soul Session→MemoryRuntime.query(Session,limit=100)→筛 roleplay_recall→validate_query/纯 select_recall→试验上下文 JSON | 不从 Owner 全历史直接喂模型；未接受/隐藏/已忘项不应入围。fixture 严格限量以避免 query 的旧硬上限；不声称通用全库检索 |
| 反馈/导出/停止 | controller 从固定字段构造脱敏反馈→可预览导出→关闭 HTTP 与 Core 连接、释放本片锁 | 无任意文件读写接口；不删除 store，不自动回滚业务状态 |

建议首片硬上限：每 fixture 最多 7 个 RP session、每 session 最多 4 轮；每条用户/回放文本最多 1200 UTF-8 bytes（超限拒绝），每 session 最多 8 个 RP 记录；每 session 最多一个回忆录候选及一个接受后继，Soul 总原始条目最多 14。会话/记录全由控制器限量且验证 API；达到上限明确 `FIXTURE_LIMIT_REACHED`，不重建空库或默认隐藏旧条目。这使 main 的 limit=100 不截断本片受控集合，不需要为首片合入完整扫描。有限样机不能推广为生产长期存储规模。

查询最多 4096 UTF-8 bytes、最多 6 条命中；摘录最多 6×180 bytes，Core 回忆录总正文仍受 4000 bytes 限制。回忆入模型将来也只作为带来源的数据，不能增加 system authority；HTML/JS 使用 textContent/JSON，不执行内容中的标记、脚本或工具。

## 3. 数据隔离与威胁模型

一个 X2 fixture 是一个新的合成 Soul+独立 install/data/control/World/事件清单，不能共用 Hermes store。初次启动不接受 root/profile/runtime 路径；后续只接受受管索引中的随机 fixture ID。唯一索引也放在本次 X2 专用临时工作根内，不读取 `.hermes`、`.env`、全局用户身份、系统 Persona、生产 registry 或任意 `$HOME` 内容。

每次启动校验 marker/version、规范绝对路径、祖先与叶子非链接/reparse、受管目录包含关系、Core/package manifest 与 registry 的 install/data 路径；任何未知对象或链接拒绝。默认只创建，不原地升级/迁移；未知版本不调用 `_migrate`，不猜测旧结构。目录标记不是恶意同 OS 身份的认证证明；本片不提供 OS 权限隔离、不可回滚 authority 或对抗任意本地账号篡改的保证。发现并发修改/目标变化即停写保全。

整个服务持有独立 `durable.locked(fixture_root,'x2-ui',...)` 生命周期锁，不复用 Core 实例锁 key；第二进程有界拒绝，不能替换/unlink 锁文件。HTTP mutation 串行进入控制器；Owner API/路径只从服务端快照取得。启动器只 import 本包已固定 Runtime；检测已加载 life_engine 模块来源不符即停止，不靠修改 sys.path 猜测覆盖。

必须处理真实已有的初始化子进程：`durable.create_install:469` 会生成本fixture内的release/bridge参考文件，并调用 `probe_release:401` 的Python导入检查；它不是纯内存工厂。`bridges.install_bridges:308` 只写本fixture下的bridges，真正Host connect另在其后续入口，本片不调用。配置使用defaults的 `social.enabled=false`、`photos.enabled=false`、空发送目标和显式合成host路径。

薄初始化桥只允许这一个固定脚本、固定解释器、固定release runtime及Schema8的导入探针。校验完整原argv、脚本摘要、包摘要后，以 `-I -S -B -X utf8` 启动相同已审探针，显式最小环境（系统/临时目录必需变量），不继承凭据、代理、HOME、PYTHONPATH或user site；未知subprocess/network一律拒绝。禁止将其扩成通用Popen代理或放行Host依赖准备。此argv加固放在工具层，不改durable.py；若实际无法在该固定闭包里完成，标 `INITIALIZER_ISOLATION_GAP` 停止，不偷偷新增Runtime改动。必须以真实子进程导入位置及拒绝负例证明，现有92项不证明这一新初始化桥。

### HTTP 的最低安全合同

- 仅随机端口 `127.0.0.1`；Host 精确包含本次端口，拒绝 localhost 别名、外部 Host/Origin 与 DNS rebinding 输入；CORS 关闭。
- 每次启动生成至少 256-bit 随机会话口令。URL 片段传给本地静态页，随即移除片段，AJAX 通过 Authorization header 携带；不写 access log/导出/文件，重开换口令。
- GET 仅静态文件/健康信息；业务查询要认证；写请求 POST+JSON+精确 Origin+口令+CSRF token。拒绝缺/坏 token、`Origin:null`、跨域表单、未知字段/路径、重放与过长 Content-Length。
- 不提供 WebSocket、文件浏览、Shell、插件注册、远程 fetch、任意模型 endpoint 参数或任意文件上传；静态资源路径固定，不拼接用户文件名。
- 页面设CSP：只允许本源静态script/style与本源connect，禁止外部资源、inline/eval、base与frame嵌入；不把合成文本用innerHTML/Markdown执行。静态GET不含业务正文或认证凭据。
- 默认日志只保留错误码和非敏感阶段；export 默认不含原文、路径、token 或提示。原文查看仅服务端当前 fixture 的授权页面，以转义文本呈现。

这些是验收条件；现阶段没有 HTTP 代码，不能预填 PASS。

## 4. 幂等、故障与回退

fixture 外围清单只存操作状态/已创建记录 ID/摘要，不建立新的 Soul 事实表。稳定 request/batch/accept identity 在调用 Core 前保存，Core 成功后记录回执。双写不是原子事务：崩溃后按同 identity 调 Core/读取既有结果核对，不换 source/key/时间重做；不完整 user/model pair 标 `INCOMPLETE_TURN`，不生成回忆录；未知提交标 `RECOVERY_REQUIRED`，未能唯一核对就停写。

关键窗口必须注入验证：用户记录成功而回复失败；候选已写而清单失败；accept 已成而前端断连；清单更新前杀进程。重开只能查明提交事实，不自动接受、重放、删除或发送。冻结的来源时间/内容/成员 ID 不因重试变化。浏览器重试相同按钮不会获得新 identity。

回退操作为：停止服务→关连接/释放锁→保留 fixture/control/候选/回执→停用当前包。仅已证明同 fixture 协议兼容的已知包可重开；旧 main 无 ROLEPLAY_RECALL 时必须拒绝读写该 fixture，不能用 git checkout main 充当数据回滚。若无法安全重开，导出脱敏故障元数据，保留故障 fixture；可另建全新 fixture 试上一版，但明确不是恢复原实例。本片不实现删除 fixture、清游标、重置控制账本、改 source 或批量恢复。

## 5. 实施后的硬验收与自主停止点

| 门 | 必须新增并实际运行的证据 |
| --- | --- |
| A1 最小 Core | 投影闭包完整；通用 create/supersede/受众扩张/去虚构来源/异 Soul/Bridge 拒绝；原安全测试文件逐字不变；候选未接受不召回 |
| A2 HTTP/目标 | 真实 loopback HTTP 负例：坏 Host/Origin/token/CSRF、未认证业务读取、未知字段/任意路径/超长输入、HTML/脚本作为文本；production sentinel 文件不打开不改变 |
| A3 新进程与限量 | 真实服务停止/新进程重开；同 fixture 读回来源；第二进程拒绝；7×4上限与14条Soul硬界；不同 fixture 不能互查 |
| A4 故障重开 | 上述四个窗口实际中断、同 identity 无重复；候选/接受/当前可见性核对；不能核对时明确停止，不猜恢复 |
| A5 包/导出/禁网 | 单命令来自固定包、模块来源一致；标准库无第三方运行依赖；离线无模型端口/Host/外网构造；可读诊断、脱敏导出无原文/token/个人路径 |
| A6 体验/回归 | 试用卡：输入→结束→候选→接受→重开→检索/查看来源；离线标签清楚；新增行为测试及 Python3.12 全量 OK，随后精确 Head 四矩阵。不能拿 C2 全量或92项临时投影测试代替新实现验收 |

允许在此 scope 内自主编辑→定向测试→全量→自检→固定快照独立审核→最多两轮同因修复→Draft PR；推送仅限该实施分支。建议固定 Head 独立复核为产品交付门，本轮作者复核不代替未来对实际 X2 实现的独审；是否启用委派需明确授权，不自动启动代理。

14 天/两轮同因/必要安全 API 无法组合/包或源漂移/越界调用任一到界即停，交付真实失败与上一版入口；不通过扩大 allowlist、放宽拒绝断言或追加子系统消耗预算。用户批准本合同后，在范围内无需逐步回复“继续”；到期、撤销、scope/架构变化或 L2/Host 需求都另行停门。独立审核、Ready、merge 仍分离；本片不预授权后两项。
