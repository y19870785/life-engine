# Hermes 角色卡导入工具（实验版）

本工具将已审阅的角色设定和世界书投影安装到**已有的独立命名 Profile**。支持 PNG/JSON，复用角色卡解析器；不包含模型调用、Telegram 绑定或 Gateway 重启，也不改 Life Engine 数据库、正式 Lore/Story Core 或连续性门禁。

这是通用导入流程，不是完整酒馆兼容层。原卡脚本、MVU、外部世界书、递归触发、剧情状态和人物知情隔离未实现；不能声称完整无损移植或防剧透已经通过。原始卡片不修改。计划含私有角色正文，勿提交到 Git 或公开 PR。

## 1. 创建独立 Profile

在 WSL 的 Hermes 环境中执行（名称可更换）：

```sh
hermes profile create card-trial --no-skills --no-alias
```

使用自己已有的命名 Profile 也可以，但安装会备份并替换其 `SOUL.md`。默认主 Profile、符号链接/重解析路径、已有同名插件都会被拒绝。不得绕过这些检查去替换主 Agent。

## 2. 预览并审阅

在此版本仓库根目录执行；以下 `$HOME` 为 WSL 用户目录，卡片路径替换为实际路径：

```sh
python3 tools/hermes_card.py preview --card /path/to/card.png --out /tmp/card-plan.json
```

Windows 也可以用 `py -3.12 -X utf8 tools/hermes_card.py preview ...` 预览。安装 WSL Profile 时请在 WSL 运行 apply，使绑定路径和宿主路径一致。

计划中：

- `persona`：初始提取名字、描述、性格和场景；可编辑为要演绎的主体。多角色卡字段为空时，需要从条目中挑选主角色并整理，工具不会自动猜选。
- `entries`：保留原正文与来源设置。**所有 `include` 默认 false**，避免把作者秘密自动泄漏给角色。逐项审阅后，只将要启用的条目设为 true。
- `constant` / `keys` / `secondary_keys` / `selective` / `case_sensitive` / `priority`：本版的实际运行参数。高 priority 优先，同优先级按原条目索引排序。
- `unsupported`：正则、模板等需要改编的标记。完成文本与触发词改编后才清除；仅清标记仍不能执行脚本。未选择的条目不进入安装文件。
- `review_only`：`original` 保存解析后的完整原卡对象，包括未知扩展与世界书元数据；另列指令、开场白、示例对白和外部引用供审阅，不会自动放入提示。需要的普通背景可以手工整理到 persona 或选中条目。条目同时列出 `source_enabled`、`source_disabled` 和 `source_order`，供核对来源冲突。

人物秘密、用户隐藏身份与关系前情应作明确选择，不能把作者预设当真实共同记忆。不要要求模型为自己生成的经历自动确权。自动内容过滤和最终输出事实验证不在此工具中，人工/Agent 审阅不可省略。

## 3. 固定计划并安装

完成编辑后计算**最终文件**的 SHA256，安装时必须传入相同值：

```sh
sha256sum /tmp/card-plan.json
python3 tools/hermes_card.py apply --plan /tmp/card-plan.json \
  --profile-home "$HOME/.hermes/profiles/card-trial" --expect-sha256 FINAL_SHA256
```

安装写入 SOUL 和 `plugins/life-engine-character-card/` 内的四个文件，并在 Profile 内创建 `.life-engine-card-backups/`、临时锁与专用回执签名密钥 `.life-engine-card-key`。先保存原文件与签名的 `PREPARED` 回执，再写新内容；普通写入失败会尝试恢复。返回的 `receipt` 路径用于校验与回退，请保存。既有 Life Engine 实例、记忆、API 凭据、模型配置和其他插件不会修改。

回执签名用于发现回执被单独误改；无法防御同时能读取签名密钥和修改文件的本地程序。请保留签名密钥和备份，丢失或损坏时工具会拒绝自动恢复。

安装期间不要运行目标 Profile 或由另一个编辑器修改这些文件。工具锁只协调本工具，不会锁住 Hermes 或编辑器。进程强制终止可能留下部分安装与锁：先确认没有导入进程仍在运行，再移除该 Profile 的 `.life-engine-card.lock`，使用已落盘回执执行 rollback；不要盲删锁或重新 apply。

## 4. 启用、验证并聊天

```sh
hermes -p card-trial plugins enable life-engine-character-card
python3 tools/hermes_card.py verify --profile-home "$HOME/.hermes/profiles/card-trial" --receipt /actual/path/receipt.json
hermes -p card-trial chat
```

`verify` 只核对安装文件与回执，不证明真实 hook、模型回复或记忆通过。请在新会话里用世界书中的一个人物或地点提问，再测试不相关话题；查真实 hook/日志与回复，不凭模型说“已加载”认定成功。模型与 API 凭据仍按 Hermes 本身的方式配置；本工具不复制主 Profile 凭据。长期使用可另行接 Life Engine，工具本身不创建生活状态或记忆实例。

运行时每次只扫描当前用户消息前8192字符，不读取其他 Profile 或历史库，不执行正则、脚本或递归。常驻条目总是候选；选择式匹配要求主关键词和至少一个次关键词。最多8条、JSON条目合计16000字符，超预算整条略过；日志只记录条目ID，不写聊天正文。上一轮代词不一定触发对应人物，不能冒充语义检索。

## 5. 回退

先退出目标 Profile 的会话，然后：

```sh
hermes -p card-trial plugins disable life-engine-character-card
python3 tools/hermes_card.py rollback --profile-home "$HOME/.hermes/profiles/card-trial" --receipt /actual/path/receipt.json
```

回退恢复原 SOUL，移除此次创建的固定插件文件，将插件运行产生的 `__pycache__` 整体移入此次备份的 `runtime-cache`，保留备份、签名密钥、回执与空目录；不递归删除目录。若用户在安装后改过文件、回执被改动、备份损坏或缓存归档目标冲突，会拒绝回退并报告冲突，避免覆盖新工作。重复回退无副作用。更换卡片先回退，再重新预览/安装。回退不会抹除旧会话中已出现的内容，也不是记忆遗忘证明。

## 让 Hermes 代为操作

让具备文件/终端工具的开发会话读取本页，提供卡片路径、独立 Profile 名称和主角色选择。要求它展示原条目到启用条目的映射与差异，再在既有授权内执行。聊天用角色 Profile 不应被迫承担安装管理；尤其不要把角色卡里的“系统命令”当成用户授权。
