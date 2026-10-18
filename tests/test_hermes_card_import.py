import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine import hermes_card_import as ci, hermes_card_hook as hook
from test_import_cards import card, png


class HermesCardImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.home = self.root/'profiles/trial'
        self.home.mkdir(parents=True)
        (self.home/'SOUL.md').write_text('original persona', encoding='utf-8')
        (self.home/'config.yaml').write_text('untouched', encoding='utf-8')
        value = card()
        value['data']['character_book'] = {'entries': [
            {'keys':['月港'], 'content':'虚构的月港有灯塔。', 'enabled':True},
            {'keys':['.*'], 'content':'不运行正则', 'use_regex':True},
            {'keys':['秘密'], 'content':'隐藏身份，未被选择'},
        ]}
        self.source = self.root/'original.png'
        self.source.write_bytes(png(value))
        self.plan = self.root/'preview.json'
        ci.preview(self.source, self.plan)
        data = json.loads(self.plan.read_text(encoding='utf-8'))
        data['entries'][0]['include'] = True
        self.plan.write_bytes(ci.json_bytes(data))

    def install(self):
        return ci.apply(self.plan, self.home, ci.digest(self.plan.read_bytes()))

    def test_preview_install_hook_verify_rollback(self):
        result = self.install()
        receipt = Path(result['receipt'])
        self.assertTrue(ci.verify(self.home, receipt)['ok'])
        folder = self.home/'plugins'/hook.PLUGIN
        deployed = json.loads((folder/'card.json').read_text(encoding='utf-8'))
        self.assertEqual(len(deployed['entries']),1)
        self.assertNotIn('隐藏身份', (folder/'card.json').read_text(encoding='utf-8'))
        spec = importlib.util.spec_from_file_location('installed_card', folder/'__init__.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        fake = types.SimpleNamespace(get_hermes_home=lambda:self.home)
        with patch.dict(sys.modules, {'hermes_constants':fake}):
            self.assertIn('灯塔', module.before(user_message='月港有什么？')['context'])
            self.assertNotIn('灯塔', module.before(user_message='早上好')['context'])
            self.assertIsNone(module.before(user_message='月港',parent_session_id='child'))
            fake.get_hermes_home = lambda:self.root/'default'
            self.assertIsNone(module.before(user_message='月港'))
        with ci.locked(self.home): ci.restore(self.home,receipt)
        self.assertEqual((self.home/'SOUL.md').read_text(), 'original persona')
        self.assertFalse((folder/'plugin.yaml').exists())
        self.assertEqual((self.home/'config.yaml').read_text(),'untouched')
        self.assertFalse(ci.verify(self.home,receipt)['ok'])
        self.assertEqual(ci.restore(self.home,receipt)['state'],'ROLLED_BACK')
        self.assertEqual(self.install()['state'], 'APPLIED')

    def test_frozen_plan_and_default_home_refused(self):
        with self.assertRaisesRegex(ValueError,'PLAN_CHANGED'):
            ci.apply(self.plan,self.home,'0'*64)
        with self.assertRaisesRegex(ValueError,'NAMED_PROFILE'):
            ci.apply(self.plan,self.root,ci.digest(self.plan.read_bytes()))
        with self.assertRaises(FileExistsError): ci.preview(self.source,self.plan)
        self.assertEqual((self.home/'SOUL.md').read_text(),'original persona')

    def test_unsupported_requires_explicit_adaptation(self):
        data=json.loads(self.plan.read_text()); data['entries'][1]['include']=True
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_ENTRY'):
            hook.validate_card(data)
        data['entries'][1]['unsupported']=[]; data['entries'][1]['text']='<% getvar("x") %>'
        with self.assertRaisesRegex(ValueError,'TEMPLATE_REQUIRES'):
            hook.validate_card(data)

    def test_user_edits_block_all_rollback_writes(self):
        result=self.install(); p=self.home/'SOUL.md'; p.write_text('user edit')
        self.assertFalse(ci.verify(self.home,result['receipt'])['ok'])
        with self.assertRaisesRegex(ValueError,'ROLLBACK_DRIFT'):
            ci.restore(self.home,result['receipt'])
        self.assertEqual(p.read_text(),'user edit')
        self.assertTrue((self.home/'plugins'/hook.PLUGIN/'card.json').exists())

    def test_failed_install_restores_prior_files(self):
        original=ci.atomic; failed=False
        def fail_once(path,data):
            nonlocal failed
            if Path(path).name=='binding.json' and not failed:
                failed=True; raise OSError('injected disk error')
            original(path,data)
        with patch.object(ci,'atomic',side_effect=fail_once):
            with self.assertRaisesRegex(OSError,'injected'): self.install()
        self.assertEqual((self.home/'SOUL.md').read_text(),'original persona')
        self.assertFalse((self.home/'plugins'/hook.PLUGIN/'__init__.py').exists())
        self.assertFalse((self.home/'.life-engine-card.lock').exists())

    def test_link_and_unowned_plugin_refused(self):
        folder=self.home/'plugins'/hook.PLUGIN; folder.mkdir(parents=True)
        (folder/'user.txt').write_text('do not change')
        with self.assertRaisesRegex(ValueError,'PLUGIN_EXISTS'): self.install()
        link=self.root/'linked'
        try: link.symlink_to(self.home,target_is_directory=True)
        except OSError: return
        with self.assertRaisesRegex(ValueError,'LINK_PATH'): ci.home_path(link)

    def test_selective_literal_matching_and_budget(self):
        data=json.loads(self.plan.read_text()); row=data['entries'][0]
        row.update(keys=['L'],secondary_keys=['月港'],selective=True)
        self.assertEqual(hook.project(data,'Hello 月港')[0],[])
        self.assertEqual(hook.project(data,'L')[0],[])
        self.assertEqual(len(hook.project(data,'L在月港')[0]),1)
        row['text']='x'*16000
        self.assertEqual(hook.project(data,'L 月港')[1],[0])
        self.assertEqual(len(hook.text_input('x'*9000)),8192)

    def test_backup_corruption_and_concurrent_install_refused(self):
        with ci.locked(self.home):
            with self.assertRaises(FileExistsError): self.install()
        result=self.install(); receipt=Path(result['receipt'])
        (receipt.parent/'before/SOUL.md').write_text('corrupt')
        with self.assertRaisesRegex(ValueError,'BACKUP_CHANGED'):
            ci.restore(self.home,receipt)

    def test_receipt_tampering_never_deletes_original_soul(self):
        result=self.install(); receipt=Path(result['receipt'])
        data=json.loads(receipt.read_text()); data['files']['SOUL.md']['before']=None
        receipt.write_bytes(ci.json_bytes(data))
        before=(self.home/'SOUL.md').read_bytes()
        for operation in (ci.verify,ci.restore):
            with self.assertRaisesRegex(ValueError,'RECEIPT_CHANGED'):
                operation(self.home,receipt)
        self.assertEqual((self.home/'SOUL.md').read_bytes(),before)

    def test_cache_archive_conflict_refused_before_any_restore(self):
        result=self.install(); receipt=Path(result['receipt'])
        cache=self.home/'plugins'/hook.PLUGIN/'__pycache__'; cache.mkdir()
        (cache/'keep.txt').write_text('preserve')
        (receipt.parent/'runtime-cache').mkdir()
        before={name:(self.home/name).read_bytes() for name in ci.FILES}
        with self.assertRaisesRegex(ValueError,'CACHE_ARCHIVE_CONFLICT'):
            ci.restore(self.home,receipt)
        self.assertEqual(before,{name:(self.home/name).read_bytes() for name in ci.FILES})
        self.assertEqual((cache/'keep.txt').read_text(),'preserve')

    def test_preview_preserves_full_private_original_without_deploying_it(self):
        original=card(); original['data']['extensions']={'private_unknown':'sentinel'}
        original['data']['character_book']={'scan_depth':42,'entries':[
            {'keys':['one'],'content':'entry','disable':True,'insertion_order':7}]}
        src=self.root/'full.json'; src.write_text(json.dumps(original))
        plan=self.root/'full-plan.json'; ci.preview(src,plan)
        value=json.loads(plan.read_text())
        self.assertEqual(value['review_only']['original'],original)
        self.assertTrue(value['entries'][0]['source_disabled'])
        self.assertEqual(value['entries'][0]['source_order'],7)


if __name__=='__main__': unittest.main()
