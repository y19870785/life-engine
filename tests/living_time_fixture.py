"""隔离的 TZif fixture：只定义 2026 年纽约 DST 两次切换，不作为生产时区库。"""
from contextlib import contextmanager
from datetime import datetime, timezone
import io
import struct
from unittest.mock import patch
from zoneinfo import ZoneInfo


@contextmanager
def zones():
    spring=int(datetime(2026,3,8,7,tzinfo=timezone.utc).timestamp())
    autumn=int(datetime(2026,11,1,6,tzinfo=timezone.utc).timestamp())
    header=b'TZif\0'+b'\0'*15+struct.pack('>6l',0,0,0,2,2,8)
    fixture=header+struct.pack('>2l',spring,autumn)+bytes([1,0])
    fixture+=struct.pack('>lbb',-18000,0,0)+struct.pack('>lbb',-14400,1,4)+b'EST\0EDT\0'
    ny=ZoneInfo.from_file(io.BytesIO(fixture),key='America/New_York')
    fixed=b'TZif\0'+b'\0'*15+struct.pack('>6l',0,0,0,0,1,4)+struct.pack('>lbb',28800,0,0)+b'CST\0'
    sh=ZoneInfo.from_file(io.BytesIO(fixed),key='Asia/Shanghai')
    def lookup(name):
        return {'America/New_York':ny,'Asia/Shanghai':sh}[name]
    def signature(name): return 'fixture-2026-'+name
    with patch('life_engine.living_policy.ZoneInfo',side_effect=lookup) as factory, \
         patch('life_engine.living_policy.zone_fingerprint',side_effect=signature), \
         patch('life_engine.living_runtime.zone_fingerprint',side_effect=signature):
        factory.no_cache.side_effect=lookup
        yield ny
