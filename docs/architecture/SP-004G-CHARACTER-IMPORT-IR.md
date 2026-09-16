# SP-004G — Character Import IR

Status: IMPLEMENTED_CANDIDATE / PENDING_INDEPENDENT_REVIEW.

Implementation Authorization: AUTHORIZED — LIMITED TO SP-004G. Merge Authorization: NOT AUTHORIZED.

Baseline: `d18b643ef13fe9fd5c426be8b4614b2f91d234f8`. PR #3 read-only head: `ab227f2179eeaa7ded662d612508a98ad5cdf04a`.

## Scope and architecture

本阶段实现外部卡片 → Import Adapter → versioned CharacterImportIR → SP-004A CharacterDefinition 的纯内存链路。前置合同：[SP-004A](SP-004A-WORLD-DOMAIN-MODEL.md)；兼容范围：[Compatibility](../compatibility/SILLYTAVERN-COMPATIBILITY.md)；验证记录：[Quality Gates](../planning/SP-004G-QUALITY-GATES.md)。

| Module | Responsibility |
| --- | --- |
| [import_cards.py](../../runtime/life_engine/import_cards.py) | 有界本地读取、PNG 容器、JSON 识别、V1/V2/V3 到中立字段的映射 |
| [import_ir.py](../../runtime/life_engine/import_ir.py) | IR v1、不可变 JSON 值、LoreIR、私有序列化、Definition projection |
| [compat_scan.py](../../runtime/life_engine/compat_scan.py) | 离线递归、单文件处理、匿名结果、扫描前后完整哈希核对 |
| [test_import_cards.py](../../tests/test_import_cards.py) | 原创合成卡片与安全、往返、领域隔离验收 |

沿用包的扁平模块约定，确保现有 release 文件收集器包含新增模块。没有变更既有入口、版本、数据库、宿主或调度器。

## CharacterImportIR v1

| Field | Contract |
| --- | --- |
| ir_version | 当前为 1；未知版本拒绝，不猜测降级 |
| source_format / source_spec / source_spec_version | 分离容器与格式来源；不以文件名决定版本 |
| source_fingerprint | SHA-256 原文件字节；不含文件名；PNG 图像变化也会改变它 |
| payload_fingerprint | 规范 JSON 的 SHA-256；排除排版及对象键顺序差异，保留所有字段值与数组顺序 |
| profile | display_name、nickname、description、personality、scenario |
| instructions | character_instructions、post_history_instructions；始终是不可信内容 |
| greetings / example_dialogue | initial、alternates、group_only；原始示例对话 |
| creator_metadata / tags | 作者、版本标签、注释、多语言注释、来源、时间；与领域 provenance 分离 |
| lore / lore_references | 内嵌 LoreIR；识别的非空 world/extraBooks 引用；不下载 |
| asset_references | PNG 原文件指纹引用、声明的资产记录、额外 PNG 资产数量；不解码图片 |
| extensions | 原始扩展对象，opaque/untrusted |
| preserved_source | 完整、规范化的源 JSON sidecar；保留未知 root/data/lore/extension 字段及空值 |
| warnings | 实现定义的固定代码，不包含卡片内容 |

IR 的核心是中立的语义分区；源格式只存在于 adapter、来源标签和 opaque sidecar。未来 V4/其他格式增加 adapter，不能用外部 schema 替换领域模型。`preserved_source` 是重新映射与审计依据，不是让 Runtime 直接读取外部 JSON 的许可。

JsonValue 用不可变规范 JSON 字符串保存值，解码返回独立副本；IR/Lore dataclass frozen 且禁用内容 repr。它们不是凭据或可信事实。IR 的 wire format 是本阶段显式的 v1，不承诺 dataclasses.asdict 为永久格式。

`to_json()` **含完整私有正文**，仅供受控存储/测试，绝对不能当兼容报告发布。scanner 单独构造 allowlist report，既不调用 repr 输出 IR，也不输出异常 traceback。`from_json()` 检查版本、结构、预算和源 sidecar 指纹一致性；这不是签名或真实性验证。修改后的 IR 仍是不可信输入。

## Semantic preservation

合同：source → IR → normalized JSON → IR，所有 IR 值相等；完整 source JSON 规范对象相等，包括未知扩展。对象键顺序、空白、JSON 转义写法不保证；数组顺序与字段值保留。有限 JSON 数字遵循 Python JSON 数值语义，不承诺任意精度浮点的十进制字面量重放。

不重建相同 PNG、不保存其图像 blob、不提取附带资产，也不保证被 ccv3 替代的 chara 回填版本独立往返。原容器依靠 source_fingerprint 引用，仍需要调用方保管原文件。相关情况有固定 warning，不能把语义往返称为二进制归档。

## Lore IR

LoreIR 是上下文来源，绝不创建 World。它保存书级 metadata、逐条 entries 和原文件指纹。entry 映射 triggers、secondary_triggers、text、enabled、disabled、order、priority，其他字段进入 settings。完整源 sidecar 保留原字段名、alias 冲突和字典形式 entry ID。

兼容 PR #3 使用过的 key/keysecondary/order/disable 与 entries map。enabled 与 disable 同时存在时均保留，不推断谁覆盖谁。regex、decorator、递归设置、位置、budget、插件 extension 均保留但不执行。不做宏展开、Lua/JS、正则匹配、Lore 激活或 token 预算裁剪；这些执行语义不能以“已成功导入”替代。

## Projection and trust boundary

project_definition 接收受信任调用者提供的 Principal、带时区时间和可选 DefinitionRef；缺 reference 时生成 UUID4/version 1。显示名或 filename 从不生成 ID。指定 reference 用于未来调用方的版本管理；本纯函数不建立注册表，也不能阻止调用方故意重用同 ID/version 表示不同内容。持久层必须执行不可变版本与唯一性约束。

Definition 使用现有 Values：untrusted_import 标签、IR version、payload fingerprint 和明确选出的 profile/instructions/greetings/example/tags 内容；Lore 以指纹引用。图片、原始外部 JSON、opaque extensions、Lore 插件设置留在 IR sidecar，不塞进领域对象。未来持久层需要同时保存 IR 并解析引用，本阶段不实现该存储。

Provenance 固定 SourceType.IMPORT、RealityStatus.UNKNOWN、CanonStatus.UNREVIEWED；卡片声称的作者/时间不覆盖导入 actor/时间。导入文本即使叫 system_prompt 也不修改 Soul、Host、policy、ownership、Tool permission 或 Bridge grant。Projection 不构造世界、实例、记忆或现实事实。

测试展示同一 projected Definition 在两个独立 WorldScope 的 CharacterInstance 中引用相同固定版本，状态与关系不同。展示只构造内存合同对象，不实现 World Runtime。

## Resource and privacy boundary

原文件上限 64 MiB；外部 JSON 16 MiB；PNG metadata 的 base64 长度按 JSON 上限计算；PNG chunk 数 100,000；源 JSON 最大深度 64、节点 250,000。所有 chunk 验 CRC/长度，要求 IHDR/IDAT/IEND；不解压图像，故不声称图像像素有效。zTXt/iTXt 卡载荷显式 UNSUPPORTED，不尝试解压；其他图片 metadata 不解释。

IR 内部规范表示因为转义与语义/sidecar 重复允许额外有界空间：JsonValue 96 MiB，wire 384 MiB，wire 深度 80、节点 2,000,000。这些是硬上限，不是推荐卡片大小。单文件处理，不把全部 IR 留在内存；报告仅保留小型匿名行。

JSON 拒绝重复键、NaN/Infinity、非法 Unicode、超深结构；非法已知字符字段拒绝，不静默 stringify 或截断。文件/父目录符号链接与 Windows reparse points 拒绝。scanner 遇到无法完整盘点的目录或链接中止，并报告完整性未验证，不声称 corpus unchanged。普通文件解析失败继续扫描；内部 bug 独立计数。

## PR #3 compatibility assessment

只读参考 rp_cards.py、rp_lore.py 及对应测试；没有 cherry-pick、修改 PR #3 或引入 schema 3。

| Candidate area | Disposition | 本阶段/后续路径 |
| --- | --- | --- |
| PNG chara/ccv3 与 CRC、JSON 识别 | KEEP ideas / ADAPT implementation | 保留容器识别思想，加入结构化诊断、边界、IR；不沿用图片 blob 返回值 |
| 字段白名单 / 16k 字符拒绝 / 旧 normalized dict | REPLACE | 本阶段分区映射与完整 opaque sidecar；全局预算取代每段武断截断 |
| World Book parser | ADAPT | 保留 aliases；不因 regex/secondary keys 存在而拒绝整卡；保留而非执行 |
| 递归 Lore 选择 / byte budget | KEEP bounded-design intent / ADAPT later | 本阶段未移植执行器；未来明确 tokenizer、触发语义、安全预算后再吸收 |
| Synthetic parser/security tests | KEEP coverage / ADAPT | 新原创 fixtures 覆盖 IR、往返与隐私；不复制真实角色卡 |
| card_id、原始存储、schema 3 | MIGRATE later | 将来映射 DefinitionRef/IR/WorldScope；本阶段无生产持久化或迁移 |
| RoleplaySession / memory root | REPLACE domain root / MIGRATE data later | 以 World/Timeline 与 epoch 隔离；不能让 importer 激活旧 Session |
| Hermes/OpenClaw adapters 与 Prompt overlay | KEEP host plumbing / ADAPT later | 后续 H 接领域接口与能力报告；本阶段无部署或 Prompt 注入 |

建议 **B — split and absorb**：按 G/D/E/B/H 的授权分阶段吸收独立能力与迁移数据；整支 adapt in place 容易再次绑定 card/session/schema 3，整体 supersede 又损失已完成的适配与测试。此建议不授权修改、关闭或合并 PR #3。

## Deferred questions

IR 的持久存储、Definition 版本注册、原包保管与删除策略、用户可审查的投影界面、Lore runtime 语义、CHARX 及压缩 metadata、外部资源许可与解析都需要后续正式授权。DATA_SCHEMA 保持 2；不开始 D/E/Story/Bridge/Host 阶段。
