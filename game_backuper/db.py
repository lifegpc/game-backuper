from getpass import getpass as _getpass
from os import close
from os.path import join
from shutil import move
from sqlite3 import connect, Connection, DatabaseError
from tempfile import mkstemp
from threading import Lock
from typing import List, Union
from game_backuper.cml import Opts
from game_backuper.config import Config
from game_backuper.enc import EncryptStats
from game_backuper.file import File, hydrate_file_if_needed
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
ENCRYPTED_FILES_TABLE = '''CREATE TABLE encrypted_files (
id INTEGER,
key TEXT,
iv TEXT,
crc32 TEXT,
compressed INT,
compressed_size INT,
PRIMARY KEY(id)
);'''


def getpass(prompt, cfg: Config) -> str:
    if cfg.db_password is not None:
        return cfg.db_password
    return _getpass(prompt)


class Db:
    VERSION = [1, 0, 0, 2]
    fn = None

    def __check_database(self) -> bool:
        self.__updateExistsTable()
        v = self.__read_version()
        if v is None:
            return False
        if v < self.VERSION:
            if v < [1, 0, 0, 1]:
                self.db.execute(FILETYPE_TABLE)
            if v < [1, 0, 0, 2]:
                self.db.execute(ENCRYPTED_FILES_TABLE)
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
        if 'filetype' not in self._exist_table:
            self.db.execute(FILETYPE_TABLE)
        if 'encrypted_files' not in self._exist_table:
            self.db.execute(ENCRYPTED_FILES_TABLE)
        self.db.commit()

    def __init__(self, config: Config, opts: Opts):
        self._cfg = config
        self._opt = opts
        self.fn = config.db_path if config.db_path else join(
            config.dest, "data.db")
        hydrate_file_if_needed(self.fn)
        self.db = connect(self.fn, check_same_thread=False)
        if config.encrypt_db:
            passpharse = getpass('Please input the password of the database:', config)  # noqa: E501
            if not self.encrypted:
                tfn = mkstemp()
                close(tfn[0])
                tfn = tfn[1]
                db = connect(tfn)
                self.__set_encrypt_key(passpharse, db)
                for q in self.db.iterdump():
                    db.execute(q)
                self.db.close()
                db.close()
                move(tfn, self.fn)
                self.db = connect(self.fn, check_same_thread=False)
            elif opts.change_key:
                self.__set_encrypt_key(passpharse)
                passpharse = getpass('Please input new password of the database:', config)  # noqa: E501
                tfn = mkstemp()
                close(tfn[0])
                tfn = tfn[1]
                db = connect(tfn)
                self.__set_encrypt_key(passpharse, db)
                for q in self.db.iterdump():
                    db.execute(q)
                self.db.close()
                db.close()
                move(tfn, self.fn)
                self.db = connect(self.fn, check_same_thread=False)
            self.__set_encrypt_key(passpharse)
        else:
            if self.encrypted:
                passpharse = getpass('Please input the password of the database:', config)  # noqa: E501
                self.__set_encrypt_key(passpharse)
                tfn = mkstemp()
                close(tfn[0])
                tfn = tfn[1]
                db = connect(tfn)
                for q in self.db.iterdump():
                    db.execute(q)
                self.db.close()
                db.close()
                move(tfn, self.fn)
                self.db = connect(self.fn, check_same_thread=False)
        if opts.optimize_db:
            self.db.execute('VACUUM;')
            self.db.commit()
        ok = self.__check_database()
        if not ok:
            self.__create_table()
        self._lock = Lock()
        if config.encrypt_db and not self.encrypted:
            print('Warning: Current library do not support encryption.')

    def __read_version(self) -> List[int]:
        if 'version' not in self._exist_table:
            return None
        cur = self.db.execute("SELECT * FROM version WHERE id='main';")
        for i in cur:
            return [k for k in i if isinstance(k, int)]

    def __set_encrypt_key(self, key: str, db: Connection = None):
        if db is None:
            db = self.db
        db.execute('PRAGMA cipher_salt = "x\'2d506b1d2c3e7b075518f9db81039657\'";')  # noqa: E501
        db.execute('PRAGMA key = \'%s\';' % (key.replace("'", "\\'")))

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

    def add_file(self, f: File, commited: bool = True):
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
            if f.encrypted:
                cur = self.db.execute(
                    'SELECT * FROM files WHERE program=? AND file=?;',
                    (f.program, f.file))
                for i in cur:
                    self.db.execute('INSERT INTO encrypted_files VALUES (?, ?, ?, ?, ?, ?);', (i[0], f.key, f.iv, f.crc32, f.x_compress_type, f.compressed_size))  # noqa: E501
            if commited:
                self.db.commit()

    @property
    def encrypted(self):
        try:
            con = connect(self.fn)
            con.execute('SELECT count(*) FROM sqlite_master;')
            con.close()
            return False
        except DatabaseError:
            con.close()
            return True

    def get_file(self, prog: str, file: str) -> File:
        with self._lock:
            cur = self.db.execute(
                'SELECT files.*, filetype.type, encrypted_files.key, encrypted_files.iv, encrypted_files.crc32, encrypted_files.compressed, encrypted_files.compressed_size FROM files LEFT JOIN filetype ON files.id=filetype.id LEFT JOIN encrypted_files ON files.id=encrypted_files.id WHERE program=? AND file=?;',  # noqa: E501
                (prog, file))
            for i in cur:
                return File(*i)

    def get_file_list(self, prog: str) -> List[str]:
        with self._lock:
            cur = self.db.execute('SELECT file FROM files WHERE program=?;',
                                  (prog,))
            li = []
            for i in cur:
                li.append(i[0])
            return li

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
            cur = self.db.execute('SELECT * FROM encrypted_files WHERE id=?;', (iid,))  # noqa: E501
            for i in cur:
                self.db.execute('DELETE FROM encrypted_files WHERE id=?;', (iid,))  # noqa: E501
                break
            self.db.commit()

    def set_file(self, id: int, size: int, hash: str):
        with self._lock:
            self.db.execute('UPDATE files SET size=?, hash=? WHERE id=?;',
                            (size, hash, id))
            self.db.commit()

    def set_file_encrypt_information(self, id: int, stats: EncryptStats):
        if stats is not None and not isinstance(stats, EncryptStats):
            raise TypeError(f"Expected EncryptStats, got {type(stats)}")
        with self._lock:
            if stats is None:
                self.db.execute('DELETE FROM encrypted_files WHERE id=?;', (id,))  # noqa: E501
            else:
                cur = self.db.execute('SELECT * FROM encrypted_files WHERE id=?;', (id,))  # noqa: E501
                have_data = False
                for _ in cur:
                    have_data = True
                if have_data:
                    self.db.execute('UPDATE encrypted_files SET key=?, iv=?, crc32=?, compressed=?, compressed_size=? WHERE id=?;', (stats.key, stats.iv, stats.crc32, stats.compress_type.value if stats.compressed else None, stats.compressed_size if stats.compressed else None, id))  # noqa: E501
                else:
                    self.db.execute('INSERT INTO encrypted_files VALUES (?, ?, ?, ?, ?, ?);', (id, stats.key, stats.iv, stats.crc32, stats.compress_type.value if stats.compressed else None, stats.compressed_size if stats.compressed else None))  # noqa: E501
            self.db.commit()
