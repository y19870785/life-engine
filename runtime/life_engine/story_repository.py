"""Story 仓储合同与固定失败码。"""
from enum import Enum
from typing import Protocol


class StoryFailure(str, Enum):
    INVALID_ARGUMENT = 'INVALID_ARGUMENT'
    AUTHORIZATION_DENIED = 'AUTHORIZATION_DENIED'
    NOT_AVAILABLE = 'NOT_AVAILABLE'
    SESSION_STALE = 'SESSION_STALE'
    REVISION_CONFLICT = 'REVISION_CONFLICT'
    IDEMPOTENCY_CONFLICT = 'IDEMPOTENCY_CONFLICT'
    EVENT_CONFLICT = 'EVENT_CONFLICT'
    PROJECTION_CONFLICT = 'PROJECTION_CONFLICT'
    BUDGET_INPUT = 'BUDGET_INPUT'
    STORAGE_BUSY = 'STORAGE_BUSY'
    STORAGE_CORRUPT = 'STORAGE_CORRUPT'
    SCHEMA_MISMATCH = 'SCHEMA_MISMATCH'
    RECOVERY_REQUIRED = 'RECOVERY_REQUIRED'
    PERSISTENCE_FAILURE = 'PERSISTENCE_FAILURE'


class StoryRuntimeError(RuntimeError):
    """对外仅暴露固定错误码，不携带事件正文。"""
    def __init__(self, code):
        self.code = code
        super().__init__(code.value)


def fail(code):
    raise StoryRuntimeError(code)


class StoryRepository(Protocol):
    def transaction(self): ...
    def close(self): ...


class StoryTransaction(Protocol):
    world: object
    def state(self, scope): ...
    def replay(self, identity, producer, fingerprint): ...
    def cas(self, scope, expected): ...
    def event(self, scope, event_id): ...
    def insert(self, event, state, identity, fingerprint): ...
    def events(self, scope, *, after=0, limit=100): ...
