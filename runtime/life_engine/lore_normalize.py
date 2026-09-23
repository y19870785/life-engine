"""把低信任 LoreIR 归一化为有界、不可执行的注册提案。"""
from dataclasses import dataclass
import hashlib

from .domain import DomainError
from .import_ir import JsonValue, LoreIR, canonical
from .lore import (LoreDiagnostic as D, MAX_ENTRIES_PER_BOOK, MAX_ENTRY_TEXT_BYTES,
                   MAX_INT, MAX_METADATA_BYTES, MAX_TRIGGER_BYTES, byte_size)


@dataclass(frozen=True)
class NormalizedEntry:
    enabled: bool
    constant: bool
    selective: bool
    case_sensitive: bool
    priority: int
    order: int
    text: str
    primary: tuple[str, ...]
    secondary: tuple[str, ...]
    disabled_reason: D | None
    metadata: JsonValue
    diagnostics: tuple[D, ...]


@dataclass(frozen=True)
class NormalizedBook:
    source_type: str
    source_fingerprint: str
    source_metadata: JsonValue
    entries: tuple[NormalizedEntry, ...]
    payload_fingerprint: str | None = None


def normalize_lore_ir(ir, *, payload_fingerprint=None):
    """仅解释明确白名单字段；保留有限来源线索，不执行来源扩展。"""
    if type(ir) is not LoreIR or len(ir.entries) > MAX_ENTRIES_PER_BOOK:
        raise DomainError('LoreIR 类型或条目数量错误')
    if byte_size(ir.metadata.text)>8192 or sum(byte_size(item.text) for item in ir.entries)>16*1024*1024:
        raise DomainError('Lore 来源书元数据越界')
    if payload_fingerprint is not None and (type(payload_fingerprint) is not str or
            len(payload_fingerprint) != 64 or any(c not in '0123456789abcdef' for c in payload_fingerprint)):
        raise DomainError('Lore payload 指纹格式错误')
    source = ir.metadata.value()
    source_metadata = JsonValue.of({'source_metadata_fingerprint':
        hashlib.sha256(ir.metadata.text.encode('utf-8')).hexdigest(),
        'source_name':source.get('name') if type(source) is dict and type(source.get('name')) is str
            and byte_size(source['name'])<=512 else None,
        'source_keys':sorted(source)[:64] if type(source) is dict else []})
    if byte_size(source_metadata.text)>MAX_METADATA_BYTES:
        raise DomainError('Lore 规范书元数据越界')
    entries = []
    for index, value in enumerate(ir.entries):
        if byte_size(value.text)>131072:
            raise DomainError('Lore 来源条目越界')
        row = value.value()
        if type(row) is not dict or type(row.get('text')) is not str:
            raise DomainError('Lore 条目核心字段错误')
        text = row['text']
        if byte_size(text) > MAX_ENTRY_TEXT_BYTES:
            raise DomainError('Lore 条目正文越界')
        settings = row.get('settings', {})
        if type(settings) is not dict:
            raise DomainError('Lore 条目设置错误')
        diags = []

        def triggers(name):
            raw = row.get(name, [])
            if type(raw) is not list or any(type(x) is not str for x in raw):
                raise DomainError('Lore 触发词结构错误')
            result = []
            for item in raw:
                if item == '':
                    diags.append(D.EMPTY_TRIGGER)
                    continue
                if byte_size(item) > MAX_TRIGGER_BYTES:
                    raise DomainError('Lore 触发词越界')
                if item not in result:
                    result.append(item)
            if len(result) > 32:
                raise DomainError('Lore 条目触发词过多')
            return tuple(result)

        primary, secondary = triggers('triggers'), triggers('secondary_triggers')
        enabled = row.get('enabled')
        disabled = row.get('disabled')
        if enabled is not None and type(enabled) is not bool or disabled is not None and type(disabled) is not bool:
            raise DomainError('Lore 启用字段错误')
        if enabled is True and disabled is True:
            diags.append(D.CONFLICTING_ENABLE_FLAGS)
        active = enabled is not False and disabled is not True

        def flag(name):
            v = settings.get(name, False)
            if type(v) is not bool:
                raise DomainError('Lore 运行设置类型错误')
            return v

        constant, selective = flag('constant'), flag('selective')
        case_sensitive = flag('case_sensitive')
        if selective and not secondary:
            diags.append(D.SELECTIVE_WITHOUT_SECONDARY)
        priority = row.get('priority')
        if priority is None:
            priority = 0
        elif type(priority) is not int or not -MAX_INT <= priority <= MAX_INT:
            priority = 0
            diags.append(D.INVALID_PRIORITY_ORDER)
        order = row.get('order')
        if order is None:
            order = index
        elif type(order) is not int or not 0 <= order <= MAX_INT:
            order = index
            diags.append(D.INVALID_PRIORITY_ORDER)
        disabled_reason = None
        if any(key in settings and settings[key] is not None and settings[key] is not False
               for key in ('use_regex','regex')):
            disabled_reason = D.UNSUPPORTED_REGEX
        elif any(value not in (None,False,{},[]) for key,value in settings.items()
                 if key not in ('id','comment','name','constant','selective','case_sensitive','use_regex','regex')):
            disabled_reason = D.UNSUPPORTED_EXTENSION
        if disabled_reason:
            diags.append(disabled_reason)
        metadata = JsonValue.of({'source_index':index,
            'source_entry_id':settings.get('id') if type(settings.get('id')) in (int,str) else None,
            'settings_fingerprint':hashlib.sha256(canonical(settings).encode('utf-8')).hexdigest(),
            'unsupported_keys':sorted(key for key in settings if key not in
                ('id','comment','name','constant','selective','case_sensitive','use_regex','regex'))[:64]})
        if byte_size(metadata.text) > MAX_METADATA_BYTES:
            raise DomainError('Lore 条目元数据越界')
        entries.append(NormalizedEntry(active,constant,selective,case_sensitive,priority,order,text,
            primary,secondary,disabled_reason,metadata,tuple(dict.fromkeys(diags))))
    if sum(len(e.primary)+len(e.secondary) for e in entries) > 10_000:
        raise DomainError('Lore 触发词总数越界')
    return NormalizedBook('character_lore_ir',ir.source_fingerprint,source_metadata,
        tuple(entries),payload_fingerprint)


def registration_fingerprint(mode, book_id, expected_version, proposal):
    """幂等指纹在生成运行 EntryId 前计算，纳入来源位置而不把位置当身份。"""
    value = {'mode':mode,'book_id':str(book_id) if book_id else None,
        'expected_version':expected_version.value if expected_version else None,
        'source_type':proposal.source_type,'source_fingerprint':proposal.source_fingerprint,
        'payload_fingerprint':proposal.payload_fingerprint,'source_metadata':proposal.source_metadata.value(),
        'entries':[{'enabled':e.enabled,'constant':e.constant,'selective':e.selective,
            'case_sensitive':e.case_sensitive,'priority':e.priority,'order':e.order,
            'text':e.text,'primary':e.primary,'secondary':e.secondary,
            'disabled_reason':e.disabled_reason.value if e.disabled_reason else None,
            'metadata':e.metadata.value(),'diagnostics':[d.value for d in e.diagnostics]}
            for e in proposal.entries]}
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()
