# Life Engine

**让你的 Hermes / OpenClaw Agent 记住一些共同经历，在合适的时候主动联系你，并延续自己的角色日常。**

Life Engine 是运行在已有 Hermes / OpenClaw Agent 旁边的持久状态与角色世界运行层。你继续使用原来的聊天渠道、模型和角色设定；它保存状态和待跟进话题，为主动联系提供依据，并为可恢复的 World 与隔离记忆提供底层 Runtime。

> **v0.3 开发预览 · 当前状态（2026-10-01）**：SP-005A3 = **DONE**；Host-neutral Living Host Binding 已合并并通过 exact main push CI。B01–B34 证据仅为 SIMULATED_PASS，真实 Hermes/OpenClaw 验证仍 PENDING_REAL_HOST_VALIDATION。HLV0 已 DONE；当前为 Real Host Integration，下一任务 HLV1 尚未授权，NO_REAL_HOST_OPERATION = true、NO_REAL_SEND = true。见 [A3 验证](docs/SP-005A3-VALIDATION.md)与 [HLV0 架构](docs/architecture/SP-005A4-HERMES-LIVING-VALIDATION.md)。

| 能力 | 当前状态 |
| --- | --- |
| World Runtime、World Memory、Lore、Story、Prompt Runtime、Controlled Bridge、Character Card Import | **DONE**（Core Runtime） |
| Soul Continuity Host Sandbox | **TESTABLE**（已有历史 Hermes 受控实测；整体真实 Host 验收仍 PENDING_REAL_HOST_VALIDATION） |
| Living Core、Session World revision fence、只读 operation recovery | **DONE**（A1、B0、B1；Core 自动验证） |
| A3 Living Host Binding | **DONE**（Host-neutral；B01-B34 = SIMULATED_PASS；真实 adapter 未实施） |
| Full Private RP on Hermes | **BLOCKED**（官方 Host capability） |
| Full Private RP on OpenClaw | **BLOCKED**（统一 final-output commit boundary） |

**HISTORICAL_EVIDENCE — 2026-09-30**：Life Engine 在 Hermes 0.21.3 的独立测试 Profile 中完成一次 canonical sandbox 综合评测。历史证据包括插件加载与实例绑定、Owner 识别与错误身份拒绝、Soul Continuity context、上一轮一次受控真实 Discord 文字发送的证据、综合评测本轮 Organic Contact 静默判定、持久性及备份/恢复；详见[脱敏历史记录](docs/validation/HERMES-COMPREHENSIVE-EVALUATION-2026-09-30.md)。一次发送不是自然 eligible organic contact 链路通过，边界仍为 **SENT / ACK UNKNOWN**。

当前没有受信 ACK validator；Hermes / OpenClaw real Host validation 均为 **PENDING_REAL_HOST_VALIDATION**；H1/H2 与 Full Private RP 均 **BLOCKED**。DATA_SCHEMA = 8，Schema Signature = SP-005A-living-runtime-v1，Prompt Template = SP-004K-prompt-v1；SP-005A2-P1 = NOT AUTHORIZED，PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES。

## 当前阶段

- Current Phase: Real Host Integration
- Current Completed Gate: SP-005A4-HLV0 = DONE；SP-005A3 = DONE
- Canonical Base: `08bf82e89f7a4572f4931105cc5e6927ae1c5214`
- Next: SP-005A4-HLV1（GOV-ROADMAP1 正式 DONE 后才发布，当前未授权执行）
- Long-term Roadmap: [长期路线与阶段治理](docs/planning/LIFE-ENGINE-DEVELOPMENT-ROADMAP.md)

本轮 GOV-ROADMAP1 仅整理路线，NO_REAL_HOST_OPERATION = true、NO_REAL_SEND = true；不启动 H-LV1。P1 未授权；B01–B34 仍为 SIMULATED_PASS。上述长期路线是后续任务的 Gate 依据，不自动授予未来功能资格。

## 用起来是什么感觉？

下面是完成接入后的一种使用场景，**不是已经实测的聊天记录**。现有 Host 插件仍走未 enrollment 的 legacy 路径，不能作为新 Living Core 的正式 Host 接入；ComfyUI 既有可选路径也不代表新的 Media Runtime 或真实媒体闭环已验收：

> 上午，你说：“下午有个面试，有点紧张。”
>
> Agent 将这件事记为待跟进话题。
>
> 到了合适的联系窗口，如果话题已到期、你们最近没有聊天，也不在安静时段，Agent 可以主动问：“面试结束了吗，感觉怎么样？”

这句话由你原来的模型按原来的性格来写。Life Engine 提供的是“还记得这件事”和“现在适不适合联系”的依据。

如果使用陪伴模式，你还可以设置角色作息和当天的视觉细节。例如上午读书、傍晚散步，同一天的服装选择保持一致。开启照片后，可以通过你配置好的 ComfyUI 工作流生成符合当时情境的图片，再交给聊天渠道发送。

## 它能带来什么？

| 能力 | 实际作用 | 当前边界 |
| --- | --- | --- |
| 日常记录 | 保存现有主动联系系统使用的简单记忆、观察和待跟进事项 | 与新的 World Memory 是不同层；需要 Agent 调工具记录 |
| World Memory | 按 World、Timeline 和可见范围保存、查询长期记忆 | Runtime 已实现，尚未自动接入真实每轮 Prompt |
| World 隔离 | Soul World 与各 Roleplay World 默认隔离；同一 World 内按可见范围区分角色视角 | 仅显式授权的有界 BridgeProjection 可用于 Prompt，不自动写入目标 Memory/Story |
| 主动联系 | 考虑联系窗口、安静时段、最近聊天和次数上限，决定是否开口 | 需要宿主定时任务，不保证每天发满次数 |
| 角色日常 | 提供当前活动、地点和稳定的当天视觉设定 | 是来自预设作息和随机选择的虚拟状态 |
| 工作跟进 | 对已记录且到期的事项发起跟进 | 仍受联系窗口限制，不适合准点提醒 |
| 情境照片 | 把角色形象与当时状态带入 ComfyUI 工作流 | 默认关闭，需要自己的可用工作流 |
| 备份与恢复 | 保存状态、配置和照片，使用数据代次备份、迁移与恢复 | 依赖持久磁盘、有效备份及完整删除控制状态 |

你可以选择两种模式：

- **陪伴模式**：希望角色有日常延续感，偶尔主动聊天。作息和照片由你配置。
- **工作模式**：跟进已记录的事情，不生成虚拟私人生活；没有到期待办时保持静默。

## World Memory 是什么？

Life Engine 已有独立的 World Memory 层。一条记忆除了正文，还属于明确的 Soul、World 和 Timeline，并规定哪些角色或用户视角可以读取。同一世界的公共知识、单个角色的私有记忆和用户管理视角各有可见范围。同一张 Character Card 可导入为 CharacterDefinition，再在不同 World 中创建 CharacterInstance；它们不会因为卡片或定义相同就自动共享经历。

Soul World 与 Roleplay World 默认不互相读取记忆。跨 World 默认仍拒绝；只有显式 Grant 才能生成有界、瞬时的 BridgeProjection。F1 只用于 `PROMPT_CONTEXT`，不会自动把源 World 内容持久写入目标 Memory/Story。Memory 记录也不等于剧情状态自动改变；已实现的 Story Runtime 由已接受事件维护故事真源。现有主动联系系统的轻量日常记录、Hermes / OpenClaw 自己的聊天历史、World Memory 是三层不同的数据。

## 它怎样和 Agent 配合？

一次主动联系大致经过这些步骤：

```text
Hermes / OpenClaw 的定时任务唤醒 Agent
                    ↓
Life Engine 检查状态、联系窗口和最近聊天
                    ↓
          保持静默 / 允许联系
                    ↓
       原来的模型组织合适的表达
                    ↓
     宿主通过你指定的聊天渠道发送
```

现有插件会尝试向宿主补入旧生活状态和近期日常记录；新的 World Memory 尚未自动进入每轮真实聊天的 Prompt。只有渠道、发送者身份明确匹配，且宿主提供可靠信息时，才自动记录你最近联系过它。

**模型负责理解与表达，Life Engine 负责状态和联系规则，Hermes / OpenClaw 负责调度与发送。** 安装扩展不会直接提升模型的推理能力；记忆记录和发送回执仍需要接入配合。

## 现在还没有什么？

World Memory、Lore、Story、Prompt、受控 Bridge 和 Living 的 **Core Runtime 已完成**，但不会自动提取所有聊天、自动接入真实 Host 每轮对话，也没有语义向量检索。Hermes / OpenClaw 的 Full Private RP Host Adapter 和所需的 final-output commit 能力尚未完成；原始 Soul/RP 历史隔离、晚到回复阻断、首次持久化／重放／发送／授权前流式输出的统一授权均未通过完整 Host 验收。真实 Hermes/OpenClaw Living Adapter 与验证、P1 正式 Prompt 接入、语音生命周期、完整真实 Host 验收、ComfyUI 与真实渠道闭环，以及资产仓库／Definition 升级仍属后续工作。B1 查询只恢复提交事实，不重试、不协调、不授权发送。

## 开始使用

下列 legacy 安装指南保留为另行授权的通用说明；不构成 HLV1～HLV4 权限。本轮不得安装、调用或重启 Host。先选择测试模式：**模式 A：Host Sandbox / Soul Continuity，当前允许受控测试；模式 B：Full Private RP，当前不得在生产启用。** 具体隔离、停止门和验收清单见 [Hermes / OpenClaw Host 沙箱测试指南](docs/HOST-SANDBOX-TESTING.md)。你需要一个能正常使用的 Hermes 或 OpenClaw Agent，以及 **Python 3.11 或更新版本**。Python 运行部分没有第三方依赖。照片功能另需可用的 ComfyUI API 身份工作流，缺少时可以先关闭照片。

### 1. 让本机 Agent 阅读接入说明

把项目下载到运行 Agent 的电脑上，将实际目录告诉它，并让它先读 [START-HERE.md](START-HERE.md) 和 [沙箱指南](docs/HOST-SANDBOX-TESTING.md)。例如：

> 请先阅读 START-HERE.md 和 docs/HOST-SANDBOX-TESTING.md，检查当前 Agent 的运行环境，只规划隔离的 Soul Continuity 沙箱接入，不开启 Full Private RP。

接入需要确认真实的 Agent 目录、聊天目标和联系偏好。安装脚本只准备文件，**执行完成不等于已经能主动发消息**。

### 2. 运行安装引导

在项目目录打开终端：

```sh
python setup.py
```

Windows 可用 `py -3.11 setup.py`，macOS / Linux 可用 `python3 setup.py`。这是直接运行的脚本，不使用 `pip install`。

引导会让你选择 Agent、陪伴或工作模式、联系频率和照片设置。默认将程序与数据保存到用户目录下的 `.life-engine`，并输出实例 ID 和该实例的 `INSTALL.md`。

“实例”就是这一个 Agent 对应的独立数据空间。永久目录应放在宿主工作目录和本项目目录之外；用 `--root` 可指定位置。Docker 部署必须持久挂载整个永久目录和宿主数据目录。

### 3. 连接插件，完成真实验证

使用安装输出的实际路径和实例 ID，替换下面的占位内容：

```sh
python "/永久目录/manage.py" connect --instance "实例ID"
```

然后在独立测试 Profile/Agent、Session 与本人聊天目标中，按生成的 `INSTALL.md` 验证插件加载和绑定。仅在确认隔离、权限与发送目标后才建立或复用测试定时任务。确认能读取状态、识别普通主人消息、在应当静默时保持静默；开启照片还要区分生成、准备发送和真实送达回执。首次接入不替换主 Agent，也不启用 Full Private RP。

宿主的插件审查和权限规则仍然生效。OpenClaw 使用命名配置时，连接还需指定对应的 `--host-profile`。

已有 v0.2 安装应先停止旧任务和旧入口，再使用 `--import-v02` 指向旧的 Agent/life-engine 安装目录，并加 `--legacy-stopped`。迁移前请让本机 Agent 核对数据版本，避免两套入口同时运行。

## 常见问题

**会改变我原来的角色吗？**

安装器保留原有 SOUL、称呼、模型和密钥配置。插件会加入能力说明与状态，身份和表达方式仍由原设定控制。

**重启之后还记得吗？**

已保存的数据位于独立持久目录，普通宿主重启后会重新读取。当前持久化会检测活动数据库缺失、校验 Schema，并在升级与迁移时复制、验证和原子切换数据代次；旧代次保留作为恢复边界。World Memory 删除还有独立于业务代次的控制记录，正常恢复旧备份不会让已删除记忆重新进入应用查询。仍需持久磁盘、有效备份和完整控制状态；这不能擦除自行复制的旧备份、系统快照或已经发给外部模型的数据。

**关机时还能主动联系吗？**

不能。电脑和宿主 Gateway（负责收发消息与运行任务的服务）需要保持运行。恢复后按当前状态判断，不补发整段离线期间的问候。

**会增加模型或出图成本吗？**

可能会。定时唤醒模型、生成消息和调用 ComfyUI 都会使用相应资源。即使引擎判断保持静默，宿主本次唤醒仍可能产生模型费用。

**记忆有多强？**

现有主动联系功能使用轻量日常记录和待跟进话题。新的 World Memory Runtime 已能按世界、时间线和可见范围持久保存并授权查询长期记忆，但尚未自动接入 Hermes / OpenClaw 的每轮真实 Prompt，也不会自动从全部聊天提取记忆；目前没有语义向量检索。

**生成了图片，就代表已经发给我了吗？**

不代表。出图和发送是两个步骤，文字准备好也不代表送达。当前没有通用的自动回执关联，需由接入层根据真实发送结果记录确认。

## 继续了解

| 你想做什么 | 看这里 |
| --- | --- |
| 让本机 Agent 帮你接入 | [接入任务说明](START-HERE.md) |
| 在 Hermes / OpenClaw 做受控测试 | [Host 沙箱测试指南](docs/HOST-SANDBOX-TESTING.md) |
| 备份、恢复、升级、配置插件 | [维护说明](docs/OPERATIONS.md) |
| 了解当前缺陷与历史测试记录 | [已知问题](docs/KNOWN-ISSUES.md) |
| 查看当前 CI 与历史模拟宿主验证 | [验证记录](docs/VALIDATION.md) |
| 了解 World Memory 架构 | [World Memory 架构](docs/architecture/SP-004B-WORLD-MEMORY.md) |
| 查看当前开发路线 | [2026-09 后续路线](docs/planning/ROADMAP-2026-09.md) |
| 查阅 SP-004 阶段实施历史 | [实施计划](docs/planning/SP-004-IMPLEMENTATION-PLAN.md) |
| 理解私密 RP 的 Host 合同 | [Host Integration 架构](docs/architecture/SP-004H-HOST-INTEGRATION.md) |
| 查看配置样例 | [examples](examples/) |
| 查看宿主接口参考来源 | [接口来源](docs/SOURCES.md) |
| 维护旧版安装 | [v0.2 说明](V02-README.md) |

源码位于 `runtime/life_engine/`，测试位于 `tests/`。开发者可运行 `python -m unittest discover -s tests -q`。当前 canonical main 的 CI 在 Ubuntu / Windows、Python 3.11 / 3.12 四矩阵运行完整测试并通过；数量与最新结果以 [GitHub Actions](https://github.com/y19870785/life-engine/actions) 为准。

仓库保留 Apache-2.0 许可证，导入源码的 MIT 许可和版权声明另行保留。适用范围与来源见 [NOTICE.md](NOTICE.md)。
