# 给本机 Hermes / OpenClaw 的接入任务

## 当前模式门禁（先读）

**A. Soul Continuity / Living Agent Host Sandbox：可以继续受控测试。** 使用独立测试 Profile/Agent、Life Engine 实例和 Host Session，只向本人测试聊天目标发送；照片可关闭。先按 [Host 沙箱测试指南](docs/HOST-SANDBOX-TESTING.md)记录版本、绑定与停止门，再执行下面的安装和接入步骤。

**B. Full Private RP：当前停止，不得生产启用。** Core Roleplay Runtime 已完成，不等于真实 Host 已通过最终输出、历史隔离、晚到响应和流式发送安全门。Hermes experimental compatibility fork PR #1 只是实验审计证据，不能作为生产安全依据；OpenClaw 即使有 `before_message_write`、`before_agent_finalize`、`message_sending`，也没有已证明的统一 fail-closed final-output commit 授权。不得凭插件加载成功或 prompt 指令绕过此门禁。

首次真实接入默认使用空的测试 Session，不复制生产私密聊天历史，不修改原 Soul 或主模型，不开放 Full RP。若无法确认独立身份、数据目录或本人发送目标，先停止接入并报告。

用户把本目录交给你，是希望在当前 Agent 上安装并接通 Life Engine。请先读取 README.md 和 docs/OPERATIONS.md，查看 setup.py --help，再使用真实本机环境操作。安装包不包含用户的模型密钥、照片工作流或聊天目标。

识别当前宿主、版本、实际 Profile/workspace、运行用户和执行环境；OpenClaw 还需核对真实 agentId 及其所属配置/Gateway，不能默认所有工作区都属于 main。保留原有 SOUL、IDENTITY、USER、模型、密钥和已有的插件配置。

把 Life Engine 永久目录放在宿主源码、工作目录和解压目录之外。容器部署先核对持久卷与容器内路径，保证网关进程能运行独立的 Python 3.11+ 并访问固定入口。ComfyUI 无需与引擎共用 Python 环境。

若发现 v0.2 已安装，核对并暂停旧任务，停止旧 Skill/接入指针指向的运行入口，只处理 Life Engine 自己生成的内容并留备份；保留原有角色设定。之后使用 --import-v02 与 --legacy-stopped 复制迁移。若已安装 v0.3，复用原永久目录和实例，升级程序走 upgrade，修改角色参数才使用 --reconfigure，不要创建一份空角色数据替代已有数据。

根据现有设定补齐必要配置；不确定的用户偏好在聊天中问用户。使用 --answers 非交互生成预览，--home 指向真实 Agent 目录，OpenClaw 加 --host-agent-id。预览文件放在 Agent 与永久目录之外。核对预览后 --apply-plan 应用；不要把命令中展示的“示例目录”直接照抄。

生成的 INSTALL.md 记录这个实例的固定路径、插件和工具名。通过永久目录/manage.py connect 调用原生插件管理命令，按宿主规定完成来源审查；遇到阻止时说明具体原生命令及其原因，不得关闭扫描、执行策略或覆盖整个 allowlist。仅添加本插件所需的加载/上下文许可。OpenClaw 的 --host-profile、OPENCLAW_CONFIG_PATH 必须与已识别的 Gateway 一致。

根据本机版本在**已选测试 Host**中重载插件；不得为首次沙箱测试擅自重启生产 Gateway。实际调用测试实例的 status 工具，发一条普通主人消息，核对 manage.py doctor 是否记录了 last_prompt_hook_at。只有主人渠道/sender ID 有明确匹配依据时启用自动入站时间记录；缺少时如实说明，不要声称所有消息均已捕获。

仅在测试绑定和静默行为验证通过后，才按 INSTALL.md 用宿主原生接口建立/复用一个稳定名称的每 23 分钟**测试任务**，绑定实际测试 Agent、账号、渠道和用户明确指定的本人聊天目标。不要使用全渠道或默认 last 路由来猜目标，也不要直接修改宿主的任务数据库。先做隔离 simulate 和静默验证；真实文字/图片测试仅发送到用户已经指定的本人对话。验证后启用这一套测试任务并记录任务 ID。

照片读取用户现有 ComfyUI 身份工作流；缺失时保持照片关闭并完成其余步骤。发图必须是 photo 返回的真实文件，使用宿主原生媒体。直接发送与自动投递避免重复；只根据真实回执记录 ack，不能把工具生成文本当成已送达。

检查宿主已有的开机服务和持久化任务，在相同运行用户/配置下设置必要的自动启动，避免重复服务。Life Engine 无需独立守护进程。已有服务被外部 supervisor 管理时沿用它。升级宿主后用真实工具调用和静默运行验证加载；不能仅凭插件列表判断在线进程可用。

完成时告诉用户实际永久路径、绑定 Agent、真实任务 ID、照片状态和验证结果；把仍未接通的部分明确列入本机接入记录，不能用“安装成功”替代聊天与图片实测。
