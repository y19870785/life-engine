"""One deterministic /rp dispatcher shared by CLI and host adapters."""
import shlex

from .rp_sessions import active, card_row, import_card, import_book, status, transition, record_message
from .rp_prompt import build_prompt


def dispatch(store, cfg, command):
    text = command.strip()
    if text in ('退出角色','退出扮演'):
        text = 'exit'
    if text.startswith('/rp '):
        text = text[4:]
    if text == '/rp':
        text = 'status'
    # posix=False preserves Windows path backslashes. Quote paths/names with spaces.
    parts = [p[1:-1] if len(p)>=2 and p[0]==p[-1] and p[0] in "\"'" else p
             for p in shlex.split(text, posix=False)]
    action = parts.pop(0) if parts else 'status'
    if action in ('enter','switch','exit'):
        if (action=='exit' and parts) or (action!='exit' and not parts):
            raise ValueError('Usage: /rp enter|switch <card name>, /rp exit')
        return transition(store, action, ' '.join(parts) if parts else None,
                          memory_enabled=cfg['memory']['enabled'])
    if action=='import' and len(parts)==1:
        return import_card(store, parts[0])
    if action=='book' and len(parts)==2:
        return import_book(store, parts[0], parts[1])
    if action=='context' and not parts:
        return build_prompt(store, cfg)
    if action=='aside':
        return {**build_prompt(store,cfg,aside=True), 'question': ' '.join(parts)}
    if action=='record' and len(parts)>=2 and parts[0] in ('user','assistant'):
        if not cfg['memory']['enabled']:
            raise ValueError('Memory is disabled')
        return {'ok': record_message(store, ' '.join(parts[1:]), parts[0])}
    with store.tx() as db:
        if action=='status' and not parts:
            return {'ok': True, **status(db)}
        if action=='who' and not parts:
            state=status(db)
            identity=cfg.get('display_name') or '宿主原有 SOUL 定义的身份'
            return {'ok': True, **state, 'message': f"我是 {identity}" +
                    (f"，目前正在扮演 {state['card_name']}。" if state['mode']=='roleplay' else '，目前使用原有 SOUL 身份。')}
        if action=='list' and not parts:
            return {'ok': True, 'cards': [dict(r) for r in db.execute(
                'SELECT id,name,created_at,avatar IS NOT NULL AS has_avatar FROM roleplay_cards ORDER BY name')]}
        if action=='show' and parts:
            card = dict(card_row(db, ' '.join(parts)))
            card['avatar_saved'] = card.pop('avatar') is not None
            return {'ok': True, 'card': card}
        if action=='delete' and parts:
            card = card_row(db, ' '.join(parts))
            current = active(db)
            if current and current['card_id']==card['id']:
                raise ValueError('Exit this character before deleting it')
            db.execute('DELETE FROM roleplay_cards WHERE id=?', (card['id'],))
            return {'ok': True, 'deleted': card['name'], 'note': 'Persona history deleted; Soul meta-memories retained'}
    raise ValueError('Usage: /rp list|status|import <path>|show <name>|delete <name>|enter <name>|switch <name>|exit|book "name" "path"|context|aside <question>|record user|assistant <text>')
