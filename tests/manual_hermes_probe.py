"""Opt-in real Hermes integration probe, isolated Life Engine and session data.

Run with the installed Hermes Python. --llm uses that profile's configured provider.
Never enable a plugin in persisted config, send channel messages, or modify SOUL.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--hermes-source', type=Path, required=True)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--llm', action='store_true')
    args=p.parse_args()
    os.environ['HERMES_HOME']=str(args.profile.resolve())
    sys.path.insert(0,str(args.hermes_source))
    sys.path.insert(0,str(ROOT/'runtime'))
    from life_engine.config import defaults
    from life_engine.durable import create_install, registry, state_home
    from hermes_cli.plugins import get_plugin_manager
    from hermes_cli.plugins_manifest import parse_manifest_file
    from hermes_cli.lifecycle import invoke_hook
    from hermes_constants import set_hermes_home_override, reset_hermes_home_override
    home_token=set_hermes_home_override(args.profile.resolve())
    protected=[args.profile/'SOUL.md',args.profile/'config.yaml']
    before={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in protected if f.exists()}
    transcript=[]
    def add(step,result):
        transcript.append({'step':step,'result':result})
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps({'in_progress':True,'transcript':transcript},ensure_ascii=False,indent=2),encoding='utf-8')
        print(step,flush=True)
    with tempfile.TemporaryDirectory(prefix='life-engine-real-hermes-') as temp:
        base=Path(temp)
        cfg=defaults('rp_probe','')
        cfg['integration'].update(adapter='hermes',host_home=str(args.profile.resolve()))
        installed=create_install(ROOT,base/'engine',cfg)
        installed['tool_name']=registry(base/'engine')['instances'][installed['instance']]['tool_name']
        folder=base/'engine/bridges'/installed['instance']/'hermes'
        manager=get_plugin_manager()
        manager.discover_and_load()
        if 'rp' in manager._plugin_commands:
            raise RuntimeError('Existing /rp command; do not replace it during a probe')
        manifest=parse_manifest_file(folder/'plugin.yaml',folder,'user','')
        manager._load_plugin(manifest)
        loaded=manager._plugins[installed['plugin_id']]
        if loaded.error:
            raise RuntimeError(loaded.error)
        command=manager._plugin_commands['rp']['handler']
        add('real_plugin_registered',{'tool':installed['tool_name'],'command':'/rp'})
        add('import',command('import "'+str(ROOT/'examples/roleplay/starmap.card.json')+'"'))
        add('enter',command('enter 星澜'))
        state=json.loads(command('status')); assert state['mode']=='roleplay'
        context=invoke_hook('pre_llm_call',platform='cli',user_message='星港',turn_id='probe-hook-1',session_id='probe')
        own=[c for c in context if isinstance(c,dict) and '【扮演规则】' in c.get('context','')]
        assert len(own)==1 and '月塔' in own[0]['context']
        add('real_hook_lore',{'activated':'月塔','soul_life_state_injected':'CURRENT_STATE_JSON' in own[0]['context']})
        invoke_hook('post_llm_call',turn_id='probe-hook-1',assistant_response='我和用户修复了地图。')
        add('exit',command('exit'))
        assert json.loads(command('status'))['mode']=='soul'
        if args.llm:
            from hermes_cli.env_loader import load_hermes_dotenv
            load_hermes_dotenv()
            from hermes_cli.config import load_config
            from hermes_cli.runtime_provider import resolve_runtime_provider
            from hermes_state import SessionDB
            from run_agent import AIAgent
            config=load_config(); model_cfg=config.get('model',{})
            model=model_cfg.get('default') if isinstance(model_cfg,dict) else model_cfg
            runtime=resolve_runtime_provider(target_model=model)
            session_db=SessionDB(base/'hermes-session.db')
            def tool_done(call_id,name,params,result):
                if name==installed['tool_name']:
                    add('engine_tool',{'params':params,'result':result})
            agent=AIAgent(model=model,provider=runtime.get('provider'),api_mode=runtime.get('api_mode'),
                          api_key=runtime.get('api_key'),base_url=runtime.get('base_url'),
                          max_iterations=4,run_budget_seconds=90,enabled_toolsets=[installed['plugin_id']],
                          quiet_mode=True,skip_context_files=True,load_soul_identity=True,
                          skip_memory=True,skip_background_review=True,session_db=session_db,platform='cli',
                          tool_complete_callback=tool_done)
            prompt=agent._build_system_prompt()
            soul_first_line=(args.profile/'SOUL.md').read_text(encoding='utf-8').splitlines()[0]
            assert soul_first_line in prompt, 'Selected profile SOUL was not loaded'
            add('identity_load_check',{'profile_soul_loaded': True,
                                       'provider':runtime.get('provider'), 'model':model})
            history=None
            for step,query in [('identity','你现在是谁？请区分你的原有身份和扮演角色，简短回答。'),
                               ('lore','请以星澜的口吻告诉我，星港的月塔里有什么？并用 remember 记录一句剧情摘要，传入当前 session_id。'),
                               ('exit_identity','退出角色'),
                               ('soul_identity','你现在是谁，还在扮演吗？简短回答。')]:
                if step=='identity':
                    add('llm_enter',command('enter 星澜'))
                response=agent.run_conversation(query,conversation_history=history)
                final=response.get('final_response','')
                add(step,final)
                if not final or response.get('error'):
                    raise RuntimeError('Hermes model turn failed; inspect private runtime output')
                history=response.get('messages',history)
                if step=='lore':
                    from life_engine.store import Store
                    reg=registry(base/'engine'); inst=reg['instances'][installed['instance']]
                    store=Store(state_home(base/'engine',inst)/'agents/rp_probe/life.db','rp_probe')
                    with store.tx() as db:
                        saved=db.execute("SELECT summary,scope,card_id,session_id FROM memories "
                                         "WHERE scope='persona' AND kind!='session_summary' ORDER BY id DESC LIMIT 1").fetchone()
                        assert saved is not None, 'Model failed to write persona memory'
                        add('llm_memory_verified',dict(saved))
            add('llm_final_state',json.loads(command('status')))
            assert json.loads(command('status'))['mode']=='soul'
            session_db.close()
        manager.unload(installed['plugin_id'])
    reset_hermes_home_override(home_token)
    after={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in protected if f.exists()}
    assert before==after, 'Protected profile files changed'
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps({'profile_files_unchanged':True,'live_gateway_verified':False,
                                  'llm_requested':args.llm,'transcript':transcript},ensure_ascii=False,indent=2),encoding='utf-8')
    print('PROBE_PASS',flush=True)


if __name__=='__main__': main()
