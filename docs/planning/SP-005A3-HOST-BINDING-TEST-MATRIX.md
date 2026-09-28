# SP-005A3 与 H0-RV Living 扩展测试设计

本表是 [A2 架构](../architecture/SP-005A2-LIVING-HOST-BINDING.md)的未来验收设计，不是已运行测试映射。SP-005A3 = NOT AUTHORIZED。自动化只使用隔离 fixture/fake transport，不访问生产 Host；真实验证另行授权，默认 DRY_RUN / NO_REAL_SEND。

## A3 自动化合同矩阵

| 编号 | 输入 / 故障 | 必须断言 |
| --- | --- | --- |
| B01 | 相同 tick invocation 重放、不同 invocation 并发 | 收据幂等，不重复 reservation/Day；Core 自然键有效 |
| B02 | 旧 generation token | GENERATION_STALE，零业务写入/发送 |
| B03 | wrong instance、安装复制、错误 Hermes Profile | 拒绝；不能只凭路径/instance 字符串通过 |
| B04 | wrong principal、正文伪造 Owner、转发/子 agent | 拒绝，不推进 inbound 或执行 Owner command |
| B05 | wrong/closed session、跨 Soul session | query/prepare/claim 拒绝；tick 合法窄 capability 可无 session |
| B06 | stale writer epoch、World revision 更新 | 旧 session/context ticket 失效，不降级 legacy |
| B07 | snapshot 超时、Living/policy revision 变化、seal 被改 | 重取 projection；8 KiB 边界；不得缓存自验 |
| B08 | plugin reload 与旧请求并发 | epoch 撤销，旧 ticket 不可 claim，新代次不继承 execute=true |
| B09 | Host restart，authority 保持运行 | 不重抽 choice、不重置 Day/budget/cooldown/follow-up |
| B10 | authority 也重启 | 新 incarnation，旧 session/snapshot 失效；先恢复 CLAIMED；不能每请求重建 incarnation |
| B11 | Life Engine restore | 新 generation、paused/协调、CLAIMED→UNKNOWN；旧 receipt 不直接写新代次 |
| B12 | prepare replay / 同 key 不同内容 | 幂等/IDEMPOTENCY_CONFLICT；不改 target/reason/quota；512 bytes 超限拒绝 |
| B13 | claim replay / 新 invocation 再 claim 同 Intent | 只有首次 execute=true + CLAIMED，其余 execute=false，无第二次 external call |
| B14 | claim 前 crash / commit 后响应丢失 | 原操作重查；超时不能当未提交，无新发送资格 |
| B15 | CLAIMED 后 send 前、send 后记录前 crash | UNKNOWN/协调，不自动重发；fake 外部计数不超过一次 |
| B16 | SENT 后 ACK 前 crash、无 ACK Host | 保留 SENT，不重发不伪造 ACK；无 SENT 证据不升级 |
| B17 | duplicate receipt，同 source/event/digest | 幂等状态推进，不生成 Attempt |
| B18 | receipt digest/target/message/Attempt 冲突 | ERROR/协调，零重发；模型/手工布尔 evidence 拒绝 |
| B19 | enrolled legacy context/wake/status/prepare/ack/observe/photo/loops | 分发前 LIVING_HANDOFF_REQUIRED；不先写旧 observation 或创建备份 |
| B20 | Schema 8 未 enrollment | legacy 行为继续，无隐式 enrollment |
| B21 | RP purpose、跨 World、Bridge 绕路 | 拒绝 Living context，H0 gate 不变 |
| B22 | 默认 dry-run + transport spy | 零真实 send；正式 instance 预览不 claim；隔离 fake 标 SIMULATED |
| B23 | inbound retry、同事件不同摘要、非 Owner | 稳定去重/冲突拒绝，received_at 不漂移；正文不变 follow-up |
| B24 | 满额与自身 cooldown；policy 降 cap | 复用 A1 C13–C16；claim 不重新申请 quota，下一 Intent 仍受限 |
| B25 | Intent 后 quiet/inbound，准备后 target 变化 | C17–C18 取消/重评；target mismatch 拒绝；不退款 |
| B26 | binding metadata 半写/丢失/损坏 | fail-closed，不从模型/旧 probe/path 重建权限；只用原 operation ID 恢复 |
| B27 | IPC 越权、token 泄露尝试、模型传 generation/revision | 拒绝；不输出 token/secrets；过期/错误方法 capability 拒绝 |
| B28 | prepare/claim 与 Owner 修改 policy/Scope 并发 | 保持 CAS/Core 同事务重验；不悄悄刷新陈旧确认的 revision |
| B29 | OpenClaw 同 agent/workspace、不同 Gateway/config | binding mismatch；二元组不足以通过 |
| B30 | 大量 status 历史、分页间 revision 变化 | 有界脱敏，游标失效；命令成功不等于验证 PASS |
| B31 | 当前模板与候选 context adapter | 模板未变，无 Living 自动 prepend/Memory 伪装，只结构化 dry-run |
| B32 | reload 后 incarnation 未变且有 CLAIMED | authority 阻断新 claim 并协调，不称 Core 已因 plugin epoch 自动恢复 UNKNOWN |
| B33 | session 关闭后 result-only submission | 新认证 collector 可记录当前 generation 的原 Attempt 结果，但不能发送 |
| B34 | revoked epoch 与发送执行权竞争 | 当前执行器最多消费一次；发送前失效即停；已在途只收集/协调，不能声称可撤回 |

A3 必须逐项映射具体测试，保留 A1 的 48 项回归。A2 不添加空壳自动测试。Claim 故障至少用新进程与进程退出，不能只 mock exception；Core 并发继续包含双进程竞态。

## H0-RV Living 未来真实隔离矩阵

各 Host 独立出报告；原始证据存仓库外并脱敏。先提供官方版本/checkout/package、Profile/Agent、Gateway（适用时）、测试 instance/Session、明确本人 target 和隔离证明。无安全环境记 NOT_EXECUTED，不重启生产服务。

| 编号 | 验证 | 证据与通过边界 |
| --- | --- | --- |
| R01 | plugin installed/enabled/loaded | 分开保存安装、启用、实际工具及本代 hook；文件不等于加载 |
| R02 | exact instance / wrong identity rejection | registry 封套、正确/错误 Profile/Agent/workspace/Gateway；无跨实例读取 |
| R03 | Living tick / duplicate wake | facade 响应、Core receipt/revision，无重复 reservation |
| R04 | context query / snapshot revalidation | SOUL session/epoch/revision/valid_until；reload 后旧 handle 拒绝；模板授权前不注入 |
| R05 | Owner inbound | 真实受信 event ID/Owner 判定/去重摘要；不导入生产历史 |
| R06 | prepare / claim | 隔离测试 instance，PREPARED→CLAIMED，回放 execute=false |
| R07 | fake/no-send dry-run | transport 隔离证明、零渠道调用；不标真实 SENT/ACK |
| R08 | plugin reload | 新 epoch/hook、旧 token 拒绝、generation 不变；不称 Gateway restart PASS |
| R09 | 测试 Host restart | 只操作完全隔离服务；Day/choice/budget/follow-up 不变，否则 NOT_EXECUTED |
| R10 | receipt availability probe | 只读确认 message/event/ACK 来源；无能力记 UNKNOWN/LIMITED，不自动发送 |
| R11 | restore 演练 | 独立副本、新 generation、旧 token 拒绝、paused/协调；不操作生产 |
| R12 | 未来真实发送 | 另授权准确本人 target；分别保存 GENERATED/PREPARED/CLAIMED/SENT/ACK，缺 ACK 停 SENT |

A2 本轮 R01–R12 全部 NOT_EXECUTED。Hermes real Host validation = PENDING_REAL_HOST_VALIDATION；OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP / H1 / H2 = BLOCKED。
