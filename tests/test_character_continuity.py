"""Current-turn durability, source separation, Core isolation and recovery checks."""
import copy
import importlib.util
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import types
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine import character_continuity as cc, hermes_card_runtime as rt
from life_engine.hermes_turn_proof import verify_pair
from life_engine.memory_repository import MemoryRuntimeError
from life_engine.memory import MemoryCollectionRevision
from life_engine.story import StoryRevision
from life_engine.story_sqlite_repository import StoryTransaction

PACKAGE = Path(__file__).resolve().parents[1]


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.base=Path(temp.name).resolve(); self.profile=self.base/'profiles/actor'; self.profile.mkdir(parents=True)
        self.root=self.base/'continuity'
        plan=rt.compile_plan({'name':'岚','description':'灯塔管理员。','first_mes':'灯刚亮。'},'source-hash')
        plan['options']['acknowledged']=[i['id'] for i in plan['issues']]
        self.card=self.base/'card.json'; self.card.write_bytes(cc.json_bytes(plan))
        self.sha=cc.digest(self.card.read_bytes())
        cc.init(self.root,self.profile,self.card,PACKAGE)
        with self.db() as db:
            db.execute('CREATE TABLE sessions(id TEXT PRIMARY KEY,source TEXT)')
            db.execute('CREATE TABLE messages(id INTEGER PRIMARY KEY,session_id TEXT,role TEXT,content TEXT,'
                'message_uid TEXT,tool_calls TEXT,active INTEGER,compacted INTEGER)')
            db.executemany('INSERT INTO sessions VALUES(?,?)',[('day0','cli'),('day1','cli')])

    @contextmanager
    def db(self):
        with closing(sqlite3.connect(self.profile/'state.db')) as db:
            with db:
                yield db

    def frame(self, session='day0', suffix='one'):
        return {'session_id':session,'turn_id':'turn-'+suffix,'user_uid':'user-'+suffix,
                'assistant_uid':'assistant-'+suffix,'user_text':'我明天下午去面试。',
                'assistant_text':'岚把灯擦干净，准备傍晚去码头散步。', 'watermark':0,
                'completed':True,'failed':False,'interrupted':False,'turn_exit_reason':'text_response(finish_reason=stop)'}

    def persist(self, frame):
        with self.db() as db:
            last=db.execute('SELECT coalesce(max(id),0) FROM messages').fetchone()[0]
            for offset,role in ((1,'user'),(2,'assistant')):
                db.execute('INSERT INTO messages VALUES(?,?,?,?,?,NULL,1,0)',
                    (last+offset,frame['session_id'],role,frame[role+'_text'],frame[role+'_uid']))

    def test_activation_preserves_data_and_refuses_host_drift(self):
        host=self.base/'host'
        for name in cc.HOST_FILES:
            target=host/name; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text('synthetic host source',encoding='utf-8')
        enabled=cc.activation(self.root,self.profile,self.sha,True,host)
        self.assertEqual(enabled['state'],'ENABLED')
        config=json.loads((self.profile/'.life-engine-continuity.json').read_bytes())
        self.assertEqual(len(config['host_files']),len(cc.HOST_FILES))
        world=cc.status(self.root,self.profile,self.sha)['world']
        self.assertEqual(cc.activation(self.root,self.profile,self.sha,False)['state'],'DISABLED')
        self.assertEqual(cc.status(self.root,self.profile,self.sha)['world'],world)
        self.assertTrue(list((self.root/'activation-backups').glob('*.json')))
        cc.activation(self.root,self.profile,self.sha,True,host)
        (host/cc.HOST_FILES[0]).write_text('changed source',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'ACTIVATION_CHANGED'):
            cc.activation(self.root,self.profile,self.sha,True,host)
        self.assertEqual(json.loads((self.profile/'.life-engine-continuity.json').read_bytes()),config)

    def test_new_session_reads_user_utterance_and_candidate_scene(self):
        day0=cc.context(self.root,self.profile,self.sha,'day0')
        frame=self.frame(); self.persist(frame)
        first=cc.commit(self.root,self.profile,self.sha,frame,day0['lease'])
        self.assertEqual(first,cc.commit(self.root,self.profile,self.sha,frame,day0['lease']))
        day1=cc.context(self.root,self.profile,self.sha,'day1')
        self.assertEqual(day0['world'],day1['world'])
        self.assertNotEqual(day0['lease']['session'],day1['lease']['session'])
        self.assertIn('面试',day1['records'][0]['user_said'])
        self.assertEqual(day1['records'][0]['scene_canon'],'candidate')
        self.assertIn('码头',day1['records'][0]['generated_scene'])
        self.assertEqual(cc.status(self.root,self.profile,self.sha)['turns'],{'COMMITTED':1})
        with self.assertRaisesRegex(ValueError,'SESSION_STALE'):
            cc.commit(self.root,self.profile,self.sha,frame,day0['lease'])

    def test_failed_cancelled_and_unpersisted_turns_never_write(self):
        lease=cc.context(self.root,self.profile,self.sha,'day0')['lease']
        frame=self.frame()
        with self.assertRaisesRegex(ValueError,'COMMITTED_ROW'):
            cc.commit(self.root,self.profile,self.sha,frame,lease)
        self.persist(frame)
        for field in ('failed','interrupted'):
            bad=dict(frame,**{field:True})
            with self.assertRaisesRegex(ValueError,'TURN_NOT_COMPLETE'):
                cc.commit(self.root,self.profile,self.sha,bad,lease)
        self.assertEqual(cc.status(self.root,self.profile,self.sha)['turns'],{})
        with self.assertRaisesRegex(ValueError,'TURN_NOT_COMPLETE'):
            cc.commit(self.root,self.profile,self.sha,dict(frame,turn_exit_reason='text_response(finish_reason=length)'),lease)

    def test_exact_rows_ambiguous_uids_and_old_final_rejected(self):
        frame=self.frame(); self.persist(frame)
        self.assertEqual(verify_pair(self.profile,frame)['assistant_row'],2)
        bad=dict(frame,watermark=2)
        with self.assertRaisesRegex(ValueError,'NEW_FINAL'):
            verify_pair(self.profile,bad)
        bad=dict(frame,user_text='不是原话')
        with self.assertRaisesRegex(ValueError,'TEXT_MISMATCH'):
            verify_pair(self.profile,bad)
        with self.db() as db:
            db.execute('INSERT INTO messages VALUES(3,?,?,?,?,NULL,1,0)',
                ('day0','assistant',frame['assistant_text'],frame['assistant_uid']))
        with self.assertRaisesRegex(ValueError,'UNIQUE_COMMITTED'):
            verify_pair(self.profile,frame)

    def test_profile_and_card_binding_refuse_cross_read(self):
        other=self.base/'profiles/other'; other.mkdir()
        with self.assertRaisesRegex(ValueError,'BINDING_MISMATCH'):
            cc.context(self.root,other,self.sha,'day0')
        with self.assertRaisesRegex(ValueError,'BINDING_MISMATCH'):
            cc.context(self.root,self.profile,'0'*64,'day0')
        with patch.object(cc,'verify_pair',side_effect=AssertionError('must not read another profile')):
            with self.assertRaisesRegex(ValueError,'BINDING_MISMATCH'):
                cc.commit(self.root,other,self.sha,self.frame(),{})
        other_root=self.base/'other-world'
        cc.init(other_root,other,self.card,PACKAGE)
        a=cc.context(self.root,self.profile,self.sha,'day0')
        b=cc.context(other_root,other,self.sha,'other')
        self.assertNotEqual(a['world'],b['world']); self.assertEqual(b['records'],[])

    def test_intervening_tool_round_is_not_an_ordinary_pair(self):
        frame=self.frame()
        with self.db() as db:
            db.execute('INSERT INTO messages VALUES(1,?,?,?,?,NULL,1,0)',
                       ('day0','user',frame['user_text'],frame['user_uid']))
            db.execute('INSERT INTO messages VALUES(2,?,?,?,?,?,1,0)',
                       ('day0','assistant','','tool-call','[{"id":"call"}]'))
            db.execute('INSERT INTO messages VALUES(3,?,?,?,?,NULL,1,0)',
                       ('day0','tool','tool result','tool-result'))
            db.execute('INSERT INTO messages VALUES(4,?,?,?,?,NULL,1,0)',
                       ('day0','assistant',frame['assistant_text'],frame['assistant_uid']))
        with self.assertRaisesRegex(ValueError,'ORDINARY_TEXT_PAIR'):
            verify_pair(self.profile,frame)

    def test_partial_core_write_recovers_once_and_stays_out_of_projection(self):
        lease=cc.context(self.root,self.profile,self.sha,'day0')['lease']
        frame=self.frame(); self.persist(frame)
        original=StoryTransaction.insert
        def failure(*args,**kwargs):
            raise OSError('synthetic failure before Story commit')
        with patch.object(StoryTransaction,'insert',side_effect=failure):
            with self.assertRaisesRegex(OSError,'synthetic failure'):
                cc.commit(self.root,self.profile,self.sha,frame,lease)
            with self.assertRaises(OSError):
                cc.context(self.root,self.profile,self.sha,'day0')
        self.assertEqual(cc.status(self.root,self.profile,self.sha)['turns'],{'PENDING':1})
        recovered=cc.context(self.root,self.profile,self.sha,'day1')
        self.assertEqual(len(recovered['records']),1)
        self.assertEqual(cc.status(self.root,self.profile,self.sha)['turns'],{'COMMITTED':1})
        def inspect(core):
            return (core.memory.collection_revision(core.owner).value,
                    core.story.story_revision(core.story_owner).value)
        self.assertEqual(cc.core_call(self.root,self.profile,self.sha,inspect),(1,1))

    def test_core_success_before_journal_checkpoint_recovers_without_duplicates(self):
        for failure_at in (2,3):
            with self.subTest(journal_call=failure_at):
                frame=self.frame(suffix='checkpoint-'+str(failure_at))
                lease=cc.context(self.root,self.profile,self.sha,'day0')['lease']
                self.persist(frame)
                original=cc.journal; count=0
                @contextmanager
                def interrupted(root):
                    nonlocal count
                    count+=1
                    if count==failure_at:
                        raise OSError('synthetic checkpoint failure')
                    with original(root) as db:
                        yield db
                with patch.object(cc,'journal',interrupted):
                    with self.assertRaisesRegex(OSError,'checkpoint failure'):
                        cc.commit(self.root,self.profile,self.sha,frame,lease)
                cc.context(self.root,self.profile,self.sha,'day0')
        self.assertEqual(cc.status(self.root,self.profile,self.sha)['turns'],{'COMMITTED':2})
        def inspect(core):
            return core.memory.collection_revision(core.owner).value,core.story.story_revision(core.story_owner).value
        self.assertEqual(cc.core_call(self.root,self.profile,self.sha,inspect),(2,2))

    def test_model_assertion_never_promoted_to_user_memory_and_correction_is_latest(self):
        first=self.frame(); first['assistant_text']='你以前答应陪我跑步三次。'
        lease=cc.context(self.root,self.profile,self.sha,'day0')['lease']
        self.persist(first); cc.commit(self.root,self.profile,self.sha,first,lease)
        correction=self.frame(suffix='two'); correction['user_text']='我没有答应过陪你跑步。'
        correction['assistant_text']='那就从今天重新邀请你。'
        self.persist(correction); cc.commit(self.root,self.profile,self.sha,correction,lease)
        future=cc.context(self.root,self.profile,self.sha,'day1')
        self.assertEqual(future['records'][-1]['user_said'],correction['user_text'])
        self.assertIn('用户最新明确纠正优先',future['policy'])
        self.assertNotIn(first['assistant_text'],[r['user_said'] for r in future['records']])

    def test_oversized_incomplete_and_compacted_rows_are_rejected(self):
        lease=cc.context(self.root,self.profile,self.sha,'day0')['lease']
        frame=self.frame(); frame['assistant_text']='x'*13000; self.persist(frame)
        with self.assertRaisesRegex(ValueError,'TEXT_TOO_LARGE'):
            cc.commit(self.root,self.profile,self.sha,frame,lease)
        with self.db() as db:
            db.execute('UPDATE messages SET compacted=1 WHERE role=\'assistant\'')
        with self.assertRaisesRegex(ValueError,'ORDINARY_TEXT'):
            verify_pair(self.profile,frame)

    def test_plugin_shared_user_object_gains_uid_and_writes_only_proven_completed_pair(self):
        folder=self.profile/'plugins/life-engine-character-card'; folder.mkdir(parents=True)
        runtime=PACKAGE/'runtime/life_engine'
        for source,destination in [('hermes_card_native_hook.py','__init__.py'),
            ('hermes_card_runtime.py','hermes_card_runtime.py'),('hermes_turn_proof.py','hermes_turn_proof.py')]:
            (folder/destination).write_bytes((runtime/source).read_bytes())
        (folder/'card.json').write_bytes(self.card.read_bytes())
        (folder/'binding.json').write_bytes(cc.json_bytes({'profile_home':str(self.profile)}))
        config={'format':cc.FORMAT,'enabled':True,'profile':str(self.profile),'host_root':str(PACKAGE),
                'host_files':{'README.md':cc.digest((PACKAGE/'README.md').read_bytes())},
                'python':sys.executable,'root':str(self.root),
                'runtime':str(self.root/'releases'/cc.durable.registry(self.root)['release']/'runtime')}
        (self.profile/'.life-engine-continuity.json').write_bytes(cc.json_bytes(config))
        spec=importlib.util.spec_from_file_location('continuity_test_plugin',folder/'__init__.py',
            submodule_search_locations=[str(folder)])
        module=importlib.util.module_from_spec(spec)
        def backend(config,home,action,payload):
            if action=='context':
                return cc.context(self.root,home,self.sha,payload['session_id'])
            return cc.commit(self.root,home,self.sha,payload['frame'],payload['lease'])
        frame=self.frame(); user={'role':'user','content':frame['user_text']}
        kw={'session_id':'day0','turn_id':'turn-one','platform':'cli'}
        with patch.dict(sys.modules,{'continuity_test_plugin':module,
                'hermes_constants':types.SimpleNamespace(get_hermes_home=lambda:self.profile)}):
            spec.loader.exec_module(module)
            # Actual frozen-runtime subprocess exercises stdout encoding as well
            # as the CLI JSON protocol; a mocked call would miss Windows GBK.
            actual=module.continuity_call(config,self.profile,'context',{'session_id':'day0'})
            self.assertEqual(actual['state'],'READY')
            self.assertIn('用户',actual['policy'])
            with patch.object(module,'continuity_call',side_effect=backend):
                module.before(user_message=frame['user_text'],conversation_history=[user],**kw)
                self.assertNotIn('message_uid',user)
                # The actual host flush mutates the shared message dict after pre.
                user['message_uid']=frame['user_uid']
                assistant={'role':'assistant','content':frame['assistant_text'],'message_uid':frame['assistant_uid']}
                self.persist(frame)
                module.after(conversation_history=[user,assistant],assistant_response=frame['assistant_text'],**kw)
                module.ended(completed=True,failed=False,interrupted=False,
                    turn_exit_reason=frame['turn_exit_reason'],**kw)
                self.assertEqual(cc.status(self.root,self.profile,self.sha)['turns'],{'COMMITTED':1})
                # A new session receives previous World records and not a repeated opening.
                other_user={'role':'user','content':'我们继续'}
                future=dict(session_id='day1',turn_id='future',platform='cli')
                module.before(user_message='我们继续',conversation_history=[other_user],**future)
                result=module.rewrite(request={'messages':[other_user]},**future)['request']
                whole=json.dumps(result,ensure_ascii=False)
                self.assertIn('面试',whole); self.assertIn('candidate',whole)
                self.assertNotIn('灯刚亮',whole)


if __name__=='__main__': unittest.main()
