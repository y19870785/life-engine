import json
import re
import secrets
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

TOKENS = {"{{POSITIVE_PROMPT}}", "{{NEGATIVE_PROMPT}}", "{{SEED}}", "{{WIDTH}}", "{{HEIGHT}}"}


def media_directive(path):
    text = str(path)
    return "MEDIA:" + (f'"{text}"' if any(c.isspace() for c in text) else text)


def inspect_workflow(path):
    graph = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(graph, dict) or not graph or "nodes" in graph:
        raise ValueError("Export the ComfyUI API graph, not the UI workflow")
    if any(not isinstance(n, dict) or not isinstance(n.get("inputs"), dict) or "class_type" not in n
           for n in graph.values()):
        raise ValueError("Each API node must have class_type and inputs")
    content = json.dumps(graph)
    if "{{POSITIVE_PROMPT}}" not in content:
        raise ValueError("Place {{POSITIVE_PROMPT}} in the positive text input")
    unknown = set(re.findall(r"\{\{[A-Z_]+\}\}", content)) - TOKENS
    if unknown:
        raise ValueError(f"Unknown workflow placeholders: {sorted(unknown)}")
    return graph


def replace_tokens(value, tokens):
    if isinstance(value, dict):
        return {k: replace_tokens(v, tokens) for k, v in value.items()}
    if isinstance(value, list):
        return [replace_tokens(v, tokens) for v in value]
    if isinstance(value, str):
        if value in tokens:
            return tokens[value]
        for token, replacement in tokens.items():
            value = value.replace(token, str(replacement))
    return value


def render_prompt(cfg, moment, kind):
    photo = cfg["photos"]
    parts = [photo["identity_prompt"], kind, "casual smartphone photograph"]
    if kind == "life_detail":
        parts += ["point of view photograph of an everyday object or scene, no face required"]
    for field in ("time", "activity", "location", "scene"):
        if moment.get(field):
            parts.append(f"{field}: {moment[field]}")
    parts += [f"{k}: {v}" for k, v in moment.get("visual", {}).items()]
    weather = moment.get("weather")
    if weather:
        parts.append(f"weather: {weather}")
    return ", ".join(parts)


class ComfyUI:
    def __init__(self, url):
        self.url = url.rstrip("/")

    def json(self, path, body=None, timeout=10):
        req = urllib.request.Request(self.url + path,
              data=json.dumps(body).encode() if body is not None else None,
              headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.load(res)

    def generate(self, graph, timeout, queued):
        deadline = time.monotonic() + timeout
        result = self.json("/prompt", {"prompt": graph, "client_id": uuid.uuid4().hex})
        if not result.get("prompt_id"):
            raise RuntimeError("ComfyUI did not accept the workflow")
        prompt_id = result["prompt_id"]
        queued(prompt_id)
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            history = self.json("/history/" + urllib.parse.quote(prompt_id), timeout=max(0.1, min(10, remaining)))
            record = history.get(prompt_id)
            if record:
                if record.get("status", {}).get("status_str") == "error":
                    raise RuntimeError("ComfyUI execution failed; inspect this prompt in ComfyUI history")
                for output in record.get("outputs", {}).values():
                    for img in output.get("images", []):
                        if img.get("type") == "output":
                            return img
            time.sleep(min(1, max(0, deadline - time.monotonic())))
        raise TimeoutError("Image generation timed out; the existing ComfyUI prompt may still complete")

    def download(self, info, target):
        query = urllib.parse.urlencode({k: info.get(k, "") for k in ("filename", "subfolder", "type")})
        partial = target.with_suffix(target.suffix + ".partial")
        with urllib.request.urlopen(self.url + "/view?" + query, timeout=30) as res:
            body = res.read(32 * 1024 * 1024 + 1)
        if len(body) > 32 * 1024 * 1024 or not body:
            raise ValueError("Image download empty or larger than 32 MiB")
        if not (body.startswith(b"\x89PNG\r\n\x1a\n") or body.startswith(b"\xff\xd8\xff")
                or body.startswith(b"RIFF") and body[8:12] == b"WEBP"):
            raise ValueError("Response is not a supported image")
        partial.write_bytes(body)
        partial.replace(target)


def photo(cfg, agent_home, store, engine, now, contact_id=None, kind="selfie", dry_run=False, client=None):
    with store.tx() as db:
        store.require_soul(db)
    conf = cfg["photos"]
    if not conf["enabled"]:
        raise ValueError("Photos are disabled for this agent")
    if kind not in conf["kinds"]:
        raise ValueError("Photo kind not enabled for this agent")
    graph = inspect_workflow(agent_home / conf["workflow"])
    if contact_id:
        with store.tx() as db:
            record = db.execute("SELECT * FROM contacts WHERE id=?", (contact_id,)).fetchone()
            if not record:
                raise ValueError("Contact does not belong to this agent")
            moment = json.loads(record["payload"])["moment"]
    else:
        moment = engine.status(now)["moment"]
    prompt = render_prompt(cfg, moment, kind)
    rendered = replace_tokens(graph, {
        "{{POSITIVE_PROMPT}}": prompt, "{{NEGATIVE_PROMPT}}": conf["negative_prompt"],
        "{{WIDTH}}": conf["width"], "{{HEIGHT}}": conf["height"], "{{SEED}}": secrets.randbits(63),
    })
    if dry_run:
        return {"dry_run": True, "prompt": prompt, "workflow": rendered}
    day = now.date().isoformat()
    photo_id = uuid.uuid4().hex
    with store.tx() as db:
        existing = db.execute("SELECT * FROM photos WHERE contact_id=?", (contact_id,)).fetchone() if contact_id else None
        if existing:
            if existing["status"] == "ready" and Path(existing["path"]).is_file():
                return {"status": "ready", "path": existing["path"], "media": media_directive(existing["path"])}
            raise ValueError("This photo was already attempted; inspect its ComfyUI prompt before retrying")
        count = db.execute("SELECT COUNT(*) FROM photos WHERE day=?", (day,)).fetchone()[0]
        if count >= conf["daily_max"]:
            raise ValueError("Photo attempt budget reached today")
        db.execute("INSERT INTO photos(id,contact_id,day,at,status,prompt) VALUES(?,?,?,?,?,?)",
                   (photo_id, contact_id, day, now.timestamp(), "claimed", prompt))
    client = client or ComfyUI(conf["base_url"])

    def queued(prompt_id):
        with store.tx() as db:
            db.execute("UPDATE photos SET status='queued',prompt_id=? WHERE id=?", (prompt_id, photo_id))

    try:
        info = client.generate(rendered, conf["timeout_seconds"], queued)
        suffix = Path(info["filename"]).suffix.lower()
        if suffix not in (".png", ".jpg", ".jpeg", ".webp"):
            raise ValueError("Unsupported image extension")
        target = agent_home / "photos" / (photo_id + suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        client.download(info, target)
        with store.tx() as db:
            db.execute("UPDATE photos SET status='ready',path=? WHERE id=?", (str(target), photo_id))
        # Existing Hermes MEDIA regexes differ in how paths with spaces are parsed.
        # Quoted path works with current Hermes; the guide calls for a native media test.
        media = media_directive(target)
        return {"status": "ready", "path": str(target), "media": media}
    except Exception:
        with store.tx() as db:
            db.execute("UPDATE photos SET status='unknown' WHERE id=?", (photo_id,))
        raise
