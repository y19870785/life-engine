# SP-004G — 质量门禁

日期：2026-09-16。基线： `d18b643ef13fe9fd5c426be8b4614b2f91d234f8`。

实施授权：已授权，仅限 SP-004G。合并授权：未授权。

状态：PENDING_RE_REVIEW（SP-004G-R2）。 相关：[架构说明](../architecture/SP-004G-CHARACTER-IMPORT-IR.md)、[兼容性说明](../compatibility/SILLYTAVERN-COMPATIBILITY.md)。以下原始 SP-004G 记录保留，R1 结果及 R2 验证见后文。

## 自动化测试

| 门禁 | 实际结果 |
| --- | --- |
| Windows Python 3.12，既有基线测试集 | 72 项测试，5 个错误、1 个既有跳过 |
| Windows，新增导入测试 | 23/23 PASS |
| Windows，最终完整测试集 | 95 项测试，5 个错误、1 个既有跳过；与基线相同的失败集合 |
| WSL/Linux Python 3.11.15，最终完整测试集 | 95/95 PASS，含全部 72 既有测试与 23 新测试 |
| 导入/打包 | 三个新模块可导入，现有 release_files 收集三个文件；无版本/生产入口改动 |
| 语法 / 空白字符 | Python 语法树解析；git diff --check |
| 文档 | 本任务三个文档的相对文件链接逐项解析；仓库无专用格式化/链接检查配置 |
| 数据结构 | durable.DATA_SCHEMA == 2；既有生产代码和数据结构文件没有差异 |
| 语料隐私 | 1,737 行报告通过字段白名单审计；不含路径、正文、异常文本 |
| 语料完整性 | 所有 1,737 文件测试前后 SHA-256 与相对路径一致；另与最初私有清单再核对 |
| 跨平台语料 | Windows 与 WSL/Linux 各完整扫描一次，各项汇总统计一致；两次均无修改、无内部错误 |

Windows 的五个错误均发生在已有 SQLite 测试的临时目录清理（WinError 32），不是新增导入器失败：

- test_backup_contains_committed_wal_and_assets
- test_backup_restore_preserves_reference_to_actual_photo
- test_restore_is_atomic_and_pauses_to_prevent_delivery_replay
- test_unknown_database_schema_rejects_upgrade
- test_migration_preserves_source_and_is_idempotent

保留原测试和断言；未通过新增跳过、吞异常或修改生产 SQLite 行为来使测试全部通过。原有一个跳过项为平台符号链接条件。完整日志只保留在本地临时目录，不提交。

复现：

```text
python -m unittest discover -s tests -p test_import_cards.py -v
python -m unittest discover -s tests
git diff --check
```

首次运行新增测试暴露两个测试编写问题（BridgeRequest 调用签名、截断 PNG 的期望错误码），修正为真实合同后通过；未放宽产品校验。接近深度上限的往返测试额外覆盖源数据与 IR 外层结构的不同预算。

## 真实语料匿名结果

真实语料仅在用户授权的本机目录读取，不复制到仓库，不提供逐卡文件名/角色名/文本/图片。下表的数量不是对所有酒馆生态格式的覆盖承诺。

| 指标 | 数量 / 结果 |
| --- | ---: |
| 扫描总数 | 1,737 |
| PNG | 1,285 |
| JSON | 234 |
| 其他文件 | 218 |
| V1 | 48 |
| V2 | 1,124 |
| V3 | 131 |
| 未识别版本 | 434 |
| PASS | 0 |
| PASS_WITH_WARNINGS | 1,298 |
| LOSSY | 0 |
| UNSUPPORTED | 428 |
| MALFORMED | 11 |
| INTERNAL_ERROR | 0 |
| 内嵌世界书数 | 562 |
| 含扩展的卡片数 | 1,282 |
| 未知扩展命名空间数 | 21 |
| 含非空外部背景知识引用的卡片数 | 541 |
| 逻辑重复卡片数 | 33 |
| 解析器崩溃次数 | 0 |
| 语料是否修改 | **NO** |

识别的 131 个 V3 文件全部通过 IR 往返；仍有 1 个元数据超预算的 PNG 未进入版本识别，不能据此宣称所有 V3 或所有格式 100% 支持。V1/V2 版本计数包括字段不合法的已识别卡片。全部成功导入为 PASS_WITH_WARNINGS，主要原因是未知保留字段/扩展、旧格式、背景知识仅保存不执行。

| 拒绝代码 | 数量 | 说明 |
| --- | ---: | --- |
| FILE_TYPE_UNSUPPORTED | 218 | 文档/压缩包/其他附件；不提取、不执行 |
| NOT_CHARACTER_CARD | 207 | JSON 不满足支持的角色卡包络/保守 V1 识别；包括独立数据文件，不能据此判断损坏 |
| PNG_NO_CARD | 2 | 有图片容器但没有支持的角色卡元数据 |
| PNG_METADATA_LIMIT | 1 | 超 16 MiB 解码 JSON 预算；资源限制，未尝试无界导入 |
| INVALID_JSON | 6 | 无法解析为合法 JSON；无部分导入 |
| STRING_ARRAY_TYPE | 5 | 一个 V2 tags 是字符串；四个 V1 alternate_greetings 含非字符串成员；拒绝静默丢弃元素 |

第一轮外部背景知识引用将空 world/extraBooks 也计入；检查后改为只计非空引用，并添加回归测试。错误不是隐藏：最终数据采用修正后的明确统计定义。未知扩展命名空间是顶层键去重、排除这两个已映射键，不输出私有键名称。

## 范围 / 发布检查

仅提交三个新 Python 模块、一个原创测试模块、三个文档。无语料/原始 JSON/PNG/报告明细/私有清单/数据库/宿主文件进入 Git。

PR #3 仅只读，预期 OPEN / DRAFT / NOT MERGED，提交 `ab227f2179eeaa7ded662d612508a98ad5cdf04a`。本 PR 必须 OPEN / DRAFT / NOT MERGED；最终提交/推送/状态由执行报告与 GitHub 实际状态交叉核对。没有转为正式审核、合并或启用自动合并，也没有启动后续阶段。

本阶段无范围偏离。已知限制：容器资产只保留引用；不支持 CHARX/压缩卡元数据；没有完整外部规范校验器或背景知识运行时；私有 IR 序列化需要调用方安全保管；哈希验证不能替代防并发修改的文件系统锁。所有最终存储/迁移/版本登记/宿主接入需新授权。

## SP-004G-R1 审核修复

已审核提交： `b8788a230fe4f7625c6bd8a43efcaf24871fc788`。基线不变。只修 R1-A/R1-B，沿用 PR #6，禁止转为正式审核或合并。

- R1-A：容器全局校验完成后只处理权威载荷；有效 ccv3 不受非法/超大/重复 chara 语义阻断；权威 ccv3 失败不降级。结构与全局预算保护保留。
- R1-B：assets 及四个必需字符串属性、多语言字符串映射、数值日期（排除 bool）增加固定诊断。source/character_book/extensions 类型合同保留；显式值为 null 的世界书拒绝。未知资产/V3/扩展数据继续保存。
- 新增 5 个回归测试方法，参数化覆盖审核要求的 15 类情况，并覆盖两种数据块顺序、压缩回填、被忽略数据块的 CRC 错误、缺资产属性和值为 null 的世界书。原测试中用于隔离图片的合成资产补齐标准必需字段，图片隔离断言不变。

| R1 门禁 | 实际结果 |
| --- | --- |
| 导入测试 / Windows | 28/28 PASS |
| Windows 完整测试集 | 100 项测试，5 个既有 SQLite 清理错误、1 个既有跳过；失败集合不变 |
| WSL/Linux 完整测试集 | 100/100 PASS |
| Windows + WSL 语料 | 两边完整扫描全部 1,737 文件，最终报告一致；均未修改语料、无内部错误 |
| 隐私 / 完整性 | 1,737 行匿名报告白名单审计；全部哈希与原始清单一致 |
| 导入/打包/语法 | 新模块可导入、现有发布文件收集器包含它们、Python AST 检查通过 |
| 数据结构 | DATA_SCHEMA == 2，没有生产数据结构差异 |
| 文档 / 差异 | 10 个相对文档链接通过；git diff --check 通过 |

| 语料指标 | SP-004G 修订前 | R1 修订后 |
| --- | ---: | ---: |
| 总数 | 1,737 | 1,737 |
| PASS | 0 | 0 |
| PASS_WITH_WARNINGS | 1,298 | 1,297 |
| LOSSY | 0 | 0 |
| UNSUPPORTED | 428 | 428 |
| MALFORMED | 11 | 12 |
| INTERNAL_ERROR / 解析器崩溃次数 | 0 / 0 | 0 / 0 |
| V1 / V2 / V3 / 未识别版本 | 48 / 1,124 / 131 / 434 | 48 / 1,124 / 131 / 434 |
| 含扩展的卡片数 | 1,282 | 1,281 |
| 语料是否修改 | NO | NO |

计数变化的唯一新增错误是一个 V2 卡显式 `character_book: null`，固定代码 LORE_OBJECT_REQUIRED。之前被视为缺省世界书，R1 按已知字段的对象约束拒绝；未转成字符串、丢弃或针对卡名特判。扩展卡计数只统计成功导入对象，因此同步减少 1。原 5 个 STRING_ARRAY_TYPE 与 6 个 INVALID_JSON 不变，131 个识别的 V3 仍全部成功往返，其余语料汇总统计不变。

没有提交语料、逐卡报告或私有清单，没有改动 PR #3。R1 无范围偏离，完成后停止并等待 PENDING_RE_REVIEW。

## SP-004G-R2 中文表述验证

对照提交：`7480e119e5482c8a151dd223ac3850c6b4943e0e`。本轮仅修订三个指定文档、四个 Python 文件的注释与 docstring，以及 PR #6 的说明正文。标识符、错误码、固定协议值、命令和路径保持原样。

| 门禁 | 实际结果 |
| --- | --- |
| 可执行代码比对 | 四个 Python 文件移除 docstring 后的语法树与 R1 相同；人工核对差异仅为注释和 docstring |
| 导入测试 | 28/28 PASS |
| WSL/Linux 完整测试集 | 100/100 PASS |
| Windows 完整测试集 | 100 项测试，仍为相同的 5 个 SQLite 清理错误、1 个既有跳过 |
| 文档链接 | 三个指定文档的 10 个相对链接通过 |
| 数据结构 | DATA_SCHEMA == 2 |
| 差异检查 | git diff --check 通过 |
| 私有语料 | 本轮未读取或重新扫描；沿用 R1 结果，未改变导入逻辑、断言或数据结构 |

PR #6 保持 OPEN / DRAFT / NOT MERGED，不启用自动合并；PR #3 未改动。R2 完成后停止，状态为 PENDING_RE_REVIEW。
