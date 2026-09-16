# SillyTavern 角色卡兼容性

SP-004G 候选实现；导入兼容不等于 SillyTavern 运行时功能兼容。

格式依据：[CCv3 规范](https://github.com/kwaroran/character-card-spec-v3/blob/main/SPEC_V3.md) 与 [CCv2 规范](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md)，检查日期 2026-09-16。V3 在 JSON 中保留来源标识，PNG 使用 ccv3 tEXt 的 base64 JSON，双载荷优先 ccv3。除此之外的支持范围由下表与测试限定。

| 输入 / 功能 | 状态 |
| --- | --- |
| V1 扁平 JSON | 保守识别 name/description/first_mes；统一 IR，LEGACY_FORMAT |
| V2 / V3 JSON | 按实际 spec/data 识别；未知字段保留；缺可选/兼容字段有警告 |
| V2 chara / V3 ccv3 PNG | CRC/长度/基本结构验证；V3 放在 chara 可警告兼容；ccv3 放 V2 拒绝 |
| ccv3 + chara | 先验全局容器结构，只处理权威 ccv3；无效/超大/重复 chara 回填不阻断，发出忽略警告；ccv3 失败不降级 |
| 备选问候 / 群聊问候、示例对话、创作者元数据 | 映射并保留，不执行宏或替换指令 |
| 内嵌背景知识 | 仅作为上下文来源的 LoreIR；保留触发、次级触发词、位置/排序、递归和扩展，不激活 |
| 外部背景知识引用 | 识别非空 extensions.world / extraBooks，保留引用，不访问网络或外部文件 |
| 未知扩展 / 字段 | 完整源附属数据保留；不自动授权、不执行 |
| 资产 | 仅源指纹/声明/数量引用；不下载、不解码、不进入 CharacterDefinition |
| 独立世界书 JSON / 配置 JSON | 当前不是角色导入入口，NOT_CHARACTER_CARD |
| CHARX、ZIP、7z、文档及其他附件 | UNSUPPORTED；不提取压缩包或执行其中程序 |
| zTXt / iTXt 权威角色卡载荷 | UNSUPPORTED；不解压；若只是被 ccv3 替代的 chara 则忽略其语义 |
| 非法 JSON / 重复键 / 非法已知字段类型 | MALFORMED，校验失败时拒绝导入，无部分导入 |
| 大小/深度/节点/数据块限制 | UNSUPPORTED，资源限制不伪称格式损坏 |

R1 已知字段校验：assets 必须为对象数组且每项含字符串类型的 type/uri/name/ext；creator_notes_multilingual 为字符串到字符串的映射；creation_date/modification_date 为有限 JSON 数值，布尔值、null 和字符串不接受。source、character_book、extensions 的既有类型约束保留，显式 null character_book 拒绝。未知资产键/扩展仍保留；不对 URI 联网检查，不将非法字段转成字符串。

PNG 容器 CRC、边界、IHDR/IDAT/IEND 校验仍覆盖所有数据块，包括被忽略的 chara。忽略的仅是非权威回填的语义校验；文件大小和数据块总数保护没有放宽。

## 分类

| 结果 | 含义 |
| --- | --- |
| PASS | 导入及 IR 往返通过，无警告；不是运行时语义全部实现 |
| PASS_WITH_WARNINGS | 值保留且往返通过，有旧格式、未知数据保留、功能暂未实现或容器引用等警告 |
| LOSSY | 保留合同损失的独立类别；当前适配器不提供有损截断导入，因此本次为 0 |
| UNSUPPORTED | 非卡片、未知规范、未支持容器、读限制或资源预算；不计解析器缺陷 |
| MALFORMED | 非法 JSON/PNG 或已知必需类型错误；不导入部分结果 |
| INTERNAL_ERROR | 非预期异常/往返不相等；独立记录，不改归类为 MALFORMED |

诊断字段为 code、severity、stage、source_id、field、固定安全消息。field 只用实现中固定路径，不插入未知键或内容。报告中不保存输入异常消息。

## 离线扫描器

从仓库根目录，PowerShell 示例（把占位目录替换为本地目录）：

```powershell
$env:PYTHONPATH = 'runtime'
python -m life_engine.compat_scan '<local-corpus-directory>' --report "$env:TEMP\new-anonymous-report.json"
```

Linux/WSL 示例：

```bash
PYTHONPATH=runtime python -m life_engine.compat_scan /local/corpus --report /tmp/new-anonymous-report.json
```

输出默认只有汇总统计。可选 JSON 包含以 CARD- 开头的匿名哈希标识行，没有文件名、角色名、正文、图片、扩展值或私人路径。CLI 只向系统临时目录中的新文件写报告，禁止语料目录内输出/覆盖已有文件。IR 的 to_json 与这个报告是两种不同接口，前者是私有内容，切勿上传。

递归盘点所有普通文件；PNG/JSON 按扩展名选择候选，解析时按实际载荷识别版本。其他文件仍计总数/UNKNOWN/UNSUPPORTED。版本计数包括已识别但后续字段校验失败的卡；未知是尚无法识别版本，不等于解析器错误。PNG/JSON 汇总统计是盘点扩展名计数，单行 format 是实际解析容器（成功时）。

每次扫描前后完整计算 SHA-256，比对相对路径与哈希的私有内存清单，检测修改/增删/重命名；清单不进入报告。哈希是检测，不提供并发文件系统锁。报告源码不访问网络、LLM、数据库、宿主或外部链接。退出码 0 表示扫描完整且无内部缺陷/修改，不代表全部文件成功；1 表示内部错误或语料改变；2 表示盘点/报告失败、完整性未验证。

duplicate_logical_cards 只计算规范源 JSON 完全相同的重复个数，不能推断“同角色”或依据卡名去重。unknown_extension_namespaces 是不含已映射 world/extraBooks 的顶层扩展键去重数；不打印名称，不保证识别所有第三方插件命名空间。

## 本地真实语料基线

完整统计与失败原因见 [SP-004G 质量门禁](../planning/SP-004G-QUALITY-GATES.md)。仅匿名汇总统计进入 Git；原始语料、逐卡报告、私有哈希清单均不提交。

R1 回归：总数仍为 1,737，成功附警告从 1,298 变为 1,297，MALFORMED 从 11 变为 12，UNSUPPORTED 仍为 428，内部错误为 0。唯一新增拒绝为一个 V2 卡显式 null character_book，违反对象约束；识别的 V3 仍为 131 且全部成功往返。全部原始文件哈希未变。

识别的 V3 全部通过解析/往返，不意味着未识别的超大卡片也经过验证。所有成功卡片均有至少一项兼容警告，不能宣传为“100% SillyTavern 语义兼容”。扩展执行、资产解析、背景知识触发、故事、宿主接入均未实现。
