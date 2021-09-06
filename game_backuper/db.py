from sqlite3 import connect
from os.path import join
from typing import List, Union
from threading import Lock
from game_backuper.file import File
from game_backuper.filetype import FileType


VERSION_TABLE = '''CREATE TABLE version (
id TEXT,
v1 INT,
v2 INT,
v3 INT,
v4 INT,
PRIMARY KEY(id)
);'''
FILES_TABLE = '''CREATE TABLE files (
id INTEGER,
file TEXT,
size INT,
program TEXT,
hash TEXT,
PRIMARY KEY(id)
);'''
FILETYPE_TABLE = '''CREATE TABLE filetype (
id INT,
type INT,
PRIMARY KEY(id)
);'''


class Db:
    VERSION = [1, 0, 0, 1]

    def __check_database(self) -> bool:
        self.__updateExistsTable()
        v = self.__read_version()
        if v is None:
            return False
        if v < self.VERSION:
            if v < [1, 0, 0, 1]:
                self.db.execute(FILETYPE_TABLE)
            self.__write_version()
        if v > self.VERSION:
            raise ValueError(
                'Database version is higher. Please update program.')
        return True

    def __create_table(self):
        if 'version' not in self._exist_table:
            self.db.execute(VERSION_TABLE)
            self.__write_version()
        if 'files' not in self._exist_table:
            self.db.execute(FILES_TABLE)
        self.db.commit()

    def __init__(self, loc: str):
        fn = join(loc, "data.db")
        self.db = connect(fn, check_same_thread=False)
        self.db.execute('VACUUM;')
        self.db.commit()
        ok = self.__check_database()
        if not ok:
            self.__create_table()
        self._lock = Lock()

    def __read_version(self) -> List[int]:
        if 'version' not in self._exist_table:
            return None
        cur = self.db.execute("SELECT * FROM version WHERE id='main';")
        for i in cur:
            return [k for k in i if isinstance(k, int)]

    def __updateExistsTable(self):
        cur = self.db.execute('SELECT * FROM main.sqlite_master;')
        self._exist_table = {}
        for i in cur:
            if i[0] == 'table':
                self._exist_table[i[1]] = i

    def __write_version(self):
        if self.__read_version() is None:
            self.db.execute('INSERT INTO version VALUES (?, ?, ?, ?, ?);',
                            tuple(['main'] + self.VERSION))
        else:
            self.db.execute(
                "UPDATE version SET v1=?, v2=?, v3=?, v4=? WHERE id='main';",
                tuple(self.VERSION))
        self.db.commit()

    def add_file(self, f: File):
        with self._lock:
            self.db.execute('INSERT INTO files (file, size, program, hash) VALUES (?, ?, ?, ?);',  # noqa: E501
                            (f.file, f.size, f.program, f.hash))
            if f.type is not None:
                cur = self.db.execute(
                    'SELECT * FROM files WHERE program=? AND file=?;',
                    (f.program, f.file))
                for i in cur:
                    self.db.execute('INSERT INTO filetype VALUES (?, ?);',
                                    (i[0], f.type))
            self.db.commit()

    def get_file(self, prog: str, file: str) -> File:
        with self._lock:
            cur = self.db.execute(
                'SELECT files.*, filetype.type FROM files LEFT JOIN filetype ON files.id=filetype.id WHERE program=? AND file=?;',  # noqa: E501
                (prog, file))
            for i in cur:
                return File(*i)

    def remove_file(self, id: Union[int, File]):
        with self._lock:
            ft = None
            if isinstance(id, File):
                iid = id.id
                ft = id.type
            else:
                cur = self.db.execute('SELECT type FROM filetype WHERE id=?;',
                                      (id,))
                for i in cur:
                    ft = FileType(i[0])
                iid = id
            self.db.execute('DELETE FROM files WHERE id=?;', (iid,))
            if ft is not None:
                self.db.execute('DELETE FROM filetype WHERE id=?;', (iid,))
            self.db.commit()

    def set_file(self, id: int, size: int, hash: str):
        with self._lock:
            self.db.execute('UPDATE files SET size=?, hash=? WHERE id=?;',
                            (size, hash, id))
            self.db.commit()
