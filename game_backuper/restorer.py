from threading import Thread
from game_backuper.config import Config, Program, ConfigPath, ConfigOLeveldb
from game_backuper.db import Db
from os.path import join, relpath, isabs, isfile, isdir, exists
from game_backuper.file import (
    list_all_paths,
    copy_file,
    remove_dirs,
    new_file,
    mkdir_for_file,
)
from os import remove
from game_backuper.filetype import FileType


class RestoreTask(Thread):
    def __init__(self, prog: Program, db: Db, cfg: Config):
        Thread.__init__(self, name=f"Restore_{prog.name}")
        self.cfg = cfg
        self.prog = prog
        self.db = db

    def run(self):
        b = self.prog.base
        prog = self.prog.name
        li = self.db.get_file_list(prog)
        cli = self.prog.all_configs
        pl = list_all_paths(b, cli)
        for fn in li:
            f = self.db.get_file(prog, fn)
            r = self.prog.get_config(fn)
            if isinstance(r, ConfigPath):
                if f.type is not None:
                    raise ValueError('Type dismatched.')
                nam = r.real_name
                src = join(self.cfg.dest, prog, fn)
                tmp = relpath(fn, nam)
                if isabs(r.path):
                    dest = r.path
                else:
                    dest = join(b, r.path)
                if not tmp.startswith('.'):
                    dest = join(dest, tmp)
                if dest in pl:
                    pl.remove(dest)
                if not exists(src):
                    print(f'{prog}: Warn: Can not find backup files: "{src}"({fn})')  # noqa: E501
                    continue
                if exists(dest):
                    tf = new_file(dest, nam, prog)
                    if tf.size == f.size and tf.hash == f.hash:
                        print(f'{prog}: Skip {fn}')
                        continue
                copy_file(src, dest, nam, prog)
            elif isinstance(r, ConfigOLeveldb):
                from game_backuper.leveldb import have_leveldb
                if not have_leveldb:
                    raise NotImplementedError('Leveldb is not supported.')
                if f.type != FileType.LEVELDB:
                    raise ValueError('Type dismatched.')
                nam = r.real_name
                src = join(self.cfg.dest, prog, fn + '.db')
                if isabs(r.path):
                    dest = r.path
                else:
                    dest = join(b, r.path)
                if dest in pl:
                    pl.remove(dest)
                if not exists(src):
                    print(f'{prog}: Warn: Can not find backup files: "{src}"({fn})')  # noqa: E501
                    continue
                from game_backuper.leveldb import (
                    sqlite_to_leveldb,
                    leveldb_stats,
                    list_leveldb_entries,
                )
                if exists(dest):
                    ents = list_leveldb_entries(dest, r.domains)
                    stat = leveldb_stats(dest, ents)
                    if f.size == stat.size and f.hash == stat.hash:
                        print(f'{prog}: Skip {fn}')
                        continue
                mkdir_for_file(dest)
                sqlite_to_leveldb(src, dest, r.domains)
                print(f'{prog}: Covert leveldb done. {src}({fn}) -> {dest}')
        for i in pl:
            if isfile(i):
                remove(i)
                print(f'{prog}: Removed {i}')
            elif isdir(i):
                remove_dirs(i)
                print(f'{prog}: Removed {i}')