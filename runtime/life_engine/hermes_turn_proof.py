"""Read-only proof of exactly two current Hermes CLI message rows.

Completion hooks alone are not durability evidence. No scanning of private history,
no schema repair, no inference from matching text alone, no delivery/ACK assertion.
"""
from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def safe_db(home):
    home = Path(home).absolute()
    path = home / 'state.db'
    if any(p.is_symlink() or (p.exists() and bool(getattr(p.lstat(), 'st_file_attributes', 0) & 0x400))
           for p in (path, *path.parents)) or not path.is_file():
        raise ValueError('HOST_DB_UNAVAILABLE')
    return path


def watermark(home, session):
    path = safe_db(home)
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
        return db.execute('SELECT coalesce(max(id),0) FROM messages WHERE session_id=?', (session,)).fetchone()[0]


def verify_pair(home, frame):
    if (frame.get('completed') is not True or frame.get('failed') is not False or
            frame.get('interrupted') is not False or
            frame.get('turn_exit_reason') not in ('text_response(finish_reason=stop)',
                                                  'text_response(finish_reason=end_turn)')):
        raise ValueError('TURN_NOT_COMPLETE')
    for name in ('session_id', 'turn_id', 'user_uid', 'assistant_uid', 'user_text', 'assistant_text'):
        if not isinstance(frame.get(name), str) or not frame[name].strip():
            raise ValueError('TURN_IDENTITY_REQUIRED')
    if (frame['user_uid'] == frame['assistant_uid'] or type(frame.get('watermark')) is not int
            or frame['watermark'] < 0):
        raise ValueError('TURN_IDENTITY_REQUIRED')
    path = safe_db(home)
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN')
        session = db.execute('SELECT source FROM sessions WHERE id=?', (frame['session_id'],)).fetchone()
        if session is None or session['source'] not in ('cli', 'tool'):
            raise ValueError('CLI_SESSION_REQUIRED')
        rows = []
        for role, field in (('user', 'user_uid'), ('assistant', 'assistant_uid')):
            found = db.execute('SELECT id,content,tool_calls,active,compacted FROM messages '
                'WHERE session_id=? AND role=? AND message_uid=? AND active=1',
                (frame['session_id'], role, frame[field])).fetchall()
            if len(found) != 1:
                raise ValueError('UNIQUE_COMMITTED_ROW_REQUIRED')
            row = found[0]
            if row['compacted'] or row['tool_calls'] not in (None, '', '[]'):
                raise ValueError('ORDINARY_TEXT_ROW_REQUIRED')
            if not isinstance(row['content'], str) or digest(row['content']) != digest(frame[role + '_text']):
                raise ValueError('COMMITTED_TEXT_MISMATCH')
            rows.append(row)
        if not rows[0]['id'] < rows[1]['id'] or rows[1]['id'] <= frame['watermark']:
            raise ValueError('NEW_FINAL_ROW_REQUIRED')
        # A clean final row cannot prove an intervening tool/reasoning round safe.
        # Inspect only the bounded current-turn interval, never previous history.
        if db.execute('SELECT 1 FROM messages WHERE session_id=? AND active=1 '
                      'AND id>? AND id<? LIMIT 1',
                      (frame['session_id'], rows[0]['id'], rows[1]['id'])).fetchone():
            raise ValueError('ORDINARY_TEXT_PAIR_REQUIRED')
        source = digest('|'.join((str(Path(home).resolve()), frame['session_id'],
                                 frame['user_uid'], frame['assistant_uid'])))
        return {'source': source, 'user_row': rows[0]['id'], 'assistant_row': rows[1]['id'],
                'user_sha256': digest(frame['user_text']), 'assistant_sha256': digest(frame['assistant_text']),
                'scope': 'persisted CLI text pair; not delivery acknowledgement'}
