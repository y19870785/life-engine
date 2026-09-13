# 接口来源

于 2026-09-13 读取下列官方仓库文档和公开接口代码。原生插件 API 可能随宿主版本变化，本包没有用源码 HEAD 代替真实宿主联调，也没有声明一个未经测试的全版本兼容范围。

Hermes 的用户插件目录、显式启用与工具注册依据 [Plugins](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/plugins.md)。Profile 作用域与 PluginContext 依据 [hermes_cli/plugins.py](https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/plugins.py)。每轮 pre_llm_call 的上下文返回值、sender_id/platform 参数及回调失败语义依据 [Event Hooks](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/hooks.md)。原生周期任务及静默输出依据 [Cron](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/cron.md)。

OpenClaw 的本地插件链接、启用和运行时检查依据 [Plugins](https://github.com/openclaw/openclaw/blob/main/docs/tools/plugin.md)。使用内置 JavaScript 入口、清单工具声明及启动激活依据 [Building plugins](https://github.com/openclaw/openclaw/blob/main/docs/plugins/building-plugins.md)。before_prompt_build、上下文访问许可和作用域边界依据 [Plugin hooks](https://github.com/openclaw/openclaw/blob/main/docs/plugins/hooks.md) 与 [Prompt and session hooks](https://github.com/openclaw/openclaw/blob/main/docs/plugins/hooks/prompt-and-session.md)。agentId、workspaceDir、senderId、inputProvenance 与工具工厂的具体类型依据 [hook-types.ts](https://github.com/openclaw/openclaw/blob/main/src/plugins/hook-types.ts) 和 [tool-types.ts](https://github.com/openclaw/openclaw/blob/main/src/plugins/tool-types.ts)。定时任务的持久化、NO_REPLY 与 CLI 检查依据 [Automations CLI](https://github.com/openclaw/openclaw/blob/main/docs/cli/cron.md)。插件局部配置设置依据 [Config CLI](https://github.com/openclaw/openclaw/blob/main/docs/cli/config.md)。Gateway 原生服务入口依据 [Gateway CLI](https://github.com/openclaw/openclaw/blob/main/docs/cli/gateway.md)。

持久目录拆分、实例绑定、代码版本指针、数据代次、原子切换、备份清单和照片工作区副本是本项目的实现设计，不是两个宿主提供的 Life Engine 官方功能。
