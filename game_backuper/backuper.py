from game_backuper.db import Db
from game_backuper.config import Config, Program
from game_backuper.cml import Opts
from threading import Thread
from os.path import exists, join
from os import mkdir
from game_backuper.file import new_file, copy_file


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


class Backuper:
    def __init__(self, db: Db, config: Config, opts: Opts):
        self.db = db
        self.conf = config
        self.opts = opts
        self.tasks = []

    def run(self):
        for prog in self.conf.progs:
            t = BackupTask(prog, self.db, self.conf)
            self.tasks.append(t)
            t.start()
        self.wait()
        return 0

    def wait(self):
        for task in self.tasks:
            task.join()
