"""从 C2 审定快照抽出的纯选择闭包；不导入 Hermes provider。"""
import unicodedata
MAX_HIGHLIGHT_BYTES = 180
MAX_HIGHLIGHTS = 6

def _excerpt(text, maximum=MAX_HIGHLIGHT_BYTES):
    flat = ' '.join(text.split())
    return flat.encode('utf-8')[:maximum].decode('utf-8', 'ignore')



def _select_highlights(records):
    """按追加序位选原文摘录：三个结构锚点，再以最远位置补齐。"""
    from life_engine.domain import SourceType
    first, latest, candidates, extent = None, {}, {}, 0
    for index, record in enumerate(records):
        extent = index + 1
        text = _excerpt(record.content)
        if not text:
            continue
        candidates.setdefault(text, index)
        if first is None:
            first = (text, index)
        source = record.provenance.source_type
        if source in (SourceType.USER_REPORT, SourceType.MODEL):
            latest[source] = (text, index)
    if first is None:
        return ()
    selected = {}
    for anchor in (first, latest.get(SourceType.USER_REPORT), latest.get(SourceType.MODEL)):
        if anchor is not None:
            text, position = anchor
            selected.setdefault(text, position)
    remaining = {text: (index, extent)
                 for text, index in candidates.items() if text not in selected}

    def update_distances(position):
        for text, (index, distance) in remaining.items():
            remaining[text] = (index, min(distance, abs(index - position)))

    for position in selected.values():
        update_distances(position)
    while remaining and len(selected) < MAX_HIGHLIGHTS:
        text = max(remaining, key=lambda item: (remaining[item][1], -remaining[item][0]))
        position, _ = remaining.pop(text)
        selected[text] = position
        update_distances(position)
    return tuple(sorted(selected, key=selected.get))



MAX_QUERY_BYTES = 4096



QUOTE_PAIRS = {'「': '」', '『': '』', '“': '”', '"': '"'}



QUOTE_CHARS = frozenset(QUOTE_PAIRS) | frozenset(QUOTE_PAIRS.values())



FRAMEWORK_WORDS = frozenset('''a an the and or but if then else of to in on at by for from with into onto as
is am are was were be been being do does did can could may might must shall should will would have has had
i me my mine we us our ours you your yours he him his she her hers it its they them their theirs
this that these those what which who whom whose when where why how please tell explain describe
recall remember about again ever still'''.split())



class RecallQueryError(Exception):
    """输入无效；固定代码不回显原始查询。"""
    code = 'QUERY_INVALID'

    def __init__(self):
        super().__init__(self.code)



def validate_query(query, limit, maximum):
    """即使 limit=0 也完整校验，不截断非法输入。"""
    if type(limit) is not int or not 0 <= limit <= maximum:
        raise RecallQueryError()
    if query is None:
        query = ''
    if type(query) is not str:
        raise RecallQueryError()
    try:
        if len(query.encode('utf-8')) > MAX_QUERY_BYTES:
            raise RecallQueryError()
        normalized = unicodedata.normalize('NFKC', query).casefold()
        if len(normalized.encode('utf-8')) > MAX_QUERY_BYTES:
            raise RecallQueryError()
    except UnicodeError:
        raise RecallQueryError() from None
    return normalized



def _cjk_range(char):
    point = ord(char)
    return (0x3400 <= point <= 0x9fff or 0x20000 <= point <= 0x323af
            or 0x3040 <= point <= 0x30ff or 0xac00 <= point <= 0xd7af
            or 0xf900 <= point <= 0xfaff)



def _cjk(char):
    return _cjk_range(char) and unicodedata.category(char)[0] not in 'PSC'



def _join_cjk(text, predicate=_cjk):
    result, index = [], 0
    while index < len(text):
        if text[index].isspace() and text[index] not in '\r\n':
            end = index + 1
            while end < len(text) and text[end].isspace() and text[end] not in '\r\n':
                end += 1
            if result and predicate(result[-1]) and end < len(text) and predicate(text[end]):
                index = end
                continue
        result.append(text[index])
        index += 1
    return ''.join(result)



def _runs(text):
    """每个标点、换行、引号及文字类别边界均终止 run。"""
    current, kind = [], None
    for char in _join_cjk(text):
        next_kind = 'cjk' if _cjk(char) else ('word' if char.isalnum() or char == '_' else None)
        if next_kind != kind or next_kind is None:
            if current:
                yield kind, ''.join(current)
            current, kind = [], next_kind
        if next_kind is not None:
            current.append(char)
    if current:
        yield kind, ''.join(current)



def _latin(word):
    return all(char.isalpha() and unicodedata.name(char, '').startswith('LATIN') for char in word)



def _features(text, *, short=False, framework=False):
    features = set()
    for kind, word in _runs(text):
        if kind == 'cjk':
            # 短锚点是完整2/3字 run，不从长问句内部提取短 n-gram。
            if short and len(word) in (2, 3):
                features.add((kind, word))
            for size in range(4, min(8, len(word)) + 1):
                features.update((kind, word[index:index + size]) for index in range(len(word) - size + 1))
        elif (_latin(word) and len(word) >= (2 if short else 4)
              and (not framework or word not in FRAMEWORK_WORDS)):
            features.add((kind, word))
    return features



def _quoted(text):
    """只给闭合且非嵌套的固定成对引号生成 anchor；分隔符仍留给 run 边界。"""
    anchors, stack, start, valid = [], [], 0, True
    for index, char in enumerate(text):
        if char not in QUOTE_CHARS:
            continue
        if stack and char == stack[-1]:
            stack.pop()
            if not stack and valid:
                anchors.append(text[start:index])
        elif char in QUOTE_PAIRS:
            if not stack:
                start, valid = index + 1, True
            else:
                valid = False
            stack.append(QUOTE_PAIRS[char])
        elif stack:
            valid = False
    return anchors



def _outer_punctuation(text):
    start, end = 0, len(text)
    while start < end and (text[start].isspace() or unicodedata.category(text[start]).startswith('P')):
        start += 1
    while end > start and (text[end - 1].isspace() or unicodedata.category(text[end - 1]).startswith('P')):
        end -= 1
    return text[start:end]



def _label(text):
    # 标签保留旧范围的空白兼容；普通事件用带类别过滤的_cjk。
    return ' '.join(_join_cjk(unicodedata.normalize('NFKC', text).casefold(), _cjk_range).split())



def _identifier(text):
    """明确独立/引用的连续 Han+ASCII 数字标识；不跨空白组装。"""
    text = text.strip()
    index = len(text)
    while index and '0' <= text[index - 1] <= '9':
        index -= 1
    if index < 4 or index == len(text):
        return None
    if all(0x3400 <= ord(char) <= 0x9fff or 0x20000 <= ord(char) <= 0x323af
           or 0xf900 <= ord(char) <= 0xfaff for char in text[:index]):
        return text
    return None



def _identifier_match(identifier, text):
    start = text.find(identifier)
    while start >= 0:
        end = start + len(identifier)
        if end == len(text) or not '0' <= text[end] <= '9':
            return True
        start = text.find(identifier, start + 1)
    return False



def _bullets(content):
    lines = content.splitlines()
    if (not lines or lines[0] != '[角色扮演回忆]'
            or lines[-1] != '这是一次角色扮演经历，不是真实发生过的事实。'
            or lines.count('期间记得的事：') != 1):
        return ()
    result = []
    for line in lines[lines.index('期间记得的事：') + 1:]:
        if not line.startswith('- '):
            break
        result.append(unicodedata.normalize('NFKC', line[2:]).casefold())
    return result



def select_recall(records, query, limit):
    """query 已校验/归一化；返回原对象，全部强证据候选按证据长度再时间排序。"""
    order = lambda record: (record.created_at, str(record.memory_id))
    if not query.strip():
        return sorted(records, key=order, reverse=True)[:limit]
    anchors = _quoted(query)
    independent = _outer_punctuation(query) if not (set(query) & QUOTE_CHARS) else ''
    independent_id = _identifier(independent)
    identifiers = {_identifier(anchor) for anchor in anchors}
    identifiers.discard(None)
    if independent_id:
        identifiers.add(independent_id)
    # 明确编号是完整锚点；不能再用它的共同中文前缀召回其他编号。
    strong_text = '' if independent_id else query
    for anchor in anchors:
        if _identifier(anchor):
            strong_text = strong_text.replace(anchor, ' ')
    runs = list(_runs(independent))
    single = (len(runs) == 1 and runs[0][1] == _join_cjk(independent))
    wanted = _features(strong_text, framework=not single)
    if single:
        wanted |= _features(independent, short=True)
    for anchor in anchors:
        if not _identifier(anchor):
            wanted |= _features(anchor, short=True)
    event_matches = []
    for record in records:
        evidence = set()
        for bullet in _bullets(record.content):
            evidence.update(('identifier', value) for value in identifiers if _identifier_match(value, bullet))
            # 正文可供完整短词寻找，但每个 bullet 独立，不拼成跨边界词。
            for kind, word in _runs(bullet):
                if kind == 'cjk':
                    for size in range(2, min(8, len(word)) + 1):
                        evidence.update((kind, word[index:index + size]) for index in range(len(word) - size + 1))
                elif _latin(word) and len(word) >= 2:
                    evidence.add((kind, word))
        common = (wanted | {('identifier', value) for value in identifiers}) & evidence
        if common:
            event_matches.append((max(min(8, len(word)) for _, word in common), record))
    if event_matches:
        event_matches.sort(key=lambda item: (item[0], *order(item[1])), reverse=True)
        return [record for _, record in event_matches[:limit]]
    explicit_labels = {_label(anchor) for anchor in anchors}
    if independent:
        explicit_labels.add(_label(independent))
    character_matches = []
    for record in records:
        labels = {_label(subject.text) for subject in record.subjects if subject.kind.value == 'text'}
        labels.discard('角色扮演')
        labels.discard('')
        if labels & explicit_labels:
            character_matches.append(record)
    return sorted(character_matches, key=order, reverse=True)[:limit]
