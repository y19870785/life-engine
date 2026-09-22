"""Memory 仓储合同、固定失败代码及事务内持久操作。"""
from enum import Enum
from typing import Protocol, ContextManager

from .domain import DomainError


class MemoryFailure(str, Enum):
    NOT_AVAILABLE = 'MemoryNotAvailable'
    REVISION_CONFLICT = 'MemoryRevisionConflict'
    IDEMPOTENCY_CONFLICT = 'MemoryIdempotencyConflict'
    AUTHORIZATION_DENIED = 'MemoryAuthorizationDenied'
    INVALID_SOURCE = 'MemoryInvalidSource'
    INVALID_ARGUMENT = 'MemoryInvalidArgument'
    CONTROL_REQUIRED = 'MemoryControlRequired'


class MemoryRuntimeError(DomainError):
    """错误不携带正文或可供跨域探测的记录详情。"""
    def __init__(self, code):
        self.code = code
        super().__init__(code.value)


def deny(code):
    raise MemoryRuntimeError(code)


class MemoryRepository(Protocol):
    """管理锁、控制域、life.db 按固定次序进入；不启动新的 World 运行代次。"""
    def transaction(self) -> ContextManager: ...
    def delete(self, context, memory_id, expected_revision, identity): ...
    def reconcile(self): ...
