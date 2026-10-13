import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine import hermes_card_runtime as rt, hermes_card_import as ci
from test_import_cards import card


def source():
    value = card()
    value['data'].update(name='洛宁', description='{{char}}是月港的灯塔看守。',
        personality='寡言，喜欢旧地图。', scenario='{{user}}是新来的邻居。',
        first_mes='灯刚亮。{{user}}，进来避雨吧。', alternate_greetings=['今天风很大。'],
        mes_example='<START>\n{{user}}: 忙吗？\n{{char}}: 刚换完灯。\n把湿外套挂起来。',
        system_prompt='{{original}}\n用简洁的第一人称说话。',
        post_history_instructions='保持灯塔日常的氛围。', extensions={},
        character_book={'scan_depth': 3, 'token_budget': 4096, 'entries':[
            {'keys':['月港'], 'content':'月港在岛的东侧。', 'enabled':True,
             'insertion_order':100, 'position':'before_char'},
            {'keys':[], 'content':'城里的钟慢五分钟。', 'constant':True,
             'insertion_order':200, 'position':'after_char'},
            {'keys':['地图'], 'content':'旧地图画着废弃的码头。',
             'extensions':{'position':4,'depth':1,'role':0}},
        ]})
    return value


def plan():
    value = rt.compile_plan(source(), 'source-hash')
    value['options']['acknowledged'] = [i['id'] for i in value['issues']]
    return value


class NativeCardTests(unittest.TestCase):
    def test_original_fields_layout_and_no_mutation(self):
        value = plan()
        request={'messages':[{'role':'system','content':'host authority'},
                 {'role':'user','content':'我带了月港地图。'}], 'temperature':0.7}
        before=copy.deepcopy((value,request))
        output,trace=rt.assemble(value,request)
        self.assertEqual((value,request),before)
        self.assertEqual(output['messages'][0],request['messages'][0])
        definition=output['messages'][1]['content']
        self.assertLess(definition.index('月港在岛'),definition.index('洛宁是'))
        self.assertLess(definition.index('洛宁是'),definition.index('城里的钟'))
        self.assertIn("Write 洛宁's next reply",definition)
        self.assertEqual(output['messages'][2:4],[{'role':'user','content':'忙吗？'},
            {'role':'assistant','content':'刚换完灯。\n把湿外套挂起来。'}])
        self.assertEqual(output['messages'][-3]['content'],'旧地图画着废弃的码头。')
        self.assertEqual(output['messages'][-1]['content'],'保持灯塔日常的氛围。')
        self.assertEqual(set(trace['selected']),{0,1,2})
        self.assertEqual(output['temperature'],0.7)

    def test_history_scan_depth_and_case_and_optional_filters(self):
        value=plan(); row=value['entries'][0]
        row.update(keys=['Map'],secondary_keys=['east','port'],selective=True,case_sensitive=True)
        history=[{'role':'user','content':'Map east'}, {'role':'assistant','content':'好的'},
                 {'role':'user','content':'然后呢？'}]
        for logic,expected in [(0,True),(1,True),(2,False),(3,False)]:
            row['logic']=logic
            selected=rt.select_lore(value,history)[0]
            self.assertEqual(any(r['id']==0 for r in selected),expected)
        row['logic']=0; row['scan_depth']=1
        self.assertNotIn(0,[r['id'] for r in rt.select_lore(value,history)[0]])
        row['scan_depth']=3; row['keys']=['map']
        self.assertNotIn(0,[r['id'] for r in rt.select_lore(value,history)[0]])
        row['case_sensitive']=False
        self.assertIn(0,[r['id'] for r in rt.select_lore(value,history)[0]])

    def test_budget_order_whole_entry_and_disabled_source(self):
        value=source(); entries=value['data']['character_book']['entries']
        entries[0]['disable']=True
        compiled=rt.compile_plan(value,'x')
        self.assertFalse(compiled['entries'][0]['enabled'])
        compiled['options']['lore_budget']=1
        chosen,dropped,used=rt.select_lore(compiled,[{'role':'user','content':'月港地图'}])
        self.assertEqual(chosen,[]); self.assertEqual(used,0)
        self.assertEqual(set(dropped),{1,2})

    def test_compatibility_requires_ack_and_unsupported_entry_exclusion(self):
        value=source(); value['data']['extensions']={'world':'external-book'}
        value['data']['character_book']['entries'][0]['extensions']={'position':7}
        compiled=rt.compile_plan(value,'x')
        self.assertEqual(compiled['review_only']['original'],value)
        with self.assertRaisesRegex(ValueError,'COMPATIBILITY_REVIEW'):
            rt.validate(compiled)
        compiled['options']['acknowledged']=[i['id'] for i in compiled['issues']]
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_ENTRY'):
            rt.validate(compiled)
        compiled['entries'][0]['enabled']=False
        rt.validate(compiled)

    def test_retry_and_restore_dont_duplicate_request_or_modify_history(self):
        value=plan(); request={'messages':[{'role':'user','content':'早上好'},
            {'role':'assistant','content':'刚到灯塔'}, {'role':'user','content':'后来呢？'}]}
        first,_=rt.assemble(value,request)
        second,trace=rt.assemble(value,first)
        resumed,_=rt.assemble(value,copy.deepcopy(request))
        self.assertEqual(first,second); self.assertEqual(first,resumed)
        self.assertTrue(trace['already_composed'])
        self.assertEqual(len(request['messages']),3)

    def test_depth_does_not_split_tool_results(self):
        value=plan(); value['entries'][2].update(constant=True,depth=1)
        history=[{'role':'assistant','content':None,'tool_calls':[{'id':'call1','type':'function',
                  'function':{'name':'memory','arguments':'{}'}}]},
                 {'role':'tool','tool_call_id':'call1','content':'saved'}]
        result,_=rt.assemble(value,{'messages':history})
        messages=result['messages']
        at=next(i for i,m in enumerate(messages) if m.get('tool_calls'))
        self.assertEqual(messages[at+1],history[1])

    def test_preserves_in_history_host_messages_and_reports_probability(self):
        history=[{'role':'user','content':'hello'}, {'role':'system','content':'host summary'},
                 {'role':'assistant','content':'reply'}, {'role':'user','content':'continue'}]
        result,_=rt.assemble(plan(),{'messages':history})
        at=result['messages'].index(history[0])
        self.assertEqual(result['messages'][at:at+4],history)
        raw=source(); raw['data']['character_book']['entries'][0]['probability']=50
        self.assertIn('SETTING_NOT_IMPLEMENTED:probability',rt.compile_plan(raw,'x')['entries'][0]['issues'])

    def test_tools_restricted_without_changing_host_history(self):
        value=plan(); value['options']['allowed_tools']=['memory']
        req={'messages':[{'role':'system','content':'host'}], 'tools':[
             {'type':'function','function':{'name':'terminal'}},
             {'type':'function','function':{'name':'memory'}}],
             'tool_choice':{'type':'function','function':{'name':'terminal'}}}
        result,_=rt.assemble(value,req)
        self.assertEqual([t['function']['name'] for t in result['tools']],['memory'])
        self.assertEqual(result['tool_choice'],'auto')
        value['options']['allowed_tools']=[]
        result,_=rt.assemble(value,req)
        self.assertNotIn('tools',result); self.assertNotIn('tool_choice',result)

    def test_alternate_opening_and_no_recursive_macro_execution(self):
        value=plan(); value['options']['greeting_index']=1
        self.assertEqual(rt.opening(value),'今天风很大。')
        value['options']['user_name']='{{setvar::x::1}}'
        self.assertEqual(rt.expand('{{user}}',value['character'],value['options']),'{{setvar::x::1}}')
        with self.assertRaisesRegex(ValueError,'CHAT_COMPLETIONS'):
            rt.assemble(value,{'input':[]})

    def test_multi_card_content_is_not_reauthored(self):
        for name,description,scenario in [('伊岚','巡山的精灵。','玩家是同行的旅人。'),
            ('夏宁','喜欢画画的学生。','开学第一天。'),('周遥','深夜电台主持人。','节目刚刚结束。')]:
            raw=source(); raw['data'].update(name=name,description=description,scenario=scenario)
            value=rt.compile_plan(raw,'x')
            value['options']['acknowledged']=[i['id'] for i in value['issues']]
            result,_=rt.assemble(value,{'messages':[]})
            self.assertIn(description,result['messages'][0]['content'])
            self.assertIn(scenario,result['messages'][0]['content'])
            self.assertEqual(value['review_only']['original'],raw)

    def test_native_install_binding_failure_notice_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); home=root/'profiles/trial'; home.mkdir(parents=True)
            (home/'SOUL.md').write_text('old soul')
            src=root/'source.json'; src.write_bytes(ci.json_bytes(source()))
            target=root/'plan.json'; ci.preview(src,target,'native')
            value=json.loads(target.read_text(encoding='utf-8'))
            value['options']['acknowledged']=[i['id'] for i in value['issues']]
            target.write_bytes(ci.json_bytes(value))
            result=ci.apply(target,home,ci.digest(target.read_bytes()))
            folder=home/'plugins/life-engine-character-card'
            self.assertTrue(ci.verify(home,result['receipt'])['ok'])
            self.assertNotIn('review_only',json.loads((folder/'card.json').read_text(encoding='utf-8')))
            spec=importlib.util.spec_from_file_location('test_native_plugin',folder/'__init__.py',
                                                       submodule_search_locations=[str(folder)])
            module=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,{'test_native_plugin':module,
                    'hermes_constants':types.SimpleNamespace(get_hermes_home=lambda:home)}):
                spec.loader.exec_module(module)
                ctx=dict(session_id='s',turn_id='t',platform='cli')
                req={'messages':[{'role':'user','content':'月港'}]}
                self.assertIsNone(module.rewrite(request=req,**ctx))
                module.before(**ctx)
                self.assertEqual(module.rewrite(request=req,**ctx)['reason'],'COMPOSED')
                self.assertEqual(module.guard_tool(tool_name='terminal',**ctx)['action'],'block')
                module.before(**dict(ctx,parent_session_id='parent'))
                self.assertIsNone(module.rewrite(request=req,**ctx))
                self.assertIsNone(module.guard_tool(tool_name='terminal',**ctx))
                module.before(**ctx)
                (folder/'card.json').write_text('broken')
                response=module.rewrite(request=req,**ctx)
                self.assertEqual(response['reason'],'UNAVAILABLE')
            # Restore only after repairing the deliberate drift to the signed payload.
            value.pop('review_only'); (folder/'card.json').write_bytes(ci.json_bytes(value))
            ci.restore(home,result['receipt'])
            self.assertEqual((home/'SOUL.md').read_text(),'old soul')
            self.assertFalse((folder/'hermes_card_runtime.py').exists())


if __name__ == '__main__': unittest.main()
