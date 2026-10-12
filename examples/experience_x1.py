"""X1 synthetic Soul-world trial. No Host, model, or network connection."""
import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))

from life_engine import durable
from life_engine.config import defaults
from life_engine.domain import (CanonStatus, DomainId, IdKind, Principal, Provenance,
    RealityStatus, Soul, SourceType, World, WorldKind, WorldScope, WorldStatus,
    WorldTimeline)
from life_engine.world_repository import WorldSnapshot
from life_engine.world_runtime import WorldRuntime
from life_engine.world_sqlite_repository import SQLiteWorldRepository
from life_engine.memory import (AudienceKind, IdempotencyIdentity, MemoryAudience,
    MemoryKind, OwnerMemoryContext, SessionMemoryContext)
from life_engine.memory_runtime import MemoryRuntime
from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
from life_engine.living_domain import LivingContext
from life_engine.living_policy import policy
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime
from life_engine.import_cards import parse_card

DAY0 = datetime(2026, 9, 28, 18, 30, tzinfo=timezone.utc)
INTERVIEW = '明天下午有个面试，我有点紧张。'


def output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def safe_sandbox(path):
    root = Path(tempfile.gettempdir()).resolve()
    target = Path(path).absolute()
    def linked(part):
        try:
            return part.is_symlink() or bool(getattr(part.lstat(), 'st_file_attributes', 0) & 0x400)
        except FileNotFoundError:
            return False
    # Reject links before resolving; Windows 8.3 aliases can then be compared
    # against the canonical temporary root without weakening containment.
    if any(linked(p) for p in (target, *target.parents)):
        raise ValueError('SANDBOX_PATH_REQUIRED: 路径必须是系统临时目录下的非链接子目录')
    target = target.resolve()
    if target == root or root not in target.parents:
        raise ValueError('SANDBOX_PATH_REQUIRED: 路径必须是系统临时目录下的非链接子目录')
    return target


def load(path):
    base = safe_sandbox(path)
    data = json.loads((base / 'x1.json').read_text(encoding='utf-8'))
    if data.get('marker') != 'LIFE_ENGINE_X1_SYNTHETIC_V1':
        raise ValueError('NOT_X1_SANDBOX')
    return base, data


def core(base, data, at):
    root = base / 'install'
    inst = durable.registry(root)['instances'][data['instance']]
    db = durable.state_home(root, inst) / 'agents/synthetic/life.db'
    world_repo = SQLiteWorldRepository(db)
    actor = Principal(DomainId.parse(data['principal']), DomainId.parse(data['owner']))
    scope = WorldScope(*(DomainId.parse(data[k]) for k in ('owner', 'soul', 'world', 'timeline')))
    world = WorldRuntime(world_repo)
    memory = MemoryRuntime(SQLiteMemoryRepository(root, data['instance'], runtime_id=world_repo.runtime_id))
    living_repo = LivingRepository(root, data['instance'], runtime_id=world_repo.runtime_id)
    living = LivingRuntime(living_repo, clock=lambda: at)
    return db, world, memory, living, actor, scope, LivingContext(actor, scope, living_repo.generation, 'x1-synthetic')


def init(path):
    base = safe_sandbox(path) if path else Path(tempfile.mkdtemp(prefix='life-engine-x1-')).resolve()
    if path:
        base.mkdir(parents=False, exist_ok=False)
    host = base / 'synthetic-host'
    host.mkdir()
    cfg = defaults('synthetic')
    cfg['integration'].update(adapter='hermes', host_home=str(host))
    result = durable.create_install(Path(__file__).resolve().parents[1], base / 'install', cfg)
    data = {'marker': 'LIFE_ENGINE_X1_SYNTHETIC_V1', 'instance': result['instance']}
    actor = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
    soul = Soul(DomainId.new(IdKind.SOUL), actor.owner_id, DomainId.new(IdKind.WORLD))
    scope = WorldScope(actor.owner_id, soul.soul_id, soul.soul_world_id, DomainId.new(IdKind.TIMELINE))
    data.update(principal=str(actor.principal_id), owner=str(actor.owner_id), soul=str(soul.soul_id),
                world=str(scope.world_id), timeline=str(scope.timeline_id))
    db, world, memory, living, _, _, ctx = core(base, data, DAY0)
    world.register_soul(actor, soul)
    provenance = Provenance(SourceType.OWNER_COMMAND, 'X1 合成世界', DAY0, actor,
                            RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
    with world.repository.transaction() as tx:
        tx.add_world(WorldSnapshot(World(scope.world_id, scope.owner_id, scope.soul_id,
            WorldKind.SOUL, provenance, WorldStatus.ACTIVE), WorldTimeline(scope, provenance)))
    routine = [dict(start=17*60, end=19*60, name='在书房读书', location='书房', category='HOME'),
               dict(start=19*60, end=20*60, name='散步', location='公园', category='PARK')]
    living.enroll(ctx, policy(quiet=[0, 0], routine=routine, contacts=[]), '合成目标', 'init-enroll')
    living.tick(ctx, 'init-tick')
    LivingRuntime(living.repository, clock=lambda: DAY0 + timedelta(hours=1)).tick(ctx, 'init-walk-tick')
    (base / 'x1.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    output({'status': 'SYNTHETIC_READY', 'sandbox': str(base), 'world': data['world'],
            'next': f'py -3.12 -X utf8 examples/experience_x1.py day0 --accept --sandbox "{base}"'})


def session(world, actor, scope):
    snapshot = world.snapshot(actor, scope.world_id)
    current = next((s for s in snapshot.sessions if s.status.value == 'open'), None)
    if current:
        snapshot = world.exit(actor, scope.world_id, scope.timeline_id, current.session_id,
                              snapshot.world.revision, snapshot.world.writer_epoch)
    opened = world.enter(actor, scope.world_id, scope.timeline_id, None,
                         snapshot.world.revision, snapshot.world.writer_epoch)
    binding = opened.sessions[-1]
    return SessionMemoryContext(actor, scope, binding.session_id, binding.writer_epoch,
                                MemoryAudience(AudienceKind.SOUL, scope.soul_id))


def facts(memory, context):
    result = memory.query(context)
    return [{'id': str(r.memory_id), 'content': r.content, 'source': r.provenance.source_id,
             'canon': r.provenance.canon_status.value, 'reality': r.provenance.reality_status.value,
             'scope': str(r.scope.world_id)} for r in result.records]


def activity_rows(db):
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(x) for x in conn.execute('''SELECT d.local_date,a.name,a.state,a.source,
            a.start,a.end,a.activated_at,a.ended_at,a.inferred,a.reason,
            l.name AS location,l.origin AS location_source
            FROM living_activities a JOIN living_days d ON a.day_id=d.id
            JOIN living_locations l ON a.location_id=l.id ORDER BY a.start''')]


def day1_tick(living, ctx):
    for index in range(20):
        result = living.tick(ctx, f'day1-tick-{index}')
        if result['result'] != 'RECOVERY_IN_PROGRESS':
            return
    raise ValueError('LIVING_RECOVERY_INCOMPLETE')


def hermes_prompt(db, memories, message, day):
    header = ('X1 合成体验试验。以下上下文由 Life Engine 本地样机手动复制，'
              '不是 Hermes 自动读取记忆，也不是真实 Host 验收。\n'
              '你扮演虚构 Agent S。虚拟活动不是现实中的亲身经历。'
              '只根据下列事实自然回应，不编造用户近况、共同历史或已发生的活动。'
              '若使用了列出的记忆且用户追问来源，说明这是用户此前在合成试验中说过的话。')
    if day == 0:
        return (header + '\n当前模拟时间：Day 0 傍晚。虚拟日常：在书房读书；稍后计划散步。'
                '\n这是一段新的 Hermes 测试会话。\n用户：' + INTERVIEW)
    lines = [header, '当前模拟时间：Day 1 傍晚。这是另一个新的 Hermes 测试会话。',
             '以下是本地 Core 按 Soul World 与当前会话检索的已接受记忆：']
    if memories:
        lines.extend(f'- {m["content"]}（来源：{m["source"]}；状态：{m["canon"]}；结果未知）'
                     for m in memories)
    else:
        lines.append('- 无可用的已接受记忆。')
    lines.append('虚拟日常（仅为合成时钟驱动的角色状态）：')
    for row in activity_rows(db):
        lines.append(f'- {row["local_date"]} {row["name"]}／{row["location"]}：'
                     f'{row["state"]}，来源 {row["source"]}，推断={bool(row["inferred"])}。'
                     'PLANNED 只能说计划，不能说做过。')
    lines.append('用户：' + message)
    return '\n'.join(lines)


def run_command(args):
    if args.command == 'init':
        return init(args.sandbox)
    if args.command == 'card-preview':
        ir = parse_card(args.card)
        profile = ir.profile.value()
        return output({'status': 'UNTRUSTED_SEED_PREVIEW_ONLY', 'fingerprint': ir.source_fingerprint,
                       'profile': profile, 'lore_entries': len(ir.lore.entries) if ir.lore else 0,
                       'warnings': ir.warnings, 'imported_to_world': False})
    base, data = load(args.sandbox)
    if args.command == 'reset':
        shutil.rmtree(base)
        return output({'status': 'SYNTHETIC_SANDBOX_REMOVED', 'sandbox': str(base)})
    at = DAY0 if args.command == 'day0' or (args.command == 'hermes-prompt' and args.day == 0) else DAY0 + timedelta(days=1)
    db, world, memory, living, actor, scope, ctx = core(base, data, at)
    if args.command == 'hermes-prompt':
        if args.day == 0:
            return print(hermes_prompt(db, [], INTERVIEW, 0))
        view = session(world, actor, scope)
        day1_tick(living, ctx)
        return print(hermes_prompt(db, facts(memory, view), args.message, 1))
    if args.command == 'day0':
        view = session(world, actor, scope)
        owner = OwnerMemoryContext(actor, scope)
        if args.accept and not data.get('day0_recorded'):
            provenance = Provenance(SourceType.USER_REPORT, 'X1 Day 0 用户原话（合成）', DAY0,
                actor, RealityStatus.USER_CLAIMED, CanonStatus.ACCEPTED)
            memory.create_owner_memory(owner, memory.collection_revision(owner),
                IdempotencyIdentity('x1-day0', 'interview'), content=INTERVIEW,
                kind=MemoryKind.EPISODIC, provenance=provenance,
                audience=(MemoryAudience(AudienceKind.SOUL, scope.soul_id),))
            data['day0_recorded'] = True
            (base / 'x1.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        return output({'session': str(view.session_id), 'input': INTERVIEW,
                       'acceptance': 'ACCEPTED' if args.accept else 'NOT_ACCEPTED',
                       'accepted_memory': facts(memory, view), 'model': 'MODEL_NOT_CONNECTED'})
    if args.command == 'day1':
        view = session(world, actor, scope)
        day1_tick(living, ctx)
        packet = {'session': str(view.session_id), 'input': args.message,
                  'memory': facts(memory, view), 'virtual_daily': activity_rows(db),
                  'world': str(scope.world_id), 'model': 'MODEL_NOT_CONNECTED'}
        return output(packet)
    if args.command == 'status':
        return output({'memory': facts(memory, OwnerMemoryContext(actor, scope)),
                       'virtual_daily': activity_rows(db), 'model': 'MODEL_NOT_CONNECTED'})
    if args.command == 'forget':
        owner = OwnerMemoryContext(actor, scope)
        records = memory.query(owner).records
        for record in records:
            memory.delete_memory(owner, record.memory_id, memory.collection_revision(owner),
                                 IdempotencyIdentity('x1-forget', str(record.memory_id)))
        return output({'status': 'FORGOTTEN', 'normal_query': facts(memory, owner)})
    if args.command == 'isolation-check':
        owner = OwnerMemoryContext(actor, scope)
        rp = world.create_roleplay_world(actor, scope.soul_id, at)
        other = OwnerMemoryContext(actor, rp.timeline.scope)
        provenance = Provenance(SourceType.USER_REPORT, 'X1 RP 合成密语', at, actor,
            RealityStatus.USER_CLAIMED, CanonStatus.ACCEPTED)
        memory.create_owner_memory(other, memory.collection_revision(other),
            IdempotencyIdentity('x1-rp', uuid4().hex), content='RP_ONLY_SECRET',
            kind=MemoryKind.EPISODIC, provenance=provenance,
            audience=(MemoryAudience(AudienceKind.WORLD),))
        visible = facts(memory, session(world, actor, scope))
        return output({'status': 'ISOLATED' if all('RP_ONLY_SECRET' not in r['content'] for r in visible)
                       else 'WORLD_LEAK', 'soul_memory': visible})


def main():
    parser = argparse.ArgumentParser(description='X1 合成记忆与虚拟日常本地试用')
    parser.add_argument('command', choices=['init', 'day0', 'day1', 'status', 'forget',
                                            'isolation-check', 'card-preview', 'reset', 'hermes-prompt'])
    parser.add_argument('--sandbox', help='系统临时目录下的 X1 实例路径')
    parser.add_argument('--message', default='今天总算结束了。')
    parser.add_argument('--day', type=int, choices=[0, 1], default=1,
                        help='hermes-prompt 使用的合成 Day 0 或 Day 1')
    parser.add_argument('--accept', action='store_true', help='显式接受 Day 0 合成原话为 Soul 记忆')
    parser.add_argument('--card', help='只读预览的角色卡文件')
    args = parser.parse_args()
    if args.command not in ('init', 'card-preview') and not args.sandbox:
        parser.error('此命令需要 --sandbox')
    if args.command == 'card-preview' and not args.card:
        parser.error('card-preview 需要 --card')
    try:
        run_command(args)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'{type(exc).__name__}: {exc}\n')


if __name__ == '__main__':
    main()
