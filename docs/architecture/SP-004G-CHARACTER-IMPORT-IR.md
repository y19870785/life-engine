# SP-004G — 角色卡导入 IR

状态：IMPLEMENTED_CANDIDATE / PENDING_RE_REVIEW。

实施授权：已授权，仅限 SP-004G。合并授权：未授权。

基线： `d18b643ef13fe9fd5c426be8b4614b2f91d234f8`。PR #3 只读检查提交： `ab227f2179eeaa7ded662d612508a98ad5cdf04a`。

## 范围与架构

本阶段实现外部卡片 → 导入适配器 → 版本化 CharacterImportIR → SP-004A CharacterDefinition 的纯内存链路。前置合同：[SP-004A](SP-004A-WORLD-DOMAIN-MODEL.md)；兼容范围：[兼容性说明](../compatibility/SILLYTAVERN-COMPATIBILITY.md)；验证记录：[质量门禁](../planning/SP-004G-QUALITY-GATES.md)。

| 模块 | 职责 |
| --- | --- |
| [import_cards.py](../../runtime/life_engine/import_cards.py) | 有界本地读取、PNG 容器、JSON 识别、V1/V2/V3 到中立字段的映射 |
| [import_ir.py](../../runtime/life_engine/import_ir.py) | IR v1、不可变 JSON 值、LoreIR、私有序列化、角色定义投影 |
| [compat_scan.py](../../runtime/life_engine/compat_scan.py) | 离线递归、单文件处理、匿名结果、扫描前后完整哈希核对 |
| [test_import_cards.py](../../tests/test_import_cards.py) | 原创合成卡片与安全、往返、领域隔离验收 |

沿用包的扁平模块约定，确保现有发布文件收集器包含新增模块。没有变更既有入口、版本、数据库、宿主或调度器。

## CharacterImportIR 第 1 版

| 字段 | 约束 |
| --- | --- |
| ir_version | 当前为 1；未知版本拒绝，不猜测降级 |
| source_format / source_spec / source_spec_version | 分离容器与格式来源；不以文件名决定版本 |
| source_fingerprint | SHA-256 原文件字节；不含文件名；PNG 图像变化也会改变它 |
| payload_fingerprint | 规范 JSON 的 SHA-256；排除排版及对象键顺序差异，保留所有字段值与数组顺序 |
| profile | display_name、nickname、description、personality、scenario |
| instructions | character_instructions、post_history_instructions；始终是不可信内容 |
| greetings / example_dialogue | initial、alternates、group_only；原始示例对话 |
| creator_metadata / tags | 作者、版本标签、注释、多语言注释、来源、时间；与领域来源记录分离 |
| lore / lore_references | 内嵌 LoreIR；识别的非空 world/extraBooks 引用；不下载 |
| asset_references | PNG 原文件指纹引用、声明的资产记录、额外 PNG 资产数量；不解码图片 |
| extensions | 原始扩展对象，不透明保留且不可信 |
| preserved_source | 完整、规范化的源 JSON 附属数据；保留根对象、data、背景知识及扩展中的未知字段及空值 |
| warnings | 实现定义的固定代码，不包含卡片内容 |

IR 的核心是中立的语义分区；源格式只存在于适配器、来源标签和不透明附属数据。未来 V4/其他格式增加适配器，不能用外部结构定义替换领域模型。`preserved_source` 是重新映射与审计依据，不是让运行时直接读取外部 JSON 的许可。

JsonValue 用不可变规范 JSON 字符串保存值，解码返回独立副本；IR 与 LoreIR 均为不可变 dataclass（frozen=True），且禁止 repr 展示内容。它们不是凭据或可信事实。IR 的交换格式是本阶段显式的 v1，不承诺 dataclasses.asdict 为永久格式。

`to_json()` **含完整私有正文**，仅供受控存储/测试，绝对不能当兼容报告发布。扫描器单独构造白名单报告，既不调用 repr 输出 IR，也不输出异常堆栈。`from_json()` 检查版本、结构、预算和源附属数据指纹一致性；这不是签名或真实性验证。修改后的 IR 仍是不可信输入。

## 语义保真

合同：源数据 → IR → 规范化 JSON → IR，所有 IR 值相等；完整源 JSON 规范对象相等，包括未知扩展。对象键顺序、空白、JSON 转义写法不保证；数组顺序与字段值保留。有限 JSON 数字遵循 Python JSON 数值语义，不承诺任意精度浮点的十进制字面量重放。

不重建相同 PNG、不保存其图像二进制数据、不提取附带资产，也不保证被 ccv3 替代的 chara 回填版本独立往返。原容器依靠 source_fingerprint 引用，仍需要调用方保管原文件。相关情况有固定警告，不能把语义往返称为二进制归档。

### SP-004G-R1： 权威载荷与已知字段类型

PNG/APNG 先全局验证 CRC、数据块边界、IHDR、IDAT、IEND，再选择权威载荷。存在 ccv3 时只校验/解码它；非权威 chara 仅记录存在，发出 PNG_V_TWO_BACKFILL_IGNORED。chara 的非法 Base64、元数据超预算、重复或压缩形式不会阻断有效 ccv3，且不需要解码它来生成警告。整个文件大小和数据块数量上限仍全局生效；非权威数据块的 CRC/结构错误仍拒绝。

重复、非法或超预算的权威 ccv3 拒绝，绝不回退到有效 chara。没有 ccv3 时，chara 继续接受完整的数量、元数据类型、预算、Base64 和 JSON 校验，兼容 V1/V2。

已知字段只要出现就校验：assets 必须为对象数组，每项 type/uri/name/ext 必须存在且为字符串；creator_notes_multilingual 必须为字符串到字符串的映射；creation_date/modification_date 必须为有限 JSON 数值（int/float，明确拒绝布尔值、null 和字符串）。不限制或解析资产 URI，不下载。source 保持字符串数组校验，character_book/extensions 保持对象校验，显式 null character_book 也不再当成缺省值忽略。

新固定诊断代码：ASSETS_ARRAY_TYPE、ASSET_OBJECT_TYPE、ASSET_PROPERTY_TYPE、MULTILINGUAL_STRING_MAP_TYPE、DATE_NUMBER_TYPE；错误路径只含固定字段名，绝不插入语言键、资产值或正文。已知非法字段校验失败时拒绝导入；资产对象的未知键以及任意未知 V3/扩展字段继续完整保存。这些规则应用于导入卡片中出现的相应已知字段，不改变领域模型。

## 背景知识 IR

LoreIR 是上下文来源，绝不创建 World。它保存书级元数据、逐条 entries 和原文件指纹。条目映射 triggers、secondary_triggers、text、enabled、disabled、order、priority，其他字段进入 settings。完整源附属数据保留原字段名、别名冲突和字典形式条目 ID。

兼容 PR #3 使用过的 key/keysecondary/order/disable 与 entries 映射。enabled 与 disable 同时存在时均保留，不推断谁覆盖谁。正则表达式、装饰器、递归设置、位置、预算、插件扩展均保留但不执行。不做宏展开、Lua/JS、正则匹配、背景知识激活或词元预算裁剪；这些执行语义不能以“已成功导入”替代。

## 投影与信任边界

project_definition 接收受信任调用者提供的 Principal、带时区时间和可选 DefinitionRef；缺少 reference 参数时生成 UUID4/版本 1。ID 从不由显示名或文件名生成。指定 reference 参数用于未来调用方的版本管理；本纯函数不建立注册表，也不能阻止调用方故意重用同一 ID/版本表示不同内容。持久层必须执行不可变版本与唯一性约束。

角色定义使用现有 Values：untrusted_import 标签、IR 版本、载荷指纹和明确选出的 profile/instructions/greetings/example/tags 内容；背景知识以指纹引用。图片、原始外部 JSON、不透明扩展、背景知识插件设置留在 IR 附属数据，不塞进领域对象。未来持久层需要同时保存 IR 并解析引用，本阶段不实现该存储。

Provenance 固定 SourceType.IMPORT、RealityStatus.UNKNOWN、CanonStatus.UNREVIEWED；卡片声称的作者/时间不覆盖导入主体/时间。导入文本即使叫 system_prompt 也不修改 Soul、宿主、策略、所有权、工具权限或跨世界桥接授权。投影不构造世界、实例、记忆或现实事实。

测试展示同一投影所得的角色定义在两个独立 WorldScope 的 CharacterInstance 中引用相同固定版本，状态与关系不同。展示只构造内存合同对象，不实现 World 运行时。

## 资源与隐私边界

原文件上限 64 MiB；外部 JSON 16 MiB；PNG 元数据的 base64 长度按 JSON 上限计算；PNG 数据块数 100,000；源 JSON 最大深度 64、节点 250,000。所有数据块验 CRC/长度，要求 IHDR/IDAT/IEND；不解压图像，故不声称图像像素有效。zTXt/iTXt 卡载荷显式 UNSUPPORTED，不尝试解压；其他图片元数据不解释。

IR 内部规范表示因为转义与语义/附属数据重复允许额外有界空间：JsonValue 96 MiB，交换格式 384 MiB，交换格式深度 80、节点 2,000,000。这些是硬上限，不是推荐卡片大小。单文件处理，不把全部 IR 留在内存；报告仅保留小型匿名行。

JSON 拒绝重复键、NaN/Infinity、非法 Unicode、超深结构；非法已知字符字段拒绝，不静默转成字符串或截断。文件/父目录符号链接与 Windows 重解析点拒绝。扫描器遇到无法完整盘点的目录或链接中止，并报告完整性未验证，不声称语料未变。普通文件解析失败继续扫描；内部缺陷独立计数。

## PR #3 兼容性评估

只读参考 rp_cards.py、rp_lore.py 及对应测试；没有拣选提交、修改 PR #3 或引入第 3 版数据结构。

| 候选部分 | 处置建议 | 本阶段/后续路径 |
| --- | --- | --- |
| PNG chara/ccv3 与 CRC、JSON 识别 | 保留思想（KEEP）/调整实现（ADAPT） | 保留容器识别思想，加入结构化诊断、边界、IR；不沿用图片二进制数据返回值 |
| 字段白名单 / 16,000 字符拒绝 / 旧规范化字典 | REPLACE | 本阶段分区映射与完整不透明附属数据；全局预算取代每段武断截断 |
| 世界书解析器 | ADAPT | 保留别名；不因正则表达式/次级触发词存在而拒绝整卡；保留而非执行 |
| 递归背景知识选择 / 字节预算 | 保留有界设计（KEEP）/后续调整（ADAPT） | 本阶段未移植执行器；未来明确分词器、触发语义、安全预算后再吸收 |
| 合成解析与安全测试 | 保留覆盖范围（KEEP）/调整（ADAPT） | 新原创测试样例覆盖 IR、往返与隐私；不复制真实角色卡 |
| card_id、原始存储、第 3 版数据结构 | 后续迁移（MIGRATE） | 将来映射 DefinitionRef/IR/WorldScope；本阶段无生产持久化或迁移 |
| RoleplaySession / 记忆根对象 | 替换领域根对象（REPLACE）/后续迁移数据（MIGRATE） | 以 World/Timeline 与 epoch 隔离；不能让导入器激活旧 Session |
| Hermes/OpenClaw 适配器与提示词叠加层 | 保留宿主接线（KEEP）/后续调整（ADAPT） | 后续 H 接领域接口与能力报告；本阶段无部署或提示词注入 |

建议 **B — 拆分吸收**：按 G/D/E/B/H 的授权分阶段吸收独立能力与迁移数据；整支原地调整容易再次绑定卡片/会话/第 3 版数据结构，整体替换又损失已完成的适配与测试。此建议不授权修改、关闭或合并 PR #3。

## 后续待决问题

IR 的持久存储、角色定义版本注册、原包保管与删除策略、用户可审查的投影界面、背景知识运行语义、CHARX 及压缩元数据、外部资源许可与解析都需要后续正式授权。DATA_SCHEMA 保持 2；不开始 D/E/故事/桥接/宿主阶段。
