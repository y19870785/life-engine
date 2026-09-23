# ADR-SP-004J-003 — Lore 激活、字面触发与递归

状态：**PROPOSED / PENDING_INDEPENDENT_REVIEW**。J0 仅冻结 J1 安全子集；总览见[SP-004J0 主文档](../SP-004J-LORE-RUNTIME.md)。

## 注册时规范化

受信适配器把 [LoreIR](../../../runtime/life_engine/import_ir.py) 的已支持字段转为 `enabled`、`constant`、`primary_triggers`、`secondary_triggers`、`selective`、`case_sensitive`、`runtime_priority`、`runtime_order`、`text`、来源元数据与不支持设置。`enabled` 默认真，显式 `disabled=true` 优先并给 `CONFLICTING_ENABLE_FLAGS` 诊断；书级默认值只有被列入支持的规范字段才可继承。整数优先级／顺序必须有限且有界，非法值给 `INVALID_TRIGGER_FIELD` 并采用明示安全默认，不能在激活时再猜 `order`、`priority`、`insertion_order` 的原始含义。导入 IR 中的 `settings`、`use_regex`、`extensions` 继续保真，不按未知扩展求值。

原字段表示任意 regex、脚本、插件回调、宏、装饰器命令或其他需要执行的不受支持语义时，该条目运行禁用并返回固定诊断；不能把 regex 字符串当作 literal 触发词。核心格式错误如正文非字符串、条目非对象，拒绝该版本注册。未解析 `extensions.world`／`extensions.extraBooks` 外部书引用不能成为激活候选；J1 不联网、不打开任意本地路径。空正文允许保真登记，但运行时不输出、不触发后继。空触发词忽略并给诊断，绝不按 match-all；无有效主词的非常驻条目不会被触发。

## 字面匹配合同

语料由明确传入的有界近期对话投影、可选当前 viewer 已授权 Memory 投影和此前各轮已纳入结果的 Lore 正文累计组成。J 不直接读取宿主原始聊天历史或 Memory 表。每个非空触发词按 Unicode 字符串的**子串**匹配，不做分词、词界、词干化、NFC 或 NFKC。默认对触发词和语料分别使用 Python `str.casefold()`；显式 `case_sensitive=true` 使用原字符串。UTF-8 字节长度用于硬预算，匹配语义使用 Unicode 字符串；不因编码长度变化而改触发身份。

普通条目需要任一主词命中。`selective=true` 且存在有效次词时，还需任一次词命中；次词集合采用 ANY，不采用 ALL。没有有效次词时只检查主词并给可审计诊断。`selective=false` 的次词不参与门槛。常驻条目不检查主／次词，但仍必须启用、被当前 Scope 绑定并满足预算。禁用条目永不激活。重复词按规范排序去重以稳定诊断，多个条目用同一词时都可命中，不实行“第一个赢”。

## 轮次与终止

第 0 轮使用初始显式语料，同时考虑常驻与字面命中条目。该轮实际纳入输出的条目正文追加到下一轮语料，此后逐轮累计；没有新纳入条目时结束。每轮仅在当前 Scope、当前启用绑定的固定版本中搜索，可跨书，不可跨 World。一个精确 `(BookId, Version, EntryId)` 在单次请求中最多纳入一次；递归 A→A、A→B→A 不会循环。不会因为激活而写 Memory、Story、World、Session 或绑定，也不会执行正文里的命令。

每轮以[预算与排序 ADR](SP-004J-004-BUDGET-ORDERING-SAFETY.md)的完整稳定键处理候选。新条目只有在整条正文能纳入输出预算时才成为后续递归来源；未纳入的条目不贡献正文。轮次、输出条目数、正文与触发语料字节数、累计扫描工作量都有限。触及硬上限时在当前稳定顺序边界停止，返回已完整确定的前缀与 `budget_exhausted` 诊断；不输出半条正文，也不继续尝试未评估候选。越界输入、陈旧绑定、无效 Scope／Session 或损坏规范数据则直接拒绝，不以部分结果掩盖授权失败。

激活原因固定为 `CONSTANT`、`PRIMARY_TRIGGER`、`SELECTIVE_TRIGGER`、`RECURSIVE_TRIGGER`；递归条目保留具体主／次词命中信息及来源轮次。原因仅用于解释，不能授予权限。如果同条目在同轮多次命中，按固定顺序列出匹配词，结果只出现一次。相同输入、绑定快照、预算、受权 Memory 投影应得到相同 EntryIds、顺序、诊断与截断。

## J1 验证

字面命中／未命中、两种大小写、多个主词、次词 ANY 命中与未命中、selective 无次词、常驻／禁用冲突、空词、空正文、重复触发与重复正文；A→B→C、A→A、A→B→A、跨书递归、不同 World 不能递归；轮次、条目和扫描限制；regex 和扩展脚本不得执行、网络与文件路径不得访问。使用原创合成数据即可，不读取真实角色卡语料。

## J1 实现状态

**IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**。规范化阶段只读 `LoreIR` 的明确白名单，regex 与非空未知运行扩展将对应条目标为运行禁用，不回退到字面匹配。激活使用显式对话文本和可选由 `MemoryQueryResult` 转换的受权文本投影；不查询 Memory 表。字符串匹配保持原 Unicode 或 `casefold()`，不做标准化。只把实际完整纳入输出的正文添加到下一轮语料，精确条目键最多输出一次。Owner 管理结果不能直接作为 Session 投影。
