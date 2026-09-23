"""Lore 身份、不可变值和低信任归一化边界。"""
import hashlib
import unittest

from memory_fixture import ROOT
from life_engine.domain import DomainError, DomainId, IdKind
from life_engine.import_ir import JsonValue, LoreIR
from life_engine.lore import (LoreBookVersion, LoreBindingRevision, LoreBudget,
                             LoreDiagnostic, MAX_ENTRY_TEXT_BYTES)
from life_engine.lore_normalize import normalize_lore_ir, registration_fingerprint


def ir(*rows):
    return LoreIR(JsonValue.of({'name':'原创'}),tuple(JsonValue.of(row) for row in rows),
        hashlib.sha256('独立原创来源'.encode('utf-8')).hexdigest())


class LoreDomainTests(unittest.TestCase):
    def test_typed_ids_and_positive_versions(self):
        for kind in (IdKind.LORE_BOOK,IdKind.LORE_ENTRY):
            value=DomainId.new(kind)
            self.assertEqual(DomainId.parse(str(value)),value)
        for value in (True,False,0,-1,'1'):
            with self.subTest(value=value),self.assertRaises(DomainError):
                LoreBookVersion(value)
        self.assertEqual(LoreBindingRevision().next(),LoreBindingRevision(1))
        with self.assertRaises(DomainError):
            LoreBindingRevision(True)

    def test_trigger_normalization_and_stable_fingerprint(self):
        source=ir({'text':'正文','triggers':['','猫','猫'],'secondary_triggers':[],
                   'enabled':True,'disabled':True,'priority':True,'order':'bad',
                   'settings':{'selective':True}})
        proposal=normalize_lore_ir(source)
        entry=proposal.entries[0]
        self.assertEqual(entry.primary,('猫',))
        self.assertFalse(entry.enabled)
        self.assertEqual((entry.priority,entry.order),(0,0))
        self.assertIn(LoreDiagnostic.EMPTY_TRIGGER,entry.diagnostics)
        self.assertIn(LoreDiagnostic.CONFLICTING_ENABLE_FLAGS,entry.diagnostics)
        self.assertIn(LoreDiagnostic.SELECTIVE_WITHOUT_SECONDARY,entry.diagnostics)
        self.assertEqual(registration_fingerprint('NEW_BOOK',None,None,proposal),
                         registration_fingerprint('NEW_BOOK',None,None,normalize_lore_ir(source)))

    def test_regex_and_unknown_extension_never_fallback_to_literal(self):
        proposal=normalize_lore_ir(ir(
            {'text':'regex','triggers':['.*'],'settings':{'use_regex':True}},
            {'text':'regex 字段','triggers':['.*'],'settings':{'regex':'(a+)+$'}},
            {'text':'plugin','triggers':['猫'],'settings':{'unknown_plugin':{'call':'shell'}}}))
        self.assertEqual(tuple(e.disabled_reason for e in proposal.entries),
            (LoreDiagnostic.UNSUPPORTED_REGEX,LoreDiagnostic.UNSUPPORTED_REGEX,
             LoreDiagnostic.UNSUPPORTED_EXTENSION))

    def test_malformed_core_and_oversize_rejected(self):
        for source in (ir({'text':3,'triggers':[],'settings':{}}),
                       ir({'text':'x','triggers':'bad','settings':{}}),
                       ir({'text':'x'*(MAX_ENTRY_TEXT_BYTES+1),'triggers':[],'settings':{}})):
            with self.subTest(source=source.source_fingerprint),self.assertRaises(DomainError):
                normalize_lore_ir(source)
        with self.assertRaises(DomainError):
            LoreBudget(max_rounds=17)


if __name__=='__main__':
    unittest.main()
