"""HLV3 validation-only pipe-controlled real Gateway restart probe.

The external protected runner owns Gateway start/stop. This worker owns only
an isolated Core fixture, native A3 capabilities and a local fake journal.
"""
import json
import os
import sys
from pathlib import Path

from hlv3_validation_support import HLV3Fixture, HostGate, FENCE
import hlv3_validation_support as support


def main():
    case = HLV3Fixture()
    case.setUp()
    try:
        _, outcome = case.claimed()
        data = {'operation_id': 'claim'}
        envelope, capability = case.ticket('recover_operation', data)
        old_gate = case.gate
        old_snapshot = old_gate.snapshot
        session = case.session
        session_path = case.base / 'VALIDATION_SESSION.json'
        session_metadata = dict(source='VALIDATION_SESSION', real_inbound=False,
            session_id=str(session.session_id), writer_epoch=session.writer_epoch.value,
            world_revision=session.world_revision.value, generation=case.lr.generation)
        with session_path.open('w', encoding='utf-8') as handle:
            json.dump(session_metadata, handle)
            handle.flush()
            os.fsync(handle.fileno())
        before = case.business_snapshot()
        print('PERMIT_ISSUED_WAITING_FOR_REAL_RESTART', flush=True)
        if sys.stdin.readline().strip() != 'RESTART_COMPLETE':
            raise RuntimeError('HLV3_RESTART_NOT_CONFIRMED')
        case.reject('HOST_LIFECYCLE_STALE', lambda: case.send(outcome))
        case.authority.close()
        case.gate = HostGate(old_gate.fixture)
        case.assertNotEqual(old_snapshot['process'], case.gate.snapshot['process'])
        case.assertEqual(old_gate.persistent_digest, case.gate.persistent_digest)
        case.authority = case.new_authority()
        case.bind_consumers()
        case.reject('CAPABILITY_STALE', lambda: case.send(outcome))
        case.reject('CAPABILITY_STALE', lambda: case.facade.recover_operation(envelope, capability, data))
        recovered = case.call('recover_operation', data)
        case.assertEqual(recovered['result']['status'], 'COMMITTED')
        case.assertNotIn('permit', recovered['result'])
        case.assertEqual(session, case.session)
        case.assertEqual(json.loads(session_path.read_text()), session_metadata)
        case.assertEqual(before, case.business_snapshot())
        case.assertFalse(case.transport.journal.exists())
        result = dict(LIFE_01='PASS', LIFE_02='PASS', LIFE_03='PASS',
            REAL_TRANSPORT_INVOCATION_COUNT=support.FENCE.real_transport_invocations,
            REAL_NETWORK_SEND_COUNT=support.FENCE.network_attempts,
            session_persistence='VALIDATION_SESSION_NOT_REAL_INBOUND',
            process_identity_changed=True, persistent_identity_unchanged=True)
        Path(sys.argv[1]).write_text(json.dumps(result, indent=2), encoding='utf-8')
        print('LIFECYCLE_VALIDATION_PASS', flush=True)
    finally:
        case.tearDown()
        case.doCleanups()


if __name__ == '__main__':
    main()
