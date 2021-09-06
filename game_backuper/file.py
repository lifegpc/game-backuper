from collections import namedtuple
from os.path import exists, dirname, abspath, isfile, isdir, join
from os import stat, makedirs, listdir
from game_backuper.hashl import sha512
from shutil import copy2
from game_backuper.filetype import FileType


File = namedtuple('File', ['id', 'file', 'size', 'program', 'hash', 'type'])


def mkdir_for_file(p: str):
    d = dirname(abspath(p))
    if not exists(d):
        makedirs(d)


def copy_file(loc: str, dest: str, name: str, prog: str):
    mkdir_for_file(dest)
    r = copy2(loc, dest)
    print(f'{prog}: Copyed {loc}({name}) -> {r}')


def listdirs(loc: str):
    bl = listdir(loc)
    r = []
    for i in bl:
        if i.startswith('.'):
            continue
        p = join(loc, i)
        if isfile(p):
            r.append(p)
        elif isdir(p):
            r += listdirs(p)
    return r


def new_file(loc: str, name: str, prog: str, type: FileType = None) -> File:
    if exists(loc):
        fs = stat(loc).st_size
        with open(loc, 'rb') as f:
            hs = sha512(f)
        return File(None, name, fs, prog, hs, type)
