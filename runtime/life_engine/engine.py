import hashlib
import json
import random
import uuid

from .config import minutes


def quiet(clock, interval):
    start, end = map(minutes, interval)
    # Equal endpoints explicitly disable quiet hours.
    if start == end:
        return False
    return start <= clock < end if start < end else clock >= start or clock < end


class Engine:
    def __init__(self, cfg, store):
        self.cfg, self.store = cfg, store

    def _plan(self, db, now):
        day = now.date().isoformat()
        row = db.execute("SELECT plan FROM days WHERE day=?", (day,)).fetchone()
        if row:
            return json.loads(row["plan"])
        seed = hashlib.sha256(f"{self.cfg['seed']}:{self.cfg['agent_id']}:{day}".encode()).digest()
        rng = random.Random(seed)
        social = self.cfg["social"]
        count = min(len(social["windows"]), rng.randint(social["daily_min"], social["daily_max"]))
        windows = rng.sample(social["windows"], count)
        slots = []
        for start, end in windows:
            clock = rng.randrange(minutes(start), minutes(end))
            slots.append({"time": f"{clock // 60:02d}:{clock % 60:02d}",
                          "photo": rng.random() < self.cfg["photos"]["probability"]})
        visual = {k: rng.choice(v) for k, v in self.cfg["world"]["visual_options"].items() if v}
        plan = {"day": day, "slots": sorted(slots, key=lambda s: s["time"]), "visual": visual,
                "routine": self.cfg["world"]["routine"]}
        db.execute("INSERT INTO days VALUES(?,?)", (day, json.dumps(plan, ensure_ascii=False)))
        return plan

    def _moment(self, now, plan):
        moment = {"time": now.isoformat(timespec="minutes"), "mode": self.cfg["mode"],
                  "origin": "fictional_role_state" if self.cfg["mode"] == "companion" else "recorded_context",
                  "visual": plan["visual"] if self.cfg["mode"] == "companion" else {}}
        if self.cfg["mode"] == "companion":
            clock = now.hour * 60 + now.minute
            for activity in plan["routine"]:
                end = 1440 if activity["end"] == "24:00" else minutes(activity["end"])
                if minutes(activity["start"]) <= clock < end:
                    moment.update({k: v for k, v in activity.items() if k not in ("start", "end", "visual")})
                    moment["visual"] = {**moment["visual"], **activity.get("visual", {})}
                    break
            moment["scene"] = self.cfg["world"]["scene"]
            weather = self.cfg["world"].get("weather")
            if weather:
                moment["weather"] = weather
        return moment

    def status(self, now):
        with self.store.tx() as db:
            from .rp_sessions import active
            if active(db):
                return {'agent_id': self.cfg['agent_id'], **self._context(db)}
            plan = self._plan(db, now)
            return {"agent_id": self.cfg["agent_id"], "moment": self._moment(now, plan),
                    "today": plan, **self._context(db)}

    def _context(self, db):
        data = self.store.context(db)
        if not self.cfg["memory"]["enabled"]:
            data["memories"] = []
            data["open_loops"] = []
            data["recent_user_messages"] = []
        return data

    def wake(self, now, preview=False):
        # One transaction covers day creation, budget checks and slot claim.
        # Concurrent wake invocations cannot create duplicate contacts.
        with self.store.tx() as db:
            from .rp_sessions import active
            if active(db):
                return {'agent_id': self.cfg['agent_id'], 'action': 'silent', 'reason': 'roleplay_active', 'preview': preview}
            plan = self._plan(db, now)
            moment = self._moment(now, plan)
            context = self._context(db)
            base = {"agent_id": self.cfg["agent_id"], "moment": moment, "preview": preview}

            def silent(reason):
                return {**base, "action": "silent", "reason": reason}

            social = self.cfg["social"]
            paused = db.execute("SELECT value FROM meta WHERE key='paused'").fetchone()
            if not social["enabled"] or paused and paused["value"] == "true":
                return silent("paused")
            clock = now.hour * 60 + now.minute
            if quiet(clock, social["quiet_hours"]):
                return silent("quiet_hours")
            at = now.timestamp()
            count = db.execute("SELECT COUNT(*) FROM contacts WHERE day=?", (plan["day"],)).fetchone()[0]
            if count >= social["daily_max"]:
                return silent("daily_budget")
            last = db.execute("SELECT MAX(at) FROM contacts").fetchone()[0]
            if last is not None and at - last < social["min_gap_minutes"] * 60:
                return silent("contact_cooldown")
            inbound = db.execute("SELECT MAX(at) FROM observations").fetchone()[0]
            if inbound is not None and at - inbound < social["recent_chat_minutes"] * 60:
                return silent("recent_conversation")
            if self.cfg["mode"] == "assistant":
                # A role with no virtual life needs a recorded, due reason to contact.
                if not any(item["due"] is not None and item["due"] <= at for item in context["open_loops"]):
                    return silent("no_due_followup")
            slot = None
            for candidate in plan["slots"]:
                if 0 <= clock - minutes(candidate["time"]) <= social["slot_grace_minutes"]:
                    found = db.execute("SELECT 1 FROM contacts WHERE day=? AND slot=?",
                                       (plan["day"], candidate["time"])).fetchone()
                    if not found:
                        slot = candidate
                        break
            if slot is None:
                return silent("no_due_slot")
            photo_count = db.execute("SELECT COUNT(*) FROM photos WHERE day=?", (plan["day"],)).fetchone()[0]
            payload = {**base, "action": "contact", "persona": "inherit_existing_soul",
                       "photo_requested": bool(slot["photo"] and self.cfg["photos"]["enabled"]
                                               and photo_count < self.cfg["photos"]["daily_max"]),
                       **context}
            if not preview:
                event_id = uuid.uuid4().hex
                db.execute("INSERT INTO contacts(id,day,slot,at,status,payload) VALUES(?,?,?,?,?,?)",
                           (event_id, plan["day"], slot["time"], at, "claimed",
                            json.dumps(payload, ensure_ascii=False)))
                payload["contact_id"] = event_id
            return payload
