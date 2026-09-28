"""副本 generation 围栏；恢复不推断外部消息不存在。"""
from contextlib import closing
from datetime import datetime, timezone
import sqlite3

from .living_runtime import finish
from .living_repository import validate_living_data


def fence_generation(path, generation):
    with closing(sqlite3.connect(path)) as db:
        db.row_factory=sqlite3.Row
        with db:
            db.execute('BEGIN IMMEDIATE')
            validate_living_data(db)
            for row in db.execute('SELECT root_id FROM living_roots').fetchall():
                rid=row[0]
                db.execute('UPDATE living_roots SET generation=?,paused=1,reconciliation=1 WHERE root_id=?',(generation,rid))
                db.execute("UPDATE living_intents SET state='QUARANTINED',invalidated=1 WHERE root_id=? AND state IN ('DECIDED','PREPARED')",(rid,))
                db.execute("UPDATE living_attempts SET state='UNKNOWN' WHERE root_id=? AND state='CLAIMED'",(rid,))
                finish(db,rid,datetime.now(timezone.utc).timestamp(),'restore',{'generation':generation})
            validate_living_data(db)
