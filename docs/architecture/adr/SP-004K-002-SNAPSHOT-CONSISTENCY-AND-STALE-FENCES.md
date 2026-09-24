# SP-004K-002 — Prompt 快照一致性与陈旧围栏

状态：**架构候选 / 待独立审核**。主合同见[Prompt Runtime 架构](../SP-004K-PROMPT-RUNTIME.md)。

## 决策

`PromptSnapshot` 是不可变、非持久的派生物，记录完整 WorldScope、principal 引用、purpose、viewer、Session、WriterEpoch、runtime_id、generation、固定 DefinitionRef、World revision、Memory 不透明查询版本、Lore 绑定修订/结果版本/固定书版本、Story 修订/投影版本、模板版本、预算、各 Section、诊断、规范 fingerprint 与不透明 token。它不建立数据库真源表；K1 不改变 Schema 6。

各 Runtime 查询可能来自不同 SQLite 快照。K1 用乐观两阶段合同：受信适配器取得会话授权结果 → 组装并交叉检查 → 末尾重新校验 → H 发模型前再次校验。Session 已关闭、epoch/runtime/generation 变化、World/Memory/Lore/Story/Definition 任一相关版本变化，都使整份快照 stale；不能仅丢失效 Section 后继续。模型响应回来后，宿主或写入者仍需再验会话围栏。模型调用期间绝不持 SQLite transaction 或锁。

当前实现差异决定 K1 的适配工作：`MemoryQueryResult` 只含记录与不透明 `version`，`SessionMemoryContext` 没有 runtime_id；`StoryProjection` 不显式含 session_id、epoch、runtime_id、generation，尽管其 token 生成时绑定这些值；`LoreActivationResult` 显式携带前三者。K1 不能解析 Memory/Story token，也不能信任调用方手填的“授权标记”。受信适配器必须把原产生 Context、结果、Repository 运行代次绑定。Memory 版本重验采用同 context、同 query/limit/history 的受信重查并比较不透明值，或另经审核增加验证 API；Owner collection revision 不可代替。Story 会话重验需重新获取 Session projection 或等效只读围栏，Owner `story_revision()` 只比较数值不足以证明 Session 有效。Lore 需重验当前 Session、激活输入与绑定版本。若无法完成可靠重验，失败关闭。

Fingerprint 对相同输入、预算与模板必须确定性；不含墙钟。可用 HMAC token 绑定全部输入和 Section 指纹，但 token 不是认证凭据，也不能以单个 Story token 代替。启动/恢复后的旧 runtime_id 或 generation 必须让旧快照失效。

## 取舍与结果

不用跨子系统长事务或跨 LLM 网络调用持锁；那会阻塞生命周期变更且仍无法控制宿主历史。代价是有可能在重验时发现变化并重新组装，但这种显式失败优于发送混合时点上下文。K1 测试必须覆盖 EXIT/SWITCH/重启/恢复、版本变更和查询与组装之间的竞争。
