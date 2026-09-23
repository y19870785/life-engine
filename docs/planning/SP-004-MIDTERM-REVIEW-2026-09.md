# SP-004 项目中期复盘与后续路线

## 复盘基线与结论

本复盘以 canonical main `10b75a6f8fe6fd94b98e82a6e903cdcfcb8c6d1e` 为基线。SP-004C1 在此基线上实施；本分支的 Story 实现仍待独立审核和合并，不能计入该 main 的已完成能力。

Life Engine 已形成**持久化 Agent 世界运行内核**：身份、世界与角色实例生命周期、按世界隔离的 Memory、固定版本的 Lore，以及同一实例 `life.db` 上的备份、恢复和副本迁移。它尚不是完整可聊天角色产品。真实 Hermes/OpenClaw 角色模式、统一 Prompt 组装和受控跨世界共享都没有进入 canonical main。

## 已完成阶段与能力

| 阶段 | canonical 状态 | 已进入 main 的能力 | 当前边界 |
| --- | --- | --- | --- |
| SP-004 | DONE | 持久 World Runtime 架构 | 不是全部产品功能 |
| SP-004A | DONE | Owner、Soul、World、Timeline、身份与领域约束 | 无完整 Bridge 服务 |
| SP-004G | DONE | V1/V2/V3 Character Card 有界导入、CCv3 权威来源、CharacterImportIR、CharacterDefinition 投影、LoreIR 保真 | 导入不等于 Lore 激活或宿主角色模式 |
| SP-004D | DONE | CharacterInstance、SessionBinding、ENTER/EXIT/SUSPEND/RESUME/SWITCH、revision、WriterEpoch | 最小 Values 不是 Story 真源 |
| SP-004E | DONE | 同库 SQLite、精确 Schema 验证、代次、副本迁移、原子激活、WAL 安全备份、恢复、runtime_id 与重启围栏 | 持久化不等于宿主自动接线 |
| SP-004B | DONE | WorldScope、Audience、Owner/Session 授权、候选与接受语义、不可变后继、CAS、幂等、删除/撤销控制及恢复不复活 | 不自动读取所有聊天或注入 Host |
| SP-004J | DONE | LoreBookId、不可变版本、显式固定 WorldScope 绑定、literal/selective/constant 激活、有界递归、确定排序、预算、Session 围栏、Schema 5 | 不执行脚本、regex 或完整 World Book 宿主体验 |
| SP-004C0 | DONE | Story 真源、修订与独立时钟、确定性投影、前向修正、线索/关系边界的架构冻结 | 基线 main 尚无 Story Runtime 实现 |

World Runtime 已覆盖 Soul World 与 Roleplay World 的独立身份和生命周期。Memory 的删除控制独立于业务 generation，恢复旧备份不会在应用查询中自动复活已删除记录。Lore 的 BookVersion 固定于 WorldScope 绑定，登记新版不会让既有 World 自动跟随。上述能力均是后端 Runtime 合同，不能写成用户聊天时已自动启用。

三个子系统的含义必须分开：**Lore 是世界设定是什么；Memory 是谁知道或记得什么；Story 是世界实际发生了什么。** 一条 Memory 被接受，并不等于 Story 事件被接受；Lore 激活也不改变故事状态。SP-004C1 候选以显式接受的不可变 StoryEvent 作为唯一 Story 真源，仍须经过独立审核。

## 当前产品闭环缺口

目前没有统一 Prompt assembly、真实 Hermes/OpenClaw 角色模式、自动 Memory 注入、受控 Soul↔Roleplay 共享，也没有让模型输出自动确权 Story 的路径。后端内核已经成型，但 Runtime 结果尚未统一进入模型上下文，真实 Host 体验没有闭环。

## 路线调整的依据

旧建议顺序为 `B → J → C → F → K → H`。B、J 已完成，C0 已冻结；先做 F 再做 K 不再是合适的主线。普通 Roleplay 世界在默认隔离下，可以由 CharacterDefinition、CharacterInstance、World、Memory、Lore 和 Story 构成角色上下文，不需要预先开放 Soul Bridge。

K 是已有 Runtime 结果进入模型前的统一消费层。它应组合固定 Definition、当前 Instance、World/Session、受授权的 MemoryProjection、LoreActivationResult 和有界 StoryProjection，并检验快照一致性与预算。先做 K 可以具体看到模型实际需要哪些跨域字段。F 随后只提供**经授权的跨世界投影**，而不是同步数据库、开放全部 Soul Memory 或全部 Story 历史。若桥接结果需持久写入目标，仍应经过目标 Memory 创建或 Story 候选与接受流程。Bridge 结果可供 K 消费，K 不应以 Prompt 文本充当权限边界。

H 拆为 H0 宿主合同、H1 Hermes Adapter、H2 OpenClaw Adapter，使两种宿主的路由、历史和能力差异留在适配层，不渗入核心 Runtime。L 作为旁线，处理原始 PNG、头像、角色卡原包、导入历史、Definition 升级与旧数据映射，不阻挡 Story、Prompt、Bridge 或 Host 主线。

## 最新建议路线

```text
已完成：A Domain → G Import → D World → E Persistence → B Memory → J Lore → C0 Story 架构
当前候选：C1 Story Runtime + Schema 6（待独立审核）
后续建议：K0 Prompt 架构 → K1 Prompt Runtime → F0 Bridge 架构 → F1 Bridge Runtime
          → H0 宿主合同 → H1 Hermes → H2 OpenClaw
旁线：L 资产、原包、历史与 Definition 升级
```

后续顺序仍需各阶段任务书与独立审核。C1 候选不授权自动启动 K/F/H；本复盘也不把 Prompt、Bridge、Hermes 或 OpenClaw Integration 标记完成。

当前阶段事实与详细边界见[实施计划](SP-004-IMPLEMENTATION-PLAN.md)、[Story 架构](../architecture/SP-004C-STORY-RUNTIME.md)、[Memory 架构](../architecture/SP-004B-WORLD-MEMORY.md)及[Lore 架构](../architecture/SP-004J-LORE-RUNTIME.md)。
