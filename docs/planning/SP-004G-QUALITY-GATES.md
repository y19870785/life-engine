# SP-004G — Quality Gates

日期：2026-09-16。Baseline: `d18b643ef13fe9fd5c426be8b4614b2f91d234f8`。

Implementation: AUTHORIZED — LIMITED TO SP-004G. Merge: NOT AUTHORIZED.

Status: PENDING_RE_REVIEW (SP-004G-R1). 相关：[Architecture](../architecture/SP-004G-CHARACTER-IMPORT-IR.md)、[Compatibility](../compatibility/SILLYTAVERN-COMPATIBILITY.md)。以下原始 SP-004G 记录保留，R1 最新结果见末节。

## Automated tests

| Gate | Actual result |
| --- | --- |
| Windows Python 3.12，既有 baseline suite | 72 tests，5 errors、1 existing skip |
| Windows，新 importer tests | 23/23 PASS |
| Windows，最终完整 suite | 95 tests，5 errors、1 existing skip；与 baseline 相同的失败集合 |
| WSL/Linux Python 3.11.15，最终完整 suite | 95/95 PASS，含全部 72 既有测试与 23 新测试 |
| Import/package | 三个新模块可导入，现有 release_files 收集三个文件；无版本/生产入口改动 |
| Syntax / whitespace | Python AST parse；git diff --check |
| Documentation | 本任务三个文档的相对文件链接逐项解析；仓库无专用 formatter/link-check 配置 |
| Schema | durable.DATA_SCHEMA == 2；既有生产代码和 schema 文件没有 diff |
| Corpus privacy | 1,737 行报告通过字段 allowlist 审计；不含路径、正文、异常文本 |
| Corpus integrity | 所有 1,737 文件测试前后 SHA-256 与相对路径一致；另与最初私有 manifest 再核对 |
| Cross-platform corpus | Windows 与 WSL/Linux 各完整扫描一次，aggregate 各项一致；两次均无修改、无内部错误 |

Windows 的五个错误均发生在已有 SQLite 测试的临时目录清理（WinError 32），不是新增 importer 失败：

- test_backup_contains_committed_wal_and_assets
- test_backup_restore_preserves_reference_to_actual_photo
- test_restore_is_atomic_and_pauses_to_prevent_delivery_replay
- test_unknown_database_schema_rejects_upgrade
- test_migration_preserves_source_and_is_idempotent

保留原测试和断言；未通过新增 skip、吞异常或修改生产 SQLite 行为来使 suite 变绿。原有一个 skip 为平台符号链接条件。完整日志只保留在本地临时目录，不提交。

复现：

```text
python -m unittest discover -s tests -p test_import_cards.py -v
python -m unittest discover -s tests
git diff --check
```

首次运行新增测试暴露两个测试编写问题（BridgeRequest 调用签名、截断 PNG 的期望错误码），修正为真实合同后通过；未放宽产品校验。near-depth-limit 往返测试额外覆盖 source 与 IR envelope 的不同预算。

## Anonymous real corpus results

真实语料仅在用户授权的本机目录读取，不复制到 repo，不提供逐卡文件名/角色名/文本/image。下表的数量不是对所有酒馆生态格式的覆盖承诺。

| Metric | Count / result |
| --- | ---: |
| Total Scanned | 1,737 |
| PNG | 1,285 |
| JSON | 234 |
| Other files | 218 |
| V1 | 48 |
| V2 | 1,124 |
| V3 | 131 |
| Unknown | 434 |
| PASS | 0 |
| PASS_WITH_WARNINGS | 1,298 |
| LOSSY | 0 |
| UNSUPPORTED | 428 |
| MALFORMED | 11 |
| INTERNAL_ERROR | 0 |
| Embedded World Books | 562 |
| Cards With Extensions | 1,282 |
| Unknown Extension Namespaces | 21 |
| Nonempty Linked Lore Cards | 541 |
| Duplicate Logical Cards | 33 |
| Parser Crash Count | 0 |
| Corpus Modified | **NO** |

识别的 131 个 V3 文件全部通过 IR 往返；仍有 1 个 metadata 超预算的 PNG 未进入版本识别，不能据此宣称所有 V3 或所有格式 100% 支持。V1/V2 版本计数包括字段不合法的已识别卡片。全部成功导入为 PASS_WITH_WARNINGS，主要原因是 opaque fields/extensions、legacy 格式、Lore 仅保存不执行。

| Rejection code | Count | Interpretation |
| --- | ---: | --- |
| FILE_TYPE_UNSUPPORTED | 218 | 文档/压缩包/其他附件；不提取、不执行 |
| NOT_CHARACTER_CARD | 207 | JSON 不满足支持的角色卡包络/保守 V1 识别；包括独立数据文件，不能据此判断损坏 |
| PNG_NO_CARD | 2 | 有图片容器但没有支持的角色卡 metadata |
| PNG_METADATA_LIMIT | 1 | 超 16 MiB 解码 JSON 预算；资源限制，未尝试无界导入 |
| INVALID_JSON | 6 | 无法解析为合法 JSON；无部分导入 |
| STRING_ARRAY_TYPE | 5 | 一个 V2 tags 是字符串；四个 V1 alternate_greetings 含非字符串成员；拒绝静默丢弃元素 |

第一轮 linked lore 将空 world/extraBooks 也计入；检查后改为只计非空引用，并添加回归测试。错误不是隐藏：最终数据采用修正后的明确统计定义。未知扩展 namespace 是顶层 key 去重、排除这两个已映射键，不输出私有 key 名称。

## Scope / publication checks

仅提交三个新 Python 模块、一个原创测试模块、三个文档。无 corpus/raw JSON/PNG/报告明细/私有 manifest/数据库/宿主文件进入 Git。

PR #3 仅只读，预期 OPEN / DRAFT / NOT MERGED，head `ab227f2179eeaa7ded662d612508a98ad5cdf04a`。本 PR 必须 OPEN / DRAFT / NOT MERGED；最终 commit/push/状态由 Execution Report 与 GitHub 实际状态交叉核对。没有 Ready、Merge、Auto Merge，也没有启动后续阶段。

本阶段无范围偏离。Known limits：容器资产只保留引用；不支持 CHARX/压缩卡 metadata；没有完整外部规范 validator 或 Lore runtime；私有 IR 序列化需要调用方安全保管；哈希验证不能替代防并发修改的文件系统锁。所有最终存储/迁移/版本登记/宿主接入需新授权。

## SP-004G-R1 review fixes

Reviewed head: `b8788a230fe4f7625c6bd8a43efcaf24871fc788`。Base 不变。只修 R1-A/R1-B，沿用 PR #6，禁止 Ready/Merge。

- R1-A：容器全局校验完成后只处理权威 payload；有效 ccv3 不受非法/超大/重复 chara 语义阻断；权威 ccv3 失败不降级。结构与全局预算保护保留。
- R1-B：assets 及四个必需 string 属性、多语言 string map、数值日期（排除 bool）增加固定诊断。source/character_book/extensions 类型合同保留；显式 null book 拒绝。未知 asset/V3/extension 数据继续保存。
- 新增 5 个回归测试方法，参数化覆盖审核要求的 15 类情况，并覆盖两种 chunk 顺序、压缩回填、被忽略 chunk 的 CRC 错误、缺资产属性和 null book。原测试中用于隔离图片的合成 asset 补齐标准必需字段，图片隔离断言不变。

| R1 Gate | Actual result |
| --- | --- |
| Importer tests / Windows | 28/28 PASS |
| Windows full suite | 100 tests，5 既有 SQLite cleanup errors、1 既有 skip；失败集合不变 |
| WSL/Linux full suite | 100/100 PASS |
| Windows + WSL corpus | 两边完整扫描全部 1,737 文件，最终报告一致；均未修改语料、无内部错误 |
| Privacy / integrity | 1,737 行匿名报告 allowlist 审计；全部 hash 与原始清单一致 |
| Import/package/syntax | 新模块可导入、现有 release collector 包含它们、Python AST 检查通过 |
| Schema | DATA_SCHEMA == 2，没有生产 schema diff |
| Documentation / diff | 10 个相对文档链接通过；git diff --check 通过 |

| Corpus metric | SP-004G before | R1 after |
| --- | ---: | ---: |
| Total | 1,737 | 1,737 |
| PASS | 0 | 0 |
| PASS_WITH_WARNINGS | 1,298 | 1,297 |
| LOSSY | 0 | 0 |
| UNSUPPORTED | 428 | 428 |
| MALFORMED | 11 | 12 |
| INTERNAL_ERROR / Parser Crash Count | 0 / 0 | 0 / 0 |
| V1 / V2 / V3 / Unknown | 48 / 1,124 / 131 / 434 | 48 / 1,124 / 131 / 434 |
| Cards With Extensions | 1,282 | 1,281 |
| Corpus Modified | NO | NO |

计数变化的唯一新增错误是一个 V2 卡显式 `character_book: null`，固定代码 LORE_OBJECT_REQUIRED。之前被视为缺省 book，R1 按已知字段的 object 合同拒绝；未 stringify、丢弃或针对卡名特判。扩展卡计数只统计成功导入对象，因此同步减少 1。原 5 个 STRING_ARRAY_TYPE 与 6 个 INVALID_JSON 不变，131 个识别的 V3 仍全部成功往返，其余 corpus aggregate 不变。

没有提交 corpus、逐卡报告或私有 manifest，没有改动 PR #3。R1 无范围偏离，完成后停止并等待 PENDING_RE_REVIEW。
