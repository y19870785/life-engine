"""Plan/apply/rollback for a local agent extension. Never edits host config or credentials."""
import base64
import hashlib
import json
import os
import re
import stat
import tempfile
import uuid
from pathlib import Path

from .config import json_bytes, validate, valid_id
from .photos import inspect_workflow


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f"Refusing a symlink target: {path}")
    if path.exists():
        if not path.is_file():
            raise ValueError(f"Expected a file: {path}")
        return digest(path.read_bytes())
    return None


def no_symlinks(path):
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError(f"Path traverses a symlink: {parent}")


def atomic_write(path, content, mode=0o600):
    path = Path(path)
    no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".pending", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def inspect_host(host, adapter="generic", soul=None):
    host = Path(host).expanduser().absolute()
    if not host.is_dir():
        raise ValueError("Choose an existing Agent directory")
    no_symlinks(host)
    soul = Path(soul).expanduser().absolute() if soul else host / "SOUL.md"
    if not soul.is_relative_to(host) or soul.name.upper() != "SOUL.MD":
        raise ValueError("Select a SOUL.md inside the selected Agent directory")
    no_symlinks(soul)
    raw = soul.read_bytes() if soul.is_file() else b""
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("SOUL is too large for automatic local inspection")
    text = raw.decode("utf-8-sig")
    match = re.search(r"(?im)^\s*(?:[-*]\s*)?(?:name|姓名|名字|名称)\s*[:：]\s*([^\r\n]{1,80})\r?$", text)
    warnings = []
    lower = text.lower()
    if any(term in lower for term in ("不要主动", "禁止主动", "不得主动", "never initiate", "do not initiate")):
        warnings.append("SOUL 中发现可能限制主动联系的语句；引导仅做关键词提示，请按原规则选择关闭主动联系。")
    if (host / "data" / "xiaoxue-life" / "life.db").exists():
        warnings.append("发现 v0.1 数据。安装不会改它；可用 migrate-v01 复制导入，切换前停用旧定时任务。")
    tracked = {}
    for path in (soul, host / "config.yaml", host / "config.json", host / "openclaw.json"):
        if path.is_file():
            tracked[str(path)] = file_hash(path)
    cron_count = None
    cron_file = host / "cron" / "jobs.json"
    if adapter == "hermes" and cron_file.is_file():
        try:
            data = json.loads(cron_file.read_text(encoding="utf-8"))
            jobs = data.get("jobs", []) if isinstance(data, dict) else data
            cron_count = len(jobs)
            if any("xiaoxue-life" in json.dumps(j) or "life-engine" in json.dumps(j) for j in jobs):
                warnings.append("发现可能已存在的生活引擎定时任务；请核对，避免新旧同时唤醒。")
        except (ValueError, TypeError):
            warnings.append("已有 Cron 文件无法自动识别，请在宿主中查看任务。")
    return {
        "host_home": str(host), "adapter": adapter, "soul_path": str(soul),
        "soul_exists": soul.is_file(), "soul_sha256": file_hash(soul),
        "name_suggestion": match.group(1).strip() if match else "",
        "credentials_present": (host / ".env").is_file(), "cron_count": cron_count,
        "warnings": warnings, "source_hashes": tracked,
    }


def discover_homes():
    results = []
    roots = [Path.home() / ".hermes"]
    if os.environ.get("HERMES_HOME"):
        roots.insert(0, Path(os.environ["HERMES_HOME"]).expanduser())
    seen = set()
    for root in roots:
        candidates = [root]
        if (root / "profiles").is_dir():
            candidates += sorted(p for p in (root / "profiles").iterdir() if p.is_dir())
        for candidate in candidates:
            if candidate.is_dir() and (candidate / "config.yaml").is_file() and str(candidate.absolute()) not in seen:
                seen.add(str(candidate.absolute()))
                results.append({"home": str(candidate.absolute()), "label": candidate.name, "adapter": "hermes"})
    return results


def soul_block(agent_id, host, soul_bytes):
    newline = "\r\n" if b"\r\n" in soul_bytes else "\n"
    begin = f"<!-- life-engine:{agent_id}:begin -->"
    end = f"<!-- life-engine:{agent_id}:end -->"
    block = newline.join([
        begin,
        "## Life Engine capability",
        "Continue using the identity, tone, relationship boundaries and prohibitions defined above.",
        "For current continuity state, explicit follow-ups or the owner's photo requests, read",
        str(host / "life-engine" / "agents" / agent_id / "INTEGRATION.md"),
        "This capability does not redefine your personality. Follow the existing rules on conflicts.",
        end,
    ]).encode("utf-8")
    b_begin, b_end = begin.encode(), end.encode()
    if b_begin in soul_bytes or b_end in soul_bytes:
        if soul_bytes.count(b_begin) != 1 or soul_bytes.count(b_end) != 1:
            raise ValueError("Malformed or duplicate Life Engine SOUL block; inspect manually")
        start, finish = soul_bytes.index(b_begin), soul_bytes.index(b_end) + len(b_end)
        if finish < start:
            raise ValueError("Malformed Life Engine SOUL block")
        return soul_bytes[:start] + block + soul_bytes[finish:]
    return soul_bytes + (newline * 2).encode() + block + newline.encode()


def build_plan(package_root, cfg, append_soul=False, workflow_source=None):
    validate(cfg)
    host = Path(cfg["integration"]["host_home"]).expanduser().absolute()
    info = inspect_host(host, cfg["integration"]["adapter"], cfg["persona"]["soul_path"] or None)
    cfg = json.loads(json.dumps(cfg))
    cfg["persona"]["soul_path"] = info["soul_path"]
    agent_id = cfg["agent_id"]
    base = host / "life-engine"
    agent_home = base / "agents" / agent_id
    if (base / "agents").exists():
        others = [p.name for p in (base / "agents").iterdir()
                  if p.is_dir() and p.name != agent_id and (p / "agent.json").exists()]
        if others:
            raise ValueError(f"This host already belongs to {others}; choose a separate agent home")
    manifest_path = agent_home / "install-manifest.json"
    old = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"owned": {}}
    owned = old["owned"]
    files = {}
    root = Path(package_root)
    files[base / "life.py"] = (root / "life.py").read_bytes()
    for source in sorted((root / "runtime" / "life_engine").glob("*.py")):
        files[base / "runtime" / "life_engine" / source.name] = source.read_bytes()
    if cfg["photos"]["enabled"]:
        source = Path(workflow_source) if workflow_source else agent_home / cfg["photos"]["workflow"]
        inspect_workflow(source)
        files[agent_home / "workflow_api.json"] = source.read_bytes()
        cfg["photos"]["workflow"] = "workflow_api.json"
    from .integration import integration_text, schedule_recipe, skill_text
    files[agent_home / "agent.json"] = json_bytes(cfg)
    files[agent_home / "INTEGRATION.md"] = integration_text(cfg, base).encode("utf-8")
    files[agent_home / "SCHEDULE.md"] = schedule_recipe(cfg, base).encode("utf-8")
    if cfg["integration"]["adapter"] == "hermes":
        skill_dir = host / "skills" / ("life-engine-" + agent_id)
        files[skill_dir / "SKILL.md"] = skill_text(cfg, base).encode("utf-8")
        launcher = (
            "import runpy,sys\n"
            f"sys.argv=[{str(base / 'life.py')!r},'--home',{str(base)!r},'--agent',{agent_id!r}]+sys.argv[1:]\n"
            f"runpy.run_path({str(base / 'life.py')!r},run_name='__main__')\n"
        )
        files[skill_dir / "run.py"] = launcher.encode("utf-8")
    soul_path = Path(info["soul_path"])
    if append_soul:
        files[soul_path] = soul_block(agent_id, host, soul_path.read_bytes() if soul_path.exists() else b"")
    editable = {agent_home / "agent.json", agent_home / "workflow_api.json"}
    writes = []
    for path, data in files.items():
        no_symlinks(path)
        previous = file_hash(path)
        expected = owned.get(str(path))
        if previous and path != soul_path:
            if expected is None:
                raise ValueError(f"File collision with an unmanaged file: {path}")
            if previous != expected and path not in editable:
                raise ValueError(f"Managed integration file was edited since installation: {path}; review before replacing")
        if previous != digest(data):
            writes.append({"path": str(path), "before": previous, "after": digest(data),
                           "content": base64.b64encode(data).decode(),
                           "mode": stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600})
    new_owned = {str(p): digest(data) for p, data in files.items() if p != soul_path}
    manifest = {"version": 2, "agent_id": agent_id, "owned": {**owned, **new_owned},
                "soul_path": str(soul_path), "soul_hook": append_soul or old.get("soul_hook", False)}
    manifest_data = json_bytes(manifest)
    if file_hash(manifest_path) != digest(manifest_data):
        writes.append({"path": str(manifest_path), "before": file_hash(manifest_path),
                       "after": digest(manifest_data), "content": base64.b64encode(manifest_data).decode(),
                       "mode": 0o600})
    source_hashes = dict(info["source_hashes"])
    source_hashes[str(soul_path)] = info["soul_sha256"]
    return {"version": 2, "id": uuid.uuid4().hex, "agent_id": agent_id, "host": str(host),
            "base": str(base), "source_hashes": source_hashes, "writes": writes,
            "summary": {"name": cfg["display_name"] or "继承原 SOUL", "mode": cfg["mode"],
                        "proactive": cfg["social"]["enabled"], "daily_max": cfg["social"]["daily_max"],
                        "quiet_hours": cfg["social"]["quiet_hours"], "photos": cfg["photos"]["enabled"],
                        "memory": cfg["memory"]["enabled"], "soul_hook": append_soul,
                        "soul_path": str(soul_path), "adapter": cfg["integration"]["adapter"]},
            "warnings": info["warnings"]}


def plan_view(plan):
    return {
        "agent": plan["agent_id"], **plan["summary"], "host": plan["host"],
        "changes": [{"path": row["path"], "action": "update" if row["before"] else "create"}
                    for row in plan["writes"]],
        "warnings": plan["warnings"],
        "effects": "安装只写本地扩展。不会启动计划任务，也不会发送测试消息。",
    }


def guard_plan(plan):
    host = Path(plan["host"])
    base = host / "life-engine"
    valid_id(plan["agent_id"])
    if str(base) != plan["base"] or not host.is_absolute():
        raise ValueError("Invalid installation root")
    for name, expected in plan["source_hashes"].items():
        path = Path(name)
        if not path.is_relative_to(host):
            raise ValueError("Source outside selected host")
        no_symlinks(path)
        if file_hash(path) != expected:
            raise ValueError(f"Source changed after preview: {path}; rerun setup")
    seen = set()
    for row in plan["writes"]:
        path = Path(row["path"])
        allowed = (path.is_relative_to(base) or
                   path.is_relative_to(host / "skills" / ("life-engine-" + plan["agent_id"])) or
                   path == Path(plan["summary"]["soul_path"]) and path.name.upper() == "SOUL.MD")
        if not allowed or not path.is_relative_to(host) or ".." in path.parts or str(path) in seen:
            raise ValueError("Plan contains an unexpected or duplicate destination")
        seen.add(str(path))
        no_symlinks(path)
        data = base64.b64decode(row["content"], validate=True)
        if digest(data) != row["after"] or file_hash(path) != row["before"]:
            raise ValueError(f"Destination changed or plan damaged: {path}")


def apply_plan(plan):
    guard_plan(plan)
    if not plan["writes"]:
        return {"changed": False, "message": "Already configured"}
    backup = Path(plan["base"]) / "backups" / plan["id"]
    backup.mkdir(parents=True, exist_ok=False)
    journal = {"id": plan["id"], "host": plan["host"], "status": "applying", "files": []}
    for index, row in enumerate(plan["writes"]):
        path = Path(row["path"])
        entry = {k: row[k] for k in ("path", "before", "after", "mode")}
        entry["backup"] = str(backup / f"{index}.bin") if row["before"] else None
        if row["before"]:
            atomic_write(Path(entry["backup"]), path.read_bytes())
        journal["files"].append(entry)
    journal_path = backup / "journal.json"
    atomic_write(journal_path, json_bytes(journal))
    completed = []
    try:
        guard_plan(plan)
        for row in plan["writes"]:
            if file_hash(row["path"]) != row["before"]:
                raise ValueError("A destination changed during apply; stop and re-preview")
            atomic_write(row["path"], base64.b64decode(row["content"]), row["mode"])
            completed.append(row["path"])
        journal["status"] = "applied"
        atomic_write(journal_path, json_bytes(journal))
    except BaseException:
        for row in reversed(journal["files"]):
            if row["path"] in completed and file_hash(row["path"]) == row["after"]:
                if row["backup"]:
                    atomic_write(row["path"], Path(row["backup"]).read_bytes(), row["mode"])
                else:
                    Path(row["path"]).unlink()
        journal["status"] = "failed_reverted"
        atomic_write(journal_path, json_bytes(journal))
        raise
    return {"changed": True, "journal": str(journal_path), "host": plan["host"]}


def rollback(journal_path):
    journal_path = Path(journal_path).absolute()
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    if journal["status"] == "rolled_back":
        return {"changed": False, "message": "Already rolled back"}
    if journal["status"] != "applied":
        raise ValueError("Only an applied installation can be rolled back automatically")
    host = Path(journal["host"])
    for row in journal["files"]:
        path = Path(row["path"])
        if not path.is_relative_to(host) or ".." in path.parts:
            raise ValueError("Rollback path outside selected host")
        no_symlinks(path)
        if file_hash(path) != row["after"]:
            raise ValueError(f"File was edited after installation: {path}; automatic rollback stopped")
        if row["backup"]:
            saved = Path(row["backup"])
            if not saved.is_relative_to(journal_path.parent) or file_hash(saved) != row["before"]:
                raise ValueError("Backup is missing or damaged")
    for row in reversed(journal["files"]):
        if row["backup"]:
            atomic_write(row["path"], Path(row["backup"]).read_bytes(), row["mode"])
        else:
            Path(row["path"]).unlink()
    journal["status"] = "rolled_back"
    atomic_write(journal_path, json_bytes(journal))
    return {"changed": True, "status": "rolled_back", "data": "Existing runtime state retained"}
