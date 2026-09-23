# ADR-SP-004C-003 — Story 独立逻辑时钟与 World 生命周期

状态：**PROPOSED / PENDING_INDEPENDENT_REVIEW**。固定基线 `0028faedc36e00c52b9328e15a43fa81c31f9475`。总览见[SP-004C0 主文档](../SP-004C-STORY-RUNTIME.md)。

## 背景

现有 `WorldTimeline.logical_tick` 是最小 Timeline 字段，尚无 Story 事件接受方。若 C1 每次接受都修改它，就可能与 `World.revision`/WorldSnapshot 保存合同发生隐式耦合；若按真实时间推进，又会把离线时长误作剧情。

## 决策

C1 建立完整 WorldScope 的独立 `StoryClock.logical_tick` 与 `StoryRevision`。初始均为 0；第一版每接受一个事件，两者各加 1，Scope 内 `event_sequence` 也连续加 1，但各列保持不同语义。Event sequence 是数据库接受顺序，tick 是故事内部顺序，`accepted_at` 是真实 UTC 审计时间。调用方不能回填旧 tick、插入历史或用墙钟计算 tick；纠正只在下一 tick 追加事件。

C1 不改 `WorldTimeline.logical_tick`，不因 Story 接受推进 `World.revision`、MemoryCollectionRevision 或 LoreBindingRevision。未来是否统一 Timeline/Story 时钟另立审查。World 为 ACTIVE 但没有 accepted event 时 StoryClock 不动；Roleplay SUSPENDED、离线、重启均不动。Soul World 虽有独立生命周期策略，StoryClock 也不能因默认 ACTIVE 或宿主定时工作自动推进。

受信 Owner 可在 CREATED/SUSPENDED World 明确 bootstrap/修正，不能伪装为会话，也不能把离线自动模拟为发生事件。Session 只可在 ACTIVE、当前 OPEN Binding、正确 Principal/Scope/角色/WriterEpoch/runtime_id/安装 generation 和 StoryRevision 的事务围栏内接受。ARCHIVED 默认只读，TOMBSTONED 只读审计；当前尚无完整 ARCHIVE/UNARCHIVE 应用入口，C1 不假设已有。

EXIT、SUSPEND、SWITCH、重启和 restore 都使旧 Session 失效；Story 接受必须与生命周期变更在同一稳定锁/SQLite 事务序列内核验，不能先验证旧会话、后把迟到结果写入新世界。备份恢复按当时日志精确恢复 tick/revision，不自动重演模型或补偿离线时间。

## 后果与验证

时钟从 WorldTimeline 最小字段中暂时分离，避免 C1 侵入既有 World CAS，但未来统一需显式映射。C1 必须验收初始 0、逐事件 +1、墙钟/ACTIVE 空转/SUSPEND 无变化、重启与 restore 精确恢复、旧 epoch/旧 runtime 拒绝、EXIT/SWITCH 与接受竞争不产生越界事件。

## C1 实现状态

C1 候选每接受一条事件推进独立 StoryRevision、事件序号和 StoryClock；不写 `world_timelines.logical_tick`，Session 接受在稳定 SQLite 事务中核对运行代次与 WriterEpoch。状态为 **IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**，原决策不变。
