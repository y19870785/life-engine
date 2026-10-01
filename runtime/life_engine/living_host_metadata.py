"""与 Living DB 分离的本地、受保护、单写者 metadata。"""
import csv
import hashlib
import hmac
import json
import os
from pathlib import Path
from functools import lru_cache
import secrets
import stat
import subprocess

from .durable import locked, no_symlinks, sync_dir
from .living_domain import canonical, fail

LIMIT = 1024 * 1024


@lru_cache(maxsize=1)
def current_sid():
    raw = subprocess.check_output(['whoami', '/user', '/fo', 'csv', '/nh'],
                                   text=True, encoding='utf-8')
    return next(csv.reader(raw.strip().splitlines()))[1]


def protect(path):
    if os.name == 'nt':
        sid = current_sid()
        # 清除预先存在的显式 ACE，再禁用继承；只保留当前可信 OS 用户。
        subprocess.run(['icacls', str(path), '/reset'], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r',
                        '*' + sid + (':(OI)(CI)F' if path.is_dir() else ':F')],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        path.chmod(0o700 if path.is_dir() else 0o600)


class BindingMetadata:
    """锁持有整个 authority 生命周期；异常不重新 enrollment、不回退 legacy。"""
    def __init__(self, directory, *, initial=None, test_key=None):
        no_symlinks(Path(directory).absolute())
        self.directory = Path(directory).resolve()
        no_symlinks(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        protect(self.directory)
        self._lease = locked(self.directory, 'binding-authority', timeout=0)
        try:
            self._lease.__enter__()
        except TimeoutError:
            fail('AUTHORITY_ALREADY_RUNNING')
        self.path = self.directory / 'binding.json'
        key_path = self.directory / 'binding.key'
        marker = self.directory / 'binding.enrolled'
        try:
            no_symlinks(self.path); no_symlinks(key_path); no_symlinks(marker)
            exists = self.path.exists()
            if not exists and (key_path.exists() or marker.exists()):
                fail('BINDING_MISSING')
            if test_key is not None:
                if type(test_key) is not bytes or len(test_key) < 32:
                    fail('INVALID_ARGUMENT')
                self._key = test_key
            elif key_path.exists():
                if key_path.stat().st_size != 32:
                    fail('BINDING_CORRUPT')
                if os.name != 'nt' and stat.S_IMODE(key_path.stat().st_mode) & 0o077:
                    fail('BINDING_UNPROTECTED')
                self._key = key_path.read_bytes()
            else:
                if exists or initial is None:
                    fail('BINDING_MISSING')
                self._key = secrets.token_bytes(32)
                with key_path.open('xb') as handle:
                    protect(key_path)
                    handle.write(self._key); handle.flush(); os.fsync(handle.fileno())
                sync_dir(self.directory)
            if exists:
                self.read()
            elif initial is not None:
                self.write(initial)
                with marker.open('xb') as handle:
                    protect(marker)
                    handle.write(b'v1'); handle.flush(); os.fsync(handle.fileno())
                sync_dir(self.directory)
            else:
                fail('BINDING_MISSING')
        except BaseException:
            self.close()
            raise

    def _checksum(self, data):
        return hmac.new(self._key, canonical(data).encode('utf-8'), hashlib.sha256).hexdigest()

    def read(self):
        no_symlinks(self.path)
        if not self.path.exists():
            fail('BINDING_MISSING')
        if os.name != 'nt' and stat.S_IMODE(self.path.stat().st_mode) & 0o077:
            fail('BINDING_UNPROTECTED')
        if self.path.stat().st_size > LIMIT:
            fail('BINDING_CORRUPT')
        def pairs(items):
            out = {}
            for key, value in items:
                if key in out:
                    fail('BINDING_CORRUPT')
                out[key] = value
            return out
        try:
            doc = json.loads(self.path.read_text(encoding='utf-8'), object_pairs_hook=pairs)
            if (set(doc) != {'version', 'data', 'checksum'}
                    or type(doc['version']) is not int or doc['version'] != 1):
                fail('BINDING_CORRUPT')
            if not hmac.compare_digest(doc['checksum'], self._checksum(doc['data'])):
                fail('BINDING_CORRUPT')
            return doc['data']
        except (ValueError, TypeError, KeyError, OSError):
            fail('BINDING_CORRUPT')

    def write(self, data):
        encoded = canonical(dict(version=1, data=data, checksum=self._checksum(data))).encode('utf-8')
        if len(encoded) > LIMIT:
            fail('BINDING_BUDGET')
        temporary = self.directory / ('binding-' + secrets.token_hex(12) + '.tmp')
        try:
            with temporary.open('xb') as handle:
                protect(temporary)
                handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            sync_dir(self.directory)
        finally:
            temporary.unlink(missing_ok=True)

    def close(self):
        lease, self._lease = self._lease, None
        if lease is not None:
            lease.__exit__(None, None, None)
