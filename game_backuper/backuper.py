from game_backuper.db import Db
from game_backuper.config import (
    Config,
    Program,
    ConfigNormalFile,
    ConfigLeveldb,
)
from game_backuper.cml import Opts, OptAction
from threading import Thread
from os.path import exists, join, isdir
from os import mkdir, remove
from game_backuper.file import new_file, copy_file, File, mkdir_for_file
from game_backuper.filetype import FileType
from game_backuper.restorer import RestoreTask
from game_backuper.file import remove_compress_files
from game_backuper.compress import compress


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
        fl = self.db.get_file_list(prog)
        for f in self.prog.files:
            if isinstance(f, ConfigNormalFile):
                if exists(f[1]):
                    if f.name in fl:
                        fl.remove(f.name)
                    c = f.compress_config
                    ori = self.db.get_file(prog, f[0])
                    nf = new_file(f[1], f[0], prog)
                    if nf is None:
                        continue
                    de = join(bp, f[0])
                    if ori is not None:
                        if ori.size == nf.size and ori.hash == nf.hash:
                            if c is None:
                                if exists(de):
                                    print(f'{prog}: Skip {f[0]}.')
                                    remove_compress_files(de, prog, f.name)
                                    continue
                            else:
                                if exists(de + c.ext):
                                    print(f'{prog}: Skip {f.name}.')
                                    remove_compress_files(de, prog, f.name, c.ext)  # noqa: E501
                                    continue
                        if c is None:
                            copy_file(f[1], de, f[0], prog)
                            remove_compress_files(de, prog, f.name)
                        else:
                            compress(f[1], de, c, f.name, prog)
                        self.db.set_file(ori.id, nf.size, nf.hash)
                    else:
                        if c is None:
                            copy_file(f[1], de, f[0], prog)
                            remove_compress_files(de, prog, f.name)
                        else:
                            compress(f[1], de, c, f.name, prog)
                        self.db.add_file(nf)
            elif isinstance(f, ConfigLeveldb):
                from game_backuper.leveldb import have_leveldb
                if not have_leveldb:
                    raise NotImplementedError('Leveldb is not supported.')
                if not exists(f.full_path):
                    continue
                if f.name in fl:
                    fl.remove(f.name)
                from game_backuper.leveldb import (
                    list_leveldb_entries,
                    leveldb_stats,
                    leveldb_to_sqlite,
                )
                ent = list_leveldb_entries(f.full_path, f.domains)
                stats = leveldb_stats(f.full_path, ent)
                ori = self.db.get_file(prog, f.name)
                de = join(bp, f.name + ".db")
                if ori is not None:
                    if ori.size == stats.size and ori.hash == stats.hash:
                        print(f'{prog}: Skip {f[0]}')
                        continue
                    if ori.type is None or ori.type != FileType.LEVELDB:
                        pp = join(bp, ori.file)
                        if exists(pp):
                            remove(pp)
                        self.db.remove_file(ori)
                        ori = None
                if exists(de):
                    remove(de)
                mkdir_for_file(de)
                leveldb_to_sqlite(f.full_path, de, ent)
                print(f'{prog}: Covert leveldb done. {f.full_path}({f.name}) -> {de}')  # noqa: E501
                if ori is None:
                    nf = File(None, f.name, stats.size, prog, stats.hash,
                              FileType.LEVELDB)
                    self.db.add_file(nf)
                else:
                    self.db.set_file(ori.id, stats.size, stats.hash)
        for fn in fl:
            f = self.db.get_file(prog, fn)
            if f.type is None:
                de = join(bp, fn)
                if exists(de):
                    remove(de)
                    print(f'{prog}: Remove {de}({fn})')
                self.db.remove_file(f)
            if f.type == FileType.LEVELDB:
                de = join(bp, fn + '.db')
                if exists(de):
                    remove(de)
                    print(f'{prog}: Remove {de}({fn})')
                self.db.remove_file(f)


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
        elif self.opts.action == OptAction.LIST:
            print(prog.name)
        elif self.opts.action == OptAction.RESTORE:
            t = RestoreTask(prog, self.db, self.conf)
            self.tasks.append(t)
            t.start()

    def run(self):
        if self.opts.action == OptAction.LIST_LEVELDB_KEY:
            from game_backuper.leveldb import have_leveldb
            if not have_leveldb:
                raise NotImplementedError('Leveldb is not supported.')
            from game_backuper.leveldb import list_leveldb_entries
            for db in self.opts.programs_list:
                if exists(db):
                    if isdir(db):
                        print(f'Keys in "{db}":')
                        for i in list_leveldb_entries(db):
                            print(i)
                    else:
                        raise FileExistsError(f'"{db}" should be a directory.')
                else:
                    raise FileNotFoundError(f'Can not find "{db}"')
        elif self.opts.programs_list is None:
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
