from collections import namedtuple
from os.path import exists, dirname, abspath, isfile, isdir, join, isabs
from os import stat, makedirs, listdir
from game_backuper.hashl import sha512
from shutil import copy2
from game_backuper.filetype import FileType
from os import remove
from game_backuper.compress import supported_exts


File = namedtuple('File', ['id', 'file', 'size', 'program', 'hash', 'type'])


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
                r += listdirs(bp, c.ignore_hidden_files)
        elif isinstance(c, ConfigOLeveldb):
            r.append(c.path if isabs(c.path) else join(base, c.path))
    return r


def new_file(loc: str, name: str, prog: str, type: FileType = None) -> File:
    if exists(loc):
        fs = stat(loc).st_size
        with open(loc, 'rb') as f:
            hs = sha512(f)
        return File(None, name, fs, prog, hs, type)


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
    exts = supported_exts.copy()
    if ext is not None:
        exts.remove(ext)
        exts.append('')
    for i in exts:
        f = loc + i
        if exists(f) and isfile(f):
            remove(f)
            print(f'{prog}: Removed {f}({name})')
