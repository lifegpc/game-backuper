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
    hydrate_file_if_needed,
)
from os import remove, close
from game_backuper.filetype import FileType
from game_backuper.compress import CompressConfig, decompress
from game_backuper.enc import decrypt_file
from tempfile import mkstemp


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
                if f.encrypted:
                    src = join(self.cfg.dest, '.encrypt', prog, fn)
                    if not exists(src):
                        src = join(self.cfg.dest, '.encrypt', '.id', str(f.id))  # noqa: E501
                else:
                    src = join(self.cfg.dest, prog, fn)
                c = r.compress_config
                tmp = relpath(fn, nam)
                if isabs(r.path):
                    dest = r.path
                else:
                    dest = join(b, r.path)
                if not tmp.startswith('.'):
                    dest = join(dest, tmp)
                if dest in pl:
                    pl.remove(dest)
                if not f.encrypted and ((c is None and not exists(src)) or (c is not None and not exists(src + c.ext))):  # noqa: E501
                    print(f'{prog}: Warn: Can not find backup files: "{src}"({fn})')  # noqa: E501
                    continue
                elif f.encrypted and not exists(src):
                    print(f'{prog}: Warn: Can not find backup files: "{src}"({fn})')  # noqa: E501
                    continue
                if exists(dest):
                    tf = new_file(dest, fn, prog)
                    if tf.size == f.size and tf.hash == f.hash:
                        print(f'{prog}: Skip {fn}')
                        continue
                if f.encrypted:
                    decrypt_file(src, dest, f, fn, prog, CompressConfig(f.compressed_type.to_str()) if f.compressed else None)  # noqa: E501
                elif c is None:
                    hydrate_file_if_needed(src)
                    copy_file(src, dest, fn, prog)
                else:
                    decompress(src, dest, c, fn, prog)
            elif isinstance(r, ConfigOLeveldb):
                from game_backuper.leveldb import have_leveldb
                if not have_leveldb:
                    raise NotImplementedError('Leveldb is not supported.')
                if f.type != FileType.LEVELDB:
                    raise ValueError('Type dismatched.')
                nam = r.real_name
                if f.encrypted:
                    src = join(self.cfg.dest, '.encrypt', prog, fn + '.db')
                    if not exists(src):
                        src = join(self.cfg.dest, '.encrypt', '.id', str(f.id))  # noqa: E501
                else:
                    src = join(self.cfg.dest, prog, fn + '.db')
                c = r.compress_config
                if isabs(r.path):
                    dest = r.path
                else:
                    dest = join(b, r.path)
                if dest in pl:
                    pl.remove(dest)
                if not f.encrypted and ((c is None and not exists(src)) or (c is not None and not exists(src + c.ext))):  # noqa: E501
                    print(f'{prog}: Warn: Can not find backup files: "{src}"({fn})')  # noqa: E501
                    continue
                elif f.encrypted and not exists(src):
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
                if f.encrypted:
                    tmp = mkstemp()
                    close(tmp[0])
                    tmp = tmp[1]
                    decrypt_file(src, tmp, f, fn, prog, CompressConfig(f.compressed_type.to_str()) if f.compressed else None)  # noqa: E501
                    sqlite_to_leveldb(tmp, dest, r.domains)
                    print(f'{prog}: Convert leveldb done. {tmp}({fn}) -> {dest}')  # noqa: E501
                    remove(tmp)
                    print(f'{prog}: Removed temp file {tmp}')
                elif c is None:
                    hydrate_file_if_needed(src)
                    sqlite_to_leveldb(src, dest, r.domains)
                    print(f'{prog}: Convert leveldb done. {src}({fn}) -> {dest}')  # noqa: E501
                else:
                    tmp = mkstemp()
                    close(tmp[0])
                    tmp = tmp[1]
                    decompress(src, tmp, c, fn, prog)
                    sqlite_to_leveldb(tmp, dest, r.domains)
                    print(f'{prog}: Convert leveldb done. {tmp}({fn}) -> {dest}')  # noqa: E501
                    remove(tmp)
                    print(f'{prog}: Removed tempfile {tmp}')
        for i in pl:
            if isfile(i):
                remove(i)
                print(f'{prog}: Removed {i}')
            elif isdir(i):
                remove_dirs(i)
                print(f'{prog}: Removed {i}')
