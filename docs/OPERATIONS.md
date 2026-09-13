# v0.3 运维说明

日常维护使用永久目录中的 manage.py；运行能力使用同目录中的 life.py。每个宿主工作目录绑定一个实例，内部角色名相同也不会复用数据库。不要手工改 registry.json 的实例标识或路径，它负责原子选择已激活的代码和数据代次。

## 非交互安装

answers JSON 沿用 v0.2 字段。可额外提供 _owner_channel 和 _owner_sender_id，用于原生 Hook 严格识别本人的入站联系。_append_soul 在新版永久安装中不生效，插件会补入能力上下文，原 SOUL 不需要改写。

```sh
python setup.py --adapter openclaw --home "/实际workspace" --host-agent-id "实际agentId" \
  --answers examples/openclaw.answers.json --out "/工作区之外/plan.json"
python setup.py --apply-plan "/工作区之外/plan.json"
```

预览记录原 SOUL、已知宿主配置与已有部署注册文件的摘要，应用时再次核对；别人刚改过配置会要求重新生成预览。密码文件不被读取。对已有永久实例重复安装，默认保留它现有的 agent.json；显式 --reconfigure 才应用参数调整，并创建新数据代次，旧状态保留为备份。

## 升级与程序回退

从新包执行 setup.py --root 永久目录 upgrade。每个实例先被加锁、检查 schema 并备份，再验证新代码导入；通过后一次原子替换代码版本指针。程序采用版本目录，旧代码仍在 releases 下。导入失败不会切换当前代码。

程序回退用永久目录/manage.py rollback-code --release 完整目录名，只换代码入口，不撤销后来新增的记忆。跨数据 schema 的程序回退会被阻止。备份、恢复及升级的锁与日常调用相同，忙时命令提示稍后重试，而不会在出图/写库中途复制不一致数据。

永久入口使用记录的 Python 可执行文件，尽量避开 Hermes/OpenClaw 自己的可重建虚拟环境。系统移除了这个 Python 版本时，先在系统安装一个可用的 Python 3.11+，再用新 Python 执行：

```sh
python "/永久目录/manage.py" repair-python --python "/新的实际Python路径"
```

原生桥接器每次读取这个路径，不需要重新生成所有角色配置。宿主原生插件 API 变更则需适配桥接器并重新连接，不能以数据持久化代替接口兼容性检查。

## 数据备份与恢复

每天首次 wake 进行一次完整快照，没有独立定时线程。未设置唤醒任务时不会发生每日快照，应使用 backup 命令或交给现有备份系统。快照包含本实例的 agent.json、SQLite、工作流和生成图片；它不是 Hermes/OpenClaw 整个平台配置及凭据的替代备份，宿主配置仍使用平台自己的备份方式保存。

SQLite 通过 backup API 复制，包含已提交 WAL 页面；随后记录每个文件的 SHA-256。恢复先检查文件与实例绑定，复制到新的数据代次，再切换 registry.json 的 generation。当前数据在恢复前另留一份快照。失败的校验/切换不会先删除原数据，失败过程中留下的未激活代次可以稍后人工清理。

恢复会暂停主动联系，因为备份之后已发送的消息可能不在旧账本里；核对实际聊天再 resume。备份恢复不会重新启用一个被用户主动禁用的宿主定时任务，也不会重新建立已删除的原生插件。

备份存在异盘才覆盖整盘损坏风险；v0.3 不自动清理旧快照、旧数据代次、照片或旧代码。在容量较小的机器上定期转存。不要在运行目录内放任意其他文件作为“备份”，受管理数据禁止符号链接。

## 插件启用与启动

connect 仅操作当前 Life Engine 插件，使用宿主原生命令。OpenClaw 先用 agents list --json 核对所选 agentId/workspace，再链接稳定桥接目录。安装来源被原生策略拒绝时，查看具体错误；程序不会自动加 --force、关闭扫描或移除 deny 规则。需要信任确认的交互安装应在本机按当前 CLI 提示完成。

connect 会设置本插件的 allowConversationAccess，以便读取并补入本实例状态；不会覆盖用户显式设定的 allowPromptInjection:false 或工具禁用规则。若规则阻止 Hook，保留规则并报告只接通了哪些工具。Hermes 的 Profile 在调用子进程时通过 HERMES_HOME 精确绑定，插件内部也核对当前上下文 Profile。

OpenClaw 的桥接器严格要求同时匹配 agentId 和 workspaceDir。未提供上下文、子 Agent 或不同 worktree 不会自动获得这份状态。主 Agent 的 SOUL 原文不被替换，记忆中的文本视为数据。

打开生成的 INSTALL.md，按当前版本决定是否重载插件或重启现有 Gateway。宿主的升级、重新部署或开机服务均由它自己的管理员命令负责；本包不写操作系统服务定义、不直接修改 Cron 数据库，也不调用模型来静默替用户完成配置。

本机联调后保留原生任务 ID，后续检查或修改复用同一个任务。主动暂停应同时按需要暂停宿主任务与 life.py pause；仅暂停引擎会静默，但宿主仍可能按周期唤醒模型并计费。

## 照片与回执

ComfyUI API 工作流需要包含 {{POSITIVE_PROMPT}}；其余可用占位符与身份一致性方法延续 v0.2。原图在永久数据目录，OpenClaw 仅把该实例实际生成的图片复制到 workspace/life-engine-media/实例ID 下，用于遵守工作区媒体访问规则；不会把数据库目录加入全局允许路径。

photo 成功只表示文件生成并可读取，宿主媒体工具/渠道还需实际投递。本版不会猜消息回执与 contact ID 的对应关系；若需要完全自动的送达确认，应由本机接入层按真实发送返回值调用 ack。超时或未知回执不自动重发，恢复备份也不补发旧任务。

## 老版参考

V02-OPERATIONS.md、V02-README.md 和 setup_legacy.py 保存了旧部署布局及旧命令参考。新版默认只使用 setup.py；不要把旧脚本的 --rollback 参数用于新版状态恢复。
