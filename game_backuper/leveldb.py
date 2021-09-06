try:
    from plyvel import DB
    have_leveldb = True
except ImportError:
    have_leveldb = False


if have_leveldb:
    from typing import List
    from hashlib import sha512
    from base64 import b85encode
    from collections import namedtuple
    from sqlite3 import connect
    LeveldbStats = namedtuple('LeveldbStats', ['hash', 'size'])
    MAP_TABLE = '''CREATE TABLE map (
    key TEXT,
    value TEXT,
    PRIMARY KEY(key)
    )'''

    def list_leveldb_entries(db: str, dms: List[bytes] = None):
        d = DB(db)
        r = []
        for i in d.iterator(include_value=False):
            if isinstance(i, bytes):
                if dms is None:
                    r.append(i)
                else:
                    if i == b'VERSION':
                        r.append(i)
                    elif i.startswith(b'META:'):
                        dm = i[5:]
                        if dm in dms:
                            r.append(i)
                    elif i.startswith(b'_'):
                        dmi = i.find(b'\x00\x01')
                        dm = i[1:dmi]
                        if dm in dms:
                            r.append(i)
        r.sort()
        return r

    def leveldb_stats(db: str, entries: List[bytes]) -> LeveldbStats:
        d = DB(db)
        h = sha512()
        le = 0
        for e in entries:
            v = d.get(e)
            if v is not None:
                h.update(e)
                h.update(v)
                le += len(e) + len(v)
        d.close()
        return LeveldbStats(b85encode(h.digest()).decode(), le)

    def leveldb_to_sqlite(db: str, dest: str, entries: List[bytes]):
        d = DB(db)
        s = connect(dest)
        s.text_factory = bytes
        s.execute(MAP_TABLE)
        for e in entries:
            v = d.get(e)
            if v is not None:
                s.execute('INSERT INTO map VALUES (?, ?);', (e, v))
        s.commit()
        s.execute('VACUUM;')
        s.commit()
        d.close()
        s.close()
