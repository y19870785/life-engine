# 配置与运行

## 预览、应用和回滚

引导将可审阅安装方案写入当前目录，不改 Agent，直到你在终端选择安装或显式运行：

    python setup.py --apply-plan "/路径/life-engine-plan-xiaoxue.json"

方案里包含准备写入的文件内容。如果选择追加 SOUL，方案和备份会包含 SOUL 原文，请作为本地私人文件保留，不要把它当成公共模板分享。

每次应用成功会输出一个 journal.json 路径。它对应这次具体安装的备份，回滚命令为：

    python setup.py --rollback "/路径/Agent/life-engine/backups/安装ID/journal.json"

回滚按最新一次安装开始倒序操作。若安装后又改过受影响的文件，自动回滚会停止，保留后续改动。回滚配置不会删除期间新增的状态库或照片；需要重新接入时可以继续使用它们。回滚前在宿主中停用相关定时任务，避免它调用已撤回的代码。

预览与应用之间、应用与回滚之间均检查文件摘要；单个文件使用原子替换，并为可捕获的写入异常恢复已写文件。断电或进程被强制杀死可能留下 applying 状态的 journal；此时应检查对应备份，不能把一次未结束安装当作完整成功。

## 不同用户复用同一个发行包

examples/companion.answers.json 展示一个不改变原有人格的陪伴接入；examples/work-assistant.answers.json 展示仅按事实跟进的工作助手。把内部代号改成自己的，再生成预览：

    python setup.py --home "/实际Profile路径" --adapter hermes --answers examples/companion.answers.json --out "/预览目录/plan.json"

加上 --apply 会应用这组已明确指定的设置。普通使用推荐运行交互式引导。

配置采用 JSON，目的是不要求用户另装 YAML 解析依赖；引导会完成常规编辑。新增 Agent 的可变项都在 agent.json，内核没有固定的人名、发型或衣着。新增图像服务需要实现一个 provider，目前实际实现的是 ComfyUI。

## 照片和虚拟日常

在引导中启用照片之前，准备自己已验证的 ComfyUI API JSON。普通 UI 工作流不是 API 图；不能只把扩展名改成 JSON。把希望自动注入的节点值改成下表中的标记：

| 标记 | 用途 |
| --- | --- |
| {{POSITIVE_PROMPT}} | 正向文本，必需 |
| {{NEGATIVE_PROMPT}} | 负向文本，可选 |
| {{SEED}} | 整数随机种子，可选 |
| {{WIDTH}} / {{HEIGHT}} | 整数图片尺寸，可选 |

你的模型加载、LoRA、身份参考和输出节点保留在原图中。包内 graph-shape.example.json 仅说明 API 输入结构，不是一份能直接出图的模型工作流。姓名和一段文字不能保证同脸，身份一致性由原工作流负责并需目视验证。

先在引导里选中照片，再测试：

    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue photo --dry-run
    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue doctor --network
    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue photo --kind selfie

ComfyUI 的地址可以是同机回环地址或可信局域网地址。结果通过 /prompt 排队、/history 查询、/view 下载。未安装模型、身份节点不兼容和真实 GPU 性能不在本地模拟测试覆盖范围内。

每天的照片上限统计“尝试”，失败/结果未知的尝试也占额度；这避免网络不稳定导致反复排 GPU 任务。同一主动联系的照片再次请求会复用已就绪图片，结果未知则要求先查看 ComfyUI 队列。图片路径含空格时返回带引号的 MEDIA 标记；最终回复中应把该标记独立成行，不包裹加粗或追加标点，仍需在实际渠道验收。

默认 companion 不生成服装或发型。要加入自己的设定，在 world.visual_options 添加选项，例如：

    "visual_options": {
      "outfit": ["your existing outfit A", "your existing outfit B"],
      "hair": ["your established hairstyle"]
    }

一旦选定，它们在当天保持不变。routine 每个时间段可通过 visual 对这些值做明确覆盖，例如晚间换衣。你没有选择作息示例、也没有填写活动时，引擎只返回时间和已记录上下文，不会凭空添加生活情节。

## 主动联系与记录

手动记录接收到的用户消息（框架有消息 ID 时传 --event-key 防重复）：

    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue observe --summary "用户回来继续聊今天的工作" --event-key "实际消息ID"

精选记忆和未完成话题：

    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue remember --summary "用户希望偶尔发生活细节" --kind preference
    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue loop-add --topic "明天跟进用户的实际事项" --due "2026-09-14T10:00:00+08:00"
    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue loop-close --id 1 --resolution "已实际跟进"

工作模式必须有已记录、带时间且已到期的未完成事项才可能主动联系。联系还需命中候选窗口并通过上限、安静时段和聊天冷却条件，因此不用于精确到分钟的重要提醒。关闭 memory 后不再提供既有精选记忆与话题，observe 仅保存联系时间和可选去重键，不保留摘要；已有数据不会被删除。

临时暂停/恢复：

    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue pause
    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue resume

resume 只解除运行时暂停，不能绕过 agent.json 中关闭的 social.enabled。

## 从小雪 v0.1 迁移

先在引导中创建新 Agent，停用旧版定时任务，再执行：

    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue migrate-v01 --source "/旧版/data/xiaoxue-life/life.db"

迁移按只读方式打开旧库，生成完整数据库快照，把历史用户联系、精选记忆、未完成话题和主动联系尝试导入新库。重复运行同一来源不会重复导入。旧版的 sent 记录没有真正投递回执，新版按 unknown 保留。

v0.1 的旧日程与照片元数据保留在 legacy-v01.snapshot.db 中，不混入新配置的当天日程；旧照片文件仍在原目录，不会随数据库快照复制。不要因此删除旧数据目录。迁移异常时会停止，不自动覆盖已有快照；保留快照后检查再处理。

## 接入依据

Hermes 的 Profile 使用独立 home 保存 SOUL、设置、Skills 和任务，工作目录与 Profile 不一定相同，因此生成的接入命令绑定到选定目录：
https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/profiles.md

Hermes Skills 的目录/说明格式：
https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/creating-skills.md

Cron 的暂停创建、附加 Skill、自动投递和 [SILENT] 约定：
https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/cron.md

ComfyUI 官方 Python API 示例：
https://github.com/Comfy-Org/ComfyUI/blob/master/script_examples/websockets_api_example.py

实现按 2026-09-12 可检索官方资料编写，宿主 API 的具体可用性仍应通过本机版本、技能调用和真实渠道验证。
