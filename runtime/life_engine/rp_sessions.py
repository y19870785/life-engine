"""Transactional roleplay state and memory namespaces, one active persona per instance."""
import json
import time
from pathlib import Path

from .rp_cards import parse_card, read_local, MAX_JSON
from .rp_lore import normalize_book


def active(db):
    return db.execute("SELECT s.*,c.name,c.parsed_json FROM roleplay_sessions s JOIN roleplay_cards c "
                      "ON c.id=s.card_id WHERE s.status='active'").fetchone()


def card_row(db, name):
    row = db.execute('SELECT * FROM roleplay_cards WHERE name=? COLLATE NOCASE', (name,)).fetchone()
    if not row:
        raise ValueError('Character card not found: ' + name)
    return row


def import_card(store, path, at=None):
    raw, card, avatar = parse_card(path)
    with store.tx() as db:
        key = db.execute('INSERT INTO roleplay_cards(name,source_path,raw_json,parsed_json,avatar,created_at) '
                         'VALUES(?,?,?,?,?,?)', (card['name'], str(Path(path).expanduser().resolve()),
                         json.dumps(raw, ensure_ascii=False), json.dumps(card, ensure_ascii=False), avatar,
                         at if at is not None else time.time())).lastrowid
        _entries(db, key, 'embedded', card['character_book']['entries'])
    return {'ok': True, 'card_id': key, 'name': card['name'], 'avatar_saved': avatar is not None}


def _entries(db, card_id, book_name, entries):
    db.executemany('INSERT INTO roleplay_lorebook_entries(card_id,book_name,entry_json) VALUES(?,?,?)',
                   [(card_id, book_name, json.dumps(e, ensure_ascii=False)) for e in entries])


def import_book(store, name, path):
    data = read_local(path)
    if len(data) > MAX_JSON:
        raise ValueError('World book JSON exceeds 2 MiB')
    book = json.loads(data.decode('utf-8-sig'))
    entries = normalize_book(book)
    with store.tx() as db:
        card = card_row(db, name)
        book_name = Path(path).name
        db.execute('DELETE FROM roleplay_lorebook_entries WHERE card_id=? AND book_name=?', (card['id'], book_name))
        _entries(db, card['id'], book_name, entries)
    return {'ok': True, 'name': name, 'entries': len(entries)}


def status(db, at=None):
    row = active(db)
    if not row:
        return {'mode': 'soul', 'card_id': None, 'session_id': None}
    return {'mode': 'roleplay', 'card_id': row['card_id'], 'card_name': row['name'],
            'session_id': row['id'], 'started_at': row['started_at'],
            'duration_seconds': max(0, int((at if at is not None else time.time()) - row['started_at']))}


def write_memory(db, at, kind, summary, provenance, session=None):
    if not isinstance(summary, str) or not summary.strip() or len(summary) > 8000:
        raise ValueError('Memory must be 1..8000 characters')
    scope = 'persona' if session else 'soul'
    key = db.execute('INSERT INTO memories(at,kind,summary,provenance,scope,card_id,session_id) '
                     'VALUES(?,?,?,?,?,?,?)', (at, kind, summary, provenance, scope,
                     session['card_id'] if session else None, session['id'] if session else None)).lastrowid
    return key


def remember(store, at, kind, summary, provenance, expected_session=None):
    with store.tx() as db:
        session = active(db)
        if expected_session is not None and expected_session != (session['id'] if session else 0):
            raise ValueError('Roleplay session changed; discard this stale memory write')
        key = write_memory(db, at, kind, summary, provenance, session)
        if session:
            # This is a labeled roleplay experience, never a fact about the real user.
            write_memory(db, at, 'roleplay_meta',
                         f"与用户一起扮演了「{session['name']}」。虚构情节摘录（非现实事实）：{summary[:240]}",
                         f"roleplay:{session['id']}:memory:{key}")
        return key


def finish(db, session, at, memory_enabled=True):
    rows = db.execute("SELECT summary FROM memories WHERE scope='persona' AND session_id=? "
                      'ORDER BY id DESC LIMIT 3', (session['id'],)).fetchall()
    summary = '；'.join(r['summary'][:160] for r in reversed(rows))
    if not summary and memory_enabled:
        messages = db.execute('SELECT role,content FROM roleplay_messages WHERE session_id=? ORDER BY id DESC LIMIT 3',
                              (session['id'],)).fetchall()
        summary = '；'.join(r['role'] + ' 对话摘录：' + r['content'][:160] for r in reversed(messages))
    summary = summary or '本次未记录具体情节。'
    db.execute("UPDATE roleplay_sessions SET status='ended',ended_at=?,summary=? WHERE id=?",
               (at, summary if memory_enabled else '', session['id']))
    if memory_enabled:
        write_memory(db, at, 'session_summary', summary, 'roleplay_session_summary', session)
        write_memory(db, at, 'roleplay_meta',
                     f"与用户一起完成了「{session['name']}」的扮演。虚构情节摘录（非现实事实）：{summary}",
                     f"roleplay:{session['id']}:ended")
    return summary


def transition(store, action, name=None, at=None, memory_enabled=True):
    at = at if at is not None else time.time()
    with store.tx() as db:
        current = active(db)
        card = card_row(db, name) if action in ('enter','switch') else None
        if action == 'enter' and current:
            raise ValueError('Already roleplaying; use /rp switch or /rp exit')
        if action == 'switch' and not current:
            raise ValueError('Not roleplaying; use /rp enter')
        if action == 'switch' and current['card_id'] == card['id']:
            return {'ok': True, **status(db, at), 'message': '已在扮演该角色。'}
        summary = finish(db, current, at, memory_enabled) if current else None
        if action == 'exit':
            return {'ok': True, **status(db, at), 'message': '已退出角色，恢复原有 SOUL 身份。' +
                    ('本次扮演记录（虚构）：' + summary if summary else ''), 'summary': summary}
        db.execute("INSERT INTO roleplay_sessions(agent_id,card_id,started_at,status) VALUES(?,?,?,'active')",
                   (store.agent_id, card['id'], at))
        return {'ok': True, **status(db, at),
                'message': f"好的，我现在将扮演 {card['name']}。你可以随时说 /rp exit 让我回来。",
                'previous_summary': summary}


def record_message(store, content, role='user', event_key=None, at=None, expected_session=None):
    if not isinstance(content, str) or len(content) > 8000 or role not in ('user','assistant'):
        raise ValueError('Invalid roleplay message (maximum 8000 characters)')
    with store.tx() as db:
        session = active(db)
        if not session:
            return False
        if expected_session is not None and session['id'] != expected_session:
            return False
        db.execute('INSERT OR IGNORE INTO roleplay_messages(session_id,card_id,at,role,content,event_key) '
                   'VALUES(?,?,?,?,?,?)', (session['id'],session['card_id'], at or time.time(),role,content,event_key))
        # Only a small local scan window is retained; summaries live in persona memories.
        db.execute('DELETE FROM roleplay_messages WHERE session_id=? AND id NOT IN '
                   '(SELECT id FROM roleplay_messages WHERE session_id=? ORDER BY id DESC LIMIT 64)',
                   (session['id'],session['id']))
    return True
