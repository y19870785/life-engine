"""独立进程执行与 crash 注入，只用于合成验收。"""
import json
import os
from pathlib import Path
import sys
from datetime import datetime

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
from life_engine.domain import DomainId, Principal, WorldScope
from life_engine.living_domain import LivingContext
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime
from life_engine.world_sqlite_repository import SQLiteWorldRepository


if __name__=='__main__':
    config=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    mode=sys.argv[2]
    rid=config['runtime_id']
    if mode=='restart':
        rid=SQLiteWorldRepository(Path(config['path'])).runtime_id
    repo=LivingRepository(config['root'],config['instance'],runtime_id=rid)
    principal=Principal(DomainId.parse(config['principal']),DomainId.parse(config['scope'][0]))
    scope=WorldScope(*map(DomainId.parse,config['scope']))
    ctx=LivingContext(principal,scope,repo.generation,'child')
    runtime=LivingRuntime(repo,clock=lambda:datetime.fromisoformat(config['now']))
    if mode=='scope':
        from dataclasses import replace
        from life_engine.domain import WorldStatus
        world=SQLiteWorldRepository(Path(config['path']),runtime_id=rid)
        with world.transaction() as tx:
            current=tx.get_world(scope.world_id)
            tx.save_world(replace(current,world=replace(current.world,status=WorldStatus.SUSPENDED,revision=current.world.revision.next())),current.world.revision)
        print('{}');sys.exit(0)
    if mode=='before': os._exit(71)
    if mode=='inside':
        import life_engine.living_runtime as module
        def crash(*args,**kwargs): os._exit(72)
        module.finish=crash
    result=runtime.tick(ctx,'child-'+sys.argv[3])
    if mode=='after': os._exit(73)
    if mode in ('claimed','sent'):
        ident=config['intent']
        result=runtime.begin_attempt(ctx,result['revision'],'attempt-'+sys.argv[3],ident)
        if mode=='sent': Path(config['send_file']).write_text(json.dumps(result),encoding='utf-8')
        os._exit(74)
    print(json.dumps(result))
