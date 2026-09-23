# ADR-SP-004J-004 — Lore 预算、排序与不可信内容

状态：**PROPOSED / PENDING_INDEPENDENT_REVIEW**。固定基线 `1a73f6e43caf54bd34ae810c9b58eddb25f6fb88`；总览见[SP-004J0 主文档](../SP-004J-LORE-RUNTIME.md)。数字是 J1 首版候选硬上限，J1 任务书须在实施前复核并用测试固定；J0 不改代码。

## 预算层次

J1 的 `LoreBudget` 是运行时安全限制：最多 32 个启用书、32 个当前 Scope 绑定、每书 10,000 条、当前绑定合计最多 10,000 条可扫描条目和 10,000 个有效触发词；单触发词不超过 256 UTF-8 字节，单条正文不超过 64 KiB，初始对话与 Memory 投影合计不超过 256 KiB，追加已激活 Lore 后的累计触发语料也不超过 256 KiB；激活最多 16 轮、128 个输出条目和 512 KiB 输出正文。累计扫描工作量最多 16 MiB，按每次字面触发检查所扫描语料的 UTF-8 字节数累计；递归新增语料也计入。注册时对每书条目数、字段数与正文设硬上限；激活时在任何数据库全表扫描前检查绑定、条目和触发词总数。书版本不符合这些限制即不可供 J1 激活，不能临时抬高限制。

输入文本、绑定数或规范数据超过硬限制时拒绝请求或拒绝注册；运行中在轮次、扫描工作量、输出数或输出字节触顶时返回已确定的有界结果与固定耗尽诊断。输出按完整条目纳入，绝不裁剪半条 Lore 文本。遇到无法完整容纳的条目就在该位置停止，不扫描后续未知候选来“填满”预算；停止点按稳定顺序确定。常驻条目同样占用所有相应预算。

`byte_count`、`character_count`、`entry_count` 可以报告，但 J 不知道最终模型 tokenizer，不声称精确 token 数或可装进模型上下文。SP-004K 的 Prompt Runtime 另行执行模型 token 预算；K 不得通过扩大 J 安全上限来满足上下文需求。

## 完整排序键

每轮候选及结果采用 `(round 升序, activation_class, runtime_priority 降序, binding_order 升序, runtime_order 升序, BookId 升序, BookVersion 升序, EntryId 升序)`。`activation_class` 中常驻先于触发；同轮普通／selective 触发同类。`runtime_priority`、`runtime_order` 是注册时确定的有界整数，缺省为 0 和源顺序；绑定顺序由 Owner 显式管理。UUID 按其规范字节排序。轮次置首是为了保持递归因果：后轮高优先级条目不能倒插到已接受的前轮输出之前，也不会改变先前预算决策。若多个触发词同轮命中，匹配词按规范字符串顺序列出。不能依赖 SQL 自然行序、Python 字典迭代、时钟、随机数或哈希随机化。

超过上限时稳定停止并给固定诊断，例如 `ACTIVATION_ROUND_LIMIT`、`ACTIVATION_ENTRY_LIMIT`、`ACTIVATION_BYTE_LIMIT`、`ACTIVATION_SCAN_LIMIT`。`UNSUPPORTED_REGEX`、`UNSUPPORTED_EXTENSION`、`INVALID_TRIGGER_FIELD`、`CONFLICTING_ENABLE_FLAGS`、`DISABLED_ENTRY` 可报告登记决策；`BOOK_VERSION_UNAVAILABLE`、`BINDING_STALE`、`SCOPE_DENIED`、`SESSION_STALE`、`SCHEMA_MISMATCH` 属拒绝类别，不能被“空结果”吞掉。诊断携带代码、规范身份与计数，不拼接原始正文、触发文本或外部 URL。

## 权限与内容安全

Lore 文本是数据，即使看起来像 system 指令、工具调用、SQL、URL 或本地路径，也不产生 Principal、Bridge grant、Memory audience、Story 接受、宿主工具权限或网络／文件操作。J 只做字符串匹配和数据投影；不执行 regex、JavaScript、插件、宏、装饰器或动态扩展。后续 K 应将 `ActivatedLoreEntry.text` 置于低信任数据层并重验结果快照，不能让文本改写系统指令。J 无法撤回已发送给外部模型的内容。

恶意书文本、regex DoS、递归爆炸、超大触发集合、重复词、跨 World ID 猜测、同 Definition 跨 World 污染、Owner 私有 Memory 泄漏、陈旧绑定、旧书版本恢复、外部 URL 自动获取和工具指令注入均纳入 J1 验收。直接资产管理与会话激活使用不同接口；缓存与索引若未来存在也只是派生加速，不是权限票据。物理同库存放不放宽 Scope 或会话围栏。

## 验证

固定输入重复激活必须字节级一致地给出条目顺序、截断点、诊断和预算计数；同优先级、同条目顺序、同名书仍由后续 ID tie-break。分别测常驻占满预算、过长正文、扫描字节上限、轮次上限、递归循环、超大 trigger 集和不同输入顺序。所有安全测试使用合成文本，不执行源脚本或访问网络、宿主与真实角色卡。
