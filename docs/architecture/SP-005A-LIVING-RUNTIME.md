# SP-005A0 — Living Runtime 架构冻结候选

状态：**PENDING_INDEPENDENT_REVIEW**。固定 Base：`95f7485d426a0eee36c7b87b4bac2ae52f34216d`。本 PR 只有架构文档；以下“必须”约束未来 A1，不表示已有接口、表或行为。**SP-005A1 = NOT AUTHORIZED**。

当前版本保持 `DATA_SCHEMA = 7`、`SP-004F-bridge-runtime-v1`、`SP-004K-prompt-v1`。GOV-DOC2、SP-005H0 implementation 已完成；Hermes/OpenClaw real Host validation 均为 **PENDING_REAL_HOST_VALIDATION**。Full Private RP、H1、H2 均 **BLOCKED**。A0 不依赖真实 Host PASS：本领域由 Core 持有状态，Host 只提供 wake/tool invocation/delivery；这不意味着宿主接线已经完成。

阅读顺序：[CURRENT_STATE_AUDIT](SP-005A-CURRENT-STATE-AUDIT.md) → 本架构 → [A1 测试矩阵](../planning/SP-005A1-TEST-MATRIX.md)。本文件集中记录需要长期保留的决定，不再复制成内容相同的 ADR 文件。

## 1. 冻结决定与取舍

| 决定 | 采用方案及理由 | 不采用 |
| --- | --- | --- |
| A-01 领域归属 | Living 为独立 Core 子域，首版只绑定一个 ACTIVE Soul World 的完整 WorldScope；自己持有 living_revision | 用 Host chat/profile 当 World，或为 RP 自动建立第二份日常 |
| A-02 真源 | SQLite 当前状态＋原子转换记录＋幂等记录；转换记录解释改变，快照/索引可校验 | cron 表当 schedule，模型记忆当数据库，另一套全量 Story event sourcing |
| A-03 恢复 | 按持久计划、有效 UTC 时刻和固定恢复策略收敛到当前；错过联系过期，不补发积压问候 | 重启时逐条模拟错过时刻并向用户发送 |
| A-04 随机 | 每个事件/用途独立确定性采样，选择与状态一起提交，重放读取已存选择 | 全局 PRNG 序列或每次 Prompt 重抽 |
| A-05 联系 | Opportunity、Decision、Intent、Attempt、DeliveryResult 分离；意图预留即占额，未知发送不自动重试 | 将生成/prepare/调用成功视为送达，承诺跨 Host exactly-once |
| A-06 数据升级 | 建议 A1 Schema 8，显式 enrollment、copy migration 和原子激活；旧数据不自动变成 World/Story 事实 | Schema 7 里放一个无法约束的 JSON 总包，启动时静默迁移 |
| A-07 Prompt | 只读、受信 factory 生成的 LivingContextSnapshot；版本/有效期可重验 | 模型回写当前活动，用 Bridge 绕开来源授权 |

## 2. Domain boundary 与身份

`LivingScope = WorldScope(owner_id, soul_id, world_id, timeline_id)`，额外绑定 durable `instance_id`、`runtime_id/generation`。首版 WorldKind 必须 SOUL、World ACTIVE；不创建假 CharacterInstance，继续保持 `CharacterDefinition → World → CharacterInstance → SessionBinding` 的既有 RP 模型。Soul 没有 CharacterInstance 的事实不改变。

每个 installation 内，一个 durable instance 只能 enroll 到一个 LivingScope，同一 Scope 只能有一个启用的 LivingRoot。Owner 必须显式通过已有 World Runtime 注册/核对 Soul World 后 enrollment；不能从 legacy agent_id、工作目录、profile 名或模型正文推导 Principal/Scope。缺失绑定返回 `LIVING_BINDING_REQUIRED`，不自动新建 Soul。跨安装复制数据不构成多主支持；复制体默认暂停，独立激活前须确认唯一 writer，不能宣称靠本地 SQLite 锁解决跨机器冲突。

后台 wake 不需要人为制造 OPEN chat Session：它只持有受信本地部署层授予的窄权限 `LivingTickContext`，限定 instance、Scope、generation、policy revision；只允许推进该 Soul 日常与决策，不授予 Owner Memory/Story/Bridge 操作或消息发送权限。Session 工具修改仍核对 Principal、完整 Scope、OPEN Session、WriterEpoch 和 expected living_revision。Host 文本或模型提供的身份参数不能构造这些上下文。A1 可先用本地受信维护入口及模拟 Host；不得为接线偷做 H1/H2。

## 3. 数据结构与真源

下表是领域结构草案，不是本轮新增类。所有持久实体隐含 `scope/root_id`，且 FK/查询均携带完整 scope，不允许凭裸 ID 跨 scope 获取。ID 为稳定不透明值；自然键负责去重，不能把名称当身份。可变实体带单调 revision；配置与原因正文都只是有界 DATA。

| 实体 | identity / 主要字段 | 可变部分与生命周期 | 持久化、失效与重启 |
| --- | --- | --- | --- |
| LivingRoot | root_id；Scope；instance；active_generation；policy_revision；timezone_epoch | enabled/paused；living_revision；last_evaluated_at；recovery_cursor；clock_guard | 持久根；generation 变化使旧命令/投影失效；重启从 DB 读取 |
| LivingPolicy | root_id + policy_revision；时区、tzdata 标识、daypart、预算、reason 权重、例程、seed 引用、算法版本 | revision 内容不可变；切换活动 revision 是显式命令 | 历史版本保留供审计/重放；不能用当前配置重算旧日 |
| LivingDay | day_id；自然键(root, timezone_epoch, local_date)；开始/结束 UTC；policy/plan version；visual choice IDs | OPEN → CLOSED/PARTIAL；last_updated；计划修订号 | 持久计划容器；已关闭日不因回拨重新开启，不承诺每个停机日都建一行 |
| LivingActivity | activity_id；day；类别、planned_start/end；location_id；source/reason；choice IDs | PLANNED → ACTIVE → COMPLETED；PLANNED → SKIPPED/CANCELLED；ACTIVE → CANCELLED；activated_at、ended_at、inferred 标志 | 每 root 最多一项 ACTIVE；转换入事务日志；restart 按第 7 节恢复，不补造实际开始时间 |
| LivingLocation | location_id；root；虚拟地点 category/name；catalog_revision | catalog 版本化、禁用可变；已引用历史不原地改名 | 位置不是 GPS；当前位置从 ACTIVE activity.location_id 派生。停留 start/duration/source 由该 activity 提供，避免第二份 occupancy 真源 |
| ScheduleItem | schedule_id；subject_type/id；due_at/expires_at UTC；local_spec；policy revision；recovery_policy | PENDING → CONSUMED/EXPIRED/CANCELLED；reschedule 取消旧项并建新 ID | 持久业务时刻；唯一(subject, occurrence, action)；重启按 due_at、固定优先级、ID 排序 |
| ContactOpportunity | opportunity_id；day；reason_code/source_ref；eligible_at/expires_at；目标绑定引用 | OPEN → CONSUMED/EXPIRED/CANCELLED；暂时抑制不伪装消费 | 来自 schedule、显式 follow-up 或受信事件；不会因模型“想联系”自动创建 |
| ContactDecision | decision_id；opportunity；evaluated_at；policy/input version；ALLOW/SUPPRESS；首要与全部阻断码；next_check_at | 追加后不可变；相同输入版本不重复写同一抑制原因 | 可解释审计；decision 不是发送授权或回执 |
| ContactIntent | intent_id；opportunity UNIQUE；decision；reserved_at；budget attribution；reason/context fingerprint | DECIDED → PREPARED → CANCELLED/EXPIRED，或由 Attempt 进入交付流程 | 预留额度不可因取消/失败返还；已有相同请求只返回原 ID |
| ContactAttempt / DeliveryResult | attempt_id；intent UNIQUE（A1 最多一次）；request fingerprint；target binding；evidence refs | CLAIMED → SENT → ACKNOWLEDGED；或 FAILED/UNKNOWN；结果附 verified/source/time/message ID | CLAIMED 不等于已发送；UNKNOWN 只协调不自动重发。可信外部验证器未来提供结果，A1 不实现渠道 validator |
| PhotoOpportunity | opportunity_id；day/activity；主题、时间窗、location/visual refs、reason、continuity_identity | PLANNED → OFFERED/EXPIRED/CANCELLED；未来受信媒体消费者认领后 CONSUMED | 仅意图，无 ComfyUI prompt_id/file/job；重启复用同一机会 |
| VoiceOpportunity | opportunity_id；contact context ref；时间窗；适合语音的 reason、policy version | PLANNED → OFFERED/EXPIRED/CANCELLED；未来 V 消费 | 仅表达形式建议，无 TTS provider/音频；不因生成建议追加联系预算 |
| ExternalObservation | observation_id；provider/region/type；observed_at/fetched_at/expires_at；payload digest/version | 新 observation 追加；有效、STALE、UNKNOWN 为时效判定 | 缓存可丢弃；已影响持久选择的有界输入摘要/引用随选择保存，不调用外部 API 重放 |
| LivingContextSnapshot | Scope/viewer/session fencing；living/policy/day revision；as_of、valid_until；有界时间/活动/联系/媒体投影 | 不可变，只读派生 | 不建持久快照表；进程重启、generation/输入修订/时间边界变化即失效 |

Daily State 是 LivingDay 及其实体的一致性读模型，不再同时保存另一份“current activity/current location”。已发生主动联系来自 Intent/Attempt；last_updated 来自提交，不代表最后发送时间。临时活动作为 source=SPONTANEOUS 的 LivingActivity，临时外部输入先成为 observation，不直接改当前状态。

情绪/能量首版**不设连续自治真源**：可保留经 Owner 配置的表达标签和 provenance，但不自动从用户情绪或聊天文字推断数值，不让“心情”绕过 quiet/budget。Prompt 的“有点疲惫”只能是标注为虚构的可选表述，不是改变 schedule 的命令。

## 4. Time Context、时区与午夜

唯一时钟输入是受信执行层注入的 aware UTC instant；不信任模型指定 now、Host OS local time 或调用方正文。`TimeContext` 含 as_of_utc、IANA timezone、timezone_epoch、tzdata_version、offset、fold、local_date/time、ISO weekday、daypart、calendar_status、holiday/special-date observations。模拟时钟只用于独立测试库。

daypart 默认夜间 00–06、早晨 06–11、午间 11–14、下午 14–18、晚间 18–22、夜间 22–24，半开区间，以 policy 版本固定；quiet hours 是独立安全规则，不由 daypart 名称推断。workday/weekend 按受配置的每周工作日得到 calendar baseline；地区调休/holiday 只有未过期的明确地区数据才覆盖，未知写 UNKNOWN，不由模型猜节日。special date 是 Owner 明确登记的有界月日/年日规则；2 月 29 日默认只在闰年触发，不隐式改为 2 月 28 日。

持久 schedule 存 UTC instant 和解析时的 local spec/offset/fold/tzdata_version。DST 不存在的本地分钟：活动/联系机会移到跳变后的第一个合法分钟，若已超过窗口结束则 EXPIRED；重复分钟固定 fold=0，只创建一次。有效时长/cooldown 使用 UTC 秒，不能用墙钟减法。午夜按当前 policy 的两个当地午夜映射为 UTC 边界，允许 23/25 小时日；恰在边界先关闭旧日、使旧日 contact 过期，再生成新日。

修改 timezone 为显式有幂等键的 Owner 配置命令：原日标 PARTIAL，推进 timezone_epoch，取消尚未领取的旧 epoch 日程，按新时区建立当前日；ACTIVE 活动在变更时取消，保留原时间和原因，不挪改历史。已预留/发送的 contact 不退额，Attempt 不换 ID；未发送 Intent 取消。新预算按第 6 节跨 epoch 统计，不能“换时区领第二份额度”。tzdata 更新同样显式推进 policy/epoch，不重写已决定的 UTC 时间。

若 now 小于 last_evaluated_at：`CLOCK_REGRESSION`，不推进活动、不释放发送资格；返回上次状态并标时间异常，待 clock 追平或受权协调，绝不重新打开已关闭日。向前跳跃按恢复策略处理，不把跳跃当真实发生的活动证据。

## 5. Activity、Location 与环境输入

计划创建时验证时间区间不重叠，A1 无多活动并行。正常 wake 在窗口内将 PLANNED 转 ACTIVE，记录真正处理时刻 activated_at；到 end_at 才结束已 ACTIVE 项。用户明确的 `reschedule_activity`/`cancel_activity` 可改变未来计划；当前活动切换必须在同一事务结束旧项、建立新项并递增 revision，location 随活动一次变化。两地点之间不自动捏造“路上”：需要计划里的 transit activity，否则直接切换并保留来源。

spontaneous activity 只在 policy 允许的空白窗口产生；候选按稳定优先级/ID排序并通过持久 random choice 决定，不覆盖 Owner 固定计划。用户互动或受信外部事件可以提出候选；只有 Runtime 的类型化命令和规则可以接受，不解析模型正文为直接转换。已接受 Story 事件若要影响活动，必须由显式同 Scope 命令引用 event ID，重新核权；不能反向订阅全部 Story 原文。

location category 至少 HOME/WORK/EXERCISE/CAFE/TRANSIT/SHOP/PARK/OTHER；身份是 catalog ID，不是字符串地点名。所有地点、outfit 与 routine 明确 `origin=FICTIONAL_ROLE_STATE`。assistant 模式不生成这些虚拟项目，只产生真实登记的 follow-up、时间与工作语境；不推断用户位置。

weather 取 Owner 配置的虚拟地区，禁止设备定位或由聊天猜用户地址。weather TTL 上限 3 小时、holiday 缓存上限 7 天，实际 expiry 取 provider 有效期与上限较早者，且节日只用于所覆盖地区/日期。无 provider、网络失败、未知地区或过期时输出 UNKNOWN/STALE，不悄悄套用旧天气。允许在事务外读取 provider，在事务内验证 observation ID/version/expiry 后决定；不在事务内等待网络。

Observation 不是生活事实。新的天气只能通过明确决策改变未来未领取计划；不能重写已 ACTIVE/COMPLETED 活动、已决定 outfit 或声称已下雨。外部 API 本轮与 A1 最小实现均可保持禁用，A1 用注入的 observation 验证合同即可。复制到决策的有界摘要只用于解释该次选择，不与缓存竞争“最新天气”真源。

## 6. 联系生命周期、理由与静默规则

```text
ContactOpportunity OPEN → ContactDecision ALLOW → ContactIntent DECIDED → PREPARED
            │                                                       │
            └ SUPPRESS（OPEN 保留并设 next_check）                     └ Attempt CLAIMED
              或 EXPIRED / CANCELLED                                    ├ SENT → ACKNOWLEDGED
                                                                        └ FAILED / UNKNOWN
```

SUPPRESSED 是 Decision 结果，不表示机会已发送；DECIDED 是已保留预算的联系意图。PREPARED 只登记表达材料的 fingerprint/reference，不等于 GENERATED 媒体或发送。SENT 只接受可信 transport 的实际提交证据，ACKNOWLEDGED 只接受与同 target/message ID 对应的渠道回执验证结果；模型文字、旧 ack 文本、shell 返回 0、图片文件和 H0 report.ok 都不算。

A1 最多一次 attempt，不实现自动发送重试。CLAIMED 在出进程调用前持久化；崩溃后无法判断是否调用过渠道就标 UNKNOWN，绝不重排。可独立验证未提交的 FAILED 仍不自动重试；需要未来单独 retry 合同。一个 attempt 的 SENT/ACK 证据更新必须幂等，冲突回执进入 RECONCILIATION_REQUIRED。取消只能阻止尚未开始的 attempt；已提交消息不能撤回。此协调不构成 Host final-output transaction，也不证明 late-response、历史或 stream 隔离。

稳定 reason taxonomy（枚举版本 v1）：`MORNING_GREETING`、`LUNCH_CHECKIN`、`AFTER_WORK`、`REMEMBERED_FOLLOWUP`、`LONG_SILENCE`、`ACTIVITY_TRANSITION`、`WEATHER_EVENT`、`HOLIDAY`、`PHOTO_SHARING`、`USER_PROMISED_FOLLOWUP`、`SOCIAL_IMPULSE`。每项必须有结构化 source_ref：日计划、登记的 follow-up、活动转换、有效 observation 或持久 choice。UNKNOWN reason 拒绝；模型只能将 reason 渲染为话语。assistant 仅允许显式 due follow-up 两类，不因随机冲动虚构生活。LONG_SILENCE 没有可靠 inbound 基准时不启用。

每次决策及未来开始 attempt 前按以下顺序重查（记录全部阻断码，首个为 primary）：

1. 身份/scope/generation/clock/corruption 门禁；失败即拒绝操作，不伪装静默成功。
2. paused/disabled；机会取消/过期、来源 follow-up 已解决；前者可 SUPPRESS，后者终止。
3. quiet hours；默认继承 `[23:00,08:00)`，相等端点表示关闭 quiet，跨午夜照常。
4. daily budget 与 rolling 24h 上限；`daily_min` 仅影响候选计划数量，不是保底发送承诺。
5. minimum spacing/contact cooldown：从最后一次 Intent 预留算 UTC 间隔，沿用“失败也防连发”；两项配置并存时取较大值。
6. recent inbound suppression，再 recent verified outbound suppression；两个窗口独立，取各自最晚可信时间，不用 receipt 到达时间替换 sent_at。
7. reason 仍成立、活动/环境条件有效、eligible_at 到期；从合格机会中按 follow-up 优先、到期时间、reason 固定序、ID 选择最多一个。

暂时抑制只设 `next_check_at = min(max(eligible_at, 解除已知阻断的最晚时刻), expires_at)`；若不早于 expiry 就 EXPIRED。input version 是 opportunity revision、policy revision、可信 inbound/outbound 水位、预算相关 intent 水位和时间规则区间 ID 的规范摘要；时间区间边界包括 eligible/expiry、quiet 边界、冷却解除与预算释放时间，不能只使用进程计数或每秒变化的时间戳。跨边界即重新评估。新可信 inbound 或配置变更也会使 input version 变化，可提前复核；不能在未变输入下每个 cron tick 重写相同决定。允许路径创建 Intent、消费 Opportunity、预算预留和决定日志在一个事务完成。

预算唯一真源是 Intent.reserved_at 的持久记录；不另存可独立漂移的计数。统计当前时区当天 `[start_utc,end_utc)` 内所有 root Intent（跨 timezone_epoch/policy），并同时限制过去 24h 的预留数量，默认两项上限同为 daily_max。新上限降低后已占额不撤销，但不再新增；取消/失败/未知不退款。当天跨时区移出某些预留也不能绕过 rolling cap。活动、photo、voice 本身不占联系额；若转为发送建议，必须共用一个 ContactIntent，不能一份文本、一份图片分别绕开预算。

可信 inbound 在 begin_attempt 前到达会递增 root/input revision，使准备中的 Intent 必须重新判断；若仍在抑制期则取消该 Intent（不退额）。在实际渠道调用之后才到达无法撤销已提交消息，不宣称网络边界与 DB 原子一致。

## 7. ScheduleState 与确定性恢复

ScheduleItem 是业务真源，Host 每 23 分钟只是可替换的 tick 频率，不保证准点。持久范围只需要当前日和下一日；规则可在新一天生成，不无限预排。创建/更新/消费都关联稳定 subject、occurrence 和 operation key；修改用取消旧项＋新项 supersedes 引用，不能改写已消费项。

推进流程：读最新 Scope/generation/policy → 检查 clock → 原子处理过期和活动转换 → 生成必要新日/选择 → 检查联系 → 提交 revision、cursor、转换日志、幂等 receipt。每事务最多处理 128 个到期项，排序固定 `(due_at, action_priority, schedule_id)`：关闭/取消先于激活，再到联系/媒体机会。若仍有积压，返回 `RECOVERY_IN_PROGRESS`、继续游标，禁止产出新的 ContactIntent，直到恢复收敛。响应的 `next_wake_at` 是优化提示，不成为第二份 schedule 真源。

| 到达时刻及持久状态 | 固定恢复规则 |
| --- | --- |
| 尚未到 due_at | 保持 PENDING，不提前消费 |
| PLANNED 活动 `start <= now < end` | infer-current-state：转 ACTIVE，activated_at=now，inferred=true，保留原 planned_start；不声称计划时刻真正执行 |
| PLANNED 活动 `end <= now` | SKIPPED，reason=MISSED_WINDOW；不创建 ACTIVE/COMPLETED 历史 |
| 先前已 ACTIVE 且 end 已过 | COMPLETED，scheduled_end 保留，processed_at=now，completion_basis=INFERRED_ELAPSED；只是虚拟日常收敛，不证明真实行动 |
| contact 已过 expires_at 或跨旧日 | EXPIRED，绝不逐条 catch-up 问候 |
| contact 在 grace 内 | 重新跑所有静默门；最多一个 Intent，不能补足 daily_min |
| follow-up 错过一次窗口但未解决 | 旧机会 EXPIRED，原 follow-up 保留；下一合法窗口用新的 occurrence 建机会。不是“已跟进完成” |
| photo/voice 机会错过 | EXPIRED；不触发旧场景出图/TTS，不搬到今天假装同一时刻 |
| 跨多日停机 | 关闭已有旧日；未创建过的中间日不伪造日常。只建当前/下一日，并记录 gap(start,end) |
| PREPARED/CLAIMED attempt 在重启后不明 | PREPARED 重验并按 expiry 取消；已 CLAIMED 且未确认结果转 UNKNOWN，禁止自动 resend |

例：14:00 已持久计划 15:30–16:30 咖啡店；14:20 停止，16:10 wake。结果为 ACTIVE，planned_start=15:30、activated_at=16:10、inferred=true，不能叙述“15:30 刚到”。若计划原本结束于 16:00，则 SKIPPED，按 16:10 应处的下一个活动收敛；若没有活动则明确 UNSPECIFIED，不继承咖啡店。15:30 联系机会 grace=30 分钟已经 EXPIRED，不发迟到问候。

重启相同代码、相同持久输入及相同 effective_now，处理输出顺序和状态 fingerprint 必须一致；分批恢复完成后的状态应与一次足量恢复一致（提交 revision 次数可不同，不作为业务 fingerprint）。普通停机不随机 reschedule；只有明确命令才能 reschedule。原始计划、处理时刻与推断来源并列保留。

## 8. 随机性、照片与语音机会

采样键为 `(root_id, semantic_event_key, purpose, algorithm_version, policy_revision)`，例如某日 visual、某机会 minute、某空档 spontaneous。固定算法用 HMAC-SHA256(seed, canonical_input) 产生随机字节，通过拒绝采样选择稳定排序候选的索引；canonical input 编码、候选顺序、单位和范围都版本化。不得依赖 Python hash、未固定 Random 序列或执行次数。seed 只留可信配置，不进入 Prompt。

`LivingChoice` 持久化 choice_id、自然键、input digest、候选版本、已选值及选择算法；与使用它的状态同事务提交。已提交选择是恢复真源；算法升级不能重抽旧选择。新增无关机会不会影响今天穿什么；同一键携带不同输入返回 IDEMPOTENCY_CONFLICT，不覆盖。legacy days 的具体已选值按原值导入，标 LEGACY_PERSISTED，不伪造旧算法的 choice trace。

PhotoOpportunity 固定主题、时间窗、activity/location/outfit refs、reason 和 continuity identity（root/day/visual choice 集合）；同日已决定视觉不因新的 Prompt 改变。A1 只保存/投影机会；SP-005M 才拥有 ComfyUI job、生成 seed、实际文件、media preparation 与生成结果，Host 拥有发送事实，receipt 由可信渠道证明。不把 photos 旧 job 表搬成生活真源。

VoiceOpportunity 只表示适合语音的形式建议，默认禁用；不生成音频、不选择 TTS provider、不写“已说出”。SP-005V 单独授权。photo/voice 不因到期自动调用现有外部工具，disabled 时不创建新机会，旧未消费机会取消并保留原因。

## 9. World / Memory / Lore / Story / Bridge

“今天 14:00 在咖啡店工作”默认只属于虚拟 LivingActivity/Daily State。它不是 World 地理事实、不是用户真实位置，也不是已经接受的 Story event。日常小事不自动逐条写 Story 或长期 Memory。

| 系统 | 唯一职责及允许衔接 |
| --- | --- |
| World | Owner/Soul/World/Timeline、生命周期、Session、WriterEpoch 真源；Living 验证，不复制并另行确权 |
| Living | 短期日常、未来 schedule、联系决策、预算和机会；living_revision 独立，不因每个 tick 推进 World revision |
| Memory | 经显式授权保存长期记忆；可记录“曾经一起聊过咖啡店”的记忆及 Living source_ref，但不能成为当前地点真源 |
| Story | 显式提交 proposal 并由既有 Runtime accept 才成为叙事真源；Living 只提供候选来源，不自动 accept，不直接修改 StoryState |
| Lore | 规则/设定及激活投影；不从 Lore 文本自动执行 schedule 命令；需要明示配置转换 |
| Bridge | 仍仅按现有授权字段进行 Prompt-only 跨 World 投影；A1 不新增 Living bridge data class，不读取 RP 私史或复制 Soul/RP memory |
| Prompt | 消费有界快照表达状态；不负责计算新日程、选择权威事实或回写状态 |

如 Owner 认为某次日常应升级成故事：用既有 Story 命令显式提交有 provenance 的事件，Living 保留 source ID 与历史，不将 Story 的结果复制成另一份“当前活动”。跨 Runtime 不做双写事务；失败可用同一操作身份重试既有命令，不能先自行标记 Story 已接受。源被删除/撤销时遵循各 Runtime 删除/可见性规则，Living 引用不能恢复被删除正文。计划真源与记忆叙述是不同命题，不允许两个系统共同写同一个状态字段。

## 10. Prompt projection 与用户命令

候选 `LivingContextSnapshot.from_session_query` 必须绑定 `PromptSessionContext` 的 Scope、Soul viewer、Principal、Session/WriterEpoch、runtime_id/generation，验证 World ACTIVE 和当前 LivingRoot。后台管理投影不能当会话投影使用。快照包括 TimeContext、当前 activity/location、最多 5 项近期转换、3 项下一计划、1 项联系 context、各 1 项 photo/voice 机会；总 UTF-8 上限 8 KiB、单条正文上限 512 bytes，原子整项裁剪。current time、origin、当前状态和版本必需，装不下则拒绝；可选项固定最近优先顺序裁剪并留诊断。

`valid_until` 为下一 schedule 边界、下一分钟边界、observation expiry、机会 expiry 的最早值。版本包括 living/policy/day revision、generation、时间分钟桶及已用 observation/choice IDs。revalidate 检查实际 now 未越界、权威身份和当前版本，不仅比较旧对象自身字段；进程密钥变化后的 token 失效。正文是 UNTRUSTED_CONTENT_DATA，ID/版本等结构是 TRUSTED_STRUCTURED_STATE，都不授予工具。模型输出不作为 state delta。

当前 K 的 section 顺序和 `SP-004K-prompt-v1` **没有 Living section**。A1 若获授权纳入 Prompt，须同步新增受信 Living 输入/validator、SOUL_RESPONSE 专用 `LIVING_CONTEXT`（置于 STORY_CONTEXT 前）、预算/指纹/失效测试，并显式升级为新的 Prompt Template 版本；A0 不修改当前模板。不准把 Living 塞进 Story/Memory 字段假装兼容，也不在 v1 模板后私接字符串。A1 未实现这项受审核扩展前，仅提供独立查询投影，不宣称已接通当前 PromptSnapshot；Roleplay purpose 一律不接收 Living。

“晚上一起聊”是自然语言，不自动承诺发送。受信工具可展示并确认 `create_followup(due_window, topic, source_ref, expiry)`，写入一个持久 follow-up 后才派生机会。A1 命令集限定 enrollment、pause/resume、policy/timezone change、create/resolve/cancel follow-up、reschedule/cancel activity、observe inbound、tick、prepare intent、begin attempt、record verified result；后三项不使 Host callback 自动可用。所有变更带 operation key、expected revision 和授权上下文。模型建议未经受信命令接纳只是 DATA；普通 remember 只写 Memory，不隐含 follow-up；Story proposal 也不隐含 schedule。

## 11. 并发、幂等与恢复围栏

SQLite 单库事务须同时覆盖当前 World 身份/状态检查、Living 状态转换、revision CAS、自然键/幂等约束、预算预留及 operation receipt；不能先在 WorldRepository 检查再无保护地写 Living。未来 LivingRepository 复用同一连接中的 World 只读校验，不嵌套独立事务；锁顺序为 durable instance 锁 → SQLite transaction，与现有安装/恢复流程一致。不跨模型、网络、Host 或媒体生成持锁。

幂等键 `(root_id, generation, producer_namespace, operation_id)`，同键不同规范 payload fingerprint 拒绝；同键重试返回原 receipt，但 receipt 不是可重复使用的发送授权。即使 Host 没有稳定 invocation ID，业务自然键(day/occurrence/opportunity/intent)仍阻止重复 effect；无稳定 ID 的非 tick 变更拒绝。stale revision 重读后仅对 tick 有限重试 3 次，其余返回 REVISION_CONFLICT，不静默重放用户操作。

每次 attempt 前重验 generation、当前 target binding、expiry、pause、inbound/outbound 水位与 budget reservation；重复 begin_attempt 返回已有 attempt 状态，不重复执行外部 side effect。单 root 并发 wake 由事务/CAS/UNIQUE 保证一个 Intent；活动每个转换键唯一；photo/voice 一个自然机会只建一次。日志和当前行任何一个提交失败全部回滚。

普通进程重启读取已提交状态即可；restore 不同于重启：新 generation 使旧 Context/Snapshot/Attempt token 失效，复制库的待发/未知项隔离，主动联系暂停。按照现有 durable 恢复规则人工核对备份后实际发送；恢复历史不能证明那些外部消息不存在。协调命令记录明确新水位/预算保留后才允许 resume，不能用旧 operation 记录防重假装完整。

错误类别至少为 BINDING_REQUIRED、SCOPE_MISMATCH、GENERATION_STALE、REVISION_CONFLICT、IDEMPOTENCY_CONFLICT、CLOCK_REGRESSION、STATE_CORRUPT、RECOVERY_IN_PROGRESS、RECONCILIATION_REQUIRED、RECEIPT_UNVERIFIED。状态损坏时停止推进和发送资格，不静默清空数据库重建“新的一天”。

## 12. Persistence strategy 与 Schema 8 判断

**建议 Schema 8，只有 A1 单独授权后才能实施。** Schema 7 的 legacy days/contacts/loops 缺少 WorldScope、版本化策略、活动生命周期、schedule expiry/cursor、decision/attempt 和严格自然键；把这些全部塞回 plan JSON 会丢失数据库约束与原子去重能力。文件化 artifact 适合 H0 报告，不适合作为多进程业务真源。

候选表（DDL 与迁移代码不在 A0 创建）：

| 表组 | 主键/关系及必要索引约束 |
| --- | --- |
| living_roots / living_policies | root PK；完整 Scope FK 到 World/Timeline，验证 SOUL；instance 与 Scope 启用映射唯一；policy PK(root,revision)，不可变历史；root revision 非负 |
| living_days / living_locations / living_activities | day UNIQUE(root,timezone_epoch,date)；location 版本 PK(root,id,revision)；activity FK(day,location version)；start < end；部分唯一索引 root WHERE ACTIVE；按(root,status,planned_end)检索 |
| living_schedule | schedule PK，复合 FK 指向同 scope 的 subject（按 subject_type CHECK 并验证有效目标）；UNIQUE(root,subject,occurrence,action)；due <= expiry；索引(root,status,due_at,id) |
| living_followups / living_opportunities | followup PK、OPEN/RESOLVED/CANCELLED、due/expiry、授权 provenance；opportunity 带 CONTACT/PHOTO/VOICE discriminator 和对应 CHECK；UNIQUE(root,kind,source_ref,occurrence)，索引(root,kind,status,eligible_at) |
| living_decisions / living_intents | decision 追加，UNIQUE(opportunity,input_version,policy_revision)；intent UNIQUE(opportunity)；索引(root,reserved_at)，预算只从这里算 |
| living_attempts / living_delivery_results | attempt UNIQUE(intent)，request fingerprint/target binding 固定；result UNIQUE(attempt,source,event_id)；同消息关联，冲突不覆盖终态，索引(root,status) |
| living_choices / living_observations | choice UNIQUE(root,event,purpose,algorithm,policy)，持久选择不可重抽；observation UNIQUE(provider,event_id,root)，expiry 索引；保留被引用输入摘要 |
| living_inbound / living_transitions / living_operations | inbound UNIQUE(root,source,event_id)，索引(root,received_at)；transition UNIQUE(root,subject,transition_key)，包含 before/after revision、processed_at/source；operation 复合 PK 及 payload fingerprint/result_ref |

所有表持有 root FK，跨 scope 的关联使用复合键或等效 fail-closed 校验，不接受只验证裸 ID 的多态外键。可变状态和生命周期必须由 CHECK/UNIQUE 加 Runtime 转换规则共同保护；doctor 检查 FK、状态集合、活动互斥、时间区间、日志/revision 连续性、choice 指纹、重复预算预留。发现损坏返回 STATE_CORRUPT，不自动补一条假 transition。转换日志用于诊断和一致性校验，不承担重建其它 Runtime 全量事件的职责；无授权不清理影响幂等/额度/恢复的记录。外部缓存可以按 TTL 清理，被持久 choice 引用的最小输入摘要必须保留。

迁移冻结为两步，二者不能混淆：

1. **Schema copy migration**：暂停写入并备份；在新 generation 副本建立空 Living 表，原样保留 Schema 7 所有 World/Memory/Lore/Story/Bridge、legacy 表、照片和控制日志；校验所有实例成功才一次原子切 registry。修改 DATA_SCHEMA/签名由 A1 专门评审，不在此指定已生效的 Schema 8 字符串。任一失败保留旧入口。
2. **显式 enrollment / legacy handoff**：核对 Owner 与已有 Soul World，仍保持 paused；关联 legacy agent 与唯一 Scope。当前日已存 plan 的 slots/visual/routine 按原值导入并记录 legacy key，所有旧联系人占额保守导入为 legacy reservation，绝不导入为 ACK。claimed/prepared/unknown 隔离，不发起新 attempt；旧 delivered 只为 UNVERIFIED_LEGACY，不伪造送达。loops 通过明确授权复制为 follow-up 并保存一对一 source key；legacy memories 不自动迁入 World Memory/Story。完成后设置单一 writer 标记，旧 legacy wake/prepare/loop 写入口对该 instance 返回 LIVING_HANDOFF_REQUIRED，不得新旧引擎并行决策。未 enrollment 的实例沿用旧行为，不静默启用 A1。

hand-off 要跨时区/当天判断无法确定时停止并请求显式协调，不重新随机当天；首次新实例的 enrollment 必须创建明确空初始状态和新日，不伪称迁移历史。handoff 自然键与指纹确保中途崩溃/重试不双份复制；旧表保留只读供审计。新旧版本是否可处理混合实例由 migration validator 检查，不能只更新 meta 版本骗过旧代码。

rollback：激活前丢弃失败副本；激活后回到已验证的 Schema 7 backup/generation＋对应旧 release，保持主动联系暂停，保留 Schema 8 副本供审计，明确回退点之后的业务写入未合入旧库。**不支持原地 downgrade 8→7，也不在 Schema 8 数据上运行旧 release**。不能丢弃 Memory 删除/Bridge 撤销控制，须沿用 durable 的控制协调；发送结果须人工 reconcile。Code rollback 必须通过 schema compatibility gate。

## 13. A1 交付边界与审核门

A1 的最小目标为上述 Core domain、SQLite persistence、copy migration/enrollment、确定性时间与恢复、受控命令及 projection 合同，具体任务书仍需单独授权。外部天气 provider、Host callback、真实发送、ComfyUI、TTS、RP mode 全部不因 A0 解锁；测试使用受控 clock/observation/transport 替身，不连接生产 Host。

[测试矩阵](../planning/SP-005A1-TEST-MATRIX.md) 逐项定义前置条件和可观察断言。A0 只核对文档链接、diff 和既有完整 CI，不新增“关键词存在即架构正确”的静态测试。架构通过仍需 ChatGPT / 小雪独立审核；本 PR 保持 Draft，不转 Ready、不 Merge。
