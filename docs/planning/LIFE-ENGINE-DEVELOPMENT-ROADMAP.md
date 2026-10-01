# Life Engine 长期开发路线与阶段治理

## 1. 治理地位与当前事实

本路线由 GOV-ROADMAP1 冻结，作为后续 SP / RFC / ADR / Implementation Task / Validation Task 的阶段顺序与 Gate 依据。Roadmap 不是愿望清单；值得做不等于现在授权做。Roadmap Stage 与 Why Now 无法明确回答时，默认 NOT AUTHORIZED。

Roadmap Stage: Real Host Integration / 路线治理冻结。
Why Now: Core 与 Host-neutral Binding 已完成，HLV0 已 DONE；进入真实 Host 验证前需固定长期方向、证据门禁与防跑偏规则。

本任务 Base / canonical main：`08bf82e89f7a4572f4931105cc5e6927ae1c5214`，对应 [PR #35](https://github.com/y19870785/life-engine/pull/35) Squash Merge；SP-005A4-HLV0 = DONE，由 ChatGPT / 小雪独立确认。SP-005A3 = DONE；当前阶段 = REAL HOST INTEGRATION PHASE。阶段具备开展验证的基础，不构成执行授权。GOV-ROADMAP1 = PENDING_INDEPENDENT_REVIEW；必须正式 DONE 后才能发布 SP-005A4-HLV1 任务。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = NOT AUTHORIZED。Memory Evolution V1 = PLANNED。B01–B34 = SIMULATED_PASS；Hermes / OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION。Full Private RP = BLOCKED；H1 = BLOCKED_BY_OFFICIAL_HERMES_HOST_CAPABILITY；H2 = BLOCKED。

本次仅 Docs / Governance：不改 Runtime、Python、tests语义、Schema、数据库、Prompt或workflow，不操作 Hermes/OpenClaw/WSL、配置、Bot、cron或Gateway；不执行 discovery、Living Attempt、permit、真实验证/发送。NO_REAL_HOST_OPERATION = true；NO_REAL_SEND = true；H_LV1_STARTED = NO。历史 Host 测试不升级为当前能力或授权。

当前执行状态见 [ROADMAP-2026-09](ROADMAP-2026-09.md)；Hermes验证的细项安全合同与逐case计划见 [HLV0架构](../architecture/SP-005A4-HERMES-LIVING-VALIDATION.md)及 [HLV矩阵](SP-005A4-HERMES-LIVING-VALIDATION-MATRIX.md)。本路线不修改这些冻结语义。

## 2. 长期目标

构建可在 Hermes、OpenClaw 等 Host 旁运行的通用 Personal Agent Runtime，让 Agent 跨时间、跨进程重启、跨长期关系持续存在，具有可信世界状态、长期记忆、故事与关系连续性、时间意识、安全主动行为，以及后续照片、语音和生活化表达。目标体验是 Agent 与用户生活在连续的同一时间线中，不在每次会话重新开始。

保持 Host-neutral、Agent-neutral、World-aware、Persistent、Fail-closed、Auditable、Recoverable。Runtime 不硬编码为小雪、Discord、Telegram、Hermes 或 OpenClaw 专用；“小雪”是其中一个 Agent / Soul / World 使用实例，不是 Runtime 本身。Host 差异封装在 Adapter / Binding Layer，共享业务真源和安全合同。

## 3. 当前 Runtime 基线与职责

已形成能力链：World → Memory → Lore → Story → Prompt → Bridge → Living → Host Binding。箭头表达已建立的能力链，不表示可互相写入或替代真源。

| 层 | 职责 / 权威边界 |
| --- | --- |
| World | 世界、Timeline、Subject / Scope 与隔离边界 |
| Memory | Subject 知道 / 记得什么；受World与可见范围约束 |
| Lore | 世界设定；不是已发生事件 |
| Story | 实际发生过什么；接受事件后的故事真源 |
| Prompt | 从可信状态派生给模型的投影，不是真相来源，不是authority |
| Bridge | Worlds间显式授权的受控投影，默认拒绝；不自动写入目标Memory/Story |
| Living | Agent是否具有主动行为资格；预算、cooldown、quiet hours等由Core决定 |
| Host Binding | Host能否安全执行已授权行为；身份、binding、capability与副作用前执行权限 |

Core Runtime已达到进入真实Host验证的阶段。当前首要工作是证明 Life Engine → Living Host Binding → Real Hermes → 真实Host生命周期 → 安全Side Effect，不继续无限扩展Core，也不把自动测试当真实Host证据。

## 4. 推荐执行顺序与 Gate

| 顺序 | 阶段 | 当前状态 / 进入与退出边界 |
| --- | --- | --- |
| 0 | SP-005A4-HLV0 架构与验证计划冻结 | DONE；只完成文档，不授权Host操作 |
| 1 | GOV-ROADMAP1 长期路线治理 | PENDING_INDEPENDENT_REVIEW；正式DONE后才发布HLV1任务 |
| 2 | SP-005A4-HLV1 Hermes Read-only Discovery | NEXT；尚未授权，当前证据逐项确认后独立PASS |
| 3 | H-LV2 Hermes Lifecycle Validation | PLANNED；HLV1独立PASS后才设计/发布执行任务，单独授权 |
| 4 | H-LV3 Living Dry Run | PLANNED；HLV2独立PASS后单独授权，零网络发送 |
| Gate | ARCHITECTURE REVIEW GATE | HLV1～3分别独立PASS后重新评估P1、Memory Evolution V1与H-LV4局部顺序 |
| 5 | H-LV4 Isolated Real Text Delivery | DEFINED_ONLY / NOT_AUTHORIZED；HLV1～3 PASS + 独立审核 + 用户明确授权 |
| 6 | Hermes Living Adapter Stabilization | PLANNED；收敛验证发现的adapter/identity/lifecycle/evidence/recovery/diagnostics gap |
| 7 | P1 / Memory Evolution V1 | 按Review Gate决策；当前P1 NOT AUTHORIZED，Memory Evolution V1 PLANNED |
| 8 | Memory Evolution | PLANNED；保持Memory/Story/Lore/Prompt边界，逐步扩展 |
| 9 | Proactive Life / Routine Runtime | PLANNED；由可信状态产生Intent，Living仍决定可否执行 |
| 10 | Media Runtime | PLANNED；一致视觉表达、artifact与delivery语义 |
| 11 | Voice Runtime | PLANNED；Media稳定后，统一World/Memory/Relationship/Living来源 |
| 12 | Relationship / Autobiographical Evolution | PLANNED；Core Soul与关系表达分离 |
| 13 | OpenClaw Living Adapter | PLANNED；Hermes成熟模式验证Host-neutral后映射，不同时大规模推进 |
| 14 | Full Private RP | BLOCKED；独立等待官方Host capability解锁，不因其它阶段PASS自动进入 |

Architecture Review Gate可依据真实证据提出P1、Memory Evolution、H-LV4具体局部顺序调整；Codex不能自行决定。即使Gate推荐了某项，仍须按本文件变更规则完成Roadmap审核、用户确认和单独实施授权。所有NEXT/PLANNED/DEFINED_ONLY均不是执行许可。

## 5. 第一阶段：Hermes Living Real Host Validation

### H-LV1：只读发现与 Binding Validation

下一正式任务应为 SP-005A4-HLV1。REAL HOST / READ ONLY / NO HOST MUTATION / NO LIVING MUTATION / NO REAL SEND。目标是用当前真实环境证据逐项确认HLV0的DISCOVERABLE / UNKNOWN / HOST_GAP：实际安装版本/官方来源、Home/Profile/Agent/process、已有plugin发现与加载证据、可信Owner/sender/channel/target/session来源、Life Engine root/instance/generation及binding唯一性，wrong Host/Profile/Agent拒绝。

只读发现不能触发plugin load/reload、Gateway restart、enrollment、tick/inbound mutation、prepare、claim、permit或send；没有已加载证据就保留UNKNOWN。历史2026-09-30仅参考，不能假定环境仍相同。来源不能满足稳定可信身份则相应case BLOCKED_BY_HOST_CAPABILITY，不猜API。全部证据经独立审核才可REAL_HOST_READONLY_PASS；这也不自动授权HLV2。

### H-LV2：生命周期、身份与 Session

HLV1 PASS后才允许设计/执行HLV2任务；HLV0既有冻结计划保留，新的执行方案不能提前落地。重点Host startup、Binding load、plugin/authority/session lifecycle、Gateway restart、plugin reload、authority restart、generation/epoch transition、stale capability拒绝。核心问题是旧authority/permit/session/generation能否错误获得执行资格。

默认NO EXTERNAL DELIVERY。只操作专用测试Host，真实Gateway restart与fresh Python process证据分开。restart/reload不重置Core generation/day/budget/cooldown或durable Intent/Attempt；restore改变generation、旧能力全部stale。有效permit撤销的完整正例按HLV0留HLV3，HLV2不得为验证方便claim或发送真实消息。独立真实生命周期证据通过后才能REAL_HOST_LIFECYCLE_PASS。

### H-LV3：Living Dry Run

HLV2 PASS后，单独授权真实Hermes生命周期驱动 tick → prepare_contact → claim_attempt → execution permit → fake/local side effect → delivery/recovery simulation。NETWORK SEND = NO；fake只写isolated local journal。所需adapter/harness若尚不存在，必须在当前阶段范围单独任务与架构审核后实施，不能把验证任务隐含变成adapter开发。

至少覆盖quiet hours、cooldown、daily cap、rolling cap、recent inbound、trusted identity、stale session/world、generation/authority mismatch、duplicate claim、permit replay、crash/restart recovery与target mismatch。继续执行HLV0 RV/CR矩阵、最终generation barrier、legacy副作用前fence，真实subprocess/os._exit故障注入不能冒充真实Gateway事件。

HLV3 PASS接近“Living Runtime已真实接入Hermes生命周期，但真实网络Side Effect尚未授权”；证据等级REAL_HOST_DRY_RUN_PASS，fake不是REAL_HOST_SENT。之后进入Architecture Review Gate，不顺手真实发送。

### H-LV4：隔离单次真实文本交付

当前DEFINED_ONLY / NOT_AUTHORIZED。只有HLV1、HLV2、HLV3分别独立PASS，经ChatGPT/小雪独立审核及用户明确授权，才允许执行。专用Host/bot/channel、Owner本人、exact验证target、明确单次预算、可信provider SENT contract及必要实现均需先过独立Gate。当前SIMULATED_CONTACT permit不能改用途直接用于网络发送；NO_REAL_SEND不能自动关闭。

第一次严格限定one Intent、one Attempt、one execution permit、one explicitly verified test target、one text message、one transport side effect。禁止auto retry、bulk send、fallback/default-last-route target、production target、multi-channel fanout。cron/scheduled wake属于之后另立阶段，不由HLV4授权。

## 6. 本机环境背景与重新验证原则

以下只属于 USER-PROVIDED ENVIRONMENT CONTEXT，尚非 CURRENT VERIFIED HOST FACT；本任务没有读取WSL或Host配置。

用户说明Windows下的WSL已存在Hermes与OpenClaw，并配置过微信、Telegram、Discord；此前有Life Engine/Hermes专用Discord Server/Test Bot。历史工作流为Hermes Telegram channel → 用户引导/控制 → Hermes → Discord isolated test channel执行测试。

HLV1必须重新核验这套结构：Discord bot当前有效性、server/channel identity、Owner allowlist、Telegram routing、Hermes Profile/Agent/Gateway、Life Engine permanent root/instance/generation、OpenClaw与微信channel的存在及scope，均不能只凭历史聊天或本段说明签PASS。只读证据不能通过发送probe获得；不足就UNKNOWN/BLOCKED。

优先Dedicated Test Host Context、Dedicated Test Agent/Bot/Channel、Explicit Owner Allowlist、Explicit Target、Separate Life Engine Root，并保持生产Gateway/config/cron untouched。Control / Guidance Channel与Test Delivery Channel分开：历史Telegram是控制来源之一，Discord是隔离delivery环境；未来验证仍成立才优先沿用。控制来源不会自动变成可信Owner、发送资格或fallback destination。生产微信/Telegram、个人正常使用频道、生产Agent/Gateway不得直接成为实验side-effect目标。

## 7. 永久冻结的 Delivery / Recovery 边界

CLAIMED != SENT != ACKNOWLEDGED；DB transaction != network transaction。Core transaction → Attempt CLAIMED durable commit → transaction ends，之后首次成功execute=true才可Host执行授权与one-time permit → consume前完整重验 → external side effect → trusted delivery evidence → Core record_delivery。Core须验证provider evidence，facade digest不是provider truth；模型说“我已经发送”、CLI rc=0、人工boolean、prepared或CLAIMED都不是Delivery Evidence。

可信message ID/API结果经独立SENT contract验证后最多证明SENT；ACKNOWLEDGED需要独立可信ACK contract。fake journal仅为本地模拟证据。没有ACK不能伪造或用重复发送补齐。

Recovery != Authorization。query_operation_recovery可恢复durable operation association，COMMITTED/historical CLAIMED不能生成或恢复permit、resend、automatic retry。claim durable commit但response lost→B1只读projection→关联恢复→reconciliation→NO PERMIT / NO RESEND；不改operation ID猜结果。发送后Core结果丢失也只能UNKNOWN/冻结合同允许的conservative reconciliation，不能重建旧权限。

## 8. 第二阶段：Hermes Integration Stabilization

HLV4后先收敛真实验证暴露的adapter gap、identity/lifecycle/delivery evidence mapping、recovery integration与operational diagnostics，不立即无限扩功能。Host差异优先封装Adapter / Binding Layer，不污染World/Memory/Story/Living Core；需要改共享权威或安全语义则先Architecture Review，不能把Host便利条件转成Core policy。

## 9. Architecture Review Gate：P1 与 Memory Evolution V1

HLV1～3独立完成后正式复审：真实身份与session保证、同步lifecycle fence、dry-run与recovery证据、adapter gap、运维风险；据此比较SP-005A2-P1 Prompt Integration和Memory Evolution V1优先级，并评估H-LV4所需条件。当前不提前决定。

输出应包含exact证据、选项与理由、阶段依赖、是否需要Schema/Prompt/authority语义变化及Roadmap修改提案；经独立架构审核、用户确认后才发布实施任务。P1当前NOT AUTHORIZED，Prompt模板/HMAC/fingerprint/预算裁剪不因整理路线改变；Memory Evolution V1仅PLANNED。

## 10. 第三阶段：Memory Evolution

长期“同一个人”的体验需要World Memory逐步发展Working Memory、Episodic Memory、Semantic Memory、Relationship Memory、Autobiographical Memory；再加入Consolidation、Deduplication、Conflict Resolution、Supersession、Importance、Decay、Controlled Forgetting。具体存储/检索/删除语义须各自SP/RFC/ADR，不在本路线设计Schema。

Retrieval不等于最近N条全进入Prompt；应逐步综合人物相关度 × World相关度 × 时间相关度 × 事件重要度 × 关系相关度。该表达是选择维度，不提前冻结评分公式。Memory仍是Subject的知识/经历投影，不能替代Story事实或Lore设定；Prompt仍是派生投影，不能成为记忆权威。世界隔离、controlled forgetting与可审计supersession必须保持。

## 11. 第四阶段：Proactive Life / Routine Runtime

Living回答“是否允许主动联系”；未来Life/Routine回答“为什么此刻产生联系意图”。组合World State、Time、Calendar/Weather Context、Memory、Relationship、Recent Interaction、Living Policy产生Proactive Intent，再由Living决定执行资格。

不把长期体验做成08:30固定早上好、12:00固定吃饭了吗、22:00固定晚安的Cron Bot。调度只是唤醒来源，不是业务authority或Intent真源；没有合适Intent就静默，不承诺每日填满预算。

## 12. 第五阶段：Media Runtime

World State + Time + Location Context + Weather + Current Activity + Character Identity + Relationship Context → Media Intent → ComfyUI / Media Provider → Media Artifact → Host Delivery。

优先Character / World / Temporal / Context Consistency，表现当前World中的Agent此刻可能产生的照片，避免随机图片与文字世界脱节。artifact/job、生成、prepared、发送及receipt分别记录；Provider abstraction保持Host-neutral，真实ComfyUI与渠道测试需另授权，不由文本验证自动通过。

## 13. 第六阶段：Voice Runtime

Media稳定后推进Agent Identity + Voice Identity + Current Context + Emotion/Expression + Speech Style → Voice Runtime → Audio Artifact → Host Delivery。文字、照片、语音共享World、Memory、Relationship、Living State，不能成为三个独立人格系统。TTS/provider、artifact生命周期、发送与证据各自验证；照片链路PASS不等于Voice授权。

## 14. 第七阶段：Relationship / Personality Evolution

Core Soul + Relationship State + Shared Experience + Current Context → Personality Expression。Core Soul与Relationship-dependent expression分离；长期关系变化不简单通过直接重写Soul实现。同一Agent因长期共同经历形成不同表达，保留身份连续性、世界隔离与可审计关系状态。Autobiographical演进与Memory阶段积累衔接，不能将未核验模型叙事当Story事实。

## 15. OpenClaw正式目标路线

OpenClaw仍是正式目标Host。Hermes Living Integration未稳定前，不同时大规模推进两套Adapter。先Hermes Living Adapter → Host-neutral contract validation → OpenClaw Living Adapter，用成熟Binding模式映射Host差异，分别取得真实环境与生命周期证据。OpenClaw已存在的用户环境说明不是Adapter PASS，也不需要在本轮操作它。

## 16. Full Private RP 独立 blocker

Full Private RP = BLOCKED；H1 = BLOCKED_BY_OFFICIAL_HERMES_HOST_CAPABILITY；H2 = BLOCKED。这是已审核能力门禁，非本任务重新调查官方upstream后的结论。Hermes尚缺已验证满足要求的统一final-output commit boundary，理想合同如llm_final_output_commit(candidate, context) → ALLOW | DROP，DROP terminal、callback failure fail closed；OpenClaw同样缺已验证统一final-output transaction boundary。

等待upstream能力成熟后单独版本/执行链验证，不侵入式魔改Hermes/OpenClaw，不绕authority或伪造安全边界。Living permit不能替代final-output commit；H1 blocker不阻止Living只读/lifecycle/fake验证。Living真实集成PASS也不自动解锁原始历史隔离、晚到结果、授权前streaming或Full Private RP。

## 17. 防跑偏治理与任务声明

每个未来SP、RFC、ADR、Implementation Task、Validation Task必须声明：

```text
Roadmap Stage: <当前对应阶段及Gate>
Why Now: <为何属于当前阶段、依赖证据和单独授权>
```

任务不属于当前阶段默认NOT AUTHORIZED。实现简单、顺手能做、代码相关、未来肯定需要都不是提前开发理由。发现旁线需求先记录提案，不写实现；NEXT只是准备发布任务，不是开始执行。

任务应另列固定Base、范围/禁止范围、预置Gate、输出证据、完成/停止点与是否需要Host mutation/send权限，不能由代码依赖或green CI推导授权。每项阶段完成须独立证据，不自动升级SIMULATED_PASS→REAL_HOST_PASS或历史real send→当前Living PASS。

## 18. Roadmap变更规则与治理流程

改变阶段顺序、新增重大Runtime、提前Runtime、跳过Validation Gate、改变Host优先级或安全边界，必须先改Roadmap → ChatGPT/小雪独立架构审核 → 用户确认 → 再发布实施任务。不得先实现后补Roadmap；Architecture Review Gate的局部调整也适用，Codex不得自行改顺序。

继续Codex实现/文档 → Draft PR → ChatGPT/小雪独立审核 → 明确授权Ready → Codex仅Mark Ready → 轻量终审 → 明确授权Squash Merge → Codex Squash Merge → exact main push CI → ChatGPT/小雪独立核canonical main及四矩阵 → DONE。禁止Merge Commit/Rebase Merge/Auto Merge。merge本身不等于DONE，PR Head CI不能代替canonical main push CI。

GOV-ROADMAP1 Draft与CI交付后立即STOP，不Ready/Merge，不操作Host。只有GOV-ROADMAP1正式DONE后才发布HLV1；之后HLV1仍须明确授权并只读重新发现WSL中的Hermes/OpenClaw/Telegram/Discord测试bot/server/微信channel/Life Engine root。

## 19. STOP / ARCHITECTURE_CHANGE_REQUIRED

当前阶段无法在冻结架构下安全实现，且涉及Schema semantics、Prompt/Memory/Story authority、Attempt lifecycle、Recovery/Delivery semantics、Execution Permit、Authority lifecycle、Host trust boundary、World isolation或Bridge security时，停止并报告ARCHITECTURE_CHANGE_REQUIRED。报告冻结合同、发现gap、无法在现有架构解决的原因、最小可选方案及需经过的Roadmap/架构Gate；不得自行重构继续实施。

固定canonical main漂移则STOP并报告新SHA，不换Base或rebase本任务。需要真实Host操作/send才能完成文档治理、需要production改动或把Full Private RP变成Living前置依赖，也必须STOP。没有证据的能力保留UNKNOWN/BLOCKED，不用Prompt或model声明填补。
