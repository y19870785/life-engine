import argparse
import base64
import json
import re
from pathlib import Path

from .config import defaults, json_bytes, minutes, tz, valid_id, validate
from .install import (apply_plan, atomic_write, build_plan, discover_homes, inspect_host,
                      plan_view, rollback)
from .photos import ComfyUI, inspect_workflow


ROUTINE = [
    {"start": "00:00", "end": "08:00", "location": "home", "activity": "resting"},
    {"start": "08:00", "end": "10:00", "location": "home", "activity": "starting the day"},
    {"start": "10:00", "end": "12:00", "location": "desk", "activity": "working on personal projects"},
    {"start": "12:00", "end": "14:00", "location": "home", "activity": "lunch break"},
    {"start": "14:00", "end": "18:00", "location": "desk", "activity": "reading and working"},
    {"start": "18:00", "end": "20:00", "location": "home", "activity": "dinner and a break"},
    {"start": "20:00", "end": "24:00", "location": "home", "activity": "relaxing"},
]


def ask(label, default="", validator=None, input_fn=input, output=print):
    while True:
        value = input_fn(f"{label}" + (f" [{default}]" if default != "" else "") + "：").strip()
        if not value:
            value = str(default)
        try:
            return validator(value) if validator else value
        except (ValueError, TypeError) as exc:
            output(f"请再确认一下：{exc}")


def yes(label, default=False, input_fn=input, output=print):
    def check(value):
        if value.lower() in ("y", "yes", "是"):
            return True
        if value.lower() in ("n", "no", "否"):
            return False
        raise ValueError("输入 y 或 n")
    return ask(label + " (y/n)", "y" if default else "n", check, input_fn, output)


def merged(base, patch):
    result = json.loads(json.dumps(base))
    for key, value in patch.items():
        if key.startswith("_"):
            continue
        if key not in result:
            raise ValueError(f"Unknown setting: {key}")
        if isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merged(result[key], value)
        else:
            result[key] = value
    return result


def choose_home(explicit, adapter, input_fn=input, output=print):
    if explicit:
        return Path(explicit).expanduser().absolute(), adapter or "generic"
    candidates = discover_homes()
    output("选择要接入的现有 Agent。可选择已发现的 Hermes，也可输入其他 Agent 的完整目录。")
    for index, item in enumerate(candidates, 1):
        output(f"{index}: {item['label']} — {item['home']}")
    value = ask("编号或完整目录", input_fn=input_fn, output=output)
    if value.isdigit() and 1 <= int(value) <= len(candidates):
        item = candidates[int(value) - 1]
        return Path(item["home"]), item["adapter"]
    def check_adapter(value):
        if value not in ("hermes", "generic"):
            raise ValueError("输入 hermes 或 generic")
        return value
    adapter = adapter or ask("接入方式（其他 Agent 选 generic）", "generic", check_adapter, input_fn, output)
    return Path(value).expanduser().absolute(), adapter


def existing_cfg(host):
    directory = host / "life-engine" / "agents"
    candidates = sorted(directory.glob("*/agent.json")) if directory.exists() else []
    if len(candidates) > 1:
        raise ValueError("This host has multiple agent configs; choose a separate agent home")
    return json.loads(candidates[0].read_text(encoding="utf-8")) if candidates else None


def guide(host, adapter, input_fn=input, output=print, *, current=None, agent_home=None, ask_append=True):
    info = inspect_host(host, adapter)
    cfg = json.loads(json.dumps(current)) if current else existing_cfg(host)
    output(f"\n已选择：{host}")
    output("现有人格：保留 SOUL 原文与宿主的称呼、语气。")
    output("已有主配置：保留；密钥文件只检查是否存在，不读取内容。")
    for warning in info["warnings"]:
        output(warning)
    if cfg:
        output(f"发现已安装配置：{cfg['agent_id']}；以下默认值沿用当前设置。")
    else:
        proposed = re.sub(r"[^a-z0-9_-]+", "-", host.name.lower()).strip("-")[:40] or "assistant"
        agent_id = ask("给这次接入一个内部代号", proposed, valid_id, input_fn, output)
        cfg = defaults(agent_id, info["name_suggestion"])
    cfg["integration"].update({"host_home": str(host), "adapter": adapter})
    cfg["persona"]["soul_path"] = info["soul_path"]
    cfg["display_name"] = ask("界面显示名（空白则沿用 SOUL，不改变身份）",
                              cfg["display_name"], input_fn=input_fn, output=output)
    cfg["owner_label"] = ask("用户称呼（空白则沿用现有称呼）", cfg["owner_label"], input_fn=input_fn, output=output)
    def timezone(value):
        tz(value)
        return value
    cfg["timezone"] = ask("与你同步的时区", cfg["timezone"], timezone, input_fn, output)
    def mode(value):
        if value not in ("assistant", "companion"):
            raise ValueError("输入 assistant 或 companion")
        return value
    cfg["mode"] = ask("工作跟进 assistant / 陪伴生活 companion", cfg["mode"], mode, input_fn, output)
    if cfg["mode"] == "assistant":
        cfg["world"]["routine"] = []
        cfg["world"]["visual_options"] = {}
    elif not cfg["world"]["routine"] and yes("采用可编辑的日常作息示例", False, input_fn, output):
        cfg["world"]["routine"] = json.loads(json.dumps(ROUTINE))
    cfg["social"]["enabled"] = yes("允许它主动联系你", cfg["social"]["enabled"], input_fn, output)
    if cfg["social"]["enabled"]:
        def budget(value):
            number = int(value)
            if not 1 <= number <= 20:
                raise ValueError("次数需在 1..20 之间")
            return number
        cfg["social"]["daily_max"] = ask("每天最多几次", cfg["social"]["daily_max"], budget, input_fn, output)
        cfg["social"]["daily_min"] = min(cfg["social"]["daily_min"], cfg["social"]["daily_max"])
        def clock(value):
            minutes(value)
            return value
        cfg["social"]["quiet_hours"] = [
            ask("安静时段开始", cfg["social"]["quiet_hours"][0], clock, input_fn, output),
            ask("安静时段结束", cfg["social"]["quiet_hours"][1], clock, input_fn, output),
        ]
        def nonnegative(value):
            number = int(value)
            if not 0 <= number <= 1440:
                raise ValueError("分钟数需在 0..1440 之间")
            return number
        cfg["social"]["recent_chat_minutes"] = ask("刚聊过后，多久不再主动打扰（分钟）",
            cfg["social"]["recent_chat_minutes"], nonnegative, input_fn, output)
        cfg["integration"]["delivery_target"] = ask("投递目标（留空只本地预览；如 weixin:实际聊天ID）",
            cfg["integration"]["delivery_target"], input_fn=input_fn, output=output)
        if cfg["mode"] == "assistant":
            output("工作模式只在已记录的跟进事项到期时联系；它不模拟私人生活。")
    cfg["memory"]["enabled"] = yes("记录精选经历与未完成话题", cfg["memory"]["enabled"], input_fn, output)
    cfg["photos"]["enabled"] = yes("启用照片", cfg["photos"]["enabled"], input_fn, output)
    workflow = None
    if cfg["photos"]["enabled"]:
        cfg["photos"]["base_url"] = ask("ComfyUI 地址", cfg["photos"]["base_url"], input_fn=input_fn, output=output)
        default_workflow = ((agent_home or host / "life-engine" / "agents" / cfg["agent_id"]) / cfg["photos"]["workflow"]
                            if cfg["photos"]["workflow"] else "")
        def workflow_path(value):
            path = Path(value).expanduser().absolute()
            inspect_workflow(path)
            return str(path)
        workflow = ask("身份保持工作流（ComfyUI API JSON）", default_workflow, workflow_path, input_fn, output)
        cfg["photos"]["workflow"] = "workflow_api.json"
        def nonempty(value):
            if not value:
                raise ValueError("填入与已有形象一致的身份提示词；不会按姓名猜脸")
            return value
        cfg["photos"]["identity_prompt"] = ask("已有形象的固定英文提示词",
            cfg["photos"]["identity_prompt"], nonempty, input_fn, output)
        if yes("现在检查 ComfyUI 连接（不会出图）", False, input_fn, output):
            try:
                ComfyUI(cfg["photos"]["base_url"]).json("/system_stats")
                output("连接成功。实际出图和人脸一致性仍需本机测试。")
            except Exception:
                output("暂时连接不上；配置可以先保存，稍后用 doctor --network 检查。")
    append = yes("把能力说明接到现有 SOUL 末尾（原文保留）", False, input_fn, output) if ask_append else False
    validate(cfg)
    return cfg, append, workflow


def preview(plan, output=print):
    view = plan_view(plan)
    output("\n配置预览")
    output(f"Agent：{view['name']} / {view['agent']}；用途：{view['mode']}")
    output(f"主动联系：{'启用' if view['proactive'] else '关闭'}；每日上限：{view['daily_max']}")
    output(f"安静时段：{' → '.join(view['quiet_hours'])}；照片：{'启用' if view['photos'] else '关闭'}")
    output("SOUL：" + ("在原文末尾接入能力说明" if view["soul_hook"] else "完全保留，使用独立能力文件"))
    output(f"将创建或更新 {len(view['changes'])} 个扩展文件。")
    # Show the concrete changed file list, but never dump original private SOUL/config content.
    for row in view["changes"]:
        output(f"  {row['action']}: {row['path']}")
    if view["soul_hook"]:
        path = plan["summary"]["soul_path"]
        row = next((r for r in plan["writes"] if r["path"] == path), None)
        if row:
            data = base64.b64decode(row["content"]).decode("utf-8-sig")
            start = data.find(f"<!-- life-engine:{plan['agent_id']}:begin -->")
            finish = data.find(f"<!-- life-engine:{plan['agent_id']}:end -->", start)
            output("\n追加/更新的能力说明：")
            output(data[start:finish + len(f"<!-- life-engine:{plan['agent_id']}:end -->")])
    output(view["effects"])
    for warning in view["warnings"]:
        output(warning)


def main(package_root, argv=None, input_fn=input, output=print):
    parser = argparse.ArgumentParser(description="现有 Agent 的 Life Engine 配置引导")
    parser.add_argument("--home", type=Path, help="Agent 目录或准确的 Hermes Profile 目录")
    parser.add_argument("--adapter", choices=("hermes", "generic"))
    parser.add_argument("--answers", type=Path, help="JSON settings for a noninteractive preview")
    parser.add_argument("--out", type=Path, help="save a local reviewable installation plan")
    parser.add_argument("--apply", action="store_true", help="apply the displayed settings")
    parser.add_argument("--apply-plan", type=Path)
    parser.add_argument("--rollback", type=Path, help="restore files from a specific install journal")
    parser.add_argument("--inspect", action="store_true", help="inspect without changing the host")
    args = parser.parse_args(argv)
    try:
        if args.rollback:
            output(json.dumps(rollback(args.rollback), ensure_ascii=False, indent=2))
            return 0
        if args.apply_plan:
            plan = json.loads(args.apply_plan.read_text(encoding="utf-8"))
            preview(plan, output)
            output(json.dumps(apply_plan(plan), ensure_ascii=False, indent=2))
            return 0
        if args.answers and not args.home:
            raise ValueError("--answers requires --home")
        host, adapter = choose_home(args.home, args.adapter, input_fn, output)
        if args.inspect:
            output(json.dumps(inspect_host(host, adapter), ensure_ascii=False, indent=2))
            return 0
        if args.answers:
            patch = json.loads(args.answers.read_text(encoding="utf-8"))
            current = existing_cfg(host)
            base = current or defaults(patch.get("agent_id", "assistant"))
            cfg = merged(base, patch)
            cfg["integration"].update({"adapter": adapter, "host_home": str(host)})
            append = patch.get("_append_soul", False)
            workflow = patch.get("_workflow_source")
            if type(append) is not bool:
                raise ValueError("_append_soul must be boolean")
        else:
            cfg, append, workflow = guide(host, adapter, input_fn, output)
        plan = build_plan(package_root, cfg, append, workflow)
        preview(plan, output)
        out = args.out or Path.cwd() / f"life-engine-plan-{cfg['agent_id']}.json"
        protected = set(plan["source_hashes"]) | {row["path"] for row in plan["writes"]}
        out = out.expanduser().absolute()
        if str(out) in protected or out.is_relative_to(host):
            raise ValueError("Save the review plan outside the Agent directory")
        atomic_write(out, json_bytes(plan))
        output(f"\n配置预览已保存：{out}")
        apply = args.apply or (not args.answers and yes("按上面预览安装", False, input_fn, output))
        if apply:
            output(json.dumps(apply_plan(plan), ensure_ascii=False, indent=2))
            output("接入文件已准备好。定时任务的具体配置在该 Agent 的 SCHEDULE.md 中。")
        else:
            output("尚未修改 Agent。可用 setup.py --apply-plan 加上该预览文件路径完成安装。")
        return 0
    except (EOFError, KeyboardInterrupt):
        output("\n引导已取消。")
        return 2
    except Exception as exc:
        output(f"未完成：{type(exc).__name__}: {exc}")
        return 1
