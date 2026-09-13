from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def tz(name):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == "Asia/Shanghai":
            return timezone(timedelta(hours=8), name)
        raise ValueError("Unknown timezone; install tzdata on Windows for this IANA zone.")


def now_in(cfg, value=None):
    zone = tz(cfg["timezone"])
    result = datetime.fromisoformat(value) if value else datetime.now(zone)
    return result.replace(tzinfo=zone) if result.tzinfo is None else result.astimezone(zone)


def minutes(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
        raise ValueError("Time must be HH:MM, 00:00 through 23:59.")
    h, m = map(int, value.split(":"))
    return h * 60 + m


def valid_id(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,47}", value):
        raise ValueError("Agent ID: 1-48 lowercase letters, digits, underscores or hyphens.")
    return value


def defaults(agent_id="assistant", name=""):
    return {
        "schema_version": 2,
        "agent_id": valid_id(agent_id),
        "display_name": name,
        "owner_label": "",
        "timezone": "Asia/Shanghai",
        "mode": "assistant",
        "persona": {"strategy": "inherit", "soul_path": ""},
        "social": {
            "enabled": False, "daily_max": 3, "daily_min": 1,
            "min_gap_minutes": 150, "recent_chat_minutes": 75,
            "quiet_hours": ["23:00", "08:00"], "slot_grace_minutes": 60,
            "windows": [["08:30", "10:00"], ["14:30", "17:30"], ["20:00", "22:30"]],
        },
        "memory": {"enabled": True},
        "world": {"routine": [], "visual_options": {}, "scene": "", "weather": None},
        "photos": {
            "enabled": False, "provider": "comfyui", "daily_max": 1, "probability": 0.35,
            "base_url": "http://127.0.0.1:8188", "workflow": "", "identity_prompt": "",
            "negative_prompt": "", "width": 832, "height": 1216, "timeout_seconds": 1200,
            "kinds": ["selfie", "life_detail"],
        },
        "integration": {"adapter": "generic", "host_home": "", "profile": "", "delivery_target": ""},
        "seed": secrets.token_hex(16),
    }


def validate(cfg):
    if cfg.get("schema_version") != 2:
        raise ValueError("This runtime requires schema_version=2; use the v0.1 migration command.")
    valid_id(cfg["agent_id"])
    tz(cfg["timezone"])
    if cfg["mode"] not in ("assistant", "companion"):
        raise ValueError("mode must be assistant or companion")
    if cfg["persona"]["strategy"] != "inherit":
        raise ValueError("Persona strategy must be inherit; change identity in the host's SOUL.")
    social = cfg["social"]
    for key, upper in (
        ("daily_min", 20), ("daily_max", 20), ("min_gap_minutes", 1440),
        ("recent_chat_minutes", 1440), ("slot_grace_minutes", 1440),
    ):
        if type(social[key]) is not int or not 0 <= social[key] <= upper:
            raise ValueError(f"social.{key} must be an integer from 0 to {upper}")
    if social["daily_min"] > social["daily_max"]:
        raise ValueError("daily_min exceeds daily_max")
    if len(social["quiet_hours"]) != 2:
        raise ValueError("quiet_hours must have a start and end")
    for clock in social["quiet_hours"]:
        minutes(clock)
    if not social["windows"] and social["enabled"]:
        raise ValueError("Provide a contact window before enabling proactive contact")
    for window in social["windows"]:
        if len(window) != 2 or minutes(window[0]) >= minutes(window[1]):
            raise ValueError("Each contact window must start before it ends on the same day")
    if type(social["enabled"]) is not bool or type(cfg["memory"]["enabled"]) is not bool:
        raise ValueError("Capability flags must be boolean")
    photo = cfg["photos"]
    if type(photo["enabled"]) is not bool:
        raise ValueError("photos.enabled must be boolean")
    if not isinstance(photo["probability"], (int, float)) or not 0 <= photo["probability"] <= 1:
        raise ValueError("Photo probability must be 0..1")
    for key, low, high in (("daily_max", 0, 20), ("width", 64, 8192), ("height", 64, 8192),
                           ("timeout_seconds", 1, 7200)):
        if type(photo[key]) is not int or not low <= photo[key] <= high:
            raise ValueError(f"photos.{key} must be an integer in {low}..{high}")
    if photo["enabled"]:
        if photo["provider"] != "comfyui":
            raise ValueError("This release implements the comfyui photo provider only")
        url = urlsplit(photo["base_url"])
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
            raise ValueError("ComfyUI URL must be HTTP(S), without embedded credentials")
        if not photo["workflow"] or not photo["identity_prompt"].strip():
            raise ValueError("Photos need an API workflow and confirmed visual identity")
    prior_end = 0
    for activity in cfg["world"]["routine"]:
        start = minutes(activity["start"])
        end = 1440 if activity["end"] == "24:00" else minutes(activity["end"])
        if not prior_end <= start < end:
            raise ValueError("Routine intervals must be ordered, non-overlapping, within a day")
        if not activity.get("activity") or not activity.get("location"):
            raise ValueError("Routine intervals need activity and location")
        prior_end = end
    if cfg["mode"] == "assistant" and cfg["world"]["routine"]:
        raise ValueError("Assistant mode does not simulate a private life; use companion mode")
    if cfg["integration"]["adapter"] not in ("hermes", "openclaw", "generic"):
        raise ValueError("Choose hermes, openclaw or generic")
    for key, options in cfg["world"]["visual_options"].items():
        if not isinstance(options, list) or not all(isinstance(i, str) for i in options):
            raise ValueError(f"visual_options.{key} must be a string array")
    return cfg


def load(home, agent_id):
    valid_id(agent_id)
    base = Path(home).expanduser().resolve()
    agent_home = base / "agents" / agent_id
    path = agent_home / "agent.json"
    if path.is_symlink() or agent_home.is_symlink():
        raise ValueError("Agent configuration must not redirect through a symlink")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    validate(cfg)
    if cfg["agent_id"] != agent_id:
        raise ValueError("Agent ID does not match its directory")
    return cfg, agent_home


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
