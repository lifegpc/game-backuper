from game_backuper.db import Db
from game_backuper.config import (
    Config,
    Program,
    ConfigNormalFile,
    ConfigLeveldb,
)
from game_backuper.cml import Opts, OptAction
from threading import Thread
from os.path import exists, join
from os import mkdir
from game_backuper.file import new_file, copy_file
from game_backuper.leveldb import have_leveldb
if have_leveldb:
    from game_backuper.leveldb import list_leveldb_entries


class BackupTask(Thread):
    def __init__(self, prog: Program, db: Db, cfg: Config):
        Thread.__init__(self, name=f"Backup_{prog.name}")
        self.cfg = cfg
        self.prog = prog
        self.db = db

    def run(self):
        self.prog.clear_cache()
        prog = self.prog.name
        bp = join(self.cfg.dest, prog)
        if not exists(bp):
            mkdir(bp)
        for f in self.prog.files:
            if isinstance(f, ConfigNormalFile):
                if exists(f[1]):
                    ori = self.db.get_file(prog, f[0])
                    nf = new_file(f[1], f[0], prog)
                    if nf is None:
                        continue
                    de = join(bp, f[0])
                    if ori is not None:
                        if ori.size == nf.size and ori.hash == nf.hash:
                            print(f'{prog}: Skip {f[0]}({f[1]}).')
                            continue
                        copy_file(f[1], de, f[0], prog)
                        self.db.set_file(ori.id, nf.size, nf.hash)
                    else:
                        copy_file(f[1], de, f[0], prog)
                        self.db.add_file(nf)
            elif isinstance(f, ConfigLeveldb):
                if not have_leveldb:
                    raise ValueError('Leveldb is not supported.')
                print(list_leveldb_entries(f.full_path, f.domains))


class Backuper:
    def __init__(self, db: Db, config: Config, opts: Opts):
        self.db = db
        self.conf = config
        self.opts = opts
        self.tasks = []

    def deal_prog(self, prog: Program):
        if self.opts.action == OptAction.BACKUP:
            t = BackupTask(prog, self.db, self.conf)
            self.tasks.append(t)
            t.start()

    def run(self):
        if self.opts.programs_list is None:
            for prog in self.conf.progs:
                self.deal_prog(prog)
        else:
            for n in self.opts.programs_list:
                if n not in self.conf.progs_name:
                    raise ValueError(f'Can not find "{n}" in config file.')
            for n in self.opts.programs_list:
                prog = self.conf.progs[self.conf.progs_name.index(n)]
                self.deal_prog(prog)
        self.wait()
        return 0

    def wait(self):
        for task in self.tasks:
            task.join()
