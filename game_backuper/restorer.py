from threading import Thread
from game_backuper.config import Config, Program, ConfigPath
from game_backuper.db import Db
from os.path import join, relpath, isabs, isfile, isdir, exists
from game_backuper.file import (
    list_all_paths,
    copy_file,
    remove_dirs,
    new_file,
)
from os import remove


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
                nam = r.name if r.name else r.path
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
                if exists(dest):
                    tf = new_file(dest, nam, prog)
                    if tf.size == f.size and tf.hash == f.hash:
                        print(f'{prog}: Skip {f.file}')
                        continue
                copy_file(src, dest, nam, prog)
        for i in pl:
            if isfile(i):
                remove(i)
                print(f'{prog}: Removed {i}')
            elif isdir(i):
                remove_dirs(i)
                print(f'{prog}: Removed {i}')
