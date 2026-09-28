# SP-005A1 测试设计矩阵

本文件保留 A0 + R1 冻结的 48 项验收规格。A0 原审计 Base 为 `95f7485d426a0eee36c7b87b4bac2ae52f34216d`，R1 Base 为 `8dde23b3c1010f45562e50e9844e2cc6c8853c90`。A1 实施 Base 为 `9159c493ad435cf947ed8c0fef278e1f5fb9dc83`；实际测试名称见 [逐项映射](../SP-005A1-VALIDATION.md)。规范见 [冻结架构](../architecture/SP-005A-LIVING-RUNTIME.md)。A1 仍待独立审核，下面的判据不因自动测试通过而自动成为真实 Host 结论。

## 测试环境与判据

A1 自动验证使用临时 SQLite、独立 registry、受控 UTC clock、固定 IANA tzdata、可信 observation fixture 和 transport 替身。并发测试使用多个独立进程/连接，重启测试销毁进程后重开数据库，不能只重建 Python 对象。故障注入覆盖事务前、事务内、提交后与外部 side effect 前后。禁止调用生产 Host、真实聊天渠道、ComfyUI 或 TTS。

所有 case 同时检查当前行、transition、operation receipt、自然键唯一性与 scope；不得只比较自然语言输出。恢复确定性比较业务状态指纹，排除提交次数等诊断字段；保证同一输入、持久选择与最终时间下，不同合法批次大小收敛一致。模拟 SENT/receipt 仅测试内部合同，不能作为真实 Host 验收。

## 时间、活动与恢复

| 编号 | 前置与操作 | 必须断言 |
| --- | --- | --- |
| T01 午夜 | 有活动/机会，跨 local midnight 连续 tick 与重启后 tick | 旧日 CLOSED、新日唯一；过期机会不补发；daily budget 的业务日为角色当前 timezone 的 local day，数据库查询与比较使用该日相邻 local midnight 映射后的 UTC instants 区间 `[start_utc,end_utc)`，不得采用固定 UTC calendar day；rolling 24h cap 独立限制且须同时满足；DST 的 23/25 小时日不得产生第二份额度或错误重置；无重复 daily plan |
| T02 活动前重启 | 14:00 计划 15:30–16:30，14:20 停机，15:20 重启 | 保持 PLANNED、原 choice/location；未提前 ACTIVE |
| T03 活动中恢复 | 同计划 16:10 重启 | ACTIVE、effective_at=16:10，标记 inferred；不伪造 15:30 的已观察执行 |
| T04 错过活动 | 改 end=16:00，16:10 重启 | SKIPPED；不先开始再完成，不发送过期 transition contact |
| T05 已开始活动 | 停机前已持久 ACTIVE，结束后恢复 | COMPLETED 且结束为推断；与从未开始的 SKIPPED 可区分 |
| T06 长停机/分批 | 停机数日，超过 128 项积压；以不同批次恢复 | 不创造缺失数日生活事实；RECOVERY_IN_PROGRESS 时无 intent；完成后业务状态收敛 |
| T07 同时刻顺序 | close/cancel、activate、contact/media 同时到期 | 固定优先级与 ID 排序；最多一个 ACTIVE，不依赖查询默认排序 |
| T08 时区修改 | 有 active、future、prepared、sent 状态时显式切 timezone | timezone_epoch 增加、旧日 PARTIAL；未来/未发取消，已发保留；滚动预算不重置 |
| T09 DST gap | 不存在的当地时间对应计划 | 推至第一个有效分钟；超 expiry 则过期，不回退至系统时区 |
| T10 DST fold | 重复小时 wake 两次 | fold=0 的单一 occurrence；无双活动/双 intent；cooldown 用 UTC |
| T11 系统时区/tzdata | Host OS 时区不同，随后 tzdata 版本变化 | OS 不改变角色日期；规则升级显式记录，不悄悄重写已决定时间 |
| T12 时钟倒退 | now 早于已提交水位 | CLOCK_REGRESSION、无发送资格；不重开已 CLOSED 日 |
| T13 活动与地点 | 计划重叠、spontaneous、显式移动、活动结束 | 拒绝重叠；自发活动只填允许空隙；current location 来自唯一 ACTIVE；不得当作用户定位 |
| T14 外部环境 | 天气过期、provider 失败、假日未知、特殊日期闰年 | UNKNOWN/STALE 明示；不变更已持久 choice；2 月 29 日不擅自顺延；缓存不升级为永久事实 |

## 联系、预算与副作用

| 编号 | 前置与操作 | 必须断言 |
| --- | --- | --- |
| C01 允许/无理由 | 分别有有效机会与无有效机会 | 前者唯一 ALLOW/Intent/reservation；后者静默，不由模型编造理由 |
| C02 Quiet hours | 跨午夜 quiet，窗口内及解除边界 tick | SUPPRESS 原因稳定；next_check 正确；跨规则边界重新判定 |
| C03 Cooldown/spacing | 新 Intent eligibility 下不同 cooldown/min spacing、recent inbound/outbound | 采用最严格解除时刻；优先级确定；重启不重置水位 |
| C04 Daily/rolling budget | 最后名额并发竞争、失败与取消、时区修改 | 仅一份预留；失败不退额；同日及滚动 24h 限额均成立 |
| C05 决定去重 | 未变输入重复 tick，再跨时间边界/新 inbound | 相同抑制决定不重复写；输入摘要变化后可重评，不永久卡 SUPPRESS |
| C06 Inbound 竞态 | PREPARED 后、begin_attempt 前收到可信用户消息 | 旧资格失效、取消/重新判定；已开始外部发送不能声称已撤回 |
| C07 Follow-up | 显式创建、同 operation 重试、联系完成、用户 resolve | 一份 follow-up；联系不自动 resolve；无自然语言承诺直接入库 |
| C08 联系证据 | GENERATED/PREPARED/CLAIMED/SENT 各阶段重启 | 不越级到 ACK；生成内容不等于发送；未知尝试不自动重发 |
| C09 回执来源 | 模型声称已送达、未受信返回值、模拟受信关联结果 | 未受信拒绝 RECEIPT_UNVERIFIED；测试受信结果校验 attempt/message/target；不构成真实 receipt validator |
| C10 Assistant | 无 follow-up、到期 follow-up、自发虚拟活动 | 保留 assistant 的到期事项联系限制，不强加 companion 虚构生活 |
| C11 Photo | 同事件重复创建机会，quiet/无预算、机会过期 | 唯一 PhotoOpportunity；使用同一 contact budget；不创建 ComfyUI job、不补发过期机会 |
| C12 Voice | 默认关闭与显式启用策略，重复 tick | 默认无 voice 机会；启用后自然键唯一、无 TTS/发送实现 |
| C13 最后一个额度可执行 | daily/rolling cap 均为 1，已有预留 0；创建唯一 Intent 并 prepare，随后 begin_attempt | reserved count=1 等于 cap 仍允许 CLAIMED；无第二份预留；所有 execution gates 须满足 |
| C14 Intent 不自我 cooldown | cooldown=150min，t0 预留并 prepare，t0+1s begin_attempt；另测单独 minimum spacing 与两者并存 | 其他执行门均允许时立即 CLAIMED，不用自身 reserved_at 自我阻断，也不要求额外等待 |
| C15 新 Intent 仍受限 | A 在 t0 已预留；有剩余额度，cooldown 未结束时为 B 申请预留 | B SUPPRESS，无新 Intent；重复 tick 不重复 Decision；A 仍可通过执行重验，修订未取消 cooldown |
| C16 Policy 改变 | cap=2 时取得两个预留，降至 1 后执行已有 Intent 并申请第三个；分别测 daily/rolling cap 下调及 cooldown/spacing 增长 | 旧预留保留、旧 Intent 不因这些变化失去执行资格；execution gates 满足时 CLAIMED；新 Intent 仍按新规则阻断，不删除或退款旧预留 |
| C17 Intent 后进入 quiet | 22:58 预留并 prepare，23:02 begin_attempt；quiet 从 23:00 起；分别测仍有效与已过期窗口 | 无 Attempt；旧 Intent CANCELLED 或 EXPIRED，预留不退款，不等天亮复用旧 Intent；有效机会可在新 revision/input 下重评，新的 ALLOW 才建新 Intent/预留；并发重评至多一个活动 Intent |
| C18 Intent 后收到 inbound | 预留后、Attempt 前收到可信 inbound，触发 recent-inbound suppression；窗口分别有效/过期 | 无 Attempt；旧 Intent CANCELLED/EXPIRED，不退款；有效机会恢复 OPEN 并新 input version 重评，到期 EXPIRED；新 Intent 仍受旧预留预算/cooldown 限制；已有 Attempt 不经此路径重发 |

## 并发、持久性与领域边界

| 编号 | 前置与操作 | 必须断言 |
| --- | --- | --- |
| P01 重复 trigger | 相同及不同 Host invocation ID 多次 wake | 业务自然键防重；没有 invocation ID 的 tick 仍不重复 effect |
| P02 并发 wake | 两进程竞争同 root/机会 | 单活动转换、单 intent/预留；原子 CAS/UNIQUE；不持锁等待网络 |
| P03 幂等冲突/stale | 同 operation 不同 payload、旧 revision/generation | 分别 IDEMPOTENCY_CONFLICT/REVISION_CONFLICT/GENERATION_STALE；不重放副作用 |
| P04 事务崩溃 | choice、activity、intent、日志写入任一步崩溃 | 全部提交或全部回滚；恢复不出现双 choice、漏预算或无日志转换 |
| P05 外部边界崩溃 | CLAIMED 后、实际 send 后未记录结果时崩溃 | UNKNOWN/协调状态，无自动第二次 attempt；不承诺 exactly-once delivery |
| P06 随机持久 | 固定 seed/event，重启、调换无关调用次序、升级候选列表 | 已持久选择逐值不变；无关调用不影响事件选择；旧 choice 不重抽 |
| P07 Host reload | Host plugin epoch 变更、重复触发 | Core instance/generation/day/choice 不变；插件加载证据与 Living 恢复分开 |
| P08 restore | 从旧 backup 恢复新 generation，外部已有后续发送 | 旧 token 失效、暂停主动联系、未知项隔离；协调前不可发送 |
| P09 损坏 | FK、活动互斥、choice 指纹、revision/log 不一致 | doctor/推进返回 STATE_CORRUPT；不清库、不重新随机、不发联系 |
| P10 Scope/World | 错 owner/world、RP、已关闭 scope、并发 scope 变化 | 同事务 fail-closed；不跨 World；不改 H0 capability gate |
| P11 Prompt | snapshot 后活动/策略/时间变化、超预算、RP mode | revision/valid_until 失效；有界结构投影；无 Living 写回；不注入 RP；新模板必须另经 A1 授权 |
| P12 Memory/Story | 普通活动与明确提升命令、重复提升 | 普通活动只写 Living；显式提升经现有 Core API/provenance；无独立冲突真源 |
| P13 Schema copy | 多实例其中一个校验失败、全部成功 | 失败不切 registry；成功才原子激活；World/Memory/Bridge 控制记录保留 |
| P14 Legacy handoff | 已选今日 plan、旧联系人/loops、未知发送、重试 | 原值导入不重抽；预留保守占额、无 ACK；一对一映射；paused；单 writer gate |
| P15 回滚/downgrade | Schema 8 激活后旧版本启动及回退备份 | compatibility gate 拒绝旧版读新库；仅备份+旧 release 回退，保留新副本并协调发送/撤销 |
| P16 未 enrollment | 已迁 Schema 但未加入 Living 的实例 | 保持原 legacy 行为；不自动创建 Soul scope、不隐式启用新 Runtime |

## 复用与执行报告

复用现有 Engine quiet/cooldown/budget、contacts 去重、durable restore/generation、World/Prompt scope、照片 unknown/reuse、Host contract 测试的 fixture 与断言；增加跨进程和新生命周期断言，不能仅复制测试提高数量。A1 完成时逐项记录测试名称、环境、结果和缺口，并运行完整 Ubuntu / Windows × Python 3.11 / 3.12 CI。

A0 矩阵原本不执行 Schema 迁移；A1 单独授权后的实施为 `DATA_SCHEMA = 8`、`SP-005A-living-runtime-v1`，Prompt 保持 `SP-004K-prompt-v1`。Hermes / OpenClaw 真实验证仍为 `PENDING_REAL_HOST_VALIDATION`；Full Private RP / H1 / H2 仍为 `BLOCKED`。本矩阵定义验收；实施结果见逐项映射和验证记录，最终结论仍需独立审核。
