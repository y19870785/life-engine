# Hermes / OpenClaw Host Sandbox 测试指南

> **当前允许：Soul Continuity / Living Agent / Host Sandbox 受控测试。当前不允许：Full Private RP 生产部署。** 已完成的 World、Memory、Lore、Story、Prompt 和 Bridge Core Runtime 不等于宿主已提供私密 RP 所需的最终输出授权、原始历史隔离和晚到回复围栏。不要通过 prompt 约束来替代 Host 能力。

本指南供用户和本机 Agent 在真实 Hermes / OpenClaw 上建立**隔离测试**。先读 [START-HERE](../START-HERE.md) 和 [Host Integration 合同](architecture/SP-004H-HOST-INTEGRATION.md)。测试以当前实际安装版本和受控身份为准，不预设插件加载即代表功能已送达。

## 四级测试边界

| 级别 | 可做的验证 | 当前门禁 |
| --- | --- | --- |
| Level 0 — Core Runtime | 不接 Host；直接验证 World、Memory、Lore、Story、Bridge、PromptSnapshot、持久化与恢复 | 可进行；是 Runtime 证据，不是 Host 私密 RP 证据 |
| Level 1 — Host Sandbox | 在真实但隔离的 Host 上验证插件加载、身份/Profile/Agent 绑定、status、wake、photo、prompt/context projection 与重启 | 可开始；测试 Profile/Agent、Session、Life Engine 实例和本人目标必须明确 |
| Level 2 — Soul Continuity | 在本人 Soul Agent 的受控会话中验证普通连续生活状态、主动联系、照片、轻量日常记录 | 可受控测试；真实发送和实际回执分别记录，不开启 Full Private RP |
| Level 3 — Full Private RP | Soul / RP 原始 Host 历史结构隔离、最终模型输出 fail-closed 授权和晚到围栏 | **BLOCKED**；Hermes 与 OpenClaw 当前均未取得生产 Host 资格 |

Level 0 中可直接构造 Roleplay World 和 PromptSnapshot；这不把 Level 3 变成可用状态。

## 建立隔离测试环境

使用独立 Life Engine instance、独立测试 World、独立 Host Session，以及只由本人控制的测试聊天目标。不要导入真实敏感聊天历史；不要在生产会话试探跨 World 或 DROP 安全性质。不需要修改原 Soul、替换主模型或开放 Full RP。照片是可选项；没有合适 ComfyUI 工作流时保持关闭。宿主插件审查、权限及发送政策继续生效。

先记下 Life Engine 永久目录、实例 ID、`DATA_SCHEMA`、测试 World 和备份位置；通过生成的 `INSTALL.md` 与 `manage.py doctor/status` 核对实际加载，而不是猜目录。插件需要重载时只操作已隔离的测试 Host；任何生产 Gateway 的重启或配置更改应另立明确任务。

### Hermes：官方安装的测试记录

使用**官方 Hermes 安装**和独立测试 Profile / `HERMES_HOME`，不要安装或测试为生产用的 [compatibility fork PR #1](https://github.com/y19870785/hermes-agent/pull/1)。记录下列字段，再执行插件加载与工具调用：

| 字段 | 实测值 |
| --- | --- |
| Hermes version / checkout | 待填写 |
| Profile / `HERMES_HOME` | 待填写；确认与生产目录不同 |
| Agent / 插件加载结果 | 待填写 |
| 测试 conversation / 本人目标 | 待填写 |
| Life Engine instance ID / data root | 待填写 |

在测试 Profile 验证 status、wake 静默规则、本人身份匹配与错误 Profile 拒绝；若启用 photo，验证文件确属本实例并单独确认真实发送。官方 [PR #120170](https://github.com/NousResearch/hermes-agent/pull/120170) 尚不能作为已发布 Full Private RP capability 使用。

### OpenClaw：实际安装的测试记录

记录真实版本、`agentId`、`workspaceDir`、配置/Profile、Gateway 身份、测试 Session 和 Life Engine instance。`workspaceDir` 是绑定证据，不代替受信发送者身份。OpenClaw 2026.9.5 已做 CAP0 审计；2026.9.6 只做相关边界的只读比对。本机以后升级版本，必须重新做 capability probe 和插件重载验证；版本号改变不自动解除 Full RP blocker。

| 字段 | 实测值 |
| --- | --- |
| `openclaw --version` / package path | 待填写 |
| `agentId` / `workspaceDir` | 待填写 |
| Config/Profile / Gateway | 待填写；确认是否测试专用 |
| 测试 Session / 本人目标 | 待填写 |
| Life Engine instance ID / data root | 待填写 |

OpenClaw 有 `before_message_write`、`before_agent_finalize`、`message_sending` 等 Hook 和 `lifecycleRevision`，但不能把这几处拼接成一次 fail-closed final-output commit 决策；不要以 Hook 名称推断 Full Private RP 已安全。

## Level 0：Core Runtime 检查

- [ ] 创建 Soul World 和独立测试 RP World；同一 CharacterDefinition 在不同 World 中对应不同 CharacterInstance。
- [ ] 两个 World 的 Memory 默认隔离；有界查询只返回授权 scope/audience。
- [ ] Lore 仅在绑定的 World 和条件下激活。
- [ ] Story 的 accepted event 在重启后可恢复，未接受内容不会成为故事真源。
- [ ] 相同输入与版本生成确定性的 PromptSnapshot。
- [ ] Bridge 无 Grant 时拒绝；有 Grant 时只有授权字段进入有界 BridgeProjection。
- [ ] Grant revoke 后旧 projection / Snapshot 判 stale；F1 不向目标 Memory/Story 自动写入源内容。

这些检查可以通过独立测试数据和 Runtime API 完成，不宣称已通过 Host 私密历史隔离。

## Level 1–2：真实 Host 沙箱检查

- [ ] Life Engine `status` 和 `doctor` 正常，实际插件工具能访问**测试实例**。
- [ ] Host Profile/Agent 与实例绑定唯一；错误 Profile/Agent 被拒绝。
- [ ] 使用独立测试 Session 与本人聊天目标；未复制生产私密历史。
- [ ] 重启测试 Host 后，Life Engine 实例状态仍存在，插件重新加载且绑定不漂移。
- [ ] `wake` 在安静时段、无联系理由或限额用尽时保持静默。
- [ ] `photo` 只返回本实例生成文件；未开启照片时不产生媒体发送。
- [ ] 区分内容生成、Host 准备发送、平台实际发送与可验证送达；**无 ACK 不声称送达**。
- [ ] Host 升级或 reload 后重新验证插件加载、身份和实例绑定。
- [ ] Full Private RP 始终关闭；测试报告写明 Host 版本、目标与实际回执。

任一出现 Host 身份不稳定、错误 Profile/Agent 可读取实例、重启后状态丢失、错误 Session 取得历史、未授权 Bridge 字段出现，或生产 conversation 被测试污染，**立即停止测试并保留证据**。

## 本阶段不进行的验证与不得宣称的结果

暂不在真实 Host 中执行 Soul secret → RP 原始历史、RP secret → Soul 原始历史、RP 切换后晚到模型回复、Full RP delivery fence 或 Host final-output transaction 试验。当前不能宣称：Full Private RP production-safe、Soul/RP raw Host history 已机械隔离、stale model output 不可能出现、Bridge 上下文总能受 Host final commit 保护，或模型输出 DROP 已同时覆盖持久化、下一轮重放、最终交付和流式输出。

Hermes compatibility fork 曾在隔离真实执行链中暴露 recovery durability 和 session incarnation/A→B→A writer 问题，路线已停止；它是审计证据，不是生产安装建议。OpenClaw CAP0/CAP1 也未使 H2 Adapter 解锁。下阶段 [SP-005H0 Host Integration Sandbox](planning/ROADMAP-2026-09.md) 应只验证 Soul Continuity 的真实宿主接线与回执。
