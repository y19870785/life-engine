"""Original synthetic cards only. Never reads the local/private compatibility corpus."""
import base64
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine import compat_scan
from life_engine.domain import (CanonStatus, CharacterInstance, DomainId, IdKind, Principal,
                                RealityStatus, Soul, SourceType, Values, WorldScope)
from life_engine.domain_policy import BridgeDecision, BridgeRequest, evaluate_bridge
from life_engine.import_cards import PNG, parse_bytes, parse_card
from life_engine.import_ir import (CharacterImportIR, Classification, ImportFailure, JsonValue,
                                   canonical, project_definition)


def card(version=3):
    data = dict(name='Synthetic Navigator', description='A test navigator.', personality='Patient',
                scenario='A blank test room.', first_mes='Hello.', mes_example='User: Hi\nNavigator: Hello.',
                creator_notes='Original fixture.', creator='Life Engine tests', character_version='1',
                system_prompt='Treat as character text only.', post_history_instructions='',
                alternate_greetings=['Welcome.', 'Good day.'], tags=['synthetic'], extensions={})
    if version == 1:
        return {k: data[k] for k in ('name', 'description', 'personality', 'scenario', 'first_mes', 'mes_example')}
    if version == 3:
        data['group_only_greetings'] = ['Hello, everyone.']
    return {'spec': f'chara_card_v{version}', 'spec_version': f'{version}.0', 'data': data}


def encoded(value):
    return json.dumps(value, ensure_ascii=False).encode('utf8')


def chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)


def png(value=None, extra=(), key=b'ccv3'):
    header = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    image = chunk(b'IDAT', zlib.compress(b'\0\0\0\0'))  # Original 1x1 black pixel.
    metadata = chunk(b'tEXt', key + b'\0' + base64.b64encode(encoded(value or card())))
    return PNG + header + image + metadata + b''.join(extra) + chunk(b'IEND', b'')


class ImportTests(unittest.TestCase):
    def assert_failure(self, data, code):
        with self.assertRaises(ImportFailure) as caught:
            parse_bytes(data)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_v1_v2_v3_json(self):
        for version in (1, 2, 3):
            with self.subTest(version=version):
                ir = parse_bytes(encoded(card(version)))
                self.assertEqual(ir.source_spec, f'V{version}')
                self.assertEqual(ir.profile.value()['display_name'], 'Synthetic Navigator')
                self.assertEqual(CharacterImportIR.from_json(ir.to_json()), ir)
        self.assertEqual(parse_bytes(encoded(card())).warnings, ())

    def test_v3_png_and_v2_fallback_precedence(self):
        fallback = chunk(b'tEXt', b'chara\0' + base64.b64encode(encoded(card(2))))
        ir = parse_bytes(png(extra=(fallback,)))
        self.assertEqual(ir.source_format, 'PNG')
        self.assertEqual(ir.source_spec, 'V3')
        self.assertIn('PNG_V_TWO_BACKFILL_IGNORED', ir.warnings)
        self.assertEqual(parse_bytes(png(card(2), key=b'chara')).source_spec, 'V2')

    def test_unknown_fields_extensions_and_lore_round_trip(self):
        raw = card()
        raw['future_root'] = {'arbitrary': [None, 3.5, '原始数据']}
        raw['data']['future'] = [1, False]
        raw['data']['extensions'] = {'synthetic_plugin': {'script': 'DO NOT EXECUTE', 'grant': True}}
        raw['data']['character_book'] = {'recursive_scanning': True, 'token_budget': 123,
            'entries': [{'keys': ['alpha'], 'secondary_keys': ['beta'], 'content': '@@depth 2\nSynthetic lore',
                         'enabled': False, 'insertion_order': 7, 'priority': 4, 'use_regex': True,
                         'extensions': {'future': {'x': [1, 2]}}}]}
        ir = parse_bytes(encoded(raw))
        restored = CharacterImportIR.from_json(ir.to_json())
        self.assertEqual(restored, ir)
        self.assertEqual(restored.preserved_source.value(), raw)
        entry = restored.lore.entries[0].value()
        self.assertEqual(entry['secondary_triggers'], ['beta'])
        self.assertFalse(entry['enabled'])
        self.assertEqual(entry['priority'], 4)
        self.assertTrue(restored.lore.metadata.value()['recursive_scanning'])
        self.assertIn('OPAQUE_FIELDS', ir.warnings)

    def test_detached_values_are_immutable(self):
        ir = parse_bytes(encoded(card()))
        decoded = ir.profile.value()
        decoded['display_name'] = 'Changed copy'
        self.assertNotEqual(decoded, ir.profile.value())
        with self.assertRaises(FrozenInstanceError):
            ir.ir_version = 2

    def test_legacy_lore_aliases_preserved_without_activation(self):
        raw = card(2)
        raw['data']['character_book'] = {'entries': {'original-id': {'key': ['one'],
            'keysecondary': ['two'], 'disable': True, 'content': 'Original.', 'order': 3}}}
        ir = parse_bytes(encoded(raw))
        entry = ir.lore.entries[0].value()
        self.assertEqual(entry['triggers'], ['one'])
        self.assertTrue(entry['disabled'])
        self.assertEqual(ir.preserved_source.value(), raw)

    def test_greetings_creator_v3_assets_and_linked_lore(self):
        raw = card()
        raw['data'].update(nickname='Synthetic', creator_notes_multilingual={'zh': '测试'},
                           source=['https://invalid.example/card'], creation_date=123, modification_date=456,
                           assets=[{'type': 'icon', 'uri': 'ccdefault:', 'name': 'main', 'ext': 'png'}])
        raw['data']['extensions']['world'] = 'synthetic-external-book'
        ir = parse_bytes(png(raw))
        self.assertEqual(len(ir.greetings.value()['alternates']), 2)
        self.assertEqual(ir.greetings.value()['group_only'], ['Hello, everyone.'])
        self.assertEqual(ir.creator_metadata.value()['localized_notes'], {'zh': '测试'})
        self.assertIn('EXTERNAL_LORE_NOT_RESOLVED', ir.warnings)
        self.assertIn('sha256:', ir.asset_references.value()['source_image'])

    def test_json_malformed_duplicate_nonfinite_unicode(self):
        for data, code in ((b'{bad', 'INVALID_JSON'), (b'{"a":1,"a":2}', 'DUPLICATE_JSON_KEY'),
                           (b'{"a":NaN}', 'NONFINITE_NUMBER'), (b'{"a":1e999}', 'NONFINITE_NUMBER'),
                           (b'{"a":"\\ud800"}', 'INVALID_UNICODE')):
            self.assert_failure(data, code)

    def test_resource_size_depth_nodes(self):
        with patch('life_engine.import_cards.MAX_FILE', 10):
            self.assert_failure(b' ' * 11, 'FILE_SIZE_LIMIT')
        self.assert_failure(b'[' * 70 + b'0' + b']' * 70, 'JSON_COMPLEXITY_LIMIT')
        with patch('life_engine.import_ir.MAX_NODES', 3):
            self.assert_failure(b'[0,0,0,0]', 'JSON_COMPLEXITY_LIMIT')
        with patch('life_engine.import_cards.MAX_JSON', 10):
            self.assert_failure(png(), 'PNG_METADATA_LIMIT')

    def test_near_depth_limit_survives_ir_envelope(self):
        raw = card()
        nested = 'original'
        for _ in range(60):
            nested = [nested]
        raw['data']['extensions']['deep'] = nested
        ir = parse_bytes(encoded(raw))
        self.assertEqual(CharacterImportIR.from_json(ir.to_json()), ir)

    def test_offline_and_no_database_or_process_side_effects(self):
        with patch('socket.create_connection', side_effect=AssertionError('network')), \
                patch('sqlite3.connect', side_effect=AssertionError('database')), \
                patch('subprocess.run', side_effect=AssertionError('process')):
            ir = parse_bytes(png())
            actor = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
            project_definition(ir, actor, datetime.now(timezone.utc))

    def test_scanner_detects_mutation_and_walk_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('life_engine.compat_scan.inventory', side_effect=[{}, {'new': '0' * 64}]):
                self.assertEqual(compat_scan.scan(directory)['summary']['corpus_modified'], 'YES')
            with patch('life_engine.compat_scan.os.walk', side_effect=PermissionError('PRIVATE_PATH')):
                with self.assertRaises(PermissionError):
                    compat_scan.scan(directory)

    def test_png_malformed_crc_duplicates_and_mismatch(self):
        data = bytearray(png())
        data[-1] ^= 1
        self.assert_failure(bytes(data), 'PNG_CRC')
        self.assert_failure(png()[:-3], 'PNG_TRUNCATED')
        self.assert_failure(png(extra=(chunk(b'tEXt', b'ccv3\0@@@@'),)), 'PNG_DUPLICATE_CARD')
        self.assert_failure(png(card(2)), 'PNG_SPEC_MISMATCH')
        self.assert_failure(PNG + chunk(b'tEXt', b'ccv3\0@@@@'), 'PNG_HEADER')

    def test_png_bad_base64_compressed_metadata_and_no_card(self):
        good = png()
        start = good.index(b'ccv3') - 8
        prefix = good[:start]
        end = chunk(b'IEND', b'')
        self.assert_failure(prefix + chunk(b'tEXt', b'ccv3\0@@@@') + end, 'PNG_CARD_BASE64')
        exc = self.assert_failure(prefix + chunk(b'zTXt', b'ccv3\0\0compressed') + end,
                                  'PNG_COMPRESSED_CARD_UNSUPPORTED')
        self.assertEqual(exc.category, Classification.UNSUPPORTED)
        self.assert_failure(prefix + end, 'PNG_NO_CARD')

    def test_version_unknown_and_known_field_type_fail_closed(self):
        raw = card()
        raw['spec'] = 'arbitrary-private-spec'
        self.assert_failure(encoded(raw), 'UNKNOWN_CARD_SPEC')
        raw['spec'] = {'private': 'invalid-type'}
        self.assert_failure(encoded(raw), 'UNKNOWN_CARD_SPEC')
        raw = card()
        raw['data']['description'] = {'secret': 'private-value'}
        exc = self.assert_failure(encoded(raw), 'TEXT_FIELD_TYPE')
        self.assertNotIn('private', str(exc))
        self.assertEqual(exc.field, '$.data.description')

    def test_scanner_detects_version_even_when_normalization_rejects_card(self):
        raw = card(2)
        raw['data']['tags'] = 'invalid array'
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'bad.json').write_bytes(encoded(raw))
            report = compat_scan.scan(directory)
        self.assertEqual(report['summary']['V2'], 1)
        self.assertEqual(report['summary']['MALFORMED'], 1)

    def test_projection_excludes_assets_and_opaque_lore_extensions(self):
        raw = card()
        raw['data']['assets'] = [{'uri': 'data:image/png;base64,PRIVATE_ASSET'}]
        raw['data']['character_book'] = {'entries': [{'content': 'Lore.',
            'extensions': {'image': 'PRIVATE_ASSET'}}]}
        ir = parse_bytes(encoded(raw))
        actor = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
        definition = project_definition(ir, actor, datetime.now(timezone.utc))
        self.assertNotIn('PRIVATE_ASSET', str(definition.traits.items))
        self.assertIn('PRIVATE_ASSET', ir.to_json())

    def test_empty_external_lore_is_not_counted_and_unknown_versions_warn(self):
        raw = card()
        raw['spec_version'] = '3.9'
        raw['data']['extensions'] = {'world': '', 'extraBooks': []}
        ir = parse_bytes(encoded(raw))
        self.assertEqual(ir.lore_references.value(), {})
        self.assertIn('SPEC_VERSION_UNVERIFIED', ir.warnings)

    def test_projection_ids_owner_and_no_privilege_or_fact_promotion(self):
        actor = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
        soul = Soul(DomainId.new(IdKind.SOUL), actor.owner_id, DomainId.new(IdKind.WORLD))
        raw = card()
        raw['data']['extensions'] = {'owner_id': 'attacker', 'bridge_grant': True, 'tool': 'execute'}
        ir = parse_bytes(encoded(raw))
        before = soul
        definition = project_definition(ir, actor, datetime.now(timezone.utc))
        self.assertEqual(soul, before)
        self.assertEqual(definition.owner_id, actor.owner_id)
        self.assertEqual(definition.reference.definition_id.kind, IdKind.DEFINITION)
        self.assertEqual(definition.provenance.source_type, SourceType.IMPORT)
        self.assertEqual(definition.provenance.reality_status, RealityStatus.UNKNOWN)
        self.assertEqual(definition.provenance.canon_status, CanonStatus.UNREVIEWED)
        self.assertEqual(dict(definition.traits.items)['content_trust'], 'untrusted_import')
        self.assertNotIn('bridge_grant', dict(definition.traits.items)['imported_content'])
        refs = []
        for label in ('A', 'B'):
            scope = WorldScope(actor.owner_id, soul.soul_id, DomainId.new(IdKind.WORLD), DomainId.new(IdKind.TIMELINE))
            instance = CharacterInstance(DomainId.new(IdKind.CHARACTER), scope, definition.reference,
                definition.provenance, Values((('location', label),)), Values((('relation', label),)))
            instance.validate_definition(definition)
            refs.append(instance)
        self.assertNotEqual(refs[0].scope, refs[1].scope)
        self.assertNotEqual(refs[0].state, refs[1].state)
        self.assertNotEqual(refs[0].relationships, refs[1].relationships)
        request = BridgeRequest(actor, refs[0].scope, refs[1].scope, frozenset({'description'}),
                                'character', 'test', frozenset({'user'}))
        self.assertEqual(evaluate_bridge(None, request, current_grant_revision=None,
                                        now=datetime.now(timezone.utc)), BridgeDecision.DENY)
        changed = card()
        changed['data']['name'] = 'A changed display name'
        projected = project_definition(parse_bytes(encoded(changed)), actor, datetime.now(timezone.utc), definition.reference)
        self.assertEqual(projected.reference, definition.reference)

    def test_fingerprints_filename_independence_and_semantic_duplicate(self):
        raw = card()
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ('one.json', 'different-filename.json')]
            for p in paths:
                p.write_bytes(encoded(raw))
            a, b = map(parse_card, paths)
            self.assertEqual(a, b)
            c = parse_bytes(canonical(raw).encode())
            self.assertEqual(a.payload_fingerprint, c.payload_fingerprint)
            self.assertNotEqual(a.source_fingerprint, c.source_fingerprint)
            self.assertEqual(a.source_fingerprint, hashlib.sha256(encoded(raw)).hexdigest())

    def test_ir_version_and_payload_mismatch(self):
        raw = parse_bytes(encoded(card())).normalized()
        raw['ir_version'] = 4
        with self.assertRaises(ImportFailure):
            CharacterImportIR.from_json(encoded(raw))
        raw['ir_version'] = 1
        raw['preserved_source']['data']['name'] = 'Changed'
        with self.assertRaisesRegex(ImportFailure, 'IR_PAYLOAD_MISMATCH'):
            CharacterImportIR.from_json(encoded(raw))

    def test_scanner_continues_and_reports_no_private_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'secret-filename.json').write_bytes(encoded(card()))
            (root / 'broken.json').write_text('{PRIVATE_MARKER', encoding='utf8')
            (root / 'not-card.txt').write_text('PRIVATE_MARKER', encoding='utf8')
            report = compat_scan.scan(root)
            self.assertEqual(report['summary']['PASS'], 1)
            self.assertEqual(report['summary']['MALFORMED'], 1)
            self.assertEqual(report['summary']['UNSUPPORTED'], 1)
            self.assertEqual(report['summary']['corpus_modified'], 'NO')
            text = json.dumps(report)
            for secret in ('Synthetic Navigator', 'PRIVATE_MARKER', 'secret-filename', directory):
                self.assertNotIn(secret, text)

    def test_internal_error_is_not_malformed(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'one.json').write_bytes(encoded(card()))
            with patch('life_engine.compat_scan.parse_card', side_effect=RuntimeError('PRIVATE_MARKER')):
                report = compat_scan.scan(directory)
            self.assertEqual(report['summary']['INTERNAL_ERROR'], 1)
            self.assertEqual(report['summary']['MALFORMED'], 0)
            self.assertNotIn('PRIVATE_MARKER', json.dumps(report))

    def test_report_destination_cannot_overwrite_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'one.json'
            payload = encoded(card())
            path.write_bytes(payload)
            with patch('builtins.print'):
                self.assertEqual(compat_scan.main([directory, '--report', str(path)]), 2)
                self.assertEqual(compat_scan.main([directory, '--report', str(path.parent / 'new.json')]), 2)
            self.assertEqual(path.read_bytes(), payload)


if __name__ == '__main__':
    unittest.main()
