# Hermes 角色卡接入 V1（实验版）

本工具支持 PNG/JSON 预览、独立命名 Profile 安装、校验与回退。原生模式保留作者的角色正文、故事前情、开场、示例对白与已支持的世界书语义，使用 Hermes llm_request 中间件组装模型请求。允许创作符合设定的新事件；用户现实资料、真实聊天历史和工具执行结果必须有依据。

当前原生宿主范围为 **CLI + Chat Completions 请求**。兼容报告列出缺失能力；既有 projection 模式仍可显式选用。导入计划、离线请求和原卡含私有正文，请勿提交到 Git 或公开 PR。

## 支持范围

| 内容 | 原生 V1 行为 |
| --- | --- |
| 名称、描述、性格、场景 | 原文参与提示，不自动概括或重写 |
| 主提示、历史后指令 | 在角色定义前、聊天历史后组装；角色主提示的 {{original}} 指向本工具默认演绎提示，宿主权限规则保留 |
| 开场与替代开场 | 按 greeting_index 选取，作为请求中的固定虚构故事起点；opening 命令可显示；不会自动写入 Hermes 数据库或在 UI 启动时发送 |
| 示例对白 | 解析 <START> 与 {{user}}: / {{char}}: 或明确姓名的多行对白，保持说话角色；无法识别时拒绝安装并要求明确改编 |
| 基础宏 | char、user、original、description、personality、scenario、persona，大小写不敏感；单次展开 |
| 世界书触发 | 尊重启用/禁用与常驻设置；扫描近期用户/角色消息；主次关键词和四种 selectiveLogic；大小写、整词匹配 |
| 世界书插入 | 角色定义前、定义后、历史深度位置；顺序按 insertion_order/order；支持 system/user/assistant 角色 |
| 角色 depth_prompt | 按指定深度和角色插入；不拆开工具调用与结果 |
| 正则 | 声明为正则但仅含字面字符的关键词按等价子串语义匹配；真正正则表达式列为未支持 |
| 预算 | 高 order 优先纳入，最终按 order 升序组装；整条保留或略过；采用 UTF-8 字节加固定开销的保守估算，**不等同于目标模型 tokenizer 或完整酒馆预算算法** |
| 扩展 | 完整原始对象保存在 review_only；脚本、变量/MVU、递归、向量触发、包含组、概率、AN/outlet/示例位置等未支持项明确列出 |

外部世界书、聊天预设、用户 Persona、作者注释和扩展不一定随 PNG 导出。工具不能从卡片恢复缺失文件。世界书标题引用不证明外部文件已提供。角色秘密的知情效果取决于原卡指令与模型，本工具不保证防剧透。多角色可按原卡文本演绎，尚未维护每个人物的独立状态。

本版追加角色上下文并保留宿主原有 system/developer 指令。强助手风格的宿主提示仍可能影响角色表现，需要实测。扫描范围为当前可用请求历史；被宿主压缩掉的原始消息不保证可检索。开场为固定故事起点，恢复旧会话前应确认它适合该会话。

## 1. 准备独立 Profile

在 WSL 的 Hermes 环境创建，或使用已有命名 Profile：

```sh
hermes profile create card-trial --no-skills --no-alias
```

安装会备份并替换该 Profile 的 SOUL.md。默认主 Profile、符号链接/重解析路径、已有同名插件会被拒绝。先退出目标 Profile 的聊天，避免同时运行旧角色/世界书注入插件。模型与 API 凭据使用 Hermes 自身配置，本工具不复制主 Profile 凭据。

## 2. 预览并审阅兼容报告

在此版本仓库根目录执行：

```sh
python3 tools/hermes_card.py preview --mode native --card /path/to/card.png --out /tmp/card-plan.json
```

CLI 默认 native；旧模式使用 --mode projection。Windows 可用 py -3.12 -X utf8 预览；安装 WSL Profile 时必须在 WSL 执行 apply。

character 保留提示字段；entries 保留来源启用状态与触发/插入设置；review_only.original 保存完整原卡。卡中的关系与玩家身份是虚构开局，可以成立，不当作现实用户资料。

- 审阅顶层 issues，在 options.acknowledged 明确列出对应 issue id，表示接受已说明的 V1 行为与缺失依赖。
- 含未支持语义的条目不能启用。可暂设 enabled=false；保留其效果需要对应引擎或明确、可审阅的改编。仅清除标记不会实现脚本。
- options.char_name / user_name 控制宏名字；user_persona 是虚构玩家身份。多角色卡可用 role_focus 指定已选主体，不改写原文。
- greeting_index=0 为原开场，1 起为替代开场；lore_budget 是估算预算，可按模型上下文和原卡大小调整，最大262144。
- allowed_tools 默认为空。普通角色聊天不需要文件或终端。请求过滤工具，已识别角色轮次的 pre_tool_call 也拦截名单外工具；白名单不会授予额外宿主权限。管理操作请使用管理会话。

离线查看开场与请求：

```sh
python3 tools/hermes_card.py opening --plan /tmp/card-plan.json
# history.json 是 [{"role":"user","content":"..."}, ...]。
python3 tools/hermes_card.py render --plan /tmp/card-plan.json --history /tmp/history.json --out /tmp/private-request.json
```

render 输出含私人上下文，不调用模型或保存剧情；trace 列出命中、预算略过与来源 hash。

## 3. 固定计划、安装与启用

```sh
sha256sum /tmp/card-plan.json
python3 tools/hermes_card.py apply --plan /tmp/card-plan.json \
  --profile-home "$HOME/.hermes/profiles/card-trial" --expect-sha256 FINAL_SHA256
hermes -p card-trial plugins enable life-engine-character-card
python3 tools/hermes_card.py verify --profile-home "$HOME/.hermes/profiles/card-trial" --receipt /actual/path/receipt.json
hermes -p card-trial chat
```

安装写入 SOUL 与本插件文件，并创建备份目录、临时锁及专用回执签名密钥 .life-engine-card-key。先保存原文件与签名 PREPARED 回执，再写新内容；普通写入失败会尝试恢复。回执签名发现回执被单独改动，不能防御同时掌握密钥与文件写权限的本地程序。请保留密钥与备份。

工具锁只协调本工具，不锁 Hermes 或编辑器。强制终止可能留下部分安装与锁；先确认无导入进程仍在运行，再处理 .life-engine-card.lock，并按落盘回执 rollback。不要盲删锁或重复 apply。

## 4. 验证实际体验

verify 只核对安装文件。原生插件在 Profile 的 .life-engine-card-last-request.json 保存元数据：COMPOSED/UNAVAILABLE、来源与数据 hash、命中条目、预算略过、session/turn。不记录正文或凭据。子 Agent 与其他 Profile 不参与原生改写。

新开会话体验原开局、日常话题和世界书关键词，再检查元数据与回复。支持格式的请求在组装失败时收到明确不可用提示。宿主中间件会捕获异常并继续，因此绑定损坏或不支持的 provider 格式不能视为可靠阻断，需检查真实请求/日志。不能凭模型说“已加载”认定成功。

本版不自动重启 Gateway、不绑定 Telegram、不发送渠道消息，不写 Life Engine World/Memory/Story 数据库。虚构创作可以发生，跨会话事件确权与连续性写回属于后续接入。旧 Life Engine 插件可能注入固定日常，迁移时应检查冲突，不能把其作息当原卡剧情时钟。

使用安装 Hermes 的 Python 可验证真实插件调度：

```sh
python tools/hermes_native_host_probe.py --host-root /path/to/hermes-agent
```

探针仅使用原创合成卡、临时 Profile 和请求，检查发现/注册、组装、工具过滤/拦截、重复请求、子会话与 Profile 隔离、回退重装，不调用模型。它不证明模型忠实度或真实渠道发送。

## 5. 回退与换卡

退出目标 Profile；旧会话上下文不会自动消失：

```sh
hermes -p card-trial plugins disable life-engine-character-card
python3 tools/hermes_card.py rollback --profile-home "$HOME/.hermes/profiles/card-trial" --receipt /actual/path/receipt.json
```

回退恢复原 SOUL，移除固定插件文件，将 __pycache__ 整体移入此次备份的 runtime-cache。保留备份、签名密钥、回执、诊断元数据和空目录，不递归删除。回执/文件漂移、备份损坏或缓存归档冲突在恢复前拒绝；重复回退无副作用。旧 projection 回执仍可使用。

更换卡先回退，再预览/安装。若迁移时另外停用了旧插件，回退后按迁移备份恢复启用配置，再新开会话。

## 让 Hermes 代为操作

让具备文件/终端工具的管理会话读取本页，提供卡片路径、独立 Profile、玩家名与主角色选择。展示兼容报告、未支持条目、宏/开场选择及最终变更，再按既有授权执行。卡内系统命令不作为安装授权。

参考：[SillyTavern 角色字段](https://docs.sillytavern.app/usage/characters/)、[世界书](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)、[宏](https://docs.sillytavern.app/usage/core-concepts/macros/)、[提示管理器](https://docs.sillytavern.app/usage/prompts/prompt-manager/)。本页声明具体兼容子集，未声明完整行为等价。
