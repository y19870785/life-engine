# SP-005A0 — CURRENT_STATE_AUDIT

审计固定 Base：`95f7485d426a0eee36c7b87b4bac2ae52f34216d`。本文件是源码审计，不是 A1 实现报告或真实 Host 验收。当前 `DATA_SCHEMA = 7`，签名 `SP-004F-bridge-runtime-v1`，Prompt Template `SP-004K-prompt-v1`。

## 1. 当前真源及重启行为

| 能力与源码入口 | 当前真源／计算方法 | 重启与缺口 | A1 处置 |
| --- | --- | --- | --- |
| [Engine._plan/status/wake](../../runtime/life_engine/engine.py) | `days(day PRIMARY KEY, plan JSON)`；同一天首次访问保存 slots、photo 布尔机会、visual 与 routine 快照 | 已持久化；status 和 wake preview 也会创建当天 plan，并非纯只读；旧日期无 timezone/policy revision | 保留一次生成、重复读取；引入有版本的 LivingDay，查询与推进分离 |
| `_plan` 随机选择 | `SHA256(config.seed:agent_id:local_date)` 初始化局部 Random；选择窗口、分钟、照片概率、visual 后存入 days | 不是每次 Prompt 重抽；seed 持久配置可恢复，但没有算法版本、输入指纹和逐项 choice 记录 | 保留已决定的选择；新选择有独立随机域和稳定事件键 |
| `Engine._moment` | 每次根据本地 HH:MM 匹配当天 plan.routine；scene/weather 来自当前配置 | 当前活动／地点是派生值，没有 ACTIVE/COMPLETED/SKIPPED、实际转换时间或恢复游标；重启能算现在，却无法解释漏过了什么 | 正式化 activity/location/schedule 生命周期；保留 companion 虚拟来源标签 |
| [config.now_in/tz](../../runtime/life_engine/config.py) | 显式 Agent timezone；ZoneInfo，上海缺 tzdata 时有固定偏移回退 | 不依赖 OS local timezone；已有日期/时间，但无 daypart、节假日、DST 歧义、timezone 修改合同 | 注入 UTC clock，冻结时区映射与 calendar policy；不把旧回退泛化到 DST 地区 |
| `Engine.wake` 静默决策 | enabled/paused → quiet → daily budget → contact cooldown → recent inbound → assistant due follow-up → due slot | 每次重新计算；SILENT reason 未持久化；窗口错过 grace 即不领取，没有显式 EXPIRED 记录 | 保留规则职责，记录规范决策理由与下一复核时间 |
| [Store.tx / contacts](../../runtime/life_engine/store.py) | SQLite BEGIN IMMEDIATE；`UNIQUE(day,slot)`；领取保存 UUID、at、payload、claimed | 并发领取已是单赢家；预算统计所有 contacts，包含失败和未发送，不是实际送达次数；cooldown 从领取时间计算 | 保留保守占额语义；拆分 Opportunity/Decision/Intent/Attempt/DeliveryResult |
| `Store.observe/context` | observations 持久化；非空 dedupe 唯一；最近 inbound 取最大 at | dedupe=None 可重复；源可信程度靠调用入口，不靠 summary。context 只取最近 5 条与 8 个 open loops | 规范可信入站事件身份；schedule 查询不得受 Prompt 展示条数截断 |
| `Store.remember/loop_add/loop_close` | legacy memories、loops 表；loop 的 due/topic/resolved 持久 | assistant 必须看到到期 open loop 才联系；context 只返回 8 个 open loops，不能充当完整 schedule 枚举；领取 contact 不自动 resolve loop | 保留用户显式 follow-up；新增关联键、幂等消费，不把联系当业务已完成 |
| `Store.prepare/acknowledge` | claimed → prepared → delivered/failed/unknown；证据是调用方文本 | prepare 幂等，unknown 可后续协调；没有发送尝试表或受信 receipt 验证器，旧 delivered 不证明 ACK | 旧记录保留为 legacy evidence；不得升级为真实 receipt |
| [photos.photo](../../runtime/life_engine/photos.py) | photos 表持久化 claimed/queued/ready/unknown、prompt_id/path；同 contact_id 重用已存在文件，否则拒绝重排 | ComfyUI seed 用 `secrets.randbits`，在调用前临时生成，不独立持久为可重放 choice；外部 job 状态不因重启消失，但不确定失败不能自动补发 | A0 只定 PhotoOpportunity；不重写现有媒体执行，SP-005M 单独处理 job/seed/receipt |
| [durable.registry/state_home/run](../../runtime/life_engine/durable.py) | registry 绑定 instance、Host home/agent、活动 generation；数据在永久目录 | 每次入口重新读取并检查状态，非进程内缓存；实例锁覆盖命令，photo 长网络调用也持锁 | 复用安装、锁与 generation；A1 的业务事务不得跨网络等待 |
| `durable.restore/upgrade` | 复制状态、新 generation、原子切 registry；恢复保留旧 generation，协调 Memory/Bridge 控制 | restore 暂停主动联系以免备份回滚造成重放；不是“旧进程重启”；重复幂等记录可能随备份回退 | 保留暂停和人工协调；旧 generation 的命令/快照必须失效 |
| `backup-day.json` | instance 目录的 UTC 日期标记；首次 wake（含静默/preview）触发当天备份 | 是运维去重状态，不是 Agent 当地日、业务 schedule 或联系人额度真源 | 不把它当 LivingDay，不借 UTC 备份日重置预算 |
| [bridges.py](../../runtime/life_engine/bridges.py) 原生工具/hook | Hermes get_hermes_home；OpenClaw agentId/workspace；context/status/wake 调独立 Python | Hook 成功时间保存在 observed.json；插件 epoch 与本代次 hook_runtime 是进程内值，reload 后清空；它们不是生活事实 | 保留诊断职责，Living 无需依赖插件 epoch 才能恢复 |
| 生成的 INSTALL.md | `bridges.installation_guide`，任务名稳定，建议每 23 分钟 Host wake | Host cron/服务负责是否触发；停机期间没有业务推进线程；现有工具对模型的指引不证明消息会被送达 | Host 只给唤醒机会；Living 持久 schedule 为业务真源 |
| [integration.schedule_recipe](../../runtime/life_engine/integration.py) | 旧接入生成器的 cron 示例与 prompt 指引 | 非 Hermes 文案仍描述旧 generic 接入；不能据此否定现有 bridges 原生插件。示例不是已注册任务 | 兼容说明后续按入口收敛；A0 不改 Host 或生成器 |

## 2. 已有证据与不能推断的结论

[test_engine.py](../../tests/test_engine.py) 已覆盖并发 wake 单领取、assistant 到期理由、preview 不占额、quiet/recent inbound、cooldown/budget、同日 visual 跨对象稳定、prepare 不等于 delivery。[test_durable.py](../../tests/test_durable.py) 用新 Python 进程验证安装存活、记忆保留、restore 暂停、跨实例隔离、备份去重和两个模拟 Host 插件；[test_photos_migration.py](../../tests/test_photos_migration.py) 使用假 HTTP 服务验证出图/reuse/未知失败不重排。[test_sandbox.py](../../tests/test_sandbox.py) 区分报告生成、本地 probe、捕获一致性与真实验证；PENDING/FAIL 的 validation_passed 均为 false。

这些测试不是 missed activity 恢复、DST、timezone 修改、独立 ScheduleState 或真实 delivery 的证据。既有测试不因新文档出现就证明 A1 已实现。未在本轮运行真实 Host、ComfyUI 或聊天发送。

真正随进程丢失的是局部计算、未提交事务、插件 epoch/hook 缓存、Prompt token 的进程密钥；已提交的 days/contacts/observations/loops/photos 不会仅因进程退出而丢失。当前没有独立的 LivingActivity 状态，因此不存在可恢复的“活动已完成”事实；不能说这些事实只是丢在内存里。静默决策理由只在返回值中，未捕获便没有持久审计记录。

## 3. 与新 Core 的断点

legacy `agent_id`/days/contacts/loops 并不携带 `WorldScope`，不是已接入 World Memory/Story 的 Living 子域。新 Core 的 World、Memory、Lore、Story、Bridge、Prompt 已独立实现，不能把同库误解成同一个领域真源。尤其不能把旧 `memories` 表当 World Memory，或把 routine 匹配写成 accepted Story event。

[README](../../README.md)、[START-HERE](../../START-HERE.md)、[沙箱指南](../HOST-SANDBOX-TESTING.md) 和 [路线图](../planning/ROADMAP-2026-09.md) 已要求 Core/Host 分工、独立测试目标、prepare/receipt 区分和 Private RP 阻塞。A0 延续这些边界，不借 Living 架构改写 H0。

## 4. 保留与正式化清单

保留：永久安装、Schema 严格校验、状态副本迁移、generation fencing、SQLite 原子领取、静默优先、预算保守占用、assistant 不虚构私人生活、已保存的日计划和照片、恢复后暂停、Host 原生调度与现有权限。

A1 才正式化：显式 Soul World enrollment、独立 Living revision、UTC/timezone epoch、活动与地点、持久 schedule/cursor、规范 reason/decision、带版本的随机选择、明确 follow-up 关联、外部环境观察 TTL、媒体机会投影、幂等和未知发送恢复。需要新增约束与实体，建议 Schema 8；**本轮不改 Schema，也不实现迁移**。

候选冻结见 [Living Runtime 架构](SP-005A-LIVING-RUNTIME.md)，未来验收见 [A1 测试矩阵](../planning/SP-005A1-TEST-MATRIX.md)。SP-005A0 = PENDING_INDEPENDENT_REVIEW；SP-005A1 = NOT AUTHORIZED。
