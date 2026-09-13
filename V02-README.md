# Life Engine v0.2 — 现有 Agent 配置引导版

让已有 Agent 增加连续状态、主动联系、精选记忆与可选照片，继续使用它原来的 SOUL、语气、称呼和模型配置。普通用户从引导开始，不需要手写 JSON。

解压后，在已经安装 Agent 的电脑上打开终端，进入本目录，运行：

    python setup.py

需要 Python 3.11 或更新版本；运行时无第三方依赖。macOS/Linux 如果没有 python 命令，使用 python3。Windows 可使用 py -3.11 setup.py，或已有的 Python 3.11+。这不是 pip 安装包。

## 引导会问什么

| 引导内容 | 如何处理已有 Agent |
| --- | --- |
| 选择 Agent | 发现常规 Hermes Profile，其他框架可手动指定 Agent 工作目录 |
| 读取人格信息 | SOUL 中明确的姓名字段仅作显示名建议；不推断性格、不上传原文 |
| 使用方式 | 工作助手按已记录的到期事项联系；陪伴角色可选择虚拟日常作息 |
| 联系节奏 | 主动联系开关、每天上限、安静时段、刚聊完后的间隔 |
| 精选记忆 | 控制是否记录经历和未完成话题 |
| 照片 | 默认关闭；开启后选择自己的 ComfyUI API 工作流和已确认的形象提示词 |
| 接入人格 | 默认独立能力文件；可选择在 SOUL 末尾追加一小段接入说明 |
| 安装前预览 | 展示能力选择、将写入的文件和实际 SOUL 接入片段 |

已有主配置和密钥文件不会被安装器改写，密钥文件的内容也不会被读取。它不会替所有角色套上“小雪”的名字、女性形象、衣着或咖啡店生活。

引导完成后可选择安装，或只保存预览。安装器自动备份它将修改的文件；如果预览后 SOUL 或配置被其他程序改动，它会停止并要求重新预览。重复安装会沿用当前扩展配置，接入说明也不会重复叠加。

## 指定已有 Agent

Hermes 独立 Profile 示例（实际目录以本机为准）：

    python setup.py --home "/你的路径/.hermes/profiles/xiaoxue" --adapter hermes

其他具备本地命令执行能力的 Agent：

    python setup.py --home "/你的Agent工作目录" --adapter generic

通用方式需要把生成的 INTEGRATION.md 接到该 Agent 的上下文，并由宿主负责定时器、入站消息和投递。此版本没有声明原生支持 OpenClaw 的事件钩子，也不会自动调整其配置。远程容器或 SSH 工具后端需要把本扩展装到命令实际运行的环境，或提供正确的挂载路径。

## 安装之后

假设所选目录为 AGENT_HOME，内部代号为 xiaoxue，扩展会位于：

    AGENT_HOME/life-engine/life.py
    AGENT_HOME/life-engine/agents/xiaoxue/agent.json
    AGENT_HOME/life-engine/agents/xiaoxue/INTEGRATION.md
    AGENT_HOME/life-engine/agents/xiaoxue/SCHEDULE.md

Hermes 接入还会生成该 Profile 专属的 life-engine-xiaoxue Skill。每个宿主 Profile 只绑定一个 Life Engine Agent；其他角色使用自己的 Profile/工作目录，因此不会混用 SOUL。配置、数据库和图片按 Agent 分目录保存，数据库也会校验自身所属 Agent。此隔离避免程序串用数据，不是操作系统级访问隔离。

先看当前状态、检查本地接入，再用隔离数据模拟一天：

    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue status
    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue doctor
    python "AGENT_HOME/life-engine/life.py" --agent xiaoxue simulate --day 2026-09-13

模拟不会发送消息、不会出图，也不会修改正式数据库。工作模式的模拟中没有真实到期事项，因此没有主动联系是正常结果。

SCHEDULE.md 包含为当前 Agent 生成的定时任务配置。用宿主 Agent 先检查旧任务，再创建暂停状态的新任务，选定自己的实际聊天目标并完成一次文字/原生图片测试后启用。安装器只准备本地接入文件，当前聊天也没有访问或配置你的本机 Agent。

## 人格和设置的优先关系

现有 SOUL 负责身份、语气、关系边界及禁止事项；Life Engine 配置只负责新增行为的参数。display_name 和 owner_label 是引导中的显示/对照信息，角色实际称呼仍以 SOUL 为准。两边冲突时，接入说明要求 Agent 遵循原规则。

检测器只识别少量明确的姓名字段和“不要主动”类关键词，不能保证理解所有自然语言冲突。它不会自动“修正”SOUL。想修改人格时，应在原 Agent 中调整人格；想调整频率或照片开关时，再次运行引导即可。

同一天已经确定的联系窗口和视觉状态保留到当天结束，避免重新设置后立刻重排、换装。安静时段、主动开关和次数上限会立即用于后续判断。

## 稳定运行需要的两处接线

Hermes Skill/SOUL 的集成方式是要求模型在收到用户消息时执行 observe。它尚未注册框架级入站回调，模型漏调用时，“最近聊过”的判断就可能滞后。需要严格捕获每条消息的部署，应让宿主真实的入站回调调用 observe。

宿主发送完消息后，本版本没有自动接收发送回执。prepare 只表示内容已准备好，不能证明送达；有真实平台回执时才能执行 ack。发生超时也不会自动重发，以减少重复消息。SQLite 的原子领取只保护本地决定，不是外部消息恰好一次投递的保证。

## 更多使用说明

照片、记忆、回滚、v0.1 迁移和非交互部署见 docs/OPERATIONS.md。example 配置位于 examples/；源码与验证记录位于 runtime/、tests/ 和 docs/VALIDATION.md。
