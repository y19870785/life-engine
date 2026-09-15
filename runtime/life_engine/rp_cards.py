"""Local SillyTavern V1/V2/V3 JSON and PNG tEXt card reader."""
import base64
import json
import struct
import zlib
from pathlib import Path

from .rp_lore import normalize_book

MAX_FILE = 20 * 1024 * 1024
MAX_JSON = 2 * 1024 * 1024


def read_local(path):
    path = Path(path).expanduser()
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_FILE:
        raise ValueError('Select a local regular file of at most 20 MiB')
    with path.open('rb') as handle:
        data = handle.read(MAX_FILE + 1)
    if len(data) > MAX_FILE:
        raise ValueError('Import file too large')
    return data


def parse_card(path):
    data = read_local(path)
    avatar = None
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        cursor, payloads, image_parts = 8, {}, [data[:8]]
        ended = False
        while cursor < len(data):
            if cursor + 12 > len(data):
                raise ValueError('Truncated PNG chunk')
            size = struct.unpack('>I', data[cursor:cursor+4])[0]
            end = cursor + size + 12
            if end > len(data):
                raise ValueError('Invalid PNG chunk length')
            kind = data[cursor+4:cursor+8]
            content = data[cursor+8:end-4]
            if zlib.crc32(kind + content) & 0xffffffff != struct.unpack('>I', data[end-4:end])[0]:
                raise ValueError('PNG CRC mismatch')
            card_chunk = False
            if kind == b'tEXt' and b'\0' in content:
                key, value = content.split(b'\0', 1)
                if key in (b'chara', b'ccv3'):
                    if key in payloads or len(value) > MAX_JSON * 2:
                        raise ValueError('Duplicate or oversized PNG card data')
                    payloads[key] = base64.b64decode(value, validate=True)
                    card_chunk = True
            if not card_chunk:
                image_parts.append(data[cursor:end])
            cursor = end
            if kind == b'IEND':
                ended = True
                break
        if not ended or cursor != len(data) or not payloads:
            raise ValueError('PNG must contain a complete chara/ccv3 tEXt card')
        avatar = b''.join(image_parts)
        data = payloads.get(b'ccv3', payloads.get(b'chara'))
    if len(data) > MAX_JSON:
        raise ValueError('Card JSON exceeds 2 MiB')
    raw = json.loads(data.decode('utf-8-sig'))
    if not isinstance(raw, dict):
        raise ValueError('Character card must be an object')
    if raw.get('spec') not in (None, 'chara_card_v2', 'chara_card_v3'):
        raise ValueError('Unsupported character card specification')
    card = raw.get('data') if raw.get('spec') else raw
    if not isinstance(card, dict):
        raise ValueError('Character card data must be an object')
    parsed = {}
    for key in ('name','description','personality','scenario','first_mes','mes_example'):
        value = card.get(key, '')
        if not isinstance(value, str) or len(value) > 16000:
            raise ValueError('Invalid or oversized character field: ' + key)
        parsed[key] = value
    parsed['name'] = parsed['name'].strip()
    if not parsed['name'] or len(parsed['name']) > 100 or any(ord(c) < 32 for c in parsed['name']):
        raise ValueError('Card name must be 1..100 printable characters')
    greetings = card.get('alternate_greetings', [])
    if not isinstance(greetings, list) or len(greetings) > 32 or any(not isinstance(x,str) or len(x)>16000 for x in greetings):
        raise ValueError('Invalid alternate greetings')
    parsed['alternate_greetings'] = greetings
    book = card.get('character_book') or {'entries': []}
    parsed['character_book'] = {'entries': normalize_book(book)}
    return raw, parsed, avatar
