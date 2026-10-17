# Hermes 自助创建角色故事（试用）

> **状态范围（2026-10-14）**：本文描述 #56—#59 堆叠 Draft 的试用能力；本轮固定实现 Base 为 #59 `1d1ec6b7681684cbc44458e94344c261c5a2011b`，不是已合并主线承诺。当前能力、历史证据和 W0/W1 验收状态见 [统一基线](planning/W0-W1-CHARACTER-BASELINE.md)。以下安装示例不单独授予 Host 操作权限；本轮仅新隔离 Profile、工具集合为空、REAL_SEND = NO。

统一入口将原卡检查、开场选择、独立 Profile 配置、World/Memory/Story 与宿主工具许可串起来。角色卡默认 user 身份由作者正文和开场承担，用户可选 Persona 补充；不默认改成现实主人身份。原卡源文件保持不变。

## 1. 让 Hermes 展示故事与开场

```sh
python tools/hermes_character.py inspect --card /private/card.png
```

返回角色名称、原卡场景、所有默认/替代开场、兼容问题与世界书条目计数。不会展示世界书全文。`--details` 可显示作者角色说明和性格。**场景、开场或完整角色说明可能自带秘密，工具不保证自动防剧透**；介绍是作者原文与基础宏展开，不是无来源的新故事。

## 2. 选开场并明确兼容处理

```sh
python tools/hermes_character.py prepare --card /private/card.png \
  --opening 1 --out /private/new-story-plan.json \
  --ack budget:UTF8_BYTE_ESTIMATE_NOT_MODEL_TOKENIZER
```

0 为默认开场，后续编号对应替代开场。逐项 review inspect.compatibility 的实际 ID，再用重复 `--ack` 接受已知兼容限制；上面的 ID 仅为示例，不是所有卡的通用完整报告。不能因为用户选择了开场就自动接受脚本/变量缺失。

明确同意暂停不支持条目时可用重复 `--disable-entry <编号>`；未知编号拒绝。`--lore-budget` 调整 UTF-8 字节估算预算，不代表目标模型 tokenizer。可选 `--user-name` 和 `--user-persona`；未提供独立 Persona 时保持卡片默认玩家前提。prepare 不覆盖已有输出，生成计划摘要用于安装重核。

## 3. 创建新 Profile 并统一安装

使用当前 Host 支持的命令先创建全新命名 Profile：

```sh
hermes profile create new-story --no-skills --no-alias
```

模型和凭据由 Hermes 管理；本工具不复制主 Profile 凭据。只对新 Profile 安装，不替换当前角色、主 Agent 或已有任务。默认主 Home 和已含聊天/任务/角色数据的目标均拒绝。

在能加载 Host YAML 依赖的受控管理环境执行：

```sh
python tools/hermes_character.py install \
  --plan /private/new-story-plan.json --expect-sha <prepare输出摘要> \
  --profile-home /home/user/.hermes/profiles/new-story \
  --source-home /home/user/.hermes \
  --root /home/user/life-engine-stories/new-story \
  --host-root /home/user/.hermes/hermes-agent \
  --tools-file /private/main-host-tool-names.json
```

配置继承只处理通用 toolsets、技能来源/禁用、工具展示模式与本插件启用，不迁移身份、历史、cron、MCP或凭据。许可清单应由管理者核对实际主 Host 能力后提供，执行时仍与本轮真实 schemas 取交集。本地角色绑定技能与旧桥接应排除。缺少 Host YAML 环境时停止，不下载依赖或 bootstrap Host。

安装创建独立 ROLEPLAY World、CharacterInstance 和冻结运行时，启用连续性及工具 sidecar。返回 INSTALLED 仅说明本地安装流程完成；必须另开 CLI 验证模型、工具、技能和跨会话记录，不能当成媒体生成或送达证明。

## 恢复与多故事

`.life-engine-onboarding.json` 记录 CONFIG/CARD/WORLD/CONTINUITY/CAPABILITIES/DONE 各阶段和回执，不包含卡正文或配置凭据。失败标记 FAILED_PARTIAL，保留现场；禁止覆盖重跑。配置恢复按 after-hash 门控，卡片恢复按签名 receipt；连续性数据不要盲删。强制终止可能留下专用 onboarding lock，确认没有导入进程后再按记录恢复。

退出目标 Profile 的聊天后，可以运行 `python tools/hermes_character.py recover-config --profile-home /home/user/.hermes/profiles/new-story` 恢复宿主配置。PREPARED 中断状态只允许配置匹配安装前或安装后摘要，且备份完整；发生用户修改时拒绝覆盖。这个命令不移除卡片、sidecar 或独立世界，卡片另用正式签名 receipt 回退。

换开场重玩应使用新的 Profile 与数据根，原故事可以继续；这版还不是同一 Profile 多存档切换界面。已有故事不会在每次新会话重播开场。当前 World 读取窗口和工具轮次跳过策略沿用 V2，媒体形象/声线、工具结果连续性与 Telegram 路由仍需后续接入。

源卡、故事介绍、开场、计划和运行记录都是私有资料，不要提交公共仓库。供 Hermes 调用的正式入口应固定到已审核代码快照，不指向会持续改动的开发分支。
