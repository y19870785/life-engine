"""受信登记、Owner 绑定和只读 Session Lore 激活。"""
from functools import wraps
import hashlib
import hmac
import secrets

from .domain import (BindingStatus, DomainError, DomainId, IdKind, WorldKind, WorldStatus,
                     check_id, require)
from .import_ir import canonical
from .lore import (ActivatedLoreEntry, LoreActivationReason as Reason, LoreActivationRequest,
                   LoreActivationResult, LoreBindingRevision, LoreBookVersion, LoreDiagnostic as D,
                   LoreRegistrationIdentity, OwnerLoreContext,
                   SessionLoreContext, MAX_ENABLED_BOOKS, MAX_SCOPE_BINDINGS, MAX_SCOPE_SCAN_ENTRIES,
                   MAX_SCOPE_TRIGGERS, MAX_RECURSIVE_CORPUS_BYTES, byte_size, bounded_int)
from .lore_normalize import normalize_lore_ir, registration_fingerprint
from .lore_repository import LoreFailure as LC, LoreRuntimeError, fail
from .memory_control import scope_values
from .world_repository import FailureCode as WC, WorldRuntimeError


def checked(method):
    @wraps(method)
    def call(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except LoreRuntimeError:
            raise
        except WorldRuntimeError as exc:
            if exc.code in (WC.STORAGE_CORRUPT,WC.SCHEMA_MISMATCH,WC.STORAGE_BUSY,WC.RECOVERY_REQUIRED):
                fail({WC.STORAGE_CORRUPT:LC.STORAGE_CORRUPT,WC.SCHEMA_MISMATCH:LC.SCHEMA_MISMATCH,
                      WC.STORAGE_BUSY:LC.STORAGE_BUSY,WC.RECOVERY_REQUIRED:LC.RECOVERY_REQUIRED}[exc.code])
            fail(LC.NOT_AVAILABLE)
        except (DomainError, TypeError, ValueError, KeyError):
            fail(LC.INVALID_ARGUMENT)
    return call


def _fingerprint(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def _activation_order(bound, entry):
    """唯一稳定排序键；轮次由外层循环先行确定。"""
    return (0 if entry.constant else 1,-entry.runtime_priority,bound.binding_order,
        entry.runtime_order,entry.book_id.value.bytes,entry.book_version.value,entry.entry_id.value.bytes)


def _owner(context, scope=False):
    require(context, OwnerLoreContext)
    if scope and context.scope is None:
        fail(LC.AUTHORIZATION_DENIED)


def _scope_world(tx, context, *, tombstone=False):
    _owner(context, True)
    snap = tx.world.get_world(context.scope.world_id)
    if snap.timeline.scope != context.scope or snap.world.owner_id != context.principal.owner_id:
        fail(LC.NOT_AVAILABLE)
    if snap.world.status is WorldStatus.TOMBSTONED and not tombstone:
        fail(LC.NOT_AVAILABLE)
    return snap


class LoreRuntime:
    """只依赖 LoreRepository；不调用宿主、网络或文件系统。"""
    def __init__(self, repository):
        self.repository = repository
        self._version_key = secrets.token_bytes(32)

    @checked
    def register_book(self, context, display_name, ir, identity, *, payload_fingerprint=None):
        _owner(context)
        require(identity,LoreRegistrationIdentity)
        proposal = normalize_lore_ir(ir,payload_fingerprint=payload_fingerprint)
        if type(display_name) is not str or not display_name.strip() or byte_size(display_name)>512:
            fail(LC.INVALID_ARGUMENT)
        stamp = _fingerprint([registration_fingerprint('NEW_BOOK',None,None,proposal),display_name])
        with self.repository.transaction(write=True) as tx:
            replay = tx.replay(identity,context.principal.principal_id,stamp)
            if replay:
                return replay
            book_id,version = DomainId.new(IdKind.LORE_BOOK),LoreBookVersion(1)
            tx.insert_book(book_id,context.principal.owner_id,display_name,proposal.source_type,
                proposal.source_metadata,context.principal.principal_id)
            tx.insert_version(book_id,version,proposal,stamp,context.principal.principal_id)
            return tx.audit(context,'register_book',book_id,version,identity,stamp)

    @checked
    def register_version(self, context, book_id, expected_current_version, ir, identity,
                         *, payload_fingerprint=None):
        _owner(context)
        check_id(book_id,IdKind.LORE_BOOK)
        require(expected_current_version,LoreBookVersion)
        require(identity,LoreRegistrationIdentity)
        proposal = normalize_lore_ir(ir,payload_fingerprint=payload_fingerprint)
        stamp = registration_fingerprint('NEW_VERSION',book_id,expected_current_version,proposal)
        with self.repository.transaction(write=True) as tx:
            replay = tx.replay(identity,context.principal.principal_id,stamp)
            if replay:
                return replay
            book = tx.book(book_id)
            if book is None or book.owner_id != context.principal.owner_id:
                fail(LC.NOT_AVAILABLE)
            next_version = expected_current_version.next()
            tx.advance_version(book_id,context.principal.owner_id,expected_current_version,next_version)
            tx.insert_version(book_id,next_version,proposal,stamp,context.principal.principal_id)
            return tx.audit(context,'register_version',book_id,next_version,identity,stamp)

    @checked
    def list_owner_books(self, context):
        _owner(context)
        with self.repository.transaction() as tx:
            return tx.owner_books(context.principal.owner_id)

    @checked
    def inspect_book(self, context, book_id, version):
        _owner(context)
        check_id(book_id,IdKind.LORE_BOOK)
        require(version,LoreBookVersion)
        with self.repository.transaction() as tx:
            book = tx.book(book_id)
            if book is None or book.owner_id != context.principal.owner_id:
                fail(LC.NOT_AVAILABLE)
            record = tx.version(book_id,version)
            if record is None:
                fail(LC.NOT_AVAILABLE)
            return book,record,tx.entries(book_id,version)

    @checked
    def list_owner_bindings(self, context):
        with self.repository.transaction() as tx:
            _scope_world(tx,context,tombstone=True)
            return tx.revision(context.scope),tx.bindings(context.scope)

    def _binding_change(self, operation, context, book_id, expected_revision, identity,
                        *, version=None, binding_order=None, source='owner'):
        _owner(context,True)
        check_id(book_id,IdKind.LORE_BOOK)
        require(expected_revision,LoreBindingRevision)
        require(identity,LoreRegistrationIdentity)
        if version is not None:
            require(version,LoreBookVersion)
        if binding_order is not None:
            bounded_int(binding_order)
        if type(source) is not str or not source or byte_size(source)>512:
            fail(LC.INVALID_ARGUMENT)
        stamp = _fingerprint([operation,scope_values(context.scope),str(book_id),
            version.value if version else None,binding_order,source,expected_revision.value])
        with self.repository.transaction(write=True) as tx:
            _scope_world(tx,context,tombstone=operation=='unbind')
            replay = tx.replay(identity,context.principal.principal_id,stamp)
            if replay:
                return replay
            book = tx.book(book_id)
            if book is None or book.owner_id != context.principal.owner_id:
                fail(LC.NOT_AVAILABLE)
            new_revision = tx.cas(context.scope,expected_revision)
            old = next((b for b in tx.bindings(context.scope) if b.book_id==book_id),None)
            if operation=='bind':
                if old is not None or tx.version(book_id,version) is None:
                    fail(LC.NOT_AVAILABLE)
                if len(tx.bindings(context.scope))>=MAX_SCOPE_BINDINGS:
                    fail(LC.BUDGET_INPUT)
            elif old is None:
                fail(LC.NOT_AVAILABLE)
            elif operation=='rebind' and tx.version(book_id,version) is None:
                fail(LC.NOT_AVAILABLE)
            if operation=='bind':
                tx.insert_binding(context.scope,book_id,version,binding_order,source)
            elif operation=='unbind':
                tx.delete_binding(context.scope,book_id)
            elif operation in ('enable','disable'):
                tx.set_enabled(context.scope,book_id,operation=='enable')
            elif operation=='rebind':
                tx.set_version(context.scope,book_id,version)
            return tx.audit(context,operation,book_id,version or old.book_version,identity,stamp,new_revision)

    @checked
    def bind(self, context, book_id, version, binding_order, expected_revision, identity, *, source='owner'):
        return self._binding_change('bind',context,book_id,expected_revision,identity,
            version=version,binding_order=binding_order,source=source)

    @checked
    def unbind(self, context, book_id, expected_revision, identity):
        return self._binding_change('unbind',context,book_id,expected_revision,identity)

    @checked
    def enable(self, context, book_id, expected_revision, identity):
        return self._binding_change('enable',context,book_id,expected_revision,identity)

    @checked
    def disable(self, context, book_id, expected_revision, identity):
        return self._binding_change('disable',context,book_id,expected_revision,identity)

    @checked
    def rebind(self, context, book_id, version, expected_revision, identity):
        return self._binding_change('rebind',context,book_id,expected_revision,identity,version=version)

    @checked
    def activate(self, request):
        require(request,LoreActivationRequest)
        context = request.context
        if context.runtime_id != self.repository.runtime_id:
            fail(LC.SESSION_STALE)
        with self.repository.transaction() as tx:
            snap = tx.world.get_world(context.scope.world_id)
            if snap.timeline.scope != context.scope or context.principal.owner_id != context.scope.owner_id:
                fail(LC.SESSION_STALE)
            try:
                binding = tx.world.get_session(context.session_id)
            except WorldRuntimeError as exc:
                if exc.code is WC.SESSION_NOT_FOUND:
                    fail(LC.SESSION_STALE)
                raise
            if (binding.scope != context.scope or binding.principal != context.principal or
                    binding.status is not BindingStatus.OPEN or
                    binding.writer_epoch != context.writer_epoch or
                    snap.world.writer_epoch != context.writer_epoch or snap.world.status is not WorldStatus.ACTIVE):
                fail(LC.SESSION_STALE)
            from .memory import MemoryAudience, AudienceKind
            viewer = (MemoryAudience(AudienceKind.SOUL,context.scope.soul_id)
                if snap.world.kind is WorldKind.SOUL else
                MemoryAudience(AudienceKind.CHARACTER_INSTANCE,binding.character_instance_id))
            if viewer != context.viewer:
                fail(LC.SESSION_STALE)
            revision = tx.revision(context.scope)
            if revision != request.expected_revision:
                fail(LC.BINDING_STALE)
            bindings = tx.bindings(context.scope)
            if len(bindings)>MAX_SCOPE_BINDINGS:
                fail(LC.BUDGET_INPUT)
            active = tuple(b for b in bindings if b.enabled)
            if len(active)>MAX_ENABLED_BOOKS:
                fail(LC.BUDGET_INPUT)
            pairs = []
            count = 0
            trigger_count = 0
            for bound in active:
                version = tx.version(bound.book_id,bound.book_version)
                if version is None:
                    fail(LC.STORAGE_CORRUPT)
                entry_count,book_triggers=tx.scan_counts(bound.book_id,bound.book_version)
                count += entry_count
                if count > MAX_SCOPE_SCAN_ENTRIES:
                    fail(LC.BUDGET_INPUT)
                trigger_count += book_triggers
                if trigger_count > MAX_SCOPE_TRIGGERS:
                    fail(LC.BUDGET_INPUT)
                pairs.extend((bound,e) for e in tx.entries(bound.book_id,bound.book_version)
                             if e.enabled and e.runtime_disabled_reason is None)
            if len(pairs)>MAX_SCOPE_SCAN_ENTRIES or sum(len(e.primary_triggers)+len(e.secondary_triggers)
                    for _,e in pairs)>MAX_SCOPE_TRIGGERS:
                fail(LC.BUDGET_INPUT)
            return self._scan(request,snap.world.revision,revision,active,pairs)

    def _scan(self, request, world_revision, revision, bindings, pairs):
        """仅纳入已输出的正文；扫描工作按每次字符串比较的语料字节数计。"""
        corpus = list(request.conversation_projection)
        if request.memory_projection:
            corpus.extend(request.memory_projection.texts)
        results, diagnostics, used = [], [], set()
        work, output_bytes, exhausted = 0, 0, False
        budget = request.budget
        ordered_pairs = sorted(pairs,key=lambda item:_activation_order(*item))
        for round_no in range(budget.max_rounds):
            candidates = []
            for bound,entry in ordered_pairs:
                key = (entry.book_id,entry.book_version,entry.entry_id)
                if key in used or not entry.text:
                    continue
                if entry.constant:
                    if round_no==0:
                        cost=byte_size(entry.text)
                        if work+cost>budget.max_scan_work_bytes:
                            diagnostics.append(D.ACTIVATION_SCAN_LIMIT)
                            exhausted=True
                            break
                        work += cost
                        candidates.append((bound,entry,Reason.CONSTANT,(),()))
                    continue
                if not entry.primary_triggers:
                    continue
                def match(triggers):
                    nonlocal work
                    hits = []
                    for trigger in triggers:
                        needle = trigger if entry.case_sensitive else trigger.casefold()
                        for text in corpus:
                            cost = byte_size(text)
                            if work+cost>budget.max_scan_work_bytes:
                                raise OverflowError
                            work += cost
                            if needle in (text if entry.case_sensitive else text.casefold()):
                                hits.append(trigger)
                                break
                    return tuple(hits)
                try:
                    primary = match(entry.primary_triggers)
                    secondary = match(entry.secondary_triggers) if primary and entry.selective and entry.secondary_triggers else ()
                except OverflowError:
                    diagnostics.append(D.ACTIVATION_SCAN_LIMIT)
                    exhausted=True
                    break
                if primary and (not entry.selective or not entry.secondary_triggers or secondary):
                    reason = Reason.RECURSIVE_TRIGGER if round_no else Reason.SELECTIVE_TRIGGER if entry.selective and entry.secondary_triggers else Reason.PRIMARY_TRIGGER
                    candidates.append((bound,entry,reason,primary,secondary))
            candidates.sort(key=lambda item:_activation_order(item[0],item[1]))
            if not candidates:
                break
            new_text = []
            for bound,entry,reason,primary,secondary in candidates:
                if len(results)>=budget.max_entries:
                    diagnostics.append(D.ACTIVATION_ENTRY_LIMIT); exhausted=True; break
                size = byte_size(entry.text)
                if (output_bytes+size>budget.max_output_bytes or
                    sum(byte_size(t) for t in corpus)+sum(byte_size(t) for t in new_text)+size>MAX_RECURSIVE_CORPUS_BYTES):
                    diagnostics.append(D.ACTIVATION_BYTE_LIMIT); exhausted=True; break
                results.append(ActivatedLoreEntry(entry.book_id,entry.book_version,entry.entry_id,entry.text,
                    reason,round_no,primary,secondary,entry.runtime_priority,bound.binding_order,entry.runtime_order))
                output_bytes += size
                used.add((entry.book_id,entry.book_version,entry.entry_id))
                new_text.append(entry.text)
                diagnostics.extend(d for d in entry.diagnostics if d not in diagnostics)
            corpus.extend(new_text)
            if exhausted or not new_text:
                break
        else:
            if any((e.book_id,e.book_version,e.entry_id) not in used for _,e in pairs):
                diagnostics.append(D.ACTIVATION_ROUND_LIMIT); exhausted=True
        context=request.context
        book_versions=tuple((b.book_id,b.book_version) for b in bindings)
        token_data = canonical({'runtime':context.runtime_id,'scope':scope_values(context.scope),
            'principal':str(context.principal.principal_id),
            'viewer':[context.viewer.kind.value,str(context.viewer.target) if context.viewer.target else None],
            'session':str(context.session_id),'epoch':context.writer_epoch.value,
            'world_revision':world_revision.value,'binding_revision':revision.value,
            'books':[(str(a),b.value) for a,b in book_versions],
            'input':_fingerprint([request.conversation_projection,
                request.memory_projection.version if request.memory_projection else None,
                request.memory_projection.texts if request.memory_projection else ()]),
            'budget':[budget.max_rounds,budget.max_entries,budget.max_output_bytes,budget.max_scan_work_bytes],
            'entries':[str(e.entry_id) for e in results]})
        token=hmac.new(self._version_key,token_data.encode('utf-8'),hashlib.sha256).hexdigest()
        return LoreActivationResult(context.scope,context.viewer,context.session_id,context.writer_epoch,
            context.runtime_id,world_revision,revision,book_versions,tuple(results),tuple(dict.fromkeys(diagnostics)),
            (work,output_bytes,len(results)),exhausted,token)
