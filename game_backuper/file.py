from collections import namedtuple
from os.path import exists, dirname, abspath, isfile, isdir, join, isabs
from os import stat, makedirs, listdir, remove
from game_backuper.hashl import sha512
from shutil import copy2
from game_backuper.filetype import FileType
from platform import system
if system() == "Windows":
    try:
        from game_backuper.cfapi import hydrate_file, unpin_file
        have_cfapi = True
    except Exception:
        have_cfapi = False
else:
    have_cfapi = False


_File = namedtuple('File', ['id', 'file', 'size', 'program', 'hash', 'type', 'key', 'iv', 'crc32', 'x_compress_type', 'compressed_size'])  # noqa: E501


class File(_File):
    @property
    def encrypted(self):
        return bool(self.key and self.iv and self.crc32)

    @property
    def compressed(self):
        return self.x_compress_type is not None

    @property
    def compressed_type(self):
        from game_backuper.compress import CompressMethod
        return CompressMethod(self.x_compress_type) if self.compressed else None  # noqa: E501

    @property
    def encrypt_file_size(self):
        return self.compressed_size if self.compressed_size else self.size

    @classmethod
    def from_encrypt_stats(cls, stats, file):
        from game_backuper.enc import EncryptStats
        if not isinstance(stats, EncryptStats):
            raise TypeError(f'Expected EncryptStats, got {type(stats)}')
        if not isinstance(file, (File, _File)):
            raise TypeError(f'Expected File, got {type(file)}')
        return cls(file.id, file.file, file.size, file.program, file.hash, file.type, stats.key, stats.iv, stats.crc32, stats.x_compress_type, stats.compressed_size)  # noqa: E501

    @classmethod
    def from_leveldb_stats(cls, stats):
        from game_backuper.leveldb import LeveldbStats
        if not isinstance(stats, LeveldbStats):
            raise TypeError(f'Expected LeveldbStats, got {type(stats)}')
        return cls(None, None, stats.size, None, stats.hash, None, None, None, None, None, None)  # noqa: E501


def mkdir_for_file(p: str):
    d = dirname(abspath(p))
    if not exists(d):
        makedirs(d)


def copy_file(loc: str, dest: str, name: str, prog: str):
    mkdir_for_file(dest)
    r = copy2(loc, dest)
    print(f'{prog}: Copyed {loc}({name}) -> {r}')


def listdirs(loc: str, ignore_hidden_files: bool = True):
    bl = listdir(loc)
    r = []
    for i in bl:
        if i.startswith('.'):
            if ignore_hidden_files or i == '.' or i == '..':
                continue
        p = join(loc, i)
        if isfile(p):
            r.append(p)
        elif isdir(p):
            r += listdirs(p)
    return r


def list_all_paths(base: str, cli):
    from game_backuper.config import ConfigPath, ConfigOLeveldb
    r = []
    for c in cli:
        if isinstance(c, ConfigPath):
            if isabs(c.path):
                bp = c.path
            else:
                bp = join(base, c.path)
            if isfile(bp):
                r.append(bp)
            elif isdir(bp):
                re = listdirs(bp, c.ignore_hidden_files)
                for ii in re:
                    if c.is_exclude(bp, ii):
                        continue
                    if not c.is_include(bp, ii):
                        continue
                    r.append(ii)
        elif isinstance(c, ConfigOLeveldb):
            r.append(c.path if isabs(c.path) else join(base, c.path))
    return r


def new_file(loc: str, name: str, prog: str, type: FileType = None) -> File:
    if exists(loc):
        fs = stat(loc).st_size
        with open(loc, 'rb') as f:
            hs = sha512(f)
        return File(None, name, fs, prog, hs, type, None, None, None, None, None)  # noqa: E501


def remove_dirs(loc: str):
    bl = listdirs(loc, False)
    for i in bl:
        if isfile(i):
            remove(i)
        elif isdir(i):
            try:
                remove_dirs(i)
            except Exception:
                remove_dirs(i)
    remove(loc)


def remove_compress_files(loc: str, prog: str, name: str, ext: str = None):
    from game_backuper.compress import supported_exts
    exts = supported_exts.copy()
    if ext is not None:
        exts.remove(ext)
        exts.append('')
    for i in exts:
        f = loc + i
        if exists(f) and isfile(f):
            remove(f)
            print(f'{prog}: Removed {f}({name})')


def hydrate_file_if_needed(fn: str):
    if not have_cfapi:
        return
    if exists(fn):
        hydrate_file(fn)


def remove_unencryped_files(loc: str, prog: str, name: str):
    if exists(loc):
        remove(loc)
        print(f'{prog}: Removed {loc}({name})')
    remove_compress_files(loc, prog, name)


def unpin_file_if_needed(fn: str):
    if not have_cfapi:
        return
    if exists(fn):
        unpin_file(fn)
