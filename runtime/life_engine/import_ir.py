"""Version 1 import interchange values; all content remains untrusted data."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
import math
import re

from .domain import (CanonStatus, CharacterDefinition, DefinitionRef, DefinitionVersion,
                     DomainId, IdKind, Principal, Provenance, RealityStatus, SourceType, Values)

MAX_JSON = 16 * 1024 * 1024
MAX_DEPTH = 64
MAX_NODES = 250000


class Classification(str, Enum):
    PASS = 'PASS'
    PASS_WITH_WARNINGS = 'PASS_WITH_WARNINGS'
    LOSSY = 'LOSSY'
    UNSUPPORTED = 'UNSUPPORTED'
    MALFORMED = 'MALFORMED'
    INTERNAL_ERROR = 'INTERNAL_ERROR'


class ImportFailure(ValueError):
    """Only implementation-owned codes/paths; never interpolate source data."""
    def __init__(self, code, stage='parse', field='$', category=Classification.MALFORMED):
        super().__init__(code)
        self.code, self.stage, self.field, self.category = code, stage, field, category


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)


def load_json(data, limit=MAX_JSON, *, max_depth=MAX_DEPTH, max_nodes=None):
    max_nodes = MAX_NODES if max_nodes is None else max_nodes
    if len(data) > limit:
        raise ImportFailure('JSON_SIZE_LIMIT', category=Classification.UNSUPPORTED)

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ImportFailure('DUPLICATE_JSON_KEY')
            result[key] = value
        return result

    def constant(_):
        raise ImportFailure('NONFINITE_NUMBER')

    try:
        value = json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, ImportFailure):
            raise
        raise ImportFailure('INVALID_JSON') from None
    except RecursionError:
        raise ImportFailure('JSON_DEPTH_LIMIT', category=Classification.UNSUPPORTED) from None
    stack, nodes = [(value, 0)], 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if depth > max_depth or nodes > max_nodes:
            raise ImportFailure('JSON_COMPLEXITY_LIMIT', category=Classification.UNSUPPORTED)
        if isinstance(item, dict):
            stack.extend((v, depth + 1) for v in item.values())
            stack.extend((k, depth + 1) for k in item)
        elif isinstance(item, list):
            stack.extend((v, depth + 1) for v in item)
        elif isinstance(item, str):
            try:
                item.encode('utf8')
            except UnicodeError:
                raise ImportFailure('INVALID_UNICODE') from None
        elif isinstance(item, float) and not math.isfinite(item):
            raise ImportFailure('NONFINITE_NUMBER')
    return value


@dataclass(frozen=True, repr=False)
class JsonValue:
    """Immutable JSON value. Decoding returns a detached copy, never shared state."""
    text: str

    def __post_init__(self):
        value = load_json(self.text.encode('utf8'), MAX_JSON * 6, max_depth=MAX_DEPTH + 8)
        object.__setattr__(self, 'text', canonical(value))

    @classmethod
    def of(cls, value):
        return cls(canonical(value))

    def value(self):
        return json.loads(self.text)


@dataclass(frozen=True, repr=False)
class LoreIR:
    """Context source, never a World or an activated lore result."""
    metadata: JsonValue
    entries: tuple[JsonValue, ...]
    source_fingerprint: str

    def __post_init__(self):
        if (type(self.metadata) is not JsonValue or type(self.entries) is not tuple
                or any(type(x) is not JsonValue for x in self.entries)
                or type(self.source_fingerprint) is not str
                or not re.fullmatch('[a-f0-9]{64}', self.source_fingerprint)):
            raise ImportFailure('INVALID_IR_LORE', 'ir')

    def normalized(self):
        return {'metadata': self.metadata.value(), 'entries': [x.value() for x in self.entries],
                'source_fingerprint': self.source_fingerprint}


@dataclass(frozen=True, repr=False)
class CharacterImportIR:
    ir_version: int
    source_format: str
    source_spec: str
    source_spec_version: str
    source_fingerprint: str
    payload_fingerprint: str
    profile: JsonValue
    instructions: JsonValue
    greetings: JsonValue
    example_dialogue: str
    creator_metadata: JsonValue
    tags: tuple[str, ...]
    lore: LoreIR | None
    lore_references: JsonValue
    asset_references: JsonValue
    extensions: JsonValue
    preserved_source: JsonValue
    warnings: tuple[str, ...]

    def __post_init__(self):
        if type(self.ir_version) is not int or self.ir_version != 1:
            raise ImportFailure('IR_VERSION_UNSUPPORTED', 'ir', category=Classification.UNSUPPORTED)
        for value in (self.source_format, self.source_spec, self.source_spec_version, self.example_dialogue):
            if type(value) is not str:
                raise ImportFailure('INVALID_IR_TEXT', 'ir')
        for fingerprint in (self.source_fingerprint, self.payload_fingerprint):
            if not isinstance(fingerprint, str) or not re.fullmatch('[a-f0-9]{64}', fingerprint):
                raise ImportFailure('INVALID_FINGERPRINT', 'ir')
        for value in (self.profile, self.instructions, self.greetings, self.creator_metadata,
                      self.lore_references, self.asset_references, self.extensions, self.preserved_source):
            if type(value) is not JsonValue:
                raise ImportFailure('INVALID_IR_VALUE', 'ir')
        if type(self.tags) is not tuple or any(type(x) is not str for x in self.tags):
            raise ImportFailure('INVALID_IR_TAGS', 'ir')
        if type(self.warnings) is not tuple or any(not re.fullmatch('[A-Z_]+', x) for x in self.warnings):
            raise ImportFailure('INVALID_IR_WARNINGS', 'ir')
        if self.lore is not None and type(self.lore) is not LoreIR:
            raise ImportFailure('INVALID_IR_LORE', 'ir')

    def semantics(self):
        return {'profile': self.profile.value(), 'instructions': self.instructions.value(),
                'greetings': self.greetings.value(), 'example_dialogue': self.example_dialogue,
                'creator_metadata': self.creator_metadata.value(), 'tags': list(self.tags),
                'lore': self.lore.normalized() if self.lore else None,
                'lore_references': self.lore_references.value()}

    def normalized(self):
        return dict(self.semantics(), ir_version=self.ir_version, source_format=self.source_format,
                    source_spec=self.source_spec, source_spec_version=self.source_spec_version,
                    source_fingerprint=self.source_fingerprint, payload_fingerprint=self.payload_fingerprint,
                    asset_references=self.asset_references.value(), extensions=self.extensions.value(),
                    preserved_source=self.preserved_source.value(), warnings=list(self.warnings))

    def to_json(self):
        """Private interchange, NOT the privacy-safe compatibility report."""
        return canonical(self.normalized())

    @classmethod
    def from_json(cls, text):
        raw = load_json(text, MAX_JSON * 24, max_depth=MAX_DEPTH + 16, max_nodes=MAX_NODES * 8)
        try:
            if type(raw) is not dict or set(raw) != set(cls.__dataclass_fields__):
                raise ImportFailure('INVALID_IR_FIELDS', 'ir')
            values = dict(raw)
            for field in ('profile', 'instructions', 'greetings', 'creator_metadata', 'lore_references',
                          'asset_references', 'extensions', 'preserved_source'):
                values[field] = JsonValue.of(values[field])
            for field in ('tags', 'warnings'):
                if type(values[field]) is not list:
                    raise ImportFailure('INVALID_IR_ARRAY', 'ir')
                values[field] = tuple(values[field])
            if values['lore'] is not None:
                lore = values['lore']
                values['lore'] = LoreIR(JsonValue.of(lore['metadata']),
                                        tuple(JsonValue.of(x) for x in lore['entries']), lore['source_fingerprint'])
            ir = cls(**values)
            if hashlib.sha256(ir.preserved_source.text.encode()).hexdigest() != ir.payload_fingerprint:
                raise ImportFailure('IR_PAYLOAD_MISMATCH', 'ir')
            return ir
        except (KeyError, TypeError):
            raise ImportFailure('INVALID_IR_STRUCTURE', 'ir') from None


def project_definition(ir, actor: Principal, created_at: datetime, reference=None):
    """Pure projection. ID/version/owner come from trusted caller, never imported fields."""
    if type(ir) is not CharacterImportIR:
        raise ImportFailure('INVALID_IR_VALUE', 'projection')
    profile = ir.profile.value()
    if not isinstance(profile, dict) or not isinstance(profile.get('display_name'), str) or not profile['display_name'].strip():
        raise ImportFailure('MISSING_DISPLAY_NAME', 'projection')
    reference = reference or DefinitionRef(DomainId.new(IdKind.DEFINITION), DefinitionVersion(1))
    provenance = Provenance(SourceType.IMPORT, 'sha256:' + ir.source_fingerprint, created_at, actor,
                            RealityStatus.UNKNOWN, CanonStatus.UNREVIEWED)
    # Opaque preservation, image assets and plugin settings remain in the IR sidecar.
    # CharacterDefinition receives only deliberately mapped character content.
    content = {'profile': profile, 'instructions': ir.instructions.value(),
               'greetings': ir.greetings.value(), 'example_dialogue': ir.example_dialogue,
               'tags': list(ir.tags), 'lore_reference': ir.payload_fingerprint if ir.lore else None}
    traits = Values((('content_trust', 'untrusted_import'), ('import_ir_version', str(ir.ir_version)),
                     ('payload_fingerprint', ir.payload_fingerprint),
                     ('imported_content', canonical(content))))
    return CharacterDefinition(reference, actor.owner_id, profile['display_name'], traits, provenance)
