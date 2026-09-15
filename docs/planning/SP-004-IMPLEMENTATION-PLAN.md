# SP-004 — Proposed Implementation Plan

状态：PROPOSED / PENDING_INDEPENDENT_REVIEW。Owner: Codex。Independent Reviewer: ChatGPT / 小雪。

Implementation Authorization: NOT AUTHORIZED。

Merge Authorization: NOT AUTHORIZED。

本文件是建议工作包，不是待自动执行的任务队列。SP-004 只交付文档和 Draft PR；任何一项启动都需要独立审核结论与新的实施授权。参见 [RFC](../architecture/SP-004-PERSISTENT-WORLD-RUNTIME.md)、[Gap Analysis](../architecture/SP-004-GAP-ANALYSIS.md)。

## 1. Dependencies and Order

保留任务书 A–H 的编号，但调整实施顺序：A → D/G → E → B → C → F → H。原因是多世界写入前需要稳定定义与实例、导入 IR 和隔离查询；不能先建 Runtime，最后才补记忆权限。F 的策略合同在 A/E 阶段先定稿，实际桥接服务在隔离通过后实现。H 的认证/能力接口也在 A 定义，实际宿主上线放在末期。

建议每阶段使用独立 Draft PR、固定基线、列出数据影响和回滚演练。每阶段完成停止审核，不以 SP-004 的通过替代后续写库、部署或合并授权。下表中的“实施”全部指将来获授权后。

## 2. Work Packages

| 阶段 | 目标与范围 | 前置依赖 | 验收 Gate | 回滚/限制 |
| --- | --- | --- | --- | --- |
| SP-004A World Domain Model | 定稿 Soul/World/Timeline IDs、Ownership、state machine、认证 envelope、Bridge policy 合同、host capability 合同；确定事件/投影一致性 | SP-004 独立审核与新授权 | 域模型能表示一个 Soul、两个世界、同定义的两个实例；错误 scope/epoch 和无许可桥接被拒绝的契约可测；补充 ADR 决议 | 先不切换生产 writer；确认事件保留和隐私删除策略 |
| SP-004D Character Definition / Instance | 版本定义、世界内实例、定义固定与升级预览、旧卡 ID 映射 | A | 同角色两世界关系不串；定义升级不改历史；删除模板不级联删世界 | 保留旧卡记录与映射；不默选多世界 |
| SP-004G External Import → Internal IR | 包装现有卡片/世界书解析器，Character/Lore/World/可选 Story IR，诊断与原包哈希 | A；与 D 接口一致 | V2/V3 JSON/PNG fixture；有损映射可见；无脚本/权限执行；导入不自动激活世界或生成 canon | 原包可重导，mapper 版本固定；不用格式宣传替代兼容测试 |
| SP-004E World Memory Isolation | world/timeline/audience 查询、真实性类型、候选与 canon 分离、索引/缓存分区、许可默认 deny、legacy 数据分类 | A、D、G 的映射合同 | 两世界/Soul 交叉读取、ID 猜测、混域 FK、缓存/导出和旧 meta 授权测试；关闭记忆不旁路写入 | shadow copy 验证，不开自动桥接；旧数据保持 |
| SP-004B Persistent World Runtime | CREATE/ENTER/SUSPEND/RESUME/EXIT/ARCHIVE/DELETE；writer lease/revision/epoch；迁移兼容 facade、短事务、outbox | A、D、E；G 可导入候选 | 进程重启与崩溃恢复；重复命令无重复事件；晚到响应拒绝；退出不删世界；旧 CLI 歧义报错 | M0–M4 分阶段切换；旧 writer 冻结；已产生新写入时不做无损回退承诺 |
| SP-004C Story State / Timeline | 事件接受、状态投影、未完成事件、故事阶段、关系变化、逻辑时钟与修正 | B、E | 清空宿主历史后仍恢复剧情；挂起不推进；任务完成需事件证据；重放结果一致；关系不跨世界 | 固定 reducer 版本；历史摘要保留 unknown，不强制生成 canon；不实现分支 |
| SP-004F Controlled World Bridge | 双向 grant、字段筛选、预览、审核、目标写入与 lineage、撤销、派生缓存删除和恢复防复活 | E、B、C；A 合同 | 上海出差单字段授权；虚构体验仅作为 fictional_shared_experience；过期/撤销/重试/源删除测试；未授权正文不进入目标 Prompt | 默认 off，可关闭投递但保留最小审计；不承诺撤回外部模型已收到的内容 |
| SP-004H Host Runtime Integration | Hermes/OpenClaw session binding、认证、隔离 context lane、消息规范化、真实命令和投递边界 | B、C、F 的安全最小闭环 | 同 Profile 多聊天切换、原 SOUL 不变、跨宿主一致 scope、历史残留检测、重载/失败降级、真实隔离试用报告 | 能力不足明确 limited；不开放私密 aside；上线另行授权，不迁移凭据 |

## 3. Migration Workstream

迁移不是最后一次大转换，贯穿 D/E/B：

1. M0：只读盘点 schema 2 与候选 schema 3、备份、原库/资产哈希、映射提案；未知 schema 停止。
2. M1：在副本创建新模型并 shadow read，对比数量、内容、来源、时间与作用域；不得让 shadow 读触发写入。
3. M2：审查同卡多故事分组；定义版本固定；旧 meta 标 legacy_unreviewed；建立可回放迁移 manifest。
4. M3：获授权的维护窗口冻结旧 writer，检查源 revision，无在途写入后切换；所有新写入经过唯一 authoritative writer。
5. M4：保留旧 generation 与兼容接口；观察后再申请退役授权。旧二进制不直接读写新布局。

切换前失败保留源数据；切换后产生的新事件先完整导出并冻结，再决定旧部署恢复或前向修复。不得以恢复旧备份掩盖新事件丢失。回滚演练必须包括卡片头像、历史消息、授权/撤销、关系和未完成事件，不能只测数据库能打开。

## 4. Review and Release Gates

各阶段报告至少提供：固定 base/head、允许变更范围、受影响数据、测试命令和原始结果、风险与回滚流程、Draft PR 状态。Independent Reviewer 核对 GitHub 实际 diff 与证据后给出结论；Codex 不代替 Reviewer 签字。

可演示的最小 World 闭环应在 A/D/G/E/B/C 完成后成立：同一个角色模板创建两个世界，分别推进剧情；退出、重启、再进入，恢复各自关系与任务，互不串记忆。F 再演示受控现实信息导入和虚构体验导出。没有这些测试，不以“角色口吻很像”判定 Runtime 完成。

不预估缺少实现调查依据的工期。复杂度最高的是宿主历史隔离、旧会话分组、事件接受语义和撤销后的派生数据清理。若宿主隔离能力不足，应缩小产品能力声明，不用强化 Prompt 冒充权限修复。

## 5. Out of Scope and Stop Condition

Timeline Branching、多人共享、长期自主世界模拟、全局事件总线、分布式数据库、自动更新现实关系分值和新的真实渠道投递均不在首个闭环中。其扩展点保留，开发另行授权。

SP-004 完成 RFC、Gap、计划、检查记录、commit/push、Draft PR 与执行报告之后立即停止。不开始 SP-004A、不修改 PR #3、不转 Ready、不合并。
