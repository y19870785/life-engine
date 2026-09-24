"""Bridge 授权仓储的窄接口；Memory/Story 来源通过各自 Runtime 读取。"""
from contextlib import AbstractContextManager
from typing import Protocol

from .bridge import BridgeGrant, BridgeIdempotencyIdentity, BridgeReceipt
from .domain import DomainId


class BridgeTransaction(Protocol):
    def grant(self, grant_id: DomainId) -> BridgeGrant | None: ...
    def effective_revoked(self, grant_id: DomainId) -> bool: ...
    def replay(self, identity: BridgeIdempotencyIdentity, fingerprint: str) -> BridgeReceipt | None: ...
    def insert_grant(self, grant: BridgeGrant, identity: BridgeIdempotencyIdentity,
                     fingerprint: str) -> BridgeReceipt: ...


class BridgeRepository(Protocol):
    runtime_id: str
    generation: str

    def transaction(self) -> AbstractContextManager[BridgeTransaction]: ...
    def reconcile(self) -> None: ...
