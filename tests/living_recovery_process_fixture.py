"""独立进程的 synthetic recovery-only 调用；不创建 incarnation 或执行 mutation。"""
from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'runtime'))
from life_engine.domain import DomainId, Principal, WorldScope
from life_engine.living_recovery import LivingRecoveryContext, RecoveryDelegation, OperationRecoveryRequest
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime

if __name__ == '__main__':
    c = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    scope = WorldScope(*map(DomainId.parse, c['scope']))
    actor = Principal(DomainId.parse(c['actor']), scope.owner_id)
    reader = Principal(DomainId.parse(c['reader']), scope.owner_id)
    delegation = RecoveryDelegation(actor, reader, actor, scope, c['instance'], c['generation'],
                                    'test', 'synthetic trusted local deployment')
    context = LivingRecoveryContext(reader, delegation)
    request = OperationRecoveryRequest(c['instance'], c['generation'], scope, 'test',
                                       c['operation'], 'begin_attempt', c['digest'])
    repo = LivingRepository(c['root'], c['instance'], runtime_id=c['runtime_id'])
    runtime = LivingRuntime(repo, clock=lambda: datetime.fromisoformat(c['now']))
    print(runtime.query_operation_recovery(context, request).to_json())
