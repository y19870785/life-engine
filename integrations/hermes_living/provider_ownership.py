"""Protected, process-local Discord credential and REST ownership gate.

Only trusted Host binding code may supply the complete configuration snapshot.
No token-derived identifier leaves this module. Hermes' (platform, fingerprint)
claim is deliberately not used for cross-platform equality.
"""

from dataclasses import dataclass, field
import inspect
from threading import RLock
from time import monotonic


class ProviderBoundaryError(Exception):
    """Stable denial code; never contains a credential or provider response."""


class PreSendDeny(ProviderBoundaryError):
    """The provider preparation gate denied before permit consumption."""


@dataclass(frozen=True)
class CredentialClaim:
    platform: str
    profile: str
    owner: str
    token: str = field(repr=False, compare=False)


class ProtectedCredentialInventory:
    """A complete protected Host configuration/live-owner snapshot.

    `complete` is a trusted Host assertion, not a user-facing enable switch.
    The future A2 Host binding must verify provenance and completeness before
    constructing this object; absent proof, the factory below denies.
    """

    def __init__(self, claims, *, complete=False):
        self._claims = tuple(claims)
        self._complete = complete is True

    def require_exclusive(self, candidate):
        if (not self._complete or type(candidate) is not CredentialClaim
                or not candidate.token or not candidate.platform
                or not candidate.profile or not candidate.owner
                or not all(type(c) is CredentialClaim and c.token
                           and c.platform and c.profile and c.owner
                           for c in self._claims)):
            raise ProviderBoundaryError('CREDENTIAL_INVENTORY_UNPROVEN')
        matches = [c for c in self._claims if c.token == candidate.token]
        if (len(matches) != 1 or matches[0].platform != candidate.platform
                or matches[0].profile != candidate.profile
                or matches[0].owner != candidate.owner):
            raise ProviderBoundaryError('DUPLICATE_CREDENTIAL_CLAIM')


class RateLimitDomain:
    """One credential-wide global and per-route admission domain.

    A blocked bucket is denied synchronously before permit consumption. No
    sleeping or network operation is performed here.
    """

    def __init__(self, *, clock=monotonic):
        self._clock = clock
        self._lock = RLock()
        self._global_until = 0.0
        self._routes = {}
        self._in_flight = False

    def admit_now(self, route):
        with self._lock:
            now = self._clock()
            if (self._in_flight or now < self._global_until
                    or now < self._routes.get(route, 0.0)):
                raise ProviderBoundaryError('RATE_LIMIT_PRE_CONSUME_DENY')
            # Conservative credential-global serialization. All authenticated
            # REST preparation, not only MESSAGE_CREATE, must use this domain.
            self._in_flight = True

    def release(self):
        with self._lock:
            self._in_flight = False

    def observe(self, route, status, headers):
        """All authenticated REST routes feed the same owner state."""
        normalized = {str(k).lower(): str(v) for k, v in headers.items()}
        with self._lock:
            now = self._clock()
            retry = _nonnegative_float(normalized.get('retry-after'))
            reset = _nonnegative_float(normalized.get('x-ratelimit-reset-after'))
            if status == 429 and retry is not None:
                global_flag = normalized.get('x-ratelimit-global', '').lower()
                if global_flag != 'false':
                    # Missing/unknown scope is treated as credential-global.
                    self._global_until = max(self._global_until, now + retry)
                else:
                    self._routes[route] = max(self._routes.get(route, 0.0), now + retry)
            elif normalized.get('x-ratelimit-remaining') == '0' and reset is not None:
                self._routes[route] = max(self._routes.get(route, 0.0), now + reset)


def _nonnegative_float(value):
    try:
        result = float(value)
        return result if 0 <= result <= 86400 else None
    except (TypeError, ValueError, OverflowError):
        return None


class DiscordRestOwnership:
    """One credential, one authenticated REST session and rate-limit domain."""

    _claims_lock = RLock()
    _active = []  # Process-local claims; A2 must also prove Host-wide inventory.

    def __init__(self, claim, session, domain, lifecycle):
        self._claim = claim
        self._session = session
        self.domain = domain
        self.lifecycle = lifecycle
        self._current = True
        self._attempts = set()

    def __repr__(self):
        return '<DiscordRestOwnership redacted>'

    @classmethod
    def create(cls, *, candidate, inventory, session_factory, lifecycle):
        # Exact token equality happens only in this protected in-memory scope.
        with cls._claims_lock:
            inventory.require_exclusive(candidate)
            if any(owner._claim.token == candidate.token
                   for owner in cls._active):
                raise ProviderBoundaryError('SECOND_REST_OWNER')
            # Session creation is deliberately AFTER the exclusivity gate.
            try:
                session = session_factory.create(candidate.token)
            except BaseException:
                raise ProviderBoundaryError('PROVIDER_SESSION_CREATE_DENIED') from None
            owner = cls(candidate, session, RateLimitDomain(), lifecycle)
            cls._active.append(owner)
            return owner

    def require_current(self, lifecycle):
        if not self._current or self.lifecycle is None or self.lifecycle != lifecycle:
            raise ProviderBoundaryError('PROVIDER_OWNERSHIP_STALE')

    def bind_lifecycle_once(self, lifecycle):
        with self._claims_lock:
            if not self._current or self.lifecycle is not None or not lifecycle:
                raise ProviderBoundaryError('PROVIDER_OWNERSHIP_STALE')
            self.lifecycle = lifecycle

    def reserve_attempt_once(self, attempt):
        with self._claims_lock:
            if not self._current or attempt in self._attempts:
                raise ProviderBoundaryError('SAFETY_VIOLATION_DUPLICATE_ATTEMPT')
            self._attempts.add(attempt)

    @property
    def session(self):
        if not self._current:
            raise ProviderBoundaryError('PROVIDER_OWNERSHIP_STALE')
        return self._session

    @property
    def authorization_header(self):
        if not self._current:
            raise ProviderBoundaryError('PROVIDER_OWNERSHIP_STALE')
        return 'Bot ' + self._claim.token

    def revoke(self):
        with self._claims_lock:
            self._current = False

    async def close(self):
        # A revoked but unclosed client still owns its credential. A successor
        # cannot be admitted until the old authenticated session has closed.
        self.revoke()
        session = self._session
        if session is not None:
            result = session.close()
            if inspect.isawaitable(result):
                await result
        with self._claims_lock:
            self._session = None
            if self in type(self)._active:
                type(self)._active.remove(self)
