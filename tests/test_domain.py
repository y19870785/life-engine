"""SP-004A pure contracts and acceptance demonstration, no production writes."""
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine.domain import (
    BindingStatus, CanonStatus, CharacterDefinition, CharacterInstance, DefinitionRef,
    DefinitionVersion, DomainError, DomainId, IdKind, Owner, Principal, Provenance,
    RealityStatus, Revision, Soul, SourceType, Values, WorldKind, WorldScope, WorldState,
    WorldStatus, WorldTimeline, WriterEpoch,
)
from life_engine.domain_lifecycle import (
    CloseReason, WorldCommand, WorldEvent, bind_session, close_session, create_world,
    transition_world, validate_write,
)
from life_engine.domain_policy import (
    BridgeDecision, BridgePolicy, BridgeRequest, Capability, HostCapabilities, Support, evaluate_bridge,
)


def new(kind):
    return DomainId.new(kind)


class DomainTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 16, tzinfo=timezone.utc)
        self.owner = Owner(new(IdKind.OWNER))
        self.actor = Principal(new(IdKind.PRINCIPAL), self.owner.owner_id)
        self.soul = Soul(new(IdKind.SOUL), self.owner.owner_id, new(IdKind.WORLD))
        self.provenance = Provenance(SourceType.OWNER_COMMAND, 'explicit-user-command', self.now,
                                     self.actor, RealityStatus.UNKNOWN)
        self.definition = CharacterDefinition(DefinitionRef(new(IdKind.DEFINITION), DefinitionVersion(1)),
                                              self.owner.owner_id, '同一个角色', Values(), self.provenance)
        self.a, self.ta, self.ca = self.make_world()
        self.b, self.tb, self.cb = self.make_world()

    def make_world(self, kind=WorldKind.ROLEPLAY):
        wid = self.soul.soul_world_id if kind is WorldKind.SOUL else new(IdKind.WORLD)
        world = create_world(self.soul, self.actor, wid, kind, self.provenance).world
        scope = WorldScope(self.owner.owner_id, self.soul.soul_id, wid, new(IdKind.TIMELINE))
        timeline = WorldTimeline(scope, self.provenance)
        character = CharacterInstance(new(IdKind.CHARACTER), scope, self.definition.reference, self.provenance)
        return world, timeline, character

    def move(self, world, command):
        return transition_world(world, command, self.actor, world.revision, world.writer_epoch).world

    def binding(self, world, timeline=None, character=None):
        return bind_session(world, timeline or self.ta, self.actor, new(IdKind.SESSION), character or self.ca)

    def test_acceptance_two_worlds_one_definition_and_reentry(self):
        soul_world, _, _ = self.make_world(WorldKind.SOUL)
        a = self.move(self.a, WorldCommand.ENTER)
        ca = replace(self.ca, state=Values((('location', '襄阳'),)), relationships=Values((('user', 'trusted'),)))
        cb = replace(self.cb, state=Values((('location', '古墓'),)), relationships=Values((('user', 'stranger'),)))
        ca.validate_definition(self.definition)
        cb.validate_definition(self.definition)
        self.assertEqual(ca.definition, cb.definition)
        self.assertNotEqual(ca.character_instance_id, cb.character_instance_id)
        self.assertNotEqual(ca.scope.world_id, cb.scope.world_id)
        self.assertNotEqual(ca.scope.timeline_id, cb.scope.timeline_id)
        self.assertNotEqual(ca.state, cb.state)
        self.assertNotEqual(ca.relationships, cb.relationships)
        self.assertEqual(soul_world.soul_id, a.soul_id)
        binding = self.binding(a, character=ca)
        exited, closed = close_session(a, binding, self.actor, a.revision)
        self.assertEqual(exited.status, WorldStatus.SUSPENDED)
        self.assertEqual(closed.status, BindingStatus.CLOSED)
        resumed = self.move(exited, WorldCommand.RESUME)
        rebound = self.binding(resumed, character=ca)
        self.assertEqual(rebound.scope, binding.scope)
        self.assertNotEqual(rebound.session_id, binding.session_id)
        self.assertEqual(resumed.world_id, a.world_id)
        validate_write(resumed, rebound, self.actor, ca, resumed.revision)
        self.assertEqual(ca.state.items, (('location', '襄阳'),))

    def test_ids_are_typed_random_and_roundtrip(self):
        ids = [new(k) for k in IdKind for _ in range(2)]
        self.assertEqual(len(ids), len(set(ids)))
        for identity in ids:
            self.assertEqual(DomainId.parse(str(identity)), identity)
        for invalid in ('星澜', '/home/user/.hermes', 'world:card.png', 'world:00000000-0000-0000-0000-000000000000'):
            with self.assertRaises(DomainError):
                DomainId.parse(invalid)
        with self.assertRaises(DomainError):
            Owner(new(IdKind.WORLD))

    def test_counter_types_reject_bool_negative_and_wrong_counter(self):
        for cls in (Revision, WriterEpoch, DefinitionVersion):
            for value in (True, -1, '1'):
                with self.assertRaises(DomainError):
                    cls(value)
        with self.assertRaises(DomainError):
            DefinitionVersion(0)
        with self.assertRaises(DomainError):
            replace(self.a, revision=WriterEpoch(1))

    def test_definition_version_is_pinned_and_values_immutable(self):
        v2 = replace(self.definition, reference=replace(self.definition.reference, version=DefinitionVersion(2)))
        self.assertEqual(self.ca.definition.version, DefinitionVersion(1))
        with self.assertRaises(DomainError):
            self.ca.validate_definition(v2)
        with self.assertRaises(FrozenInstanceError):
            self.definition.name = 'rewritten'
        with self.assertRaises(FrozenInstanceError):
            self.ca.state.items = (('x', 'y'),)
        for value in ([('x', 'y')], (('x', []),), (('x', '1'), ('x', '2'))):
            with self.assertRaises(DomainError):
                Values(value)

    def test_cross_world_and_timeline_reference_denied(self):
        a, b = self.move(self.a, WorldCommand.ENTER), self.move(self.b, WorldCommand.ENTER)
        binding = self.binding(a)
        for world, reference in ((a, self.cb), (b, self.ca),
                                 (a, replace(self.ca, scope=replace(self.ca.scope, timeline_id=new(IdKind.TIMELINE))))):
            with self.assertRaises(DomainError):
                validate_write(world, binding, self.actor, reference, world.revision)
        with self.assertRaises(DomainError):
            self.binding(a, self.tb, self.cb)

    def test_same_world_different_character_denied(self):
        a = self.move(self.a, WorldCommand.ENTER)
        other = replace(self.ca, character_instance_id=new(IdKind.CHARACTER))
        with self.assertRaises(DomainError):
            validate_write(a, self.binding(a), self.actor, other, a.revision)

    def test_owner_and_principal_mismatch_denied(self):
        a = self.move(self.a, WorldCommand.ENTER)
        binding = self.binding(a)
        for principal in (Principal(new(IdKind.PRINCIPAL), self.owner.owner_id),
                          Principal(new(IdKind.PRINCIPAL), new(IdKind.OWNER))):
            with self.assertRaises(DomainError):
                validate_write(a, binding, principal, self.ca, a.revision)
        with self.assertRaises(DomainError):
            replace(self.a, owner_id=new(IdKind.OWNER))

    def test_soul_is_world_but_has_distinct_policy(self):
        sw, timeline, _ = self.make_world(WorldKind.SOUL)
        self.assertIs(type(sw), type(self.a))
        sw = self.move(sw, WorldCommand.ENTER)
        binding = bind_session(sw, timeline, self.actor, new(IdKind.SESSION))
        live, closed = close_session(sw, binding, self.actor, sw.revision)
        self.assertEqual(live.status, WorldStatus.ACTIVE)
        self.assertEqual(closed.status, BindingStatus.CLOSED)
        for command in (WorldCommand.EXIT, WorldCommand.SUSPEND, WorldCommand.ARCHIVE, WorldCommand.DELETE):
            with self.assertRaises(DomainError):
                self.move(sw, command)
        with self.assertRaises(DomainError):
            create_world(self.soul, self.actor, self.soul.soul_world_id, WorldKind.ROLEPLAY, self.provenance)

    def test_lifecycle_and_event_are_separate(self):
        world = self.a
        for command, status, event in (
                (WorldCommand.ENTER, WorldStatus.ACTIVE, WorldEvent.ENTERED),
                (WorldCommand.SUSPEND, WorldStatus.SUSPENDED, WorldEvent.SUSPENDED),
                (WorldCommand.RESUME, WorldStatus.ACTIVE, WorldEvent.RESUMED),
                (WorldCommand.EXIT, WorldStatus.SUSPENDED, WorldEvent.EXITED),
                (WorldCommand.ARCHIVE, WorldStatus.ARCHIVED, WorldEvent.ARCHIVED),
                (WorldCommand.UNARCHIVE, WorldStatus.SUSPENDED, WorldEvent.UNARCHIVED),
                (WorldCommand.ARCHIVE, WorldStatus.ARCHIVED, WorldEvent.ARCHIVED),
                (WorldCommand.DELETE, WorldStatus.TOMBSTONED, WorldEvent.TOMBSTONED)):
            result = transition_world(world, command, self.actor, world.revision, world.writer_epoch)
            self.assertEqual(result.world.status, status)
            self.assertEqual(result.event, event)
            self.assertEqual(result.world.revision, world.revision.next())
            world = result.world
        for command in WorldCommand:
            with self.assertRaises(DomainError):
                self.move(world, command)

    def test_all_illegal_transition_pairs_rejected(self):
        allowed = {
            WorldStatus.CREATED: {WorldCommand.ENTER, WorldCommand.ARCHIVE},
            WorldStatus.ACTIVE: {WorldCommand.SUSPEND, WorldCommand.EXIT},
            WorldStatus.SUSPENDED: {WorldCommand.RESUME, WorldCommand.ARCHIVE},
            WorldStatus.ARCHIVED: {WorldCommand.UNARCHIVE, WorldCommand.DELETE},
            WorldStatus.TOMBSTONED: set(),
        }
        for status in WorldStatus:
            for command in set(WorldCommand) - allowed[status]:
                with self.subTest(status=status, command=command), self.assertRaises(DomainError):
                    self.move(replace(self.a, status=status), command)

    def test_old_epoch_rejected_after_exit_switch_suspend_resume(self):
        active = self.move(self.a, WorldCommand.ENTER)
        old = self.binding(active)
        suspended = self.move(active, WorldCommand.SUSPEND)
        exited, closed = close_session(active, old, self.actor, active.revision)
        switched, _ = close_session(active, old, self.actor, active.revision, CloseReason.SWITCH)
        for world in (suspended, exited, switched, self.move(suspended, WorldCommand.RESUME),
                      self.move(exited, WorldCommand.RESUME)):
            with self.assertRaises(DomainError):
                validate_write(world, old, self.actor, self.ca, world.revision)
        with self.assertRaises(DomainError):
            validate_write(active, closed, self.actor, self.ca, active.revision)

    def test_stale_revision_cannot_transition_or_write(self):
        active = self.move(self.a, WorldCommand.ENTER)
        with self.assertRaises(DomainError):
            transition_world(active, WorldCommand.EXIT, self.actor, Revision(0), active.writer_epoch)
        with self.assertRaises(DomainError):
            validate_write(active, self.binding(active), self.actor, self.ca, Revision(0))

    def test_scoped_world_state_reference(self):
        active = self.move(self.a, WorldCommand.ENTER)
        state = WorldState(self.ta.scope, active.revision, self.provenance)
        validate_write(active, self.binding(active), self.actor, state, active.revision)
        with self.assertRaises(DomainError):
            validate_write(active, self.binding(active), self.actor,
                           replace(state, scope=self.tb.scope), active.revision)
        invalid = replace(self.binding(active), character_instance_id=None)
        with self.assertRaises(DomainError):
            validate_write(active, invalid, self.actor, state, active.revision)
        with self.assertRaises(DomainError):
            close_session(active, invalid, self.actor, active.revision)

    def test_reality_is_not_canon(self):
        for reality in RealityStatus:
            source = SourceType.OBSERVATION if reality is RealityStatus.OBSERVED_REAL_WORLD_FACT else SourceType.MODEL
            p = replace(self.provenance, source_type=source, reality_status=reality)
            self.assertEqual(p.canon_status, CanonStatus.CANDIDATE)
            accepted = replace(p, canon_status=CanonStatus.ACCEPTED)
            self.assertEqual(accepted.reality_status, reality)
        self.assertNotEqual(RealityStatus.USER_CLAIMED, RealityStatus.OBSERVED_REAL_WORLD_FACT)
        self.assertNotEqual(RealityStatus.SIMULATED_LIFE_STATE, RealityStatus.OBSERVED_REAL_WORLD_FACT)
        self.assertNotEqual(RealityStatus.FICTIONAL_SHARED_EXPERIENCE, RealityStatus.OBSERVED_REAL_WORLD_FACT)

    def test_claim_and_model_cannot_declare_observed(self):
        for source in (SourceType.USER_REPORT, SourceType.MODEL, SourceType.SIMULATION):
            with self.assertRaises(DomainError):
                replace(self.provenance, source_type=source, reality_status=RealityStatus.OBSERVED_REAL_WORLD_FACT)

    def test_provenance_requires_trace_and_aware_time(self):
        for changes in ({'created_at': datetime(2026, 9, 16)}, {'source_id': ''},
                        {'source_timeline_id': self.ta.scope.timeline_id},
                        {'source_event_id': new(IdKind.EVENT)}):
            with self.assertRaises(DomainError):
                replace(self.provenance, **changes)
        p = replace(self.provenance, source_world_id=self.a.world_id,
                    source_timeline_id=self.ta.scope.timeline_id, source_session_id=new(IdKind.SESSION),
                    source_event_id=new(IdKind.EVENT))
        self.assertEqual(p.actor, self.actor)

    def bridge(self):
        request = BridgeRequest(self.actor, self.ta.scope, self.tb.scope,
                                frozenset({'city'}), 'user_report', 'roleplay_reaction', frozenset({'character'}))
        policy = BridgePolicy(new(IdKind.GRANT), self.actor, request.source, request.target, request.fields,
                              request.data_class, request.purpose, request.audience,
                              self.now + timedelta(hours=1), Revision(2))
        return request, policy

    def test_no_grant_denies_even_same_soul(self):
        request, _ = self.bridge()
        self.assertEqual(request.source.soul_id, request.target.soul_id)
        self.assertEqual(evaluate_bridge(None, request, current_grant_revision=None, now=self.now), BridgeDecision.DENY)

    def test_bridge_is_directional_and_field_purpose_audience_limited(self):
        request, policy = self.bridge()
        self.assertEqual(evaluate_bridge(policy, request, current_grant_revision=Revision(2), now=self.now), BridgeDecision.ALLOW)
        for changed in (replace(request, source=request.target, target=request.source),
                        replace(request, fields=frozenset({'city', 'hotel'})),
                        replace(request, purpose='marketing'), replace(request, audience=frozenset({'everyone'})),
                        replace(request, data_class='private_memory')):
            self.assertEqual(evaluate_bridge(policy, changed, current_grant_revision=Revision(2), now=self.now), BridgeDecision.DENY)

    def test_revoked_expired_or_stale_grant_denies(self):
        request, policy = self.bridge()
        for changed, revision in ((replace(policy, revoked=True), Revision(2)),
                                  (replace(policy, expires_at=self.now), Revision(2)), (policy, Revision(3))):
            self.assertEqual(evaluate_bridge(changed, request, current_grant_revision=revision, now=self.now), BridgeDecision.DENY)
        with self.assertRaises(DomainError):
            replace(policy, allowed_fields=frozenset({'*'}))

    def test_capabilities_do_not_promote_missing_limited_unsupported(self):
        for support in Support:
            caps = HostCapabilities(tuple((c, support) for c in Capability))
            if support is Support.SUPPORTED:
                caps.require_private_context_isolation()
            else:
                with self.assertRaises(DomainError):
                    caps.require_private_context_isolation()
        with self.assertRaises(DomainError):
            HostCapabilities().require_private_context_isolation()
        with self.assertRaises(DomainError):
            HostCapabilities(((Capability.HISTORY_ISOLATION, True),))

    def test_permission_enums_reject_implicit_boolean_coercion(self):
        for value in (*Support, *BridgeDecision):
            with self.assertRaises(DomainError):
                bool(value)

    def test_future_state_records_require_owner_provenance(self):
        other = Principal(new(IdKind.PRINCIPAL), new(IdKind.OWNER))
        source = replace(self.provenance, actor=other)
        for record in (self.ta, self.ca, WorldState(self.ta.scope, Revision(), self.provenance)):
            with self.assertRaises(DomainError):
                replace(record, provenance=source)


if __name__ == '__main__':
    unittest.main()
