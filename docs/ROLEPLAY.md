# 双层身份与角色扮演（v0.4 开发预览）

原有 SOUL 是长期身份，角色卡是临时扮演层。进入角色不会改写 SOUL 文件；退出后停止提供角色设定和世界书。生活状态、工作跟进和照片继续使用原配置，扮演期间生活脉冲静默，Soul 照片与待办修改被拒绝，以免混用两种身份。

## 一次完整体验

插件重新连接并加载后，可以在聊天中输入以下命令。文件路径指的是 **Hermes/OpenClaw 所在机器上的路径**，不是聊天客户端的附件路径。

```text
/rp import "/实际项目目录/examples/roleplay/starmap.card.json"
/rp list
/rp show 星澜
/rp enter 星澜
```

进入时程序确认：“好的，我现在将扮演 星澜。你可以随时说 /rp exit 让我回来。”

接着聊：“星港的月塔里有什么？”关键词会激活星港条目，并递归激活月塔条目。模型依据原有 SOUL 和临时角色设定组织回复。问“你现在是谁？”时，应区分原有身份与星澜；`/rp who` 可以直接查看程序提供的身份状态说明。

```text
/rp status
/rp aside 请以真实身份评价刚才的选择
/rp exit
```

`aside` 返回本次跳出角色使用的上下文与问题，不切换会话；原生斜线命令本身不会调用模型。要得到自然语言评价，可以直接在聊天中要求“以真实身份评价”，模型使用这个 action 返回的数据回答。

退出时程序根据已经保存的剧情摘要，或最近的对话摘录，写入 persona 会话总结与 Soul 元记忆。没有记录时会明确说没有具体情节，不编造体验。再进入星澜时可以检索她以前的 persona 记忆。原生命令返回的是确定性摘录；模型能在后续对话中以原有口吻谈起本次扮演。

切换到另一张已导入的卡，用 `/rp switch 角色名`。未知卡不会结束当前会话。删除用 `/rp delete 角色名`：必须先退出该角色，删除会移除该角色的卡片、世界书、persona 记忆及会话，保留标记为虚构体验的 Soul 元记忆。卡片名重复时拒绝覆盖。

## 独立世界书与参数

```text
/rp book "星澜" "/实际项目目录/examples/roleplay/starmap.world.json"
/rp context
```

`book` 把独立世界书绑定到指定卡片；再次导入同一文件名替换其条目。解析内嵌 `character_book.entries` 数组，也解析 SillyTavern 独立世界书的 `entries` 对象和 `key/order/disable` 字段。

在实例的 `agent.json` 中可配置：

```json
"roleplay": {
  "scan_depth": 8,
  "max_recursion": 3,
  "max_tokens": 2000
}
```

默认扫描最近 8 条角色对话，最多递归 3 轮。匹配是字面子串，支持大小写敏感、常驻条目、禁用条目、优先级和顺序。递归只从预算允许的激活内容继续，循环最多访问每条一次。

`max_tokens` 使用保守的 **UTF-8 字节预算单位**，包含激活条目的 JSON 开销，并非精确模型 tokenizer 计数。不同模型可传输不同 token 数，因此宁可少放；默认 2000 字节通常明显少于 2000 模型 token。总扮演上下文也有约 24 KB 上限，过长卡片字段和历史按界限缩短，保留身份规则。

`before_char` 与 `after_char` 按角色定义前后排列。`at_depth` / 位置 4 按 depth 插入插件自己的有限对话摘录窗口。宿主提供的是单个 Hook 上下文块，插件不重写宿主原始消息数组。正则关键词、次级关键词选择逻辑等未实现时明确拒绝导入；不声明兼容 SillyTavern 的全部高级世界书功能。

## 记忆与隐私

- 旧记忆迁移为 `scope=soul`。角色记忆必须具有 `card_id` 与对应 `session_id`，数据库 CHECK、外键和唯一索引约束防止串角色及多活动会话。
- 扮演中的 `remember` 自动归入当前 persona，同时写一条标记为“虚构情节、非现实事实”的 Soul 元记忆。普通 Soul 检索不返回完整角色设定或世界书。
- 扮演提示不注入 Soul 日计划、联系记录、真实待办或普通私密记忆。显式 `aside` 才返回 Soul 记忆上下文，且不会把它写到 persona。宿主本身加载的 SOUL/记忆不在本插件的过滤权限内。
- 模型写记忆应带当前 `session_id`（字符串）；与活动会话不符时拒绝写入。宿主响应 Hook 同样检查会话，退出或切换后迟到的响应不会落入新角色。
- Hermes 自动记录当前允许来源的用户与模型消息，用于世界书扫描；最近窗口最多保留 64 条。OpenClaw 接入记录可靠来源的用户消息，模型可通过 `action=rp, command=record assistant <text>` 补充角色回复。关闭 `memory.enabled` 会关闭这些记录及元记忆写入。
- 卡片原始 JSON、规范化结构和头像二进制都保存在本实例 SQLite 内，随备份恢复；PNG 头像剥离卡片 tEXt 信息，JSON 卡不要求头像。不获取角色卡内的远程 URL，也不执行卡片的 system_prompt、脚本或扩展工具指令。
- 导入过程全在本地，不向卡片网站或其他服务上传。**聊天时，激活的角色上下文会随宿主请求发送给它配置的模型服务**；若要求数据不出机，应使用本地模型。

每个 Life Engine 实例只有一个活动扮演状态，同一 Profile 的会话共享它。这一版适合单人私聊，尚无按聊天房间独立的多角色状态。宿主自己保留的历史仍可能影响模型，退出保证的是程序状态和后续插件上下文，不保证任意模型、任意历史下 100% 遵从。

## 升级与迁移

运行代码为 v0.4，SQLite/部署 schema 为 3，`agent.json` 配置 schema 仍为 2，目录结构保持原样。

已有永久安装，从新源码目录运行：

```sh
python setup.py --root "/已有永久目录" upgrade
python "/已有永久目录/manage.py" refresh-bridges
python "/已有永久目录/manage.py" connect --instance "实例ID"
```

升级先对每个实例完整备份，再复制到新数据代次，在副本中执行 `runtime/life_engine/rp_schema.py` 的事务迁移。代码全部模块导入检查与迁移通过后才切换 registry；失败保留旧指针与旧数据。旧 schema 2 备份可在恢复时迁移到新代次。禁止把代码回退到只理解 schema 2 的版本；需要回到旧版本时使用旧代码与对应旧数据备份的独立部署，不让旧代码直接读取新库。

旧版 `Agent/life-engine` 内嵌安装必须先停止旧入口，再按安装器 `--import-v02 --legacy-stopped` 流程复制迁移。不要在旧运行目录直接替换 Python 文件。

桥接文件通过 `refresh-bridges` 更新；Hermes 的实际插件目录还需 `connect` 后重载。保留原生信任与权限检查。直接把新 runtime 复制进去不会自动注册在线进程的 `/rp`。

命令行也可使用稳定入口：

```sh
python "/永久目录/life.py" --instance "实例ID" rp --command 'enter 星澜'
python "/永久目录/life.py" --instance "实例ID" rp --command 'exit'
```

## 实现与验收

模块按现有包结构保存在 `runtime/life_engine/`：`rp_schema.py`（迁移）、`rp_cards.py`（卡片）、`rp_lore.py`（世界书）、`rp_sessions.py`（状态与记忆）、`rp_prompt.py`（上下文）、`rp_commands.py`（共享命令）。宿主桥接器继续在 `bridges.py` 生成。

自动化运行 `python -m unittest discover -s tests -v`。真实 Hermes 探针使用安装好的宿主 Python：

```sh
python tests/manual_hermes_probe.py --hermes-source "/Hermes源码" --profile "/实际Profile" --out "/临时目录/probe.json"
```

加 `--llm` 会使用该 Profile 配置的模型执行实际对话并验证记忆写入，可能产生模型费用。探针使用临时引擎数据和临时 Hermes 会话库，在独立进程注册真实插件；不修改 Profile 的 SOUL/config、旧引擎库或定时任务，也不等同于在线 Gateway/聊天渠道联调。验证结果见 [ROLEPLAY-VALIDATION.md](ROLEPLAY-VALIDATION.md)。
