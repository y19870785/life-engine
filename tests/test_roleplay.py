import base64
import contextlib
import copy
import json
import io
import sqlite3
import struct
import sys
import tempfile
import unittest
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from life_engine.config import defaults, now_in
from life_engine.store import Store, SCHEMA
from life_engine.engine import Engine
from life_engine.rp_cards import parse_card
from life_engine.rp_lore import normalize_book, activate_lore_entries, encoded, token_cost
from life_engine.rp_commands import dispatch
from life_engine.rp_prompt import build_prompt
from life_engine.rp_sessions import active, import_card, transition, record_message
from life_engine.rp_schema import migrate
from life_engine.durable import (create_install, registry, state_home, upgrade, health, write,
                                 snapshot, locked, restore, context_text, rollback_code)


def card(name='星澜'):
    return {'spec':'chara_card_v2','spec_version':'2.0','data':{
        'name':name,'description':'居住在星港的地图修复师。', 'personality':'认真、幽默，使用简短口吻。',
        'scenario':'用户来到地图工坊。','first_mes':'欢迎来到星港。','alternate_greetings':['地图准备好了吗？'],
        'mes_example':'<START>\n{{user}}: 你好\n{{char}}: 今天想去哪？',
        'character_book': {'entries':[
            {'keys':['星港'],'content':'星港中央有月塔。','insertion_order':10},
            {'keys':['月塔'],'content':'月塔存放失落地图。','insertion_order':20},
            {'keys':['失落地图'],'content':'失落地图记载星港。','insertion_order':30}]}}}


def png(raw, key=b'chara'):
    def chunk(kind, content):
        return struct.pack('>I',len(content))+kind+content+struct.pack('>I',zlib.crc32(kind+content)&0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+
            chunk(b'tEXt',key+b'\0'+base64.b64encode(json.dumps(raw).encode()))+
            chunk(b'IDAT',zlib.compress(b'\0\xff\xff\xff'))+chunk(b'IEND',b''))


class RoleplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.cfg = defaults('yuwei','雨薇')
        self.store = Store(self.base/'life.db','yuwei')
        self.path = self.base/'card.json'
        self.path.write_text(json.dumps(card(),ensure_ascii=False),encoding='utf-8')
        self.key = import_card(self.store,self.path)['card_id']

    def tearDown(self):
        self.temp.cleanup()

    def test_json_versions_and_png_avatar_roundtrip(self):
        for raw in [card()['data'],card(),{**card(),'spec':'chara_card_v3'}]:
            self.path.write_text(json.dumps(raw),encoding='utf-8')
            self.assertEqual(parse_card(self.path)[1]['name'],'星澜')
        p=self.base/'avatar.png'; p.write_bytes(png(card('另一位')))
        raw, parsed, avatar=parse_card(p)
        self.assertTrue(avatar.startswith(b'\x89PNG'))
        self.assertNotIn(b'chara\0',avatar)
        result=import_card(self.store,p)
        with self.store.tx() as db:
            row=db.execute('SELECT raw_json,parsed_json,avatar FROM roleplay_cards WHERE id=?',(result['card_id'],)).fetchone()
            self.assertEqual(json.loads(row['raw_json']),raw)
            self.assertEqual(json.loads(row['parsed_json']),parsed)
            self.assertEqual(row['avatar'],avatar)

    def test_corrupt_png_and_invalid_cards_do_not_write(self):
        p=self.base/'bad.png'; data=bytearray(png(card())); data[-5]^=1; p.write_bytes(data)
        with self.assertRaisesRegex(ValueError,'CRC'): import_card(self.store,p)
        self.path.write_text('[]')
        with self.assertRaises(ValueError): import_card(self.store,self.path)
        self.assertEqual(len(dispatch(self.store,self.cfg,'list')['cards']),1)

    def test_lore_recursion_case_depth_and_budget(self):
        entries=normalize_book(card()['data']['character_book'])
        self.assertEqual(len(activate_lore_entries(entries,['星港'],max_recursion=0)),1)
        self.assertEqual(len(activate_lore_entries(entries,['星港'],max_recursion=1)),2)
        self.assertEqual(len(activate_lore_entries(entries,['星港'])),3)
        self.assertEqual(activate_lore_entries(entries,['星港','nothing'],scan_depth=1),[])
        for budget in [0,100,200,400,2000]:
            result=activate_lore_entries(entries,['星港'],max_tokens=budget)
            self.assertLessEqual(token_cost(encoded(result)) if result else 0,budget)
        english=normalize_book({'entries':[{'keys':['Moon'],'content':'yes','case_sensitive':True}]})
        self.assertEqual(activate_lore_entries(english,['moon']),[])
        self.assertEqual(len(activate_lore_entries(english,['Moon'])),1)

    def test_disabled_nonrecursive_and_priority(self):
        entries=normalize_book({'entries':[
            {'keys':['start'],'content':'later','priority':3},
            {'keys':['start'],'content':'disabled','enabled':False},
            {'keys':['later'],'content':'stop','recursive':False}]})
        self.assertEqual([r['content'] for r in activate_lore_entries(entries,['start'])],['later'])
        high=activate_lore_entries(entries,['start'],max_tokens=150)
        self.assertEqual(high[0]['content'],'later')

    def test_enter_switch_exit_and_meta_memory_isolation(self):
        self.store.remember(1,'private','SOUL_PRIVATE_LIFE','real_user')
        self.store.loop_add(1,'SOUL_PRIVATE_LOOP')
        transition(self.store,'enter','星澜')
        self.store.remember(2,'event','一起修好了地图','conversation')
        record_message(self.store,'星港',event_key='turn-1')
        context=build_prompt(self.store,self.cfg)
        self.assertNotIn('SOUL_PRIVATE',context['text'])
        self.assertIn('一起修好了地图',context['text'])
        self.assertEqual(len(context['activated_lore']),3)
        self.assertIn('雨薇',context['text'])
        self.assertEqual(context['mode'],'roleplay')
        other=self.base/'other.json'; other.write_text(json.dumps(card('航海者')),encoding='utf-8')
        import_card(self.store,other)
        transition(self.store,'switch','航海者')
        self.assertNotIn('一起修好了地图',build_prompt(self.store,self.cfg)['text'])
        transition(self.store,'switch','星澜')
        self.assertIn('一起修好了地图',build_prompt(self.store,self.cfg)['text'])
        result=dispatch(self.store,self.cfg,'/rp exit')
        self.assertEqual(result['mode'],'soul')
        context=build_prompt(self.store,self.cfg)
        self.assertIn('SOUL_PRIVATE_LIFE',context['text'])
        self.assertIn('roleplay_meta',context['text'])
        self.assertEqual(context['activated_lore'],[])
        with self.store.tx() as db:
            for row in db.execute('SELECT * FROM memories'):
                if row['scope']=='persona':
                    self.assertIsNotNone(row['card_id']); self.assertIsNotNone(row['session_id'])
                else: self.assertIsNone(row['card_id'])

    def test_switch_unknown_is_atomic_exit_idempotent(self):
        transition(self.store,'enter','星澜')
        before=dispatch(self.store,self.cfg,'status')['session_id']
        with self.assertRaises(ValueError): transition(self.store,'switch','missing')
        self.assertEqual(dispatch(self.store,self.cfg,'status')['session_id'],before)
        transition(self.store,'exit'); count=len(build_prompt(self.store,self.cfg)['text'])
        transition(self.store,'exit')
        self.assertEqual(len(build_prompt(self.store,self.cfg)['text']),count)

    def test_foreign_keys_scope_checks_and_active_uniqueness(self):
        state=transition(self.store,'enter','星澜')
        for sql,args in [
            ("INSERT INTO memories(at,kind,summary,provenance,scope) VALUES(1,'x','x','x','persona')",()),
            ("INSERT INTO memories(at,kind,summary,provenance,scope,card_id,session_id) VALUES(1,'x','x','x','persona',?,99999)",(self.key,)),
            ("INSERT INTO roleplay_sessions(agent_id,card_id,started_at,status) VALUES('yuwei',?,1,'active')",(self.key,))]:
            with self.assertRaises(sqlite3.IntegrityError):
                with self.store.tx() as db: db.execute(sql,args)
        self.assertEqual(dispatch(self.store,self.cfg,'status')['session_id'],state['session_id'])

    def test_parallel_enter_claims_once(self):
        def enter(_):
            try: transition(self.store,'enter','星澜'); return True
            except ValueError: return False
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sum(pool.map(enter,range(4))),1)

    def test_life_silent_photo_blocked_and_loops_protected(self):
        transition(self.store,'enter','星澜')
        engine=Engine(self.cfg,self.store); now=now_in(self.cfg)
        self.assertEqual(engine.wake(now)['reason'],'roleplay_active')
        self.assertNotIn('moment',engine.status(now))
        with self.assertRaises(ValueError): self.store.loop_add(1,'fictional appointment')
        from life_engine.photos import photo
        with self.assertRaisesRegex(ValueError,'Soul'): photo(self.cfg,self.base,self.store,engine,now)
        transition(self.store,'exit')
        self.assertIn('moment',engine.status(now))

    def test_import_book_and_delete_cascade(self):
        path=self.base/'world book.json'
        path.write_text(json.dumps({'entries':{'0':{'key':['工坊'],'content':'repair','order':5,'position':1,'depth':2}}}))
        dispatch(self.store,self.cfg,f'book "星澜" "{path}"')
        transition(self.store,'enter','星澜'); self.store.remember(1,'event','test','test')
        with self.assertRaises(ValueError): dispatch(self.store,self.cfg,'delete 星澜')
        transition(self.store,'exit'); dispatch(self.store,self.cfg,'delete 星澜')
        with self.store.tx() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM roleplay_lorebook_entries').fetchone()[0],0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM memories WHERE scope='persona'").fetchone()[0],0)
            self.assertGreater(db.execute("SELECT COUNT(*) FROM memories WHERE kind='roleplay_meta'").fetchone()[0],0)
            self.assertIsNone(db.execute('PRAGMA foreign_key_check').fetchone())

    def test_memory_disabled_and_aside(self):
        self.store.remember(1,'fact','real-only','test')
        transition(self.store,'enter','星澜')
        original=dispatch(self.store,self.cfg,'status')['session_id']
        self.assertIn('real-only',dispatch(self.store,self.cfg,'aside 请评价')['text'])
        self.assertEqual(dispatch(self.store,self.cfg,'status')['session_id'],original)
        self.cfg['memory']['enabled']=False
        with self.assertRaises(ValueError): dispatch(self.store,self.cfg,'record user secret')
        transition(self.store,'exit',memory_enabled=False)
        self.assertNotIn('real-only',build_prompt(self.store,self.cfg)['text'])

    def test_stale_session_cannot_write_soul_or_next_persona(self):
        first=transition(self.store,'enter','星澜')['session_id']
        transition(self.store,'exit')
        with self.assertRaisesRegex(ValueError,'session changed'):
            self.store.remember(1,'event','late fictional write','test',expected_session=first)
        transition(self.store,'enter','星澜')
        self.assertFalse(record_message(self.store,'late reply',role='assistant',expected_session=first))
        self.assertNotIn('late fictional write',build_prompt(self.store,self.cfg)['text'])

    def test_depth_placement_and_repeated_event_deduplication(self):
        path=self.base/'depth.json'
        path.write_text(json.dumps({'entries':[{'keys':['two'],'content':'DEPTH_LORE','position':'at_depth','depth':1}]}))
        dispatch(self.store,self.cfg,f'book "星澜" "{path}"')
        transition(self.store,'enter','星澜')
        record_message(self.store,'one',event_key='1'); record_message(self.store,'two',event_key='2')
        record_message(self.store,'two',event_key='2')
        result=build_prompt(self.store,self.cfg)
        dialogue=result['context']['dialogue_with_lore']
        self.assertEqual([m['content'] for m in dialogue],['one','DEPTH_LORE','two'])

    def test_prompt_has_hard_bound_with_large_card(self):
        raw=card('大卡'); raw['data'].update({k:'长'*16000 for k in ('description','personality','scenario','mes_example','first_mes')})
        path=self.base/'large.json'; path.write_text(json.dumps(raw))
        import_card(self.store,path); transition(self.store,'enter','大卡')
        result=build_prompt(self.store,self.cfg)
        self.assertLessEqual(token_cost(result['text']),24000)
        self.assertIn('核心身份',result['text'])


class MigrationTests(unittest.TestCase):
    def test_invalid_tool_arguments_return_json_error(self):
        from life_engine.cli import main
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(['--agent','test','remember','--summary','hello','--id','1'])
        self.assertEqual(result, 1)
        error = json.loads(output.getvalue())
        self.assertFalse(error['ok'])
        self.assertIn('--id', error['message'])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.base=Path(self.temp.name)
        self.host=self.base/'host'; self.host.mkdir(); self.root=self.base/'permanent'
        self.cfg=defaults('test'); self.cfg['integration'].update(adapter='generic',host_home=str(self.host))
        self.key=create_install(ROOT,self.root,self.cfg)['instance']

    def tearDown(self): self.temp.cleanup()

    def make_legacy(self):
        reg=registry(self.root); inst=reg['instances'][self.key]; data=state_home(self.root,inst)
        path=data/'agents/test/life.db'; path.unlink()
        with contextlib.closing(sqlite3.connect(path)) as db, db:
            db.executescript(SCHEMA)
            db.execute("INSERT INTO meta VALUES('agent_id','test')")
            db.execute("INSERT INTO meta VALUES('schema_version','2')")
            db.execute("INSERT INTO memories(at,kind,summary,provenance) VALUES(1,'fact','KEEP ME','owner')")
        reg['data_schema']=2; write(self.root/'registry.json',reg)
        return path,reg

    def test_upgrade_copies_schema2_and_preserves_original(self):
        path,reg=self.make_legacy(); before=path.read_bytes()
        result=upgrade(self.root,ROOT)
        self.assertEqual(path.read_bytes(),before)
        self.assertTrue(result['backups'])
        new=registry(self.root); self.assertEqual(new['data_schema'],3)
        inst=new['instances'][self.key]; self.assertNotEqual(inst['generation'],reg['instances'][self.key]['generation'])
        store=Store(state_home(self.root,inst)/'agents/test/life.db','test')
        with store.tx() as db:
            self.assertEqual(dict(db.execute('SELECT summary,scope FROM memories').fetchone()),{'summary':'KEEP ME','scope':'soul'})
        # A schema-2 backup remains restorable via a new migrated generation.
        restored=restore(self.root,self.key,result['backups'][0]); self.assertTrue(restored['proactive_paused'])

    def test_failed_migration_keeps_registry_and_source(self):
        path,_=self.make_legacy(); before=path.read_bytes(); pointer=(self.root/'registry.json').read_bytes()
        with patch('life_engine.rp_schema.migrate',side_effect=RuntimeError('migration failed')):
            with self.assertRaises(RuntimeError): upgrade(self.root,ROOT)
        self.assertEqual(path.read_bytes(),before)
        self.assertEqual((self.root/'registry.json').read_bytes(),pointer)

    def test_missing_database_is_not_recreated(self):
        reg=registry(self.root); path=state_home(self.root,reg['instances'][self.key])/'agents/test/life.db'
        path.unlink()
        with self.assertRaisesRegex(ValueError,'missing'): health(self.root)
        self.assertFalse(path.exists())

    def test_hook_exit_and_roleplay_context_do_not_leak_soul(self):
        reg=registry(self.root); inst=reg['instances'][self.key]; data=state_home(self.root,inst)
        store=Store(data/'agents/test/life.db','test'); store.remember(1,'private','PRIVATE_SOUL','test')
        path=self.base/'card.json'; path.write_text(json.dumps(card()))
        import_card(store,path); transition(store,'enter','星澜')
        result=context_text(self.root,reg,inst,data,True,'one','星港')
        self.assertNotIn('PRIVATE_SOUL',result['text']); self.assertEqual(len(result['activated_lore']),3)
        self.assertIn(inst['tool_name'],result['text'])
        self.assertIn('session_id',result['text'])
        result=context_text(self.root,reg,inst,data,True,'two','退出角色')
        self.assertEqual(result['mode'],'soul'); self.assertIsNotNone(result['control'])
        self.assertIn('PRIVATE_SOUL',result['text'])


if __name__=='__main__': unittest.main()
