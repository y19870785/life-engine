"""Generate dependency-light native adapters. No host core files are patched."""
import json
import os
import shutil
import subprocess
from pathlib import Path

from .config import json_bytes
from .durable import absolute, read, registry, safe_name, write
from .install import atomic_write, digest

ACTIONS = ['status', 'wake', 'observe', 'remember', 'loop-add', 'loop-close',
           'prepare', 'ack', 'photo', 'pause', 'resume']
PARAMETERS = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'action': {'type': 'string', 'enum': ACTIONS},
        **{k: {'type': 'string'} for k in ['summary', 'event_key', 'kind', 'source', 'topic', 'due',
                                         'id', 'resolution', 'outcome', 'evidence', 'contact_id']},
        'preview': {'type': 'boolean'}, 'dry_run': {'type': 'boolean'},
    }, 'required': ['action'],
}

HERMES = '''"""Life Engine native bridge; state remains outside the Hermes install."""
import json
import logging
import subprocess
from pathlib import Path

BINDING = json.loads((Path(__file__).parent / "binding.json").read_text(encoding="utf-8"))
LOG = logging.getLogger(__name__)
PARAMETERS = __PARAMETERS__


def _settings():
    root = Path(BINDING["root"])
    reg = json.loads((root / "registry.json").read_text(encoding="utf-8"))
    return root, reg, reg["instances"][BINDING["instance"]]


def _scoped():
    # Hermes home is context-local in current hosts, including multi-profile gateways.
    from hermes_constants import get_hermes_home
    return Path(get_hermes_home()).resolve() == Path(_settings()[2]["host_home"]).resolve()


def _call(action, arguments=None, timeout=20):
    root, reg, inst = _settings()
    result = subprocess.run([reg["python"], str(root / "life.py"), "--instance", inst["id"],
                             action] + (arguments or []), capture_output=True, text=True,
                            encoding="utf-8", timeout=timeout, shell=False)
    try:
        parsed = json.loads(result.stdout)
    except ValueError:
        raise RuntimeError("Life Engine did not return JSON; run manage.py doctor")
    if result.returncode:
        raise RuntimeError(parsed.get("message", "Life Engine command failed"))
    return parsed


def _handle(params, **kwargs):
    if not _scoped():
        return json.dumps({"ok": False, "error": "Different Hermes Profile"})
    if params.get("action") not in PARAMETERS["properties"]["action"]["enum"]:
        raise ValueError("Unsupported Life Engine action")
    args = []
    for key, value in params.items():
        if key == "action":
            continue
        if key not in PARAMETERS["properties"]:
            raise ValueError("Unknown parameter")
        if isinstance(value, bool):
            if value:
                args.append("--" + key.replace("_", "-"))
        elif isinstance(value, str):
            args.append("--" + key.replace("_", "-") + "=" + value)
        else:
            raise ValueError("Invalid parameter type")
    try:
        return json.dumps(_call(params["action"], args, 7250 if params["action"] == "photo" else 30), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False)


def _before(**kwargs):
    try:
        if not _scoped():
            return
        root, reg, inst = _settings()
        args = []
        if (inst.get("owner_sender_id") and inst.get("owner_channel") and
                kwargs.get("sender_id") == inst["owner_sender_id"] and
                kwargs.get("platform") == inst["owner_channel"] and
                not kwargs.get("parent_session_id")):
            args.append("--owner-seen")
            if kwargs.get("turn_id"):
                args.append("--event-key=hermes:" + str(kwargs["turn_id"]))
        return {"context": _call("context", args, 8)["text"]}
    except Exception as exc:
        LOG.warning("Life Engine context unavailable: %s", exc)
        return {"context": "Life Engine is unavailable; do not invent its current state or claim a photo was sent."}


def register(ctx):
    root, reg, inst = _settings()
    if not _scoped():
        return
    ctx.register_tool(name=inst["tool_name"], toolset=inst["plugin_id"], schema={
        "name": inst["tool_name"],
        "description": "Read continuous life state, decide on a scheduled contact, record owner follow-ups, and request an enabled ComfyUI photo. Preserve the existing persona.",
        "parameters": PARAMETERS,
    }, handler=_handle)
    ctx.register_hook("pre_llm_call", _before)
'''

OPENCLAW = '''import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { readFileSync, realpathSync } from "node:fs";
import { resolve } from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const binding = JSON.parse(readFileSync(new URL("./binding.json", import.meta.url), "utf8"));
const parameters = __PARAMETERS__;
const exec = promisify(execFile);
function settings() {
  const reg = JSON.parse(readFileSync(resolve(binding.root, "registry.json"), "utf8"));
  return { reg, inst: reg.instances[binding.instance] };
}
function scoped(ctx, inst) {
  // No ambient default agent. Worktree/unknown contexts require explicit rebinding.
  if (!ctx?.agentId || !ctx?.workspaceDir || ctx.agentId !== inst.host_agent_id) return false;
  try { return realpathSync(ctx.workspaceDir) === realpathSync(inst.host_home); }
  catch { return false; }
}
async function call(action, args = [], timeout = 20000) {
  const {reg, inst} = settings();
  try {
    const {stdout} = await exec(reg.python,
      [resolve(binding.root, "life.py"), "--instance", inst.id, action, ...args],
      {encoding: "utf8", timeout, maxBuffer: 2 * 1024 * 1024, windowsHide: true});
    return JSON.parse(stdout);
  } catch (err) {
    let message = "Life Engine unavailable; run manage.py doctor";
    try { message = JSON.parse(err.stdout).message || message; } catch {}
    throw new Error(message);
  }
}
function argumentsFor(params) {
  if (!parameters.properties.action.enum.includes(params.action)) throw new Error("Unsupported action");
  const args = [];
  for (const [key, value] of Object.entries(params)) {
    if (key === "action") continue;
    if (!Object.hasOwn(parameters.properties, key)) throw new Error("Unknown parameter");
    const flag = "--" + key.replaceAll("_", "-");
    if (typeof value === "boolean") { if (value) args.push(flag); }
    else if (typeof value === "string") args.push(flag + "=" + value);
    else throw new Error("Invalid parameter type");
  }
  return args;
}
const initial = settings().inst;
export default definePluginEntry({
  id: initial.plugin_id, name: "Life Engine", description: "Persistent life state for one existing agent.",
  register(api) {
    api.registerTool((ctx) => {
      if (!scoped(ctx, settings().inst)) return null;
      return {
        name: initial.tool_name,
        description: "Read current life state, handle a scheduled wake, record owner follow-ups, or generate an enabled ComfyUI photo. Existing SOUL controls personality.",
        parameters,
        async execute(_id, params) {
          if (!scoped(ctx, settings().inst)) throw new Error("Life Engine agent binding changed");
          const details = await call(params.action, argumentsFor(params), params.action === "photo" ? 7250000 : 30000);
          return { content: [{type: "text", text: JSON.stringify(details)}], details };
        },
      };
    }, {name: initial.tool_name});
    api.on("before_prompt_build", async (_event, ctx) => {
      const { inst } = settings();
      if (!scoped(ctx, inst)) return;
      // Respect explicit tool policy when the host supplies authority.
      if (ctx.toolAuthority && !ctx.toolAuthority.allows(inst.tool_name)) return;
      try {
        const args = [];
        if (ctx.inputProvenance?.kind === "external_user" &&
            inst.owner_sender_id && inst.owner_channel &&
            ctx.senderId === inst.owner_sender_id && ctx.channel === inst.owner_channel) {
          args.push("--owner-seen");
          if (ctx.runId) args.push("--event-key=openclaw:" + ctx.runId);
        }
        const result = await call("context", args, 8000);
        ctx.hookInvocation?.assertActive();
        return { prependContext: result.text };
      } catch (err) {
        api.logger?.warn?.("Life Engine context unavailable: " + err.message);
        return {prependContext: "Life Engine is unavailable; do not invent its current state or claim a photo was sent."};
      }
    }, {requiresToolAuthority: true});
  },
});
'''


def install_bridges(root, instance, python):
    folder = root / 'bridges' / instance['id']
    binding = json_bytes({'root': str(root), 'instance': instance['id']})
    if instance['adapter'] == 'hermes':
        contents = {
            'hermes/plugin.yaml': ('name: ' + instance['plugin_id'] + '\nversion: "0.3.0"\ndescription: Persistent life state for an existing Agent\n').encode(),
            'hermes/__init__.py': HERMES.replace('__PARAMETERS__', repr(PARAMETERS)).encode(),
            'hermes/binding.json': binding,
        }
    elif instance['adapter'] == 'openclaw':
        contents = {
            'openclaw/package.json': json_bytes({'name': instance['plugin_id'], 'version': '0.3.0',
                'type': 'module', 'openclaw': {'extensions': ['./index.mjs']}}),
            'openclaw/openclaw.plugin.json': json_bytes({'id': instance['plugin_id'], 'name': 'Life Engine',
                'version': '0.3.0', 'categories': ['other'],
                'contracts': {'tools': [instance['tool_name']]}, 'activation': {'onStartup': True},
                'configSchema': {'type': 'object', 'additionalProperties': False}}),
            'openclaw/index.mjs': OPENCLAW.replace('__PARAMETERS__', json.dumps(PARAMETERS)).encode(),
            'openclaw/binding.json': binding,
        }
    else:
        contents = {}
    contents['INSTALL.md'] = installation_guide(root, instance, python).encode()
    marker = folder / 'managed-files.json'
    prior = read(marker) if marker.exists() else {}
    for name, content in contents.items():
        path = folder / name
        if path.exists() and digest(path.read_bytes()) != digest(content):
            if prior.get(name) != digest(path.read_bytes()):
                raise ValueError('Bridge file was edited; inspect it before update: ' + str(path))
    previous = {}
    try:
        for name, content in contents.items():
            path = folder / name
            previous[path] = path.read_bytes() if path.exists() else None
            atomic_write(path, content)
        write(marker, {name: digest(content) for name, content in contents.items()})
    except BaseException:
        for path, content in previous.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, content)
        raise


def installation_guide(root, inst, python):
    from .integration import command
    cmd = command([python, str(root / 'life.py'), '--instance', inst['id']])
    silence = '[SILENT]' if inst['adapter'] == 'hermes' else 'NO_REPLY'
    host = inst['adapter']
    return f'''# Life Engine 本机接入记录

实例：{inst['id']}
宿主：{host}；原有工作目录：{inst['host_home']}
插件：{inst['plugin_id']}；工具：{inst['tool_name']}
OpenClaw agentId：{inst['host_agent_id'] or '不适用'}
稳定运行命令：{cmd}

安装器已将程序、数据和桥接器复制到永久目录；解压目录可删除。
SOUL、IDENTITY、模型和密钥仍由原 Agent 管理。数据不依赖对话记忆。
连接插件：运行永久目录/manage.py connect --instance 实例ID。
连接通过宿主自己的 CLI 安装/启用本插件；正常保留原有安装策略与权限。
OpenClaw 的 --profile 与 OPENCLAW_CONFIG_PATH 必须对应本 Agent 所属网关；
可给 connect 传 --host-profile。Hermes 使用所选 Profile 的 HERMES_HOME。

请在实际宿主完成一次调用 {inst['tool_name']} 的 status，并发一条普通主人消息；
随后 manage.py doctor 中应看到 native_events.last_prompt_hook_at。
安装文件存在或 plugins inspect 成功，不能单独证明在线网关已经加载。
若未设置 owner_channel / owner_sender_id，则不声称自动识别每条入站消息；
主人确认渠道与发送者后，重跑配置引导以启用严格匹配，仅记录时间而不复制全文。

## 一次性定时接入

检查已有任务，包括 v0.1/v0.2。迁移前暂停旧任务，避免两份数据库分别决定发送。
为此实例使用稳定任务名 life-engine-pulse-{inst['id']}，每 23 分钟运行。
固定绑定实际 Agent、渠道、账号和主人的聊天目标；不得使用全部渠道或猜测收件人。
读取本机 CLI --help 后使用宿主原生任务 API 创建或更新同名任务，记录实际任务 ID。
OpenClaw 绑定 agentId={inst['host_agent_id'] or '由实际配置确定'}，使用完整人格上下文，
不要启用会跳过 SOUL 的 light-context。Hermes 在上述 Profile 中附上工具指引。

任务提示词：调用 {inst['tool_name']}，action=wake，一次即可。
若 action=silent，最终只返回 {silence}，不要调用发送工具。
若 action=contact，按原 SOUL 口吻、返回状态和历史生成自然消息；需要照片时调用 photo。
只发送实际存在的照片文件，用宿主的原生媒体接口，不能把路径当成已经发出的照片。
发送前调用 prepare；有真实发送回执才能 ack，未知结果不自动重发。
直接发送与定时器的自动投递只选一种，避免重复发出。

用隔离 simulate 检查，再在主人已指定的聊天中验证文字/图片。
实际确认投递与静默都正常后启用这一个任务，检查宿主的持久化任务记录。
任务状态保存在宿主自己的数据目录；本扩展不会直接改写其任务数据库。

## 重启、升级和备份

让现有 Gateway 由本机支持的 systemd / launchd / Windows 服务或 Docker 管理并开机启动。
先检查已安装服务，避免重复安装；不用再单独启动 Life Engine 常驻进程。
Docker 必须持久挂载宿主数据目录和整个 Life Engine 永久目录，保持容器内路径稳定；
python 与文件访问在网关执行环境内必须可用，macOS 登录启动不等于未登录开机运行。

每次当日首次 wake 自动保存一份包含 SQLite 与图片的备份；升级和恢复前也会备份。
备份是普通目录，使用 SQLite backup API 包含已提交 WAL 数据，不复制运行中的裸数据库。
运行 永久目录/manage.py backup --instance 实例ID --out 外部磁盘目录，可留异盘副本。
同盘备份不能防止整盘损坏。照片备份会占磁盘空间，本版本不自动删除旧备份。

更新 Life Engine：解压新版，运行 setup.py --root 永久目录 upgrade。
程序按版本并存，只原子切换代码入口；schema 不支持时停止，不重置数据库。
恢复指定备份：永久目录/manage.py restore --instance 实例ID --backup 备份目录。
恢复会生成新数据副本并暂停主动联系；核对备份之后实际发出的消息，再主动 resume。
删除插件/卸载宿主不会由本扩展删除独立数据；重装后可对同一实例重新 connect。

程序可用永久目录/manage.py rollback-code --release 已安装版本目录名回退；数据不回退。
OpenClaw 照片会复制一份到 workspace/life-engine-media/实例目录，以便原生媒体访问；
原图仍在永久数据目录中，不会扩大整个数据目录的访问权限。

代码版本按 2026-09-13 官方接口编写并做适配器契约测试；真实宿主、聊天平台和 GPU
仍须本机验收。升级宿主后执行 doctor、真实 status 工具调用与一次静默检查。
宿主 API 不兼容时可能需要更新桥接器，数据保留不代表任意未来版本都自动兼容。
'''


def native_connect(root, key, host_profile=None, runner=subprocess.run):
    root = absolute(root)
    reg = registry(root)
    inst = reg['instances'][safe_name(key)]
    folder = root / 'bridges' / key
    history = []
    env = dict(os.environ)
    exe = shutil.which(inst['adapter'])
    if not exe:
        raise ValueError('Host CLI is unavailable in this environment: ' + inst['adapter'])

    def call(args, capture=False):
        result = runner([exe] + args, env=env, text=True, encoding='utf-8',
                        capture_output=capture, timeout=120, shell=False)
        history.append({'argv': [exe] + args, 'returncode': result.returncode})
        if result.returncode:
            raise RuntimeError('Native host command did not succeed; inspect its output. Installation data is preserved.')
        return result

    if inst['adapter'] == 'hermes':
        env['HERMES_HOME'] = inst['host_home']
        target = absolute(Path(inst['host_home']) / 'plugins' / inst['plugin_id'])
        source = folder / 'hermes'
        marker = target / 'life-engine-managed.json'
        prior = read(marker) if marker.exists() else {}
        content = {p.name: p.read_bytes() for p in source.iterdir() if p.is_file()}
        for name, data in content.items():
            path = target / name
            if path.exists() and digest(path.read_bytes()) != prior.get(name):
                if digest(path.read_bytes()) != digest(data):
                    raise ValueError('Existing plugin file is not owned by this installer')
        for name, data in content.items():
            atomic_write(target / name, data)
        write(marker, {name: digest(data) for name, data in content.items()})
        call(['plugins', 'enable', inst['plugin_id']])
        call(['plugins', 'list'])
    elif inst['adapter'] == 'openclaw':
        prefix = ['--profile', host_profile] if host_profile else []
        listing = call(prefix + ['agents', 'list', '--json'], capture=True)
        agents = json.loads(listing.stdout)
        if isinstance(agents, dict):
            agents = agents.get('agents', [])
        matched = [a for a in agents if a.get('id', a.get('agentId')) == inst['host_agent_id']
                   and a.get('workspace') and Path(a['workspace']).expanduser().resolve() == Path(inst['host_home']).resolve()]
        if len(matched) != 1:
            raise ValueError('Actual OpenClaw agentId/workspace does not match; check --host-profile/config path')
        # Use normal local source review. Do not auto-add --force or change policy gates.
        # Repeat connections use saved host provenance to avoid duplicate link installs.
        record = root / 'instances' / key / 'connection.json'
        # Link install is intentionally retried for repair; the host owns collision/trust decisions.
        call(prefix + ['plugins', 'install', '--link', str(folder / 'openclaw')])
        call(prefix + ['plugins', 'enable', inst['plugin_id']])
        call(prefix + ['config', 'set', 'plugins.entries.' + inst['plugin_id'] + '.hooks.allowConversationAccess', 'true'])
        call(prefix + ['plugins', 'inspect', inst['plugin_id'], '--runtime', '--json'])
    else:
        raise ValueError('Generic mode has no native plugin activation command')
    result = {'ok': True, 'instance': key, 'commands_completed': history,
              'live_gateway_verified': False,
              'next': 'Reload/restart the existing Gateway as required by its version, then verify an actual tool call and prompt hook. Configure the one persistent host schedule.'}
    write(root / 'instances' / key / 'connection.json', result)
    return result
