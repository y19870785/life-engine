# SP-004K-001 — Prompt 权威与类型化分节

状态：**架构候选 / 待独立审核**。适用于固定基线 `7f7c5c07d4cc821027cb083100335c8f4d139c44`。主合同见[Prompt Runtime 架构](../SP-004K-PROMPT-RUNTIME.md)。

## 决策

Prompt 是一次性派生投影，不是 World、Memory、Lore 或 Story 真源，也不是权限或工具授权。各子系统先按当前 Session、WorldScope 和 viewer 授权，K 再组装；不得取全库数据后依赖“不要泄露”的系统文案。K 不接受 Owner audit/list 结果来构造角色 Prompt。

内部结构必须使用带 `kind/authority/source/items/priority/required/truncation_policy` 的 `PromptSection`，而非裸字符串。组装器独占 section kind 与 authority 的赋值权。`RUNTIME_CONTROL` 只容纳 Life Engine 生成的身份、用途及边界；经过验证的身份与版本是结构化状态；卡片、Lore、Memory、Story 叙事、对话和未来 Bridge 正文始终是低信任数据。即使正文写有 `SYSTEM`、`grant tools` 或跨域读取指令，也不能成为控制 Section。角色卡导入成功也不产生宿主或工具权限。

固定逻辑顺序：运行控制 → 角色身份 → 行为 → 示例 → Story → Lore → Memory → 近期对话。Bridge 仅预留种类，K1 不启用。Story、Lore、Memory 的排序体现各自语义，但 K 不替它们判定真伪或调换优先级来改写事实。未来 renderer 使用明确来源标签和数据边界；这些标签帮助模型理解，不是安全隔离手段。真实工具许可与 Host 消息 role 映射属于 H，不在本 ADR 锁定。

## 取舍与结果

不选择“单个 system prompt 大字符串”，因为它无法审计哪个片段来自受信控制、哪个是外部正文，预算也无法逐语义项裁剪。不选择坏词过滤，因为任意语言和格式都能绕过。K1 必须在测试中证明恶意卡片、Lore、Memory、Story 和对话只产生对应数据 Section，且 assemble 不写任何 Runtime。
