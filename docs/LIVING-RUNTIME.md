# Living Runtime Core 操作与迁移

SP-005A1 已合并至 canonical main `84493be98d7ed675de6b859cafdb014a900325ca`，exact main push CI 四矩阵通过，Core 实施阶段 DONE。数据版本为 `DATA_SCHEMA = 8`、`SP-005A-living-runtime-v1`；`SP-004K-prompt-v1` 保持不变。规范见 [冻结架构](architecture/SP-005A-LIVING-RUNTIME.md)，验收逐项对应 [48 项自动测试映射](SP-005A1-VALIDATION.md)。

后续 [A2 Host Binding 架构](architecture/SP-005A2-LIVING-HOST-BINDING.md)仅冻结受信调用、prepare/claim 与证据合同，待独立审核；A3 未授权。当前仍只有 Core API，旧插件不能自动接管 enrolled 实例。Living 正式 Prompt 拼装需要单独模板升级授权，真实 Host Living 尚未上线。

## 真源和入口

Living 数据属于显式绑定的 SOUL WorldScope 和 durable instance。LivingRoot 绑定 generation，保存 revision、policy revision、timezone epoch、时钟水位与恢复门禁。Day、Activity、Schedule、机会、Decision、Intent、Attempt、choice 和操作收据保存在同一 SQLite 库。当前虚拟位置从唯一 ACTIVE activity 推导，不保存第二份当前位置，也不代表用户定位。

首版入口是受信本地 Python Core API，不增加 Host callback 或模型可调用的自动 enrollment 工具。调用方必须先取得已有 ACTIVE SOUL World、Owner 身份和实例 generation；不能根据 workspace、agent_id 或模型正文猜 Scope。`LivingContext` 用于 Owner/会话命令，`LivingTickContext` 只允许后台 tick。每个变更命令携带 producer namespace、operation ID 和 expected revision；tick 在串行事务内读取当前版本，仍有业务自然键防重。

```python
from life_engine.living_domain import LivingContext
from life_engine.living_policy import policy
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime

# owner、scope 和 world_repo 必须来自受信部署层和已存在的 SOUL World。
repository = LivingRepository(permanent_root, instance_id,
                              runtime_id=world_repo.runtime_id)
context = LivingContext(owner, scope, repository.generation, "owner-management")
living = LivingRuntime(repository)
result = living.enroll(context, policy(timezone="UTC"),
                       confirmed_target_binding, "explicit-enrollment-1")
# enrollment 初始 paused；确认计划、绑定及协调状态后才显式 resume。
living.configure(context, result["revision"], "explicit-resume-1", paused=False)
state = living.status(context)
```

上述示例适用于没有 legacy 当日计划的新实例。已有 legacy 计划的 handoff 必须提供原值和显式 loop 映射，且 legacy 配置时区与新策略一致；不明确就返回 `LEGACY_HANDOFF_REQUIRED`。迁移不会创建 SOUL World。

具名 IANA 时区需要当前 Python 可读取的真实 zoneinfo/tzdata。UTC 使用固定零偏移，不依赖外部时区文件；缺少具名数据就拒绝，不按 Host OS 时区猜测。policy 保存实际 TZif 指纹，规则文件变化后返回 `TZDATA_REVALIDATION_REQUIRED`；Owner 显式提交新 policy 才推进 epoch。DST gap 推至首个合法分钟，fold 固定 0；daily budget 使用当地相邻午夜映射的 UTC 区间，另行执行 rolling 24h cap。

## Reservation 与 Execution

`tick` 先恢复到期项，再评价机会。新 Intent 的 Reservation Eligibility 检查 quiet、daily/rolling 剩余额度、此前 Intent 的 cooldown/spacing、可信 inbound/outbound、reason 和时间窗。ALLOW Decision、Intent、Opportunity consume、操作收据和额度预留同事务提交。额度真源只有历史 `reserved_at`，取消、失败和 UNKNOWN 不退款。

`prepare_intent` 只登记准备内容；`begin_attempt` 验证已有 reservation，不再次申请额度、不把当前 Intent 的时间当作自身 cooldown。仍重新检查 Scope/generation/clock/corruption、pause、quiet、expiry、target、inbound/outbound、关键 reason 与恢复门禁。cap 下调或 cooldown 增长不追溯撤销旧预留。

quiet/inbound 在 Attempt 前阻断时，旧 Intent 终止；有效 Opportunity 可重开，新的 ALLOW 使用新 Decision、新 Intent 和新 reservation。partial unique index 保证同机会最多一个未终止 Intent，`UNIQUE(decision_id)` 与每 Intent 唯一 Attempt 防止重复领取。已有 Attempt 永远不通过重评重发。

`begin_attempt` 成功先持久化 CLAIMED。返回的 `execute` 只允许首次调用者执行一次外部尝试；重放操作收据返回 `execute=false`。Core 本身不调用 transport。新 World runtime incarnation 发现遗留 CLAIMED 后记为 UNKNOWN，进入协调门禁，不自动补发。可信 validator 在锁外验证结果，随后事务校验 attempt、target、message ID、sent_at 和自然键。默认没有 validator，模型声称发送成功返回 `RECEIPT_UNVERIFIED`。冲突结果持久记录协调门禁并返回 `RECONCILIATION_REQUIRED`；测试中的 SENT/ACK 仅证明内部合同。

## 恢复、计划和投影

到期项按 `(due_at, action_priority, schedule_id)` 排序；默认每事务最多 128 项，可配置更小合法批次。积压期间返回 `RECOVERY_IN_PROGRESS`，不创建 Intent。错过整段活动记 SKIPPED；仍在窗口内才 ACTIVE，activated_at 是当前处理时刻并标 inferred；从未发生的过去几天不补造生活事实，不补发过期机会。

持久 choice 使用独立语义键、policy revision、算法版本和 HMAC-SHA256 拒绝采样。已生成 Day 复用原 choice，候选列表更新不会重抽旧日。spontaneous activity 必须策略允许且没有时间重叠，接受的类型化候选同样记录 choice；普通自然语言不写 schedule。

`create_followup`、`resolve_followup`、`cancel_followup` 是显式命令。Follow-up 的 reason 只接受 REMEMBERED_FOLLOWUP 或 USER_PROMISED_FOLLOWUP，由 Owner 命令选择，不从自然语言自动解析。联系完成不会自动 resolve。`observe_environment` 只接受受信 fixture/本地提供的有界观测；`observation_context` 区分 UNKNOWN、VALID、STALE，不复用过期天气。没有联网 provider。

PhotoOpportunity 和 VoiceOpportunity 只保留计划。Photo 关联 day、visual、activity/location 与同一个 contact；Voice 默认关闭。两者不创建 ComfyUI/TTS job、不生成文件、不产生独立发送额度。

独立 `living_projection.query(runtime, PromptSessionContext)` 仅允许 SOUL_RESPONSE，核对 Owner、Soul viewer、Session/WriterEpoch、World revision、runtime_id 和 generation。snapshot 是带进程 seal 的不可变 JSON，最多 8 KiB，时间/当前状态/版本必需，可选整项裁剪。`revalidate` 检查当前数据库与时钟，不能把旧对象自比当验证。此 factory **未接入现有 PromptSnapshot**；Roleplay purpose 拒绝，也不把内容写入 Story/Memory/Lore。

## Schema 7→8 与 rollback

使用既有 durable `upgrade` 流程：备份旧 generation → 复制 → 仅迁移副本 → 全量结构/数据校验 → 所有实例成功后原子写 registry。迁移逐表比对旧行，只增加空 Living 表并更新 Schema 标识；World、Memory、Lore、Story、Bridge、legacy days/contacts/loops/photos 和控制日志保留。任一实例失败，旧 registry 和旧 active DB 保持不变。

Schema 8 不等于 enrollment。未 enrollment 实例继续 legacy Engine。显式 handoff 保留当前日已有选择，旧 contact 保守转为 reservation，claimed/prepared/unknown 隔离，delivered 不升级为 ACK；loops 只有显式映射才复制，旧 memory 不进入 World Memory。handoff 原子写入 single-writer 标志后，legacy wake/status（会生成计划）、prepare 和 loop 写入返回 `LIVING_HANDOFF_REQUIRED`。因此 enrolled 实例尚不能直接沿用原 Host wake 链路；本 PR 不修改 Host Adapter 来绕过这一门禁。

Schema 8 激活前失败副本不成为 active。激活后仅允许 `rollback_schema` 使用本安装升级 checkpoint、校验过的 Schema 7 backup 与对应旧 release，复制为新的 rollback generation；Memory 删除/Bridge 撤销账本继续协调。新 Schema 8 副本保留供审计，回退点后的业务写入不会自动合入旧库；主动联系暂停，外部发送需人工核对。不支持原地 8→7，也不允许旧 release 读取 Schema 8。

restore 创建新 generation，旧 Context/token 失效，待发 Intent 隔离，遗留 CLAIMED 转 UNKNOWN。Owner 的 `reconcile` 需证据引用和保守阻断水位，保留所有 reservation、取消待发并继续 paused；显式 resume 与水位解除是独立条件。doctor 检查 FK/关联、互斥、时间窗、revision/log、choice/operation 指纹与状态摘要，损坏返回 STATE_CORRUPT，不清库修复。

Hermes/OpenClaw 真实验证继续 `PENDING_REAL_HOST_VALIDATION`。Full Private RP、H1、H2 继续 `BLOCKED`；此实现不提供 history isolation、late-response fence 或 Host final-output transaction。
