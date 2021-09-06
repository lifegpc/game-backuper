try:
    from plyvel import DB
    have_leveldb = True
    from typing import List
except ImportError:
    have_leveldb = False


if have_leveldb:
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
