"""Offline external-card adapter. No databases, image decode, prompt execution or network."""
import base64
import binascii
import hashlib
from pathlib import Path
import stat
import struct
import zlib

from .import_ir import (CharacterImportIR, Classification, ImportFailure, JsonValue,
                        LoreIR, MAX_JSON, canonical, load_json)

MAX_FILE = 64 * 1024 * 1024
MAX_CHUNKS = 100000
PNG = b'\x89PNG\r\n\x1a\n'
TEXT_FIELDS = ('name', 'description', 'personality', 'scenario', 'first_mes', 'mes_example',
               'system_prompt', 'post_history_instructions', 'creator', 'creator_notes',
               'character_version', 'nickname')
ARRAY_FIELDS = ('alternate_greetings', 'group_only_greetings', 'tags', 'source')
KNOWN_FIELDS = set(TEXT_FIELDS + ARRAY_FIELDS + ('assets', 'extensions', 'character_book',
                   'creator_notes_multilingual', 'creation_date', 'modification_date'))


def is_link(path):
    info = Path(path).lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def read_card(path):
    path = Path(path)
    # Reject reparse points, including parent junctions, instead of following them.
    if any(is_link(p) for p in (path, *path.absolute().parents)) or not path.is_file():
        raise ImportFailure('NOT_REGULAR_FILE', 'read', category=Classification.UNSUPPORTED)
    if path.stat().st_size > MAX_FILE:
        raise ImportFailure('FILE_SIZE_LIMIT', 'read', category=Classification.UNSUPPORTED)
    with path.open('rb') as handle:
        data = handle.read(MAX_FILE + 1)
    if len(data) > MAX_FILE:
        raise ImportFailure('FILE_SIZE_LIMIT', 'read', category=Classification.UNSUPPORTED)
    return data


def png_payload(data):
    cursor, chunks, payloads, assets = 8, 0, {}, 0
    seen_header, seen_image, ended = False, False, False
    while cursor < len(data):
        chunks += 1
        if chunks > MAX_CHUNKS:
            raise ImportFailure('PNG_CHUNK_LIMIT', 'container', category=Classification.UNSUPPORTED)
        if cursor + 12 > len(data):
            raise ImportFailure('PNG_TRUNCATED', 'container')
        size = struct.unpack('>I', data[cursor:cursor + 4])[0]
        end = cursor + size + 12
        if end > len(data):
            raise ImportFailure('PNG_CHUNK_LENGTH', 'container')
        kind, content = data[cursor + 4:cursor + 8], data[cursor + 8:end - 4]
        crc = zlib.crc32(content, zlib.crc32(kind)) & 0xffffffff
        if crc != struct.unpack('>I', data[end - 4:end])[0]:
            raise ImportFailure('PNG_CRC', 'container')
        if not seen_header and kind != b'IHDR':
            raise ImportFailure('PNG_HEADER', 'container')
        if kind == b'IHDR':
            if seen_header or size != 13 or not all(struct.unpack('>II', content[:8])):
                raise ImportFailure('PNG_HEADER', 'container')
            seen_header = True
        if kind == b'IDAT':
            seen_image = True
        if kind in (b'tEXt', b'zTXt', b'iTXt'):
            key, separator, value = content.partition(b'\0')
            if not separator:
                raise ImportFailure('PNG_TEXT_HEADER', 'container')
            if key in (b'chara', b'ccv3'):
                # CC specs mandate tEXt. No decompression of arbitrary metadata.
                if kind != b'tEXt':
                    raise ImportFailure('PNG_COMPRESSED_CARD_UNSUPPORTED', 'container', category=Classification.UNSUPPORTED)
                if key in payloads:
                    raise ImportFailure('PNG_DUPLICATE_CARD', 'container')
                if len(value) > ((MAX_JSON + 2) // 3) * 4:
                    raise ImportFailure('PNG_METADATA_LIMIT', 'container', category=Classification.UNSUPPORTED)
                try:
                    payloads[key] = base64.b64decode(value, validate=True)
                except (binascii.Error, ValueError):
                    raise ImportFailure('PNG_CARD_BASE64', 'container') from None
            elif key.startswith(b'chara-ext-asset_:'):
                assets += 1
        cursor = end
        if kind == b'IEND':
            if size != 0:
                raise ImportFailure('PNG_END', 'container')
            ended = True
            break
    if not ended or cursor != len(data) or not seen_image:
        raise ImportFailure('PNG_INCOMPLETE', 'container')
    if not payloads:
        raise ImportFailure('PNG_NO_CARD', 'container', category=Classification.UNSUPPORTED)
    selected = b'ccv3' if b'ccv3' in payloads else b'chara'
    warnings = []
    if len(payloads) > 1:
        warnings.append('PNG_V_TWO_BACKFILL_IGNORED')
    if assets:
        warnings.append('PNG_ASSETS_REFERENCE_ONLY')
    return payloads[selected], selected, tuple(warnings), assets


def normalize_lore(book, fingerprint, warnings):
    if type(book) is not dict:
        raise ImportFailure('LORE_OBJECT_REQUIRED', 'normalize', '$.character_book')
    entries = book.get('entries', [])
    if isinstance(entries, dict):
        warnings.add('LORE_ENTRY_MAP_COMPATIBILITY')
        entries = list(entries.values())
    if not isinstance(entries, list):
        raise ImportFailure('LORE_ENTRIES_ARRAY', 'normalize', '$.character_book.entries')
    result = []
    for row in entries:
        if type(row) is not dict:
            raise ImportFailure('LORE_ENTRY_OBJECT', 'normalize', '$.character_book.entries[]')
        # Keep all original entry data, including aliases, regex, decorators and plugin settings.
        # No trigger evaluation or precedence assumptions are made here.
        mapped = {'triggers': row.get('keys', row.get('key', [])),
                  'secondary_triggers': row.get('secondary_keys', row.get('keysecondary', [])),
                  'text': row.get('content', ''), 'enabled': row.get('enabled'),
                  'disabled': row.get('disable'), 'order': row.get('insertion_order', row.get('order')),
                  'priority': row.get('priority'), 'settings': {k: v for k, v in row.items()
                      if k not in ('keys', 'key', 'secondary_keys', 'keysecondary', 'content',
                                   'enabled', 'disable', 'insertion_order', 'order', 'priority')}}
        for key in ('triggers', 'secondary_triggers'):
            if not isinstance(mapped[key], list) or any(type(x) is not str for x in mapped[key]):
                warnings.add('LORE_NONSTANDARD_FIELD_PRESERVED')
        if type(mapped['text']) is not str:
            raise ImportFailure('LORE_TEXT_REQUIRED', 'normalize', '$.character_book.entries[].content')
        if any(k in row for k in ('use_regex', 'selective', 'extensions')) or '@@' in mapped['text']:
            warnings.add('LORE_RUNTIME_SEMANTICS_DEFERRED')
        result.append(JsonValue.of(mapped))
    warnings.add('LORE_CONTEXT_ONLY')
    return LoreIR(JsonValue.of({k: v for k, v in book.items() if k != 'entries'}), tuple(result), fingerprint)


def parse_bytes(data):
    if len(data) > MAX_FILE:
        raise ImportFailure('FILE_SIZE_LIMIT', 'read', category=Classification.UNSUPPORTED)
    fingerprint = hashlib.sha256(data).hexdigest()
    source_format, key, container_warnings, assets = 'JSON', None, (), 0
    if data.startswith(PNG):
        source_format = 'PNG'
        data, key, container_warnings, assets = png_payload(data)
    elif data.startswith(b'\x89PNG'):
        raise ImportFailure('PNG_SIGNATURE', 'container')
    raw = load_json(data)
    if type(raw) is not dict:
        raise ImportFailure('CARD_OBJECT_REQUIRED')
    try:
        return normalize_card(raw, fingerprint, source_format, key, container_warnings, assets)
    except ImportFailure as exc:
        declared = raw.get('spec') if isinstance(raw.get('spec'), str) else ''
        exc.source_spec = {'chara_card_v2': 'V2', 'chara_card_v3': 'V3'}.get(declared,
            'V1' if 'spec' not in raw and all(k in raw for k in ('name', 'description', 'first_mes')) else 'UNKNOWN')
        raise


def normalize_card(raw, fingerprint, source_format, key, container_warnings, assets):
    spec = raw.get('spec')
    if spec not in (None, 'chara_card_v2', 'chara_card_v3'):
        raise ImportFailure('UNKNOWN_CARD_SPEC', category=Classification.UNSUPPORTED)
    if spec is None and not all(k in raw for k in ('name', 'description', 'first_mes')):
        raise ImportFailure('NOT_CHARACTER_CARD', category=Classification.UNSUPPORTED)
    card = raw['data'] if spec and 'data' in raw else raw if spec is None else None
    if type(card) is not dict:
        raise ImportFailure('CARD_DATA_OBJECT', field='$.data')
    if key == b'ccv3' and spec != 'chara_card_v3':
        raise ImportFailure('PNG_SPEC_MISMATCH')
    warnings = set(container_warnings)
    source_spec = {'chara_card_v2': 'V2', 'chara_card_v3': 'V3', None: 'V1'}[spec]
    version = raw.get('spec_version', '') if spec else '1'
    if type(version) is not str:
        raise ImportFailure('SPEC_VERSION_TYPE', field='$.spec_version')
    if source_spec != 'V3':
        warnings.add('LEGACY_FORMAT')
    if spec and version != ('3.0' if source_spec == 'V3' else '2.0'):
        warnings.add('SPEC_VERSION_UNVERIFIED')
    if key == b'chara' and source_spec == 'V3':
        warnings.add('PNG_LEGACY_KEY_FOR_V_THREE')
    texts = {}
    for field in TEXT_FIELDS:
        value = card.get(field, '')
        if type(value) is not str:
            raise ImportFailure('TEXT_FIELD_TYPE', 'normalize', '$.data.' + field)
        texts[field] = value
    if not texts['name'].strip():
        raise ImportFailure('MISSING_DISPLAY_NAME', 'normalize', '$.data.name')
    arrays = {}
    for field in ARRAY_FIELDS:
        value = card.get(field, [])
        if type(value) is not list or any(type(x) is not str for x in value):
            raise ImportFailure('STRING_ARRAY_TYPE', 'normalize', '$.data.' + field)
        arrays[field] = value
    required = set(TEXT_FIELDS[:11]) | {'alternate_greetings', 'tags', 'extensions'}
    if source_spec == 'V3':
        required.add('group_only_greetings')
    if required - card.keys():
        warnings.add('MISSING_FIELDS_DEFAULTED')
    extensions = card.get('extensions', {})
    if type(extensions) is not dict:
        raise ImportFailure('EXTENSIONS_OBJECT', 'normalize', '$.data.extensions')
    if extensions:
        warnings.add('OPAQUE_EXTENSIONS')
    if card.keys() - KNOWN_FIELDS or (spec and raw.keys() - {'spec', 'spec_version', 'data'}):
        warnings.add('OPAQUE_FIELDS')
    preserved = JsonValue.of(raw)
    payload_fingerprint = hashlib.sha256(preserved.text.encode()).hexdigest()
    lore = normalize_lore(card['character_book'], fingerprint, warnings) if card.get('character_book') is not None else None
    references = {}
    # Recognized ST linked-lore slots only; never guess that arbitrary URLs are lore.
    for field in ('world', 'extraBooks'):
        if extensions.get(field):
            references[field] = extensions[field]
    if references:
        warnings.add('EXTERNAL_LORE_NOT_RESOLVED')
    asset_refs = {'source_image': 'sha256:' + fingerprint if source_format == 'PNG' else None,
                  'declared': card.get('assets', []), 'embedded_asset_count': assets}
    if card.get('assets'):
        warnings.add('ASSETS_REFERENCE_ONLY')
    creator = {'author': texts['creator'], 'notes': texts['creator_notes'],
               'version_label': texts['character_version'],
               'localized_notes': card.get('creator_notes_multilingual', {}),
               'source_references': arrays['source'], 'created': card.get('creation_date'),
               'modified': card.get('modification_date')}
    return CharacterImportIR(1, source_format, source_spec, version, fingerprint, payload_fingerprint,
        JsonValue.of({'display_name': texts['name'], 'nickname': texts['nickname'],
                      'description': texts['description'], 'personality': texts['personality'],
                      'scenario': texts['scenario']}),
        JsonValue.of({'character_instructions': texts['system_prompt'],
                      'post_history_instructions': texts['post_history_instructions']}),
        JsonValue.of({'initial': texts['first_mes'], 'alternates': arrays['alternate_greetings'],
                      'group_only': arrays['group_only_greetings']}), texts['mes_example'],
        JsonValue.of(creator), tuple(arrays['tags']), lore, JsonValue.of(references),
        JsonValue.of(asset_refs), JsonValue.of(extensions), preserved, tuple(sorted(warnings)))


def parse_card(path):
    return parse_bytes(read_card(path))
