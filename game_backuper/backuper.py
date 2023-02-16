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
from os import remove, close
from shutil import move
from game_backuper.file import new_file, copy_file, File, mkdir_for_file
from game_backuper.filetype import FileType
from game_backuper.restorer import RestoreTask
from game_backuper.file import remove_compress_files, remove_unencryped_files
from game_backuper.compress import compress
from game_backuper.enc import encrypt_file
from tempfile import mkstemp


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
        ebp = join(self.cfg.dest, '.encrypt', prog)
        ebpi = join(self.cfg.dest, '.encrypt', '.id')
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
                    de = join(ebp if f.encrypt_files else bp, f[0])
                    if ori is not None:
                        de2 = join(ebpi if f.encrypt_files else bp, str(ori.id))  # noqa: E501
                        if f.protect_filename:
                            if not exists(de2) and exists(de):
                                mkdir_for_file(de2)
                                move(de, de2)
                                print(f'{prog}: Renamed {de} -> {de2}.')
                            de = de2
                        else:
                            if not exists(de) and exists(de2):
                                mkdir_for_file(de)
                                move(de2, de)
                                print(f'{prog}: Renamed {de2} -> {de}.')
                        if ori.size == nf.size and ori.hash == nf.hash:
                            if c is None:
                                if exists(de) and not f.encrypt_files:
                                    print(f'{prog}: Skip {f[0]}.')
                                    remove_compress_files(de, prog, f.name)
                                    self.remove_encrypted_file(join(ebp, f[0]), prog, f.name, ori)  # noqa: E501
                                    self.remove_encrypted_file(join(ebpi, str(ori.id)), prog, f.name, ori)  # noqa: E501
                                    continue
                                elif exists(de) and f.encrypt_files and not ori.compressed:  # noqa: E501
                                    print(f'{prog}: Skip {f[0]}.')
                                    remove_unencryped_files(join(bp, f[0]), prog, f.name)  # noqa: E501
                                    continue
                            else:
                                if not f.encrypt_files and exists(de + c.ext):
                                    print(f'{prog}: Skip {f.name}.')
                                    remove_compress_files(de, prog, f.name, c.ext)  # noqa: E501
                                    self.remove_encrypted_file(join(ebp, f[0]), prog, f.name, ori)  # noqa: E501
                                    self.remove_encrypted_file(join(ebpi, str(ori.id)), prog, f.name, ori)  # noqa: E501
                                    continue
                                elif f.encrypt_files and ori.compressed_type == c.method:  # noqa: E501
                                    print(f'{prog}: Skip {f.name}.')
                                    remove_unencryped_files(join(bp, f.name), prog, f.name)  # noqa: E501
                                    continue
                        stats = None
                        if f.encrypt_files:
                            stats = encrypt_file(f[1], de, nf, f.name, prog, c)
                            remove_unencryped_files(join(bp, f[0]), prog, f.name)  # noqa: E501
                        elif c is None:
                            copy_file(f[1], de, f[0], prog)
                            remove_compress_files(de, prog, f.name)
                            self.remove_encrypted_file(join(ebp, f[0]), prog, f.name, ori)  # noqa: E501
                            self.remove_encrypted_file(join(ebpi, str(ori.id)), prog, f.name, ori)  # noqa: E501
                        else:
                            compress(f[1], de, c, f.name, prog)
                            self.remove_encrypted_file(join(ebp, f[0]), prog, f.name, ori)  # noqa: E501
                            self.remove_encrypted_file(join(ebpi, str(ori.id)), prog, f.name, ori)  # noqa: E501
                        self.db.set_file(ori.id, nf.size, nf.hash)
                        self.db.set_file_encrypt_information(ori.id, stats)
                    else:
                        if f.protect_filename:
                            self.db.add_file(nf, False)
                            tmpori = self.db.get_file(prog, f[0])
                            de = join(ebpi if f.encrypt_files else bp, str(tmpori.id))  # noqa: E501
                        if f.encrypt_files:
                            s = encrypt_file(f[1], de, nf, f.name, prog, c)
                            nf = File.from_encrypt_stats(s, nf)
                            remove_unencryped_files(join(bp, f[0]), prog, f.name)  # noqa: E501
                        elif c is None:
                            copy_file(f[1], de, f[0], prog)
                            remove_compress_files(de, prog, f.name)
                            self.remove_encrypted_file(join(ebp, f[0]), prog, f.name, ori)  # noqa: E501
                        else:
                            compress(f[1], de, c, f.name, prog)
                            self.remove_encrypted_file(join(ebp, f[0]), prog, f.name, ori)  # noqa: E501
                        if f.protect_filename:
                            self.db.set_file_encrypt_information(tmpori.id, s)
                        else:
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
                c = f.compress_config
                de = join(ebp if f.encrypt_files else bp, f.name + ".db")
                if ori is not None:
                    de2 = join(ebpi if f.encrypt_files else bp, str(ori.id))  # noqa: E501
                    if f.protect_filename:
                        if not exists(de2) and exists(de):
                            mkdir_for_file(de2)
                            move(de, de2)
                            print(f'{prog}: Renamed {de} -> {de2}.')
                        de = de2
                    else:
                        if not exists(de) and exists(de2):
                            mkdir_for_file(de)
                            move(de2, de)
                            print(f'{prog}: Renamed {de2} -> {de}.')
                    if ori.type is None or ori.type != FileType.LEVELDB:
                        pp = join(bp, ori.file)
                        if exists(pp):
                            remove(pp)
                        remove_compress_files(pp, prog, f.name)
                        self.remove_encrypted_file(join(ebp, ori.file), prog, f.name, ori)  # noqa: E501
                        self.remove_encrypted_file(join(ebpi, str(ori.id)), prog, f.name, ori)  # noqa: E501
                        self.db.remove_file(ori)
                        ori = None
                if ori is not None:
                    if ori.size == stats.size and ori.hash == stats.hash:
                        if c is None:
                            if exists(de) and not f.encrypt_files:
                                print(f'{prog}: Skip {f[0]}.')
                                remove_compress_files(de, prog, f.name)
                                self.remove_encrypted_file(join(ebp, f[0] + '.db'), prog, f.name, ori)  # noqa: E501
                                self.remove_encrypted_file(join(ebpi, str(ori.id)), prog, f.name, ori)  # noqa: E501
                                continue
                            elif exists(de) and f.encrypt_files and not ori.compressed:  # noqa: E501
                                print(f'{prog}: Skip {f[0]}.')
                                remove_unencryped_files(join(bp, f[0] + '.db'), prog, f.name)  # noqa: E501
                                continue
                        else:
                            if not f.encrypt_files and exists(de + c.ext):
                                print(f'{prog}: Skip {f.name}.')
                                remove_compress_files(de, prog, f.name, c.ext)
                                self.remove_encrypted_file(join(ebp, f[0] + '.db'), prog, f.name, ori)  # noqa: E501
                                self.remove_encrypted_file(join(ebpi, str(ori.id)), prog, f.name, ori)  # noqa: E501
                                continue
                            elif f.encrypt_files and ori.compressed_type == c.method:  # noqa: E501
                                print(f'{prog}: Skip {f.name}.')
                                remove_unencryped_files(join(bp, f.name + '.db'), prog, f.name)  # noqa: E501
                                continue
                if f.protect_filename:
                    ori = self.db.get_file(prog, f[0])
                    if ori is None:
                        nf = File(None, f.name, 0, prog, None, FileType.LEVELDB, None, None, None, None, None)  # noqa: E501
                        self.db.add_file(nf, False)
                        ori = self.db.get_file(prog, f[0])
                    de = join(ebpi if f.encrypt_files else bp, str(ori.id))  # noqa: E501
                mkdir_for_file(de)
                st = None
                if c is None and not f.encrypt_files:
                    leveldb_to_sqlite(f.full_path, de, ent)
                    print(f'{prog}: Covert leveldb done. {f.full_path}({f.name}) -> {de}')  # noqa: E501
                    remove_compress_files(de, prog, f.name)
                    self.remove_encrypted_file(join(ebp, f[0] + '.db'), prog, f.name, ori)  # noqa: E501
                    self.remove_encrypted_file(join(ebpi, str(ori.id)), prog, f.name, ori)  # noqa: E501
                else:
                    tmp = mkstemp()
                    close(tmp[0])
                    tmp = tmp[1]
                    leveldb_to_sqlite(f.full_path, tmp, ent)
                    print(f'{prog}: Covert leveldb done. {f.full_path}({f.name}) -> {tmp}')  # noqa: E501
                    if f.encrypt_files:
                        st = encrypt_file(tmp, de, File.from_leveldb_stats(stats), f.name, prog, c)  # noqa: E501
                        remove_unencryped_files(join(bp, f[0] + '.db'), prog, f.name)  # noqa: E501
                    else:
                        compress(tmp, de, c, f.name, prog)
                        self.remove_encrypted_file(join(ebp, f[0] + '.db'), prog, f.name, ori)  # noqa: E501
                        self.remove_encrypted_file(join(ebpi, str(ori.id)), prog, f.name, ori)  # noqa: E501
                    remove(tmp)
                    print(f'{prog}: Removed tempfile {tmp}')
                if ori is None:
                    nf = File(None, f.name, stats.size, prog, stats.hash,
                              FileType.LEVELDB, None, None, None, None, None)
                    if st:
                        nf = File.from_encrypt_stats(st, nf)
                    self.db.add_file(nf)
                else:
                    self.db.set_file(ori.id, stats.size, stats.hash)
                    self.db.set_file_encrypt_information(ori.id, st)
        for fn in fl:
            f = self.db.get_file(prog, fn)
            if f.type is None:
                de = join(bp, fn)
                if exists(de):
                    remove(de)
                    print(f'{prog}: Remove {de}({fn})')
                remove_compress_files(de, prog, fn)
                self.remove_encrypted_file(join(ebp, fn), prog, fn, f)
                self.remove_encrypted_file(join(ebpi, str(f.id)), prog, fn, f)
                self.db.remove_file(f)
            if f.type == FileType.LEVELDB:
                de = join(bp, fn + '.db')
                if exists(de):
                    remove(de)
                    print(f'{prog}: Remove {de}({fn})')
                remove_compress_files(de, prog, fn + '.db')
                self.remove_encrypted_file(join(ebp, fn + '.db'), prog, fn, f)
                self.remove_encrypted_file(join(ebpi, str(f.id)), prog, fn, ori)  # noqa: E501
                self.db.remove_file(f)

    def remove_encrypted_file(self, loc: str, prog: str, name: str, f: File):
        if exists(loc):
            remove(loc)
            print(f'{prog}: Removed {loc}({name})')


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
