import contextlib
import copy
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from life_engine.config import defaults
from life_engine.durable import (create_install, health, locked, read, registry, restore, snapshot,
                                 state_home, upgrade, write)
from life_engine.deploy_cli import main, plan_install, apply_preview
from life_engine.install import build_plan, apply_plan


class DurableTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='life persistent test ')
        self.base = Path(self.temp.name).resolve()
        self.host = self.base / 'existing agent'
        self.host.mkdir()
        self.soul = b'\xef\xbb\xbfName: Existing Persona\r\nPreserve me.\r\n'
        (self.host / 'SOUL.md').write_bytes(self.soul)
        (self.host / 'config.yaml').write_text('model: existing-provider\n')
        self.root = self.base / 'permanent data'
        self.cfg = defaults('same_name')
        self.cfg['integration'].update(adapter='hermes', host_home=str(self.host))

    def tearDown(self):
        self.temp.cleanup()

    def install(self, **kwargs):
        result = create_install(ROOT, self.root, self.cfg, **kwargs)
        self.key = result['instance']
        return result

    def command(self, *args):
        done = subprocess.run([sys.executable, str(self.root / 'life.py'), '--instance', self.key, *args],
                              capture_output=True, text=True, encoding='utf-8', timeout=20,
                              env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'HERMES_HOME': str(self.base / 'unrelated')})
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return json.loads(done.stdout)

    def active(self):
        reg = registry(self.root)
        inst = reg['instances'][self.key]
        return reg, inst, state_home(self.root, inst)

    def test_entrypoint_survives_deleted_unpack_and_fresh_process(self):
        unpack = self.base / 'unpacked'
        shutil.copytree(ROOT, unpack, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        result = create_install(unpack, self.root, self.cfg)
        self.key = result['instance']
        self.command('remember', '--summary=Keep this across restart')
        shutil.rmtree(unpack)
        result = self.command('status')
        self.assertIn('Keep this across restart', json.dumps(result))
        check = subprocess.run([sys.executable, str(self.root / 'manage.py'), 'doctor'],
                               capture_output=True, text=True, timeout=20)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual((self.host / 'SOUL.md').read_bytes(), self.soul)
        self.assertEqual((self.host / 'config.yaml').read_text(), 'model: existing-provider\n')

    def test_reinstall_does_not_reset_manually_changed_settings_or_database(self):
        self.install()
        self.command('remember', '--summary=Independent memory')
        reg, inst, data = self.active()
        config = data / 'agents/same_name/agent.json'
        changed = read(config)
        changed['social']['recent_chat_minutes'] = 222
        write(config, changed)
        before_db = (data / 'agents/same_name/life.db').read_bytes()
        result = self.install()
        self.assertEqual(read(config)['social']['recent_chat_minutes'], 222)
        self.assertEqual((data / 'agents/same_name/life.db').read_bytes(), before_db)
        self.assertTrue(Path(result['backup']).is_dir())
        self.assertEqual(len(registry(self.root)['instances']), 1)

    def test_code_upgrade_backs_up_and_preserves_state_bytes(self):
        self.install()
        self.command('remember', '--summary=Before upgrade')
        reg, inst, data = self.active()
        before = {p.name: p.read_bytes() for p in (data / 'agents/same_name').iterdir() if p.is_file()}
        new = self.base / 'new release'
        shutil.copytree(ROOT, new, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        version = new / 'runtime/life_engine/__init__.py'
        version.write_text(version.read_text() + '\n# simulated next patch release\n')
        result = upgrade(self.root, new)
        self.assertNotEqual(result['release'], reg['release'])
        self.assertEqual(registry(self.root)['instances'][self.key]['generation'], inst['generation'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in (data / 'agents/same_name').iterdir() if p.is_file()})
        self.assertIn('Before upgrade', json.dumps(self.command('status')))

    def test_distinct_hosts_with_same_agent_name_do_not_share_memory(self):
        self.install()
        first = self.key
        self.command('remember', '--summary=Private to Hermes')
        second_host = self.base / 'openclaw work'
        second_host.mkdir()
        cfg = copy.deepcopy(self.cfg)
        cfg['integration'].update(adapter='openclaw', host_home=str(second_host))
        second = create_install(ROOT, self.root, cfg, host_agent_id='main')['instance']
        self.assertNotEqual(first, second)
        self.key = second
        self.assertNotIn('Private to Hermes', json.dumps(self.command('status')))

    def test_restore_is_atomic_and_pauses_to_prevent_delivery_replay(self):
        self.install()
        self.command('remember', '--summary=At backup')
        reg, inst, data = self.active()
        with locked(self.root, self.key):
            saved = snapshot(self.root, reg, inst)
        self.command('remember', '--summary=After backup')
        restored = restore(self.root, self.key, saved)
        self.assertTrue(restored['proactive_paused'])
        result = self.command('status')
        self.assertIn('At backup', json.dumps(result))
        self.assertNotIn('After backup', json.dumps(result))
        self.assertTrue(data.exists())
        self.assertTrue(Path(restored['previous_backup']).exists())
        db = Path(restored['active_data']) / 'agents/same_name/life.db'
        with contextlib.closing(sqlite3.connect(db)) as conn, conn:
            self.assertEqual(conn.execute("SELECT value FROM meta WHERE key='paused'").fetchone()[0], 'true')

    def test_failed_restore_pointer_write_leaves_active_generation_untouched(self):
        self.install()
        reg, inst, data = self.active()
        with locked(self.root, self.key):
            saved = snapshot(self.root, reg, inst)
        before = (self.root / 'registry.json').read_bytes()
        from life_engine import durable
        original = durable.write
        def fail(path, value):
            if Path(path).name == 'registry.json':
                raise OSError('Simulated disk failure before pointer replacement')
            return original(path, value)
        with patch.object(durable, 'write', fail):
            with self.assertRaises(OSError):
                restore(self.root, self.key, saved)
        self.assertEqual(before, (self.root / 'registry.json').read_bytes())
        self.command('status')

    def test_corrupt_backup_is_rejected_without_changing_active_state(self):
        self.install()
        reg, inst, data = self.active()
        with locked(self.root, self.key):
            saved = snapshot(self.root, reg, inst)
        before = (self.root / 'registry.json').read_bytes()
        (saved / 'data/agents/same_name/agent.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            restore(self.root, self.key, saved)
        self.assertEqual(before, (self.root / 'registry.json').read_bytes())

    def test_backup_contains_committed_wal_and_assets(self):
        self.install()
        reg, inst, data = self.active()
        image = data / 'agents/same_name/photos/original.png'
        image.parent.mkdir()
        image.write_bytes(b'actual-image-bytes')
        dbpath = data / 'agents/same_name/life.db'
        with contextlib.closing(sqlite3.connect(dbpath)) as live:
            live.execute('PRAGMA journal_mode=WAL')
            live.execute("INSERT INTO memories(at,kind,summary,provenance) VALUES(0,'test','WAL-only record','test')")
            live.commit()
            self.assertTrue(Path(str(dbpath) + '-wal').exists())
            with locked(self.root, self.key):
                saved = snapshot(self.root, reg, inst)
            with contextlib.closing(sqlite3.connect(saved / 'data/agents/same_name/life.db')) as copy_db, copy_db:
                self.assertEqual(copy_db.execute('SELECT summary FROM memories').fetchone()[0], 'WAL-only record')
            self.assertEqual((saved / 'data/agents/same_name/photos/original.png').read_bytes(), b'actual-image-bytes')

    def test_unknown_database_schema_rejects_upgrade(self):
        self.install()
        _, _, data = self.active()
        with contextlib.closing(sqlite3.connect(data / 'agents/same_name/life.db')) as db, db:
            db.execute("UPDATE meta SET value='999' WHERE key='schema_version'")
        before = (self.root / 'registry.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'schema'):
            upgrade(self.root, ROOT)
        self.assertEqual(before, (self.root / 'registry.json').read_bytes())

    def test_v02_import_preserves_memory_without_importing_runtime(self):
        apply_plan(build_plan(ROOT, self.cfg))
        legacy = self.host / 'life-engine'
        subprocess.run([sys.executable, str(legacy / 'life.py'), '--agent', 'same_name', 'remember', '--summary=Legacy memory'],
                       capture_output=True, check=True)
        before = (legacy / 'agents/same_name/life.db').read_bytes()
        self.install(source=legacy)
        _, _, data = self.active()
        self.assertNotIn('runtime', [p.name for p in data.iterdir()])
        self.assertIn('Legacy memory', json.dumps(self.command('status')))
        self.assertEqual(before, (legacy / 'agents/same_name/life.db').read_bytes())

    def test_preview_config_race_is_detected_before_install(self):
        plan = plan_install(ROOT, self.root, self.cfg)
        (self.host / 'SOUL.md').write_text('Changed in another session')
        with self.assertRaisesRegex(ValueError, 'changed after preview'):
            apply_preview(ROOT, plan)
        self.assertFalse((self.root / 'registry.json').exists())

    def test_daily_backup_deduplicates_across_fresh_wake_processes(self):
        self.install()
        self.command('wake')
        first = list((self.root / 'backups').iterdir())
        self.command('wake')
        self.assertEqual(first, list((self.root / 'backups').iterdir()))

    def test_refuses_data_root_inside_unpacked_or_host_tree(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            create_install(ROOT, self.host / 'will be overwritten', self.cfg)
        with self.assertRaisesRegex(ValueError, 'outside'):
            create_install(ROOT, ROOT / 'accidental state', self.cfg)

    def test_native_hermes_adapter_loads_state_and_filters_other_profiles(self):
        self.install(owner_channel='weixin', owner_sender_id='owner-123')
        path = self.root / 'bridges' / self.key / 'hermes/__init__.py'
        fake = types.ModuleType('hermes_constants')
        fake.get_hermes_home = lambda: self.host
        with patch.dict(sys.modules, {'hermes_constants': fake}):
            spec = importlib.util.spec_from_file_location('life_test_native_hermes', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            ctx = types.SimpleNamespace(tools=[], hooks={}, commands={})
            ctx.register_tool = lambda **kw: ctx.tools.append(kw)
            ctx.register_hook = lambda name, fn: ctx.hooks.update({name: fn})
            ctx.register_command = lambda name, handler, **kw: ctx.commands.update({name:handler})
            module.register(ctx)
            self.assertEqual(len(ctx.tools), 1)
            result = ctx.hooks['pre_llm_call'](platform='weixin', sender_id='owner-123', turn_id='incoming-1')
            self.assertIn('CURRENT_STATE_JSON', result['context'])
            observed = read(self.root / 'instances' / self.key / 'observed.json')
            self.assertIn('last_owner_hook_at', observed)
            self.assertIn('rp',ctx.commands)
            self.assertIn('星澜',ctx.commands['rp']('import "' + str(ROOT/'examples/roleplay/starmap.card.json') + '"'))
            self.assertIn('现在将扮演',ctx.commands['rp']('enter 星澜'))
            result = ctx.hooks['pre_llm_call'](platform='weixin',sender_id='owner-123',turn_id='rp-1',user_message='星港')
            self.assertIn('月塔',result['context'])
            self.assertNotIn('CURRENT_STATE_JSON',result['context'])
            ctx.hooks['post_llm_call'](turn_id='rp-1',assistant_response='我们一起修复地图。')
            self.assertIn('修复地图',ctx.commands['rp']('exit'))
            self.assertIn('soul',ctx.commands['rp']('status'))
            fake.get_hermes_home = lambda: self.base / 'another profile'
            self.assertIn('Different Hermes Profile',ctx.commands['rp']('enter 星澜'))
            self.assertIsNone(ctx.hooks['pre_llm_call'](platform='weixin'))
            self.assertFalse(json.loads(ctx.tools[0]['handler']({'action': 'status'}))['ok'])

    @unittest.skipUnless(shutil.which('node'), 'Node unavailable')
    def test_native_openclaw_adapter_scopes_tools_and_prompt_to_exact_agent(self):
        self.cfg['integration']['adapter'] = 'openclaw'
        self.install(host_agent_id='main', owner_channel='weixin', owner_sender_id='owner-123')
        stub = self.base / 'node_modules/openclaw'
        stub.mkdir(parents=True)
        (stub / 'package.json').write_text(json.dumps({'type': 'module', 'exports': {'./plugin-sdk/plugin-entry': './entry.mjs'}}))
        (stub / 'entry.mjs').write_text('export function definePluginEntry(entry) { return entry; }')
        bridge = self.root / 'bridges' / self.key / 'openclaw/index.mjs'
        script = self.base / 'probe.mjs'
        script.write_text('''import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const plugin = (await import(pathToFileURL(process.argv[2]))).default;
const host = process.argv[3];
let factory; const hooks = {}; const commands = {};
plugin.register({registerTool(fn){factory=fn}, registerCommand(c){commands[c.name]=c}, on(name, fn){hooks[name]=fn}, logger: console});
assert.equal(factory({agentId:'other', workspaceDir:host}), null);
assert.equal(factory({agentId:'main'}), null);
const tool = factory({agentId:'main',workspaceDir:host});
const result = await tool.execute('1',{action:'status'});
assert.ok(result.details);
assert.equal(await hooks.before_prompt_build({}, {agentId:'other',workspaceDir:host}), undefined);
const context = await hooks.before_prompt_build({}, {agentId:'main',workspaceDir:host,
 inputProvenance:{kind:'external_user'}, senderId:'owner-123',channel:'weixin',runId:'run-1',
 toolAuthority:{allows(){return true}},hookInvocation:{assertActive(){}}});
assert.ok(context.prependContext.includes('CURRENT_STATE_JSON'));
assert.equal(commands.rp.requireAuth, true);
const commandCtx={agentId:'main',workspaceDir:host,senderId:'owner-123',channel:'weixin'};
await commands.rp.handler({...commandCtx,args:'import "'+process.argv[4]+'"'});
const entered=await commands.rp.handler({...commandCtx,args:'enter 星澜'});
assert.ok(entered.text.includes('现在将扮演'));
const rp=await hooks.before_prompt_build({messages:[{role:'user',content:'星港'}]}, {...commandCtx,
 inputProvenance:{kind:'external_user'},runId:'rp-1'});
assert.ok(rp.prependContext.includes('月塔'));
const blocks=await hooks.before_prompt_build({messages:[{role:'user',content:[{type:'text',text:'月塔的失落地图'}]}]},
  {...commandCtx,inputProvenance:{kind:'external_user'},runId:'rp-blocks'});
assert.ok(blocks.prependContext.includes('月塔的失落地图'));
assert.ok(!rp.prependContext.includes('CURRENT_STATE_JSON'));
const denied=await commands.rp.handler({...commandCtx,agentId:'other',args:'exit'});
assert.ok(denied.text.includes('Different'));
const ended=await commands.rp.handler({...commandCtx,args:'exit'});
assert.ok(ended.text.includes('恢复'));
console.log('OpenClaw bridge contract probe passed');
''', encoding='utf-8')
        result = subprocess.run(['node', str(script), str(bridge), str(self.host), str(ROOT/'examples/roleplay/starmap.card.json')], capture_output=True, text=True, encoding='utf-8', timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = read(self.root / 'instances' / self.key / 'observed.json')
        self.assertIn('last_owner_hook_at', observed)

    def test_invalid_upgrade_cannot_replace_working_runtime(self):
        self.install()
        before = (self.root / 'registry.json').read_bytes()
        bad = self.base / 'broken new package'
        shutil.copytree(ROOT, bad, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        (bad / 'runtime/life_engine/cli.py').write_text('this is not valid python\n')
        with self.assertRaisesRegex(ValueError, 'import check'):
            upgrade(self.root, bad)
        self.assertEqual(before, (self.root / 'registry.json').read_bytes())
        self.command('status')

    def test_code_rollback_keeps_new_memories(self):
        from life_engine.durable import rollback_code
        first = self.install()['release']
        new = self.base / 'patch package'
        shutil.copytree(ROOT, new, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        init = new / 'runtime/life_engine/__init__.py'
        init.write_text(init.read_text() + '\n# another runtime generation\n')
        upgrade(self.root, new)
        self.command('remember', '--summary=Written on newer code')
        rollback_code(self.root, first)
        self.assertIn('Written on newer code', json.dumps(self.command('status')))

    def test_openclaw_photo_outbox_does_not_expose_other_files(self):
        from life_engine.durable import publish_photo
        self.cfg['integration']['adapter'] = 'openclaw'
        self.install(host_agent_id='main')
        _, inst, data = self.active()
        photo = data / 'agents/same_name/photos/generated.png'
        photo.parent.mkdir()
        photo.write_bytes(b'PNG-file')
        published = publish_photo(inst, data, {'status': 'ready', 'path': str(photo)})
        self.assertTrue(Path(published['path']).is_relative_to(self.host))
        self.assertEqual(Path(published['path']).read_bytes(), b'PNG-file')
        with self.assertRaises(ValueError):
            publish_photo(inst, data, {'status': 'ready', 'path': str(self.host / 'SOUL.md')})
        Path(published['path']).write_bytes(b'existing unrelated content')
        with self.assertRaisesRegex(ValueError, 'collision'):
            publish_photo(inst, data, {'status': 'ready', 'path': str(photo)})

    def test_backup_restore_preserves_reference_to_actual_photo(self):
        self.install()
        reg, inst, data = self.active()
        photo = data / 'agents/same_name/photos/real.png'
        photo.parent.mkdir()
        photo.write_bytes(b'photo bytes')
        with contextlib.closing(sqlite3.connect(data / 'agents/same_name/life.db')) as db, db:
            db.execute("INSERT INTO photos(id,day,at,status,path) VALUES('p1','2026-09-13',0,'ready',?)", (str(photo),))
        with locked(self.root, self.key):
            saved = snapshot(self.root, reg, inst)
        restored = restore(self.root, self.key, saved)
        with contextlib.closing(sqlite3.connect(Path(restored['active_data']) / 'agents/same_name/life.db')) as db, db:
            newpath = Path(db.execute("SELECT path FROM photos WHERE id='p1'").fetchone()[0])
            self.assertNotEqual(newpath, photo)
            self.assertEqual(newpath.read_bytes(), b'photo bytes')
