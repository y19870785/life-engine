# SP-004 — 历史差距与当前边界校准

本文件由 SP-004R 在 canonical main `780c7a54635e7347b914751ce0c79e350800be0b` 上校准，文档修订状态为 **PENDING_INDEPENDENT_REVIEW**。只授权治理文档，不授权新的运行实现或 PR #3 合并/关闭。

## 一、比较基线与记录职责

原分析比较 main `81ee02b561ac90641c3632f750ffd86a48310cf7` 和 [PR #3](https://github.com/y19870785/life-engine/pull/3) 的固定 Head `ab227f2179eeaa7ded662d612508a98ad5cdf04a`。那个时间点没有后来的 A/G/D/E，不能继续将当时的缺口当作当前未完成事实。

32 文件的逐项证据、唯一分类、剩余能力与关闭条件，以 [SP-004R 正式替代记录](../planning/SP-004R-PR3-SUPERSESSION.md) 为准；已完成历史和未来 PROPOSED 工作包以[实施计划](../planning/SP-004-IMPLEMENTATION-PLAN.md)为准。本文件仅保留架构差距的对照，避免重复维护两份分类表。

PR #3 不再是“受控预览合并候选”。它保持 OPEN / DRAFT / NOT MERGED，只作 read-only reference，不能通过解决冲突、cherry-pick 或迁入旧 Schema 继续合并。

## 二、已消除与尚存的差距

| 领域 | 旧 PR #3 假设或能力 | 当前 canonical 事实 | 剩余差距及建议归属 |
| --- | --- | --- | --- |
| 领域身份 | 卡片兼作角色运行身份 | A 的 World/Timeline/Definition/Instance 与 D 的运行合同已完成 | 不复活 card_id 根；定义升级和资产归 L |
| 导入 | JSON/PNG 解析后直接投影旧卡片表 | G 已实现 CharacterImportIR、诊断、来源和 Definition 投影 | 原包/头像/完整导入历史归 L；LoreIR 不执行 |
| World Book | 条目绑定 card，字面触发、递归和预算 | 当前只保留导入知识；World Book 不是 World | J 重建版本、关联、scope、激活、预算和终止规则 |
| 生命周期 | 整实例单活动 RoleplaySession | D 已实现 World、CharacterInstance、SessionBinding 和进入/退出/挂起/恢复/切换 | 完整 ARCHIVE/DELETE 应用入口不能因类型存在而算完成；另立范围 |
| 并发与持久化 | 旧 session 检查，无 World revision/epoch | E 已实现 SQLite CAS、每 World OPEN 唯一、runtime_id 重启围栏和历史保留 | 宿主事件和 Story 接受事件去重分别归 H/C |
| Schema 与部署 | 旧 Schema 3、卡片级联和版本号识别 | E 的 canonical Schema 3 与签名校验、副本迁移、整安装激活、备份/回退已完成 | 旧 Schema 3 不兼容；若确有历史数据救援，L 另提只读映射方案 |
| Memory | 同卡跨 session 查询，最近摘要代表进度 | A 有真实性/正史类型，D/E 有最小 Values；尚无 World Memory 服务 | B 重建 World/Timeline/Instance、scope/audience 与检索/缓存隔离 |
| Story | 消息与摘要隐含充当故事状态 | 没有 accepted events 和确定性投影运行层 | C 重建 Story state、关系推进、未完成线索与重启重放 |
| Soul 隔离与共同体验 | 自动 meta 与无范围 aside | A 有默认拒绝 Bridge 策略，不是完整 Bridge 服务 | F 显式 grant/preview/确认/lineage；自动写 Soul 淘汰 |
| Prompt | 卡片/Lore/记忆摘录成为唯一世界视图 | D/E 已有可持久快照，但没有 canonical Prompt Runtime | K 从授权结果投影，H 处理宿主历史；Prompt 不作权限边界 |
| Hermes | Profile 作用域、pre/post Hook 与历史真实探针 | 现有生活 Bridge 不等于角色 World 集成 | H 重建 Principal、绑定、晚到响应、重连和多聊天实机验收 |
| OpenClaw | 原生命令、前置上下文、Node 合同 | 没有新 World 角色接入的实机验收 | H 处理命令路由、消息记录能力差异、历史污染与 Gateway 验证 |
| 现实工具和调度 | 角色 active 时阻断照片/生活动作 | 当前生活 Engine 保持独立；未接入自动 Roleplay | H/F/B 明确授权边界；不新增后台任务或将剧情变现实通知 |
| 文档、CI 与演示 | 旧版本用户说明、平台矩阵和转录 | 历史证据不能证明当前可用体验；main 无旧 workflow | GOV-DOC/GOV-CI 另审；演示资产保留固定 Head，不复制二进制 |

## 三、纠正旧优先级结论

旧分析要求“Character IR 与 WorldMemory 必须在多世界写入开启前可用”，已不适合作为当前完成判定：G 的 Character IR 和 D/E 的最小隔离状态写入已交付，完整 World Memory 是下一层独立能力。不能倒推 D/E 尚未完成，也不能把最小 Values 写入当作 Memory 或 Story 已完成。

阶段历史为 SP-004/A/G/D/E DONE。E 不再指 Memory；未来 B/J/C/F/K/H 的顺序只作 PROPOSED，见实施计划。新持久字段仍须独立 Schema/迁移审核，本轮不提前分配版本。

## 四、兼容性与授权边界

Schema 版本号相同不代表 Schema 兼容。旧 PR #3 Schema 3 不等于 `SP-004E-world-runtime-v1`，不得猜测迁移或自动修复。旧卡片删除级联、自动 Soul 摘要和卡片/宿主聊天作为 World 根均淘汰。

未来若有历史数据映射需求，必须保全原包与备份、保留来源和歧义，不把旧摘要自动变成 canon 或已授权共同体验；当前没有兼容层交付承诺，也不要求先造兼容层才可关闭历史 PR。

PR #3 的关闭必须等待替代记录及路线图合并、独立审核和单独关闭授权；关闭后仍建议保留分支至少到 Lore/Memory/Host Integration 完成。当前不修改 PR #3，不启动后续能力。
