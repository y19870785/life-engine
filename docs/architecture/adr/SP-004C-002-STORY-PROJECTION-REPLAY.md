# ADR-SP-004C-002 — 确定性 Story 投影与重放

状态：**PROPOSED / PENDING_INDEPENDENT_REVIEW**。固定基线 `0028faedc36e00c52b9328e15a43fa81c31f9475`。总览见[SP-004C0 主文档](../SP-004C-STORY-RUNTIME.md)。

## 背景

持久 `StoryState` 能加快读取，但若它可以独立修改，就会与事件历史构成双真源。现有 `CharacterInstance.state/relationships` 与 `WorldState.values` 只有最小运行状态，不包含 accepted StoryEvent 依据，也不能用作重放起点。

## 决策

唯一输入是同 Scope、按连续 `event_sequence` 排列的不可变已接受事件。`reduce(previous_state, event) → next_state` 必须纯净、确定、无 I/O；网络、数据库、宿主、Memory、Lore、墙钟、随机数均不得进入 reducer。所有计算所需值必须在经过版本化验证的 Event 中。相同日志与相同投影版本在 Windows/Linux 形成相同规范序列化结果。

`StoryState` 是可重建物化投影，包含 Scope、StoryRevision、独立逻辑刻度、末序号、投影版本，以及有界 world facts、CharacterInstance 状态、有向关系和 StoryThread。`NARRATIVE_EVENT` 不改变结构化四组值。第一版建议用单行规范 JSON 保存有界投影；不为 facts/关系/线程建立可独立写入的第二真源。Story 接受在一个 SQLite 事务中进行：授权、幂等、数据库修订 CAS、reducer 预演和大小校验、插入事件、写投影、推进修订/刻度、审计/回执，全部成功才 commit。超预算整次拒绝，不截断。

候选 `StoryProjectionVersion = SP-004C-story-projection-v1`。改变 reducer 语义或 payload 解释必须显式版本迁移、重建和校验；不允许新代码静默解释旧日志。完整重放必须可执行，并在测试中与持久投影逐项及规范字节比较。生产可选择有限启动校验和按需全量重放，但末事件、修订、刻度、版本和连续序号错误须拒绝；发现重放不等时报告 `STORAGE_CORRUPT`，不得自动修补或转为成功。

投影读取区分 Owner 审计与 Session 当前 Scope 的有界结果。Session 不直接查完整事件历史；Story 世界真相也不是角色知识 ACL。未来 K 必须按用途选择可进入 Prompt 的字段，不能把 C1 内部投影直接给模型。

## 后果与验证

增加版本迁移和投影一致性成本，换来事件与当前状态原子、可重建。C1 必须测试同日志重复/跨平台结果、缺失/重复事件、错误末序号、坏版本、坏快照、事务中途失败、投影过大回滚和无法从旧 `Values` 产生无来源 Story 真相。

## C1 实现状态

C1 候选固定 `SP-004C-story-projection-v1`，事件与规范 JSON 投影同事务提交；数据校验完整重放，发现差异只拒绝，不静默修复。状态为 **IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**，原决策不变。
