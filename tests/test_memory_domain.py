"""类型、受众与输入边界验收。"""
import unittest
from memory_fixture import *


class MemoryDomainTests(unittest.TestCase):
    def test_memory_id_and_revision(self):
        value = DomainId.new(IdKind.MEMORY)
        self.assertEqual(DomainId.parse(str(value)),value)
        self.assertIs(type(MemoryCollectionRevision().next()),MemoryCollectionRevision)
        with self.assertRaises(ValueError):
            MemoryCollectionRevision(True)

    def test_audience_rules(self):
        from life_engine.memory import audiences
        for values in ((),(MemoryAudience(AudienceKind.WORLD),)*2,
                       (MemoryAudience(AudienceKind.WORLD),MemoryAudience(AudienceKind.USER,DomainId.new(IdKind.OWNER)))):
            with self.assertRaises(ValueError):
                audiences(values)
        with self.assertRaises(ValueError):
            MemoryAudience(AudienceKind.CHARACTER_INSTANCE,DomainId.new(IdKind.DEFINITION))

    def test_text_bounds_and_subject(self):
        from life_engine.memory import bounded_text
        for value in ('', '中'*22000):
            with self.assertRaises(ValueError):
                bounded_text(value,65536)
        with self.assertRaises(ValueError):
            MemorySubject(SubjectKind.TEXT,text='x'*513)
        self.assertEqual(MemorySubject(SubjectKind.TEXT,text='world:不解析路径').kind,SubjectKind.TEXT)
