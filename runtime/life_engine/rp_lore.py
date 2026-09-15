"""Bounded, literal keyword matching; no regex/macros or remote content execution."""
import json


def token_cost(text):
    # Model-independent conservative budget: one UTF-8 byte is one budget unit.
    # This is NOT an exact tokenizer count. Include JSON framing in the budget.
    return len(text.encode('utf-8'))


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def normalize_book(book):
    if not isinstance(book, dict):
        raise ValueError('World book must be a JSON object')
    rows = book.get('entries', [])
    if isinstance(rows, dict):
        rows = list(rows.values())
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError('World book supports at most 1000 entries')
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('World book entry must be an object')
        ext = row.get('extensions', {})
        if not isinstance(ext, dict):
            raise ValueError('World book extensions must be an object')
        keys = row.get('keys', row.get('key', []))
        if not isinstance(keys, list) or len(keys) > 64 or any(
                not isinstance(k, str) or not k.strip() or len(k) > 200 for k in keys):
            raise ValueError('World book keys must be nonempty literal strings')
        content = row.get('content', '')
        if not isinstance(content, str) or len(content) > 16000:
            raise ValueError('World book content must be text, at most 16000 characters')
        def integer(key, default, alias=None):
            value = row.get(key, row.get(alias, ext.get(key, default)))
            if type(value) is not int or not -100000 <= value <= 100000:
                raise ValueError('Invalid world book ' + key)
            return value
        def boolean(key, default):
            value = row.get(key, ext.get(key, default))
            if type(value) is not bool:
                raise ValueError('Invalid world book ' + key)
            return value
        position = row.get('position', ext.get('position', 'before_char'))
        position = {0: 'before_char', 1: 'after_char', 4: 'at_depth'}.get(position, position) if isinstance(position, (str, int)) else None
        if position not in ('before_char', 'after_char', 'at_depth'):
            raise ValueError('Unsupported world book position')
        depth = integer('depth', 4)
        if not 0 <= depth <= 100:
            raise ValueError('World book depth must be 0..100')
        if row.get('use_regex') or row.get('selective') or row.get('keysecondary') or row.get('secondary_keys'):
            raise ValueError('Regex and secondary-key world entries are not supported; export literal entries')
        result.append({'keys': keys, 'content': content,
                       'insertion_order': integer('insertion_order', 100, 'order'),
                       'priority': integer('priority', 0), 'position': position, 'depth': depth,
                       'enabled': boolean('enabled', not row.get('disable', False)),
                       'case_sensitive': boolean('case_sensitive', False),
                       'recursive': boolean('recursive', True), 'constant': boolean('constant', False)})
    return result


def activate_lore_entries(entries, recent_messages, max_tokens=2000, max_recursion=3, scan_depth=8):
    if not 0 <= max_tokens <= 16000 or not 0 <= max_recursion <= 8 or not 1 <= scan_depth <= 64:
        raise ValueError('Invalid lore budget, recursion or scan depth')
    corpus = '\n'.join(str(m)[-8000:] for m in recent_messages[-scan_depth:])
    selected, seen = [], set()
    ordered = sorted(enumerate(entries), key=lambda p: (-p[1].get('priority', 0), p[1]['insertion_order'], p[0]))
    for level in range(max_recursion + 1):
        additions = []
        for index, entry in ordered:
            if index in seen or not entry['enabled'] or (level and not entry['recursive']):
                continue
            haystack = corpus if entry['case_sensitive'] else corpus.casefold()
            if not entry['constant'] and not any(
                    (k if entry['case_sensitive'] else k.casefold()) in haystack for k in entry['keys']):
                continue
            seen.add(index)
            candidate = {k: entry[k] for k in ('content','insertion_order','position','depth')}
            candidate['entry_id'] = entry.get('id', index)
            if token_cost(encoded(selected + [candidate])) <= max_tokens:
                selected.append(candidate)
                additions.append(entry['content'])
        if not additions:
            break
        corpus += '\n' + '\n'.join(additions)
    return sorted(selected, key=lambda e: (e['insertion_order'], e['entry_id']))
