# 本轮可复验探针与投影生成器

全部只用于新的临时合成对象，不启动Host/模型。代码引用本机冻结目录指针是执行时的路径定位；远端复验者应先从同Base和对应diff重建新临时快照，并将路径替换为自己的受控目录。不得把它改指生产目录。

## le64-reuse-probes.py

~~~~~~~~python
from pathlib import Path
import contextlib,hashlib,json,subprocess,sys,tempfile
snapshot=Path(Path(tempfile.gettempdir(),'le64-review-path.txt').read_text(encoding='utf8'))
sys.path[:0]=[str(snapshot/'runtime'),str(snapshot/'integrations/hermes_memory')]
from recall_service import RecallService
from life_engine.domain import CanonStatus
results=[]
def close(s):
    if getattr(s,'_ready',False):
        s._memory.repository.close();s._world.repository.close()
with tempfile.TemporaryDirectory(prefix='le64-boundary-synthetic-') as temp:
    base=Path(temp)
    a=RecallService(snapshot/'runtime',base/'store',base/'a'/'same','合成甲')
    before=(base/'store').exists();ok=a.available()
    results.append({'id':'P01_AVAILABLE_INITIALIZES','available':ok,'before_root_exists':before,'after_state_exists':(base/'store/state.json').is_file()})
    scope=a._rp_owner.scope
    a.remember_turn('assistant','合成模型输出只供审查')
    raw=a._memory.query(a._rp_owner).records
    results.append({'id':'P02_MODEL_TURN_CANON','source':raw[0].provenance.source_type.value,'canon':raw[0].provenance.canon_status.value,'reality':raw[0].provenance.reality_status.value})
    receipt=a.flush_recall()
    results.append({'id':'P03_DEFAULT_FLUSH_ACCEPTS','canon':a._memory.get_memory(a._soul_owner,receipt.memory_id).provenance.canon_status.value})
    close(a)
    b=RecallService(snapshot/'runtime',base/'store',base/'b'/'same','合成乙');b.ensure()
    results.append({'id':'P04_BASENAME_ALIAS','same_rp_scope':b._rp_owner.scope==scope,'two_profile_paths_different':a.profile_home!=b.profile_home})
    # 直接调用现存迁移函数，所有输入/输出都在本次新建合成store。
    old=dict(b._state);old['version']=999;old['future_synthetic_field']='sentinel'
    migrated=b._migrate(old)
    results.append({'id':'P05_UNKNOWN_VERSION_REWRITTEN','input_version':999,'output_version':migrated['version'],'future_field_retained':'future_synthetic_field' in migrated})
    close(b)
out={'scope':'LOCAL_SYNTHETIC_ONLY','snapshot_manifest_sha256':hashlib.sha256((snapshot/'manifest.json').read_bytes()).hexdigest(),'probes':results,'real_model_requests':0,'real_host_access':False}
(snapshot/'reuse-probes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(out,ensure_ascii=False,indent=2))

~~~~~~~~

## le64-project-core.py

~~~~~~~~python
from pathlib import Path
import ast,difflib,hashlib,json,shutil,tempfile
snapshot=Path(Path(tempfile.gettempdir(),'le64-review-path.txt').read_text(encoding='utf8'))
base=Path(r'C:\Users\hechao\.codex\worktrees\le-reset-01-audit\life-engine')
target=snapshot/'core-projection'
target.mkdir()
for folder in ['runtime','tests']:
    shutil.copytree(base/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__'))
for name in ['life.py','setup.py','setup_legacy.py']:
    shutil.copyfile(base/name,target/name)
candidate=(snapshot/'runtime/life_engine/memory_runtime.py').read_text(encoding='utf8')
original=(base/'runtime/life_engine/memory_runtime.py').read_text(encoding='utf8')
def node_source(source,name,method=False):
    tree=ast.parse(source)
    nodes=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MemoryRuntime').body if method else tree.body
    node=next(n for n in nodes if isinstance(n,ast.FunctionDef) and n.name==name)
    start=min([node.lineno]+[d.lineno for d in node.decorator_list]);lines=source.splitlines(keepends=True)
    return ''.join(lines[start-1:node.end_lineno])
projected=original.replace(node_source(original,'validate_record'),node_source(candidate,'validate_record'))
added='\n\n'+node_source(candidate,'recall_source_identity')+'\n\n'+node_source(candidate,'validate_recall_write')+'\n\n'
projected=projected.replace('\ndef available(',added+'\ndef available(',1)
projected=projected.replace('    def _create(',node_source(candidate,'create_roleplay_recall',True)+'\n\n    def _create(',1)
projected=projected.replace('            validate_record(tx,record)\n','            validate_record(tx,record)\n            validate_recall_write(tx,record,old)\n',1)
projected=projected.replace('from .world_repository import WorldRuntimeError','from .world_repository import FailureCode as WC, WorldRuntimeError',1)
ast.parse(projected)
(target/'runtime/life_engine/memory_runtime.py').write_text(projected,encoding='utf8')
for name in ['domain.py','roleplay_recall.py']:
    shutil.copyfile(snapshot/'runtime/life_engine'/name,target/'runtime/life_engine'/name)
shutil.copyfile(snapshot/'tests/test_roleplay_recall.py',target/'tests/test_roleplay_recall.py')
patch=[];rows=[]
for rel in ['runtime/life_engine/domain.py','runtime/life_engine/memory_runtime.py','runtime/life_engine/roleplay_recall.py']:
    old=(base/rel).read_text(encoding='utf8').splitlines(keepends=True) if (base/rel).exists() else []
    new=(target/rel).read_text(encoding='utf8').splitlines(keepends=True)
    patch.extend(difflib.unified_diff(old,new,fromfile='a/'+rel if old else '/dev/null',tofile='b/'+rel))
    rows.append({'path':rel,'sha256':hashlib.sha256((target/rel).read_bytes()).hexdigest()})
(snapshot/'core-projection.diff').write_text(''.join(patch),encoding='utf8')
(snapshot/'core-projection.json').write_text(json.dumps({'scope':'TEMPORARY_REUSE_PROJECTION_NOT_PRODUCT_IMPLEMENTATION','files':rows},indent=2),encoding='utf8')
print(target)

~~~~~~~~

## le64-core-path-proof.py

~~~~~~~~python
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile
s=Path(Path(tempfile.gettempdir(),'le64-review-path.txt').read_text(encoding='utf8'))
p=s/'core-projection';sys.path[:0]=[str(p/'runtime'),str(p/'tests')]
from test_roleplay_recall import RoleplayRecallTests
from life_engine.domain import CanonStatus
from life_engine.memory import IdempotencyIdentity,MemoryKind
from life_engine import roleplay_recall as recall
t=RoleplayRecallTests('test_recall_is_candidate_until_accepted');t.setUp()
try:
    user=t.create('x2-path-user',content='合成蓝灯书店找到地图')
    model=t.memory.create_session_candidate(t.session,t.memory.collection_revision(t.owner),
        IdempotencyIdentity('x2-path-model','turn-1'),content='合成回应：地图放在窗边',
        kind=MemoryKind.EPISODIC,provenance=t.provenance('x2-path-model',session=True))
    raw=t.memory.get_memory(t.owner,model.memory_id,history=True)
    source=t.source(highlights=('合成蓝灯书店找到地图','合成回应：地图放在窗边'))
    candidate=recall.record_recall(t.memory,t.soul_owner,source,identity=IdempotencyIdentity('x2-path','batch-1'))
    before=t.soul_contents()
    accepted=t.memory.accept_memory(t.soul_owner,candidate.memory_id,t.memory.collection_revision(t.soul_owner),IdempotencyIdentity('x2-path','batch-1-accept'))
    data={'install':str(t.root),'instance':t.key,'db':str(t.path),'actor':str(t.actor.principal_id),'scope':[str(getattr(t.soul_scope,k+'_id')) for k in ('owner','soul','world','timeline')]}
    meta=s/'path-proof-meta.json';meta.write_text(json.dumps(data),encoding='utf8')
    t.repo.close();t.world_repo.close()
    child=r'''
import json,sys
from pathlib import Path
sys.path[:0]=[sys.argv[1]]
from life_engine.domain import DomainId,Principal,WorldScope
from life_engine.world_runtime import WorldRuntime
from life_engine.world_sqlite_repository import SQLiteWorldRepository
from life_engine.memory_runtime import MemoryRuntime
from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
from life_engine.memory import AudienceKind,MemoryAudience,SessionMemoryContext
d=json.loads(Path(sys.argv[2]).read_text(encoding='utf8'));scope=WorldScope(*(DomainId.parse(v) for v in d['scope']));actor=Principal(DomainId.parse(d['actor']),scope.owner_id)
repo=SQLiteWorldRepository(d['db']);w=WorldRuntime(repo);m=MemoryRuntime(SQLiteMemoryRepository(d['install'],d['instance'],runtime_id=repo.runtime_id))
state=w.snapshot(actor,scope.world_id);opened=w.enter(actor,scope.world_id,scope.timeline_id,None,state.world.revision,state.world.writer_epoch);b=opened.sessions[-1]
view=SessionMemoryContext(actor,scope,b.session_id,b.writer_epoch,MemoryAudience(AudienceKind.SOUL,scope.soul_id));records=m.query(view).records
print(json.dumps({'count':len(records),'reality':[r.provenance.reality_status.value for r in records],'source':[r.provenance.source_type.value for r in records],'expected_anchor_found':all('合成蓝灯书店' in r.content for r in records)},ensure_ascii=False))
m.repository.close();repo.close()
'''
    process=subprocess.run([sys.executable,'-B','-X','utf8','-c',child,str(p/'runtime'),str(meta)],capture_output=True,text=True,encoding='utf8')
    result={'scope':'TEMP_CORE_PROJECTION_ONLY','model_turn_canon':raw.provenance.canon_status.value,'soul_before_accept_count':len(before),'accept_created_successor':accepted.memory_id!=candidate.memory_id,'new_process_exit':process.returncode,'new_process':json.loads(process.stdout) if process.returncode==0 else {'error':'FAILED'},'real_model_requests':0,'web_layer':'NOT_IMPLEMENTED'}
    assert raw.provenance.canon_status is CanonStatus.CANDIDATE and not before and process.returncode==0,result
    assert result['new_process']['count']==1 and result['new_process']['expected_anchor_found'],result
    (s/'core-path-proof.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
finally:
    t.doCleanups()

~~~~~~~~

## 临时投影92项命令

~~~~~~~~python
import sys, unittest
from pathlib import Path
sys.path[:0] = [str(Path.cwd()/"runtime"), str(Path.cwd()/"tests")]
from test_roleplay_recall import RoleplayRecallTests
loader = unittest.TestLoader()
suite = unittest.TestSuite([loader.loadTestsFromTestCase(RoleplayRecallTests)])
for name in ["test_memory_runtime", "test_memory_restore", "test_bridge_runtime", "test_prompt_runtime"]:
    suite.addTests(loader.loadTestsFromName(name))
result = unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(not result.wasSuccessful())
~~~~~~~~

## le64-initializer-proof.py

~~~~~~~~python
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile
from unittest.mock import patch
s=Path(Path(tempfile.gettempdir(),'le64-review-path.txt').read_text(encoding='utf8'));p=s/'core-projection';sys.path.insert(0,str(p/'runtime'))
from life_engine import durable
from life_engine.config import defaults
original_run=subprocess.run
script=next(v for v in durable.probe_release.__code__.co_consts if type(v) is str and 'SchemaMismatch' in v)
prefix=Path(getattr(sys,'_base_executable',sys.executable)).resolve()
results=[];invocations=[]
with tempfile.TemporaryDirectory(prefix='le64-initializer-synthetic-') as temp:
    b=Path(temp);host=b/'synthetic-host';host.mkdir();install=b/'install'
    def guarded_run(argv,**kw):
        if (not isinstance(argv,list) or len(argv)!=5 or Path(argv[0]).resolve()!=prefix or argv[1]!='-c' or argv[2]!=script or argv[4]!='8'):
            raise ValueError('INITIALIZER_PROBE_DENIED')
        path=Path(argv[3]).resolve()
        if not path.is_relative_to(install/'releases') or path.name!='runtime':raise ValueError('INITIALIZER_TARGET_DENIED')
        if kw!={'capture_output':True,'text':True,'encoding':'utf-8','timeout':20,'shell':False}:raise ValueError('INITIALIZER_OPTIONS_DENIED')
        guard='import sys\ndef deny(event,args):\n if event.startswith("socket.") or event in ("subprocess.Popen","os.system","os.posix_spawn","os.exec","os.fork"): raise RuntimeError("PROBE_EXTERNAL_DENIED")\nsys.addaudithook(deny)\n'
        verify='\nimport json,os,life_engine.memory_runtime\nprint(json.dumps({"isolated":sys.flags.isolated,"no_site":sys.flags.no_site,"module":life_engine.memory_runtime.__file__,"home_in_env":"HOME" in os.environ,"profile_in_env":"USERPROFILE" in os.environ,"host_sdk_imported":any(n=="agent" or n.startswith("hermes") for n in sys.modules)}))'
        env={k:os.environ[k] for k in ('SYSTEMROOT','WINDIR','TEMP','TMP') if k in os.environ}
        cmd=[str(prefix),'-I','-S','-B','-X','utf8','-c',guard+script+verify,str(path),'8']
        done=original_run(cmd,env=env,**kw);invocations.append({'returncode':done.returncode,'observed':json.loads(done.stdout) if done.returncode==0 else None})
        return done
    cfg=defaults('synthetic');cfg['integration'].update(adapter='hermes',host_home=str(host))
    with patch.object(durable.subprocess,'run',guarded_run):created=durable.create_install(p,install,cfg)
    assert len(invocations)==1 and invocations[0]['returncode']==0
    observation=invocations[0]['observed'];assert observation['isolated']==1 and observation['no_site']==1 and not observation['home_in_env'] and not observation['profile_in_env'] and not observation['host_sdk_imported']
    valid=[str(prefix),'-c',script,str(Path(created['root'])/'releases'/created['release']/'runtime'),'8']
    for ident,change in [('wrong_script',{2:'print("unapproved")'}),('wrong_schema',{4:'9'}),('wrong_python',{0:str(b/'unknown-python')})]:
        argv=list(valid)
        for key,value in change.items():argv[key]=value
        try:guarded_run(argv,capture_output=True,text=True,encoding='utf-8',timeout=20,shell=False)
        except ValueError:results.append({'id':ident,'denied':True})
        else:raise AssertionError(ident)
    result={'scope':'TEMP_CORE_INITIALIZER_PROBE_ONLY','real_child_count':len(invocations),'child':{k:v for k,v in observation.items() if k!='module'},'module_inside_release':Path(observation['module']).is_relative_to(install/'releases'),'host_plugins_created':(host/'plugins').exists(),'bridge_reference_inside_fixture':(install/'bridges'/created['instance']).is_dir(),'negative_checks':results,'original_probe_body_sha256':hashlib.sha256(script.encode()).hexdigest(),'web_layer':'NOT_IMPLEMENTED','real_model_requests':0}
    (s/'initializer-proof.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))

~~~~~~~~
