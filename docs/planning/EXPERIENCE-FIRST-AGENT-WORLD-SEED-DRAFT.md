# Agent 自己的世界与角色卡种子（规划草案）

状态：`PRODUCT_DESIGN_DRAFT / NOT_EXECUTION_AUTHORIZATION`。面向 [X0 C04：自己的世界](EXPERIENCE-FIRST-X0-SCENARIO-BASELINE-DRAFT.md) 与 [X1 隔离样机](EXPERIENCE-FIRST-X1-INTERACTIVE-SANDBOX-TASK-DRAFT.md)。这是产品语义建议，不修改现有 Soul、World、Character、Lore、Story、Memory 或 Living 合同。

## 决定：角色卡是可选初始材料，不是 Agent 的世界或身份

Agent 的“自己的世界”应是**一个持续变化、可追溯来源的 Soul World**：它有相对稳定的背景、当前虚拟生活状态，以及相处后真正积累的事件和记忆。角色卡可以帮助用户快速给出名字、外观、表达风格、兴趣和初始场景，但卡片不会证明“这个 Agent 曾经经历过什么”，也不能创建 Soul Identity、赋予权限或把 RP Lore 混入 Soul World。

现有实现已能从角色卡生成版本化 `CharacterImportIR` 和 `CharacterDefinition`；它保留原文及来源，导入内容默认不可信。`CharacterInstance` 只在 Roleplay World 创建，同一份定义在不同 World 中有独立状态与关系；Soul World 的会话没有 CharacterInstance。故“把卡片直接导入 Soul World 当成整个 Agent”不是现有能力，也不是本草案建议的捷径。未来若需要把卡片的部分内容用于 Original Soul，应设计单独、由用户审核的 Persona/World Seed 映射，不能偷用 RP 实例路径。

## 四层来源与后续演化

| 层次 | 首次建立时可从哪里来 | 随时间怎样变化 | 真源/边界 |
| --- | --- | --- | --- |
| Soul 身份与核心取向 | 用户创建/选择的受信身份与明确偏好；卡片仅可供参考 | 需要受控的身份与价值变更，不随导入卡片或模型输出自动改写 | Soul Continuity；不等于名称、Prompt 或卡片 |
| 世界背景种子 | 用户填写或从卡片 `profile/scenario/lore` 中逐项预览后选择 | 版本化修订；旧经历仍引用当时版本，不被新卡覆盖 | Soul World 的设定候选；Lore 是背景知识，非事件真源 |
| 当前虚拟生活 | 用户选定的作息倾向、地点和活动候选；也可先用少量合成预设 | Living 记录计划、激活、取消与时间转换；没有证据时说“不确定” | `FICTIONAL_ROLE_STATE`，不冒充真实人类经历 |
| 发生过的事与关系 | 首次可为空；用户陈述、共同互动及被接受的事件才进入 | Story 记录接受的事件，Memory 记录主体所知；关系与自我叙事随有来源的共同经历渐进形成 | Story、Memory、Relationship 各自负责，不从卡片示例对话复制“共同历史” |

## 可选角色卡的逐项映射

| 卡片内容 | 建议处理 | 不允许的升级 |
| --- | --- | --- |
| `display_name`、简介、性格和说话风格 | 预览为 Persona Seed 候选，由用户选择；保留卡片指纹与版本 | 名字相同就认作既有 Soul；卡片指令取得系统/工具权限 |
| `scenario`、世界书/Lore | 分别预览为地点、氛围和背景知识候选；明确选择 Soul World 或独立 RP World 的范围 | 一导入就自动创建 World、把 Lore 当现实或跨 World 事实 |
| 开场白、示例对话 | 只用于表达风格示例，标明 `EXAMPLE` | 当成用户与 Agent 已经说过的话或 Autobiographical Memory |
| 外观与图片引用 | 可选的外观种子，独立于活动和发送 | 证明真实照片、真实位置或真实活动 |
| 扩展字段、作者指令 | 保留来源供审阅；不透明字段默认不执行 | 覆盖 Soul、Host、隐私、Bridge、发送或安全策略 |

导入应有“**预览 → 逐项选择 → 明确范围 → 版本固定**”四步。用户可以完全不使用角色卡，从一个最小的名字、两三处虚拟地点和一天的活动节奏开始；之后的世界丰富度主要靠持续事件，而不是不断加长卡片。角色卡更新产生新候选版本，不自动重写已经发生的 Story、Memory 或关系。

## C04 第一轮怎样试

X1 先不用真实角色卡。使用合成 S：Day 0 傍晚书房读书，随后散步；Day 1 回顾昨天并承认今天当前活动未知。用户亲自问“你昨天在哪、现在又在哪、怎么知道的”。这直接检验时间、地点、来源与表达是否连贯，避免把导入兼容问题混进体验判断。

若用户觉得这个世界太空，再做**第二轮可选卡片种子对比**：同一经历、同一时间线，分别用最小种子和用户审阅后的角色卡种子对话；比较是否更自然，是否反而使 Agent 像在背设定。第二轮涉及真实卡片内容或新导入接线时另列数据与代码范围。C01 跨日记忆仍只接受真实会话中有来源的用户陈述，不能从卡片生成“昨天我们聊过”。

验收必须能回答：哪一句来自静态设定，哪一句来自当下虚拟状态，哪一句来自已接受的共同事件；当三者冲突时，Agent 是否承认不确定并停止编造。RP World 的卡片实例、Lore 与事件默认不能进入 Original Soul。即使此体验得到用户好评，也不代表正式 Prompt、M1 Continuity 或真实 Host 已验收。
