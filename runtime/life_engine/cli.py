import argparse
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from .config import load, now_in
from .engine import Engine
from .photos import ComfyUI, inspect_workflow, photo
from .store import Store


def emit(data):
    print(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))


def parser(default_home):
    p = argparse.ArgumentParser(description="Life Engine: independent continuity for an existing Agent")
    p.add_argument("--home", type=Path, default=default_home)
    p.add_argument("--agent", required=True)
    subs = p.add_subparsers(dest="cmd", required=True)
    for name in ("status", "wake"):
        item = subs.add_parser(name)
        # Real-clock only for writes; time travel belongs to a separate simulation DB.
        if name == "wake":
            item.add_argument("--preview", action="store_true")
    sim = subs.add_parser("simulate")
    sim.add_argument("--day", required=True)
    obs = subs.add_parser("observe")
    obs.add_argument("--summary", required=True)
    obs.add_argument("--event-key")
    mem = subs.add_parser("remember")
    mem.add_argument("--summary", required=True)
    mem.add_argument("--kind", default="shared_experience")
    mem.add_argument("--source", default="owner_conversation")
    lp = subs.add_parser("loop-add")
    lp.add_argument("--topic", required=True)
    lp.add_argument("--due")
    close = subs.add_parser("loop-close")
    close.add_argument("--id", type=int, required=True)
    close.add_argument("--resolution", required=True)
    prep = subs.add_parser("prepare")
    prep.add_argument("--id", required=True)
    prep.add_argument("--summary", required=True)
    ack = subs.add_parser("ack")
    ack.add_argument("--id", required=True)
    ack.add_argument("--outcome", required=True, choices=("delivered", "failed", "unknown"))
    ack.add_argument("--evidence", required=True)
    ph = subs.add_parser("photo")
    ph.add_argument("--contact-id")
    ph.add_argument("--kind", default="selfie", choices=("selfie", "life_detail"))
    ph.add_argument("--dry-run", action="store_true")
    health = subs.add_parser("doctor")
    health.add_argument("--network", action="store_true", help="also probe the configured ComfyUI server")
    mig = subs.add_parser("migrate-v01")
    mig.add_argument("--source", required=True, type=Path)
    subs.add_parser("pause")
    subs.add_parser("resume")
    return p


def simulate(cfg, day):
    start = now_in(cfg, day + "T00:00:00")
    with tempfile.TemporaryDirectory(prefix="life-engine-simulation-") as directory:
        store = Store(Path(directory) / "simulation.db", cfg["agent_id"])
        engine = Engine(cfg, store)
        events = []
        for minute in range(0, 1440, 23):
            result = engine.wake(start + timedelta(minutes=minute))
            if result["action"] == "contact":
                events.append({"time": result["moment"]["time"], "activity": result["moment"].get("activity"),
                               "photo_requested": result["photo_requested"]})
        return {"simulation": True, "agent_id": cfg["agent_id"], "day": day,
                "events": events, "no_delivery": True,
                "note": "Assistant mode has no synthetic due follow-ups, so may produce no contacts."}


def main(argv=None, default_home=None, photo_result_transform=None):
    args = parser(default_home).parse_args(argv)
    try:
        cfg, agent_home = load(args.home, args.agent)
        if args.cmd == "simulate":
            emit(simulate(cfg, args.day))
            return 0
        store = Store(agent_home / "life.db", cfg["agent_id"])
        engine = Engine(cfg, store)
        now = now_in(cfg)
        result = {"ok": True}
        if args.cmd == "status":
            result = engine.status(now)
        elif args.cmd == "wake":
            result = engine.wake(now, preview=args.preview)
        elif args.cmd == "observe":
            store.observe(now.timestamp(), args.summary if cfg["memory"]["enabled"] else "", args.event_key)
        elif args.cmd in ("remember", "loop-add", "loop-close"):
            if not cfg["memory"]["enabled"]:
                raise ValueError("Memory is disabled for this agent")
            if args.cmd == "remember":
                result["id"] = store.remember(now.timestamp(), args.kind, args.summary, args.source)
            elif args.cmd == "loop-add":
                due = now_in(cfg, args.due).timestamp() if args.due else None
                result["id"] = store.loop_add(now.timestamp(), args.topic, due)
            else:
                store.loop_close(args.id, args.resolution)
        elif args.cmd == "prepare":
            store.prepare(args.id, args.summary)
            result["status"] = "prepared"
        elif args.cmd == "ack":
            store.acknowledge(args.id, args.outcome, args.evidence)
        elif args.cmd == "photo":
            result = photo(cfg, agent_home, store, engine, now, args.contact_id, args.kind, args.dry_run)
            if photo_result_transform:
                result = photo_result_transform(result)
        elif args.cmd == "migrate-v01":
            from .migrate import migrate_v01
            result = migrate_v01(args.source, store)
        elif args.cmd in ("pause", "resume"):
            store.pause(args.cmd == "pause")
        elif args.cmd == "doctor":
            result = {"ok": True, "agent_id": cfg["agent_id"], "checks": {
                "config": "valid", "database": "bound_to_agent",
                "soul": "present" if Path(cfg["persona"]["soul_path"]).is_file() else "host_managed_or_missing",
                "inbound_hook": "instruction_only; host-specific event adapter required for guaranteed capture",
                "delivery": "receipt_callback_not_registered",
            }}
            if cfg["photos"]["enabled"]:
                inspect_workflow(agent_home / cfg["photos"]["workflow"])
                result["checks"]["workflow"] = "valid_api_graph; identity quality needs visual review"
                if args.network:
                    ComfyUI(cfg["photos"]["base_url"]).json("/system_stats")
                    result["checks"]["comfyui"] = "reachable"
            emit(result)
            return 0
        emit(result)
        return 0
    except (Exception,) as exc:
        emit({"ok": False, "error": type(exc).__name__, "message": str(exc)})
        return 1
