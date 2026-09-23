# ADR-SP-004C-004 — 结构化事实、关系与 StoryThread

状态：**PROPOSED / PENDING_INDEPENDENT_REVIEW**。固定基线 `0028faedc36e00c52b9328e15a43fa81c31f9475`。总览见[SP-004C0 主文档](../SP-004C-STORY-RUNTIME.md)。

## 背景

Story 要保存当前世界事实、角色状态、关系和未完成线索，但现有 `Values` 缺少接受事件来源。若让每组状态拥有独立写入口，事件日志与状态表会相互矛盾。关系不能以 CharacterDefinition 或卡名为键，StoryThread 也不等于现实任务调度。

## 决策

`StoryState` 的四组结构均由同一事件日志确定性派生：受限命名空间 `world_facts`；以同 Scope `CharacterInstanceId` 为键的 `character_states`；以有向 `(source CharacterInstanceId, target CharacterInstanceId, relationship_key)` 为键的 `relationships`；以及以候选 `IdKind.STORY_THREAD` 为键的 `threads`。首版关系只支持本 Scope 的实例对，不新增 UserProxy、Soul/现实用户关系图、亲密度或情绪分数。键和值均有限长、有类型，序列化按稳定字节顺序。两个 World 复用同一 CharacterDefinition 不会共享任何投影。

Thread 可表达未完成任务、承诺、悬念或线索，有 `OPEN/RESOLVED/CANCELLED` 状态、有界标题/摘要和 opened/last_updated/resolved 事件引用。OPEN 才可更新、结案或取消；线索不是系统 Reminder、UserTask、Automation 或 scheduler 条目，不自动发消息或写 Memory。结构事件明确设置/移除事实、角色状态、关系与线索；`NARRATIVE_EVENT` 只记述已接受叙事，不从自然语言自动推导字段或关系分数。

现有 `CharacterInstance.state/relationships` 和 `WorldState.values` 保留供既有 Runtime 使用，不从中回填 Story，也不由 Story 双写同步。完整日志是 Story 唯一真源；持久投影可查询/重建。物理 `story_threads` 或 `story_relationships` 表若将来为检索而建，只能是派生索引，不得有独立管理写 API。角色知道哪些世界事实是 Memory/未来 K 的可见性问题，Story 投影本身不以 Memory audience 重写；K 不得把含潜在秘密的完整投影直接发给角色。

## 后果与验证

清楚保留了“世界当前事实”和“角色可记住什么”的区别，但 C1 必须对 Session 投影入口维持内部授权边界，未来 K 还需用途过滤。C1 验收 set/remove、非法实例/跨 World 主体、关系方向、thread open/update/resolve/cancel、非法状态迁移、叙事不改结构、同定义双 World 隔离及旧 Values 不产生 Story 真相。
