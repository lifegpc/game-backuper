from game_backuper.config import Config
from game_backuper.cml import Opts, OptAction
from game_backuper.db import Db
from game_backuper.backuper import Backuper
from os import makedirs
from os.path import exists


def main(cm=None):
    if cm is None:
        import sys
        cm = sys.argv[1:]
    cml = Opts(cm)
    if cml.action == OptAction.VERSION:
        from game_backuper.compress import (
            have_brotli,
            have_bz2,
            have_gzip,
            have_lzip,
            have_lzma,
            have_snappy,
            have_zstd,
        )
        from game_backuper.leveldb import have_leveldb
        from game_backuper.regexp import have_pcre2
        print("Brotli support:", have_brotli)
        print("BZip2 support:", have_bz2)
        print("GZip support:", have_gzip)
        print("LZip support:", have_lzip)
        print("LZMA support:", have_lzma)
        print("Snappy support:", have_snappy)
        print("ZSTD support:", have_zstd)
        print("LevelDB support:", have_leveldb)
        print("PCRE2 support:", have_pcre2)
        return 0
    cfg = Config(cml.config_file)
    if not exists(cfg.dest):
        makedirs(cfg.dest)
    db = Db(cfg, cml)
    bk = Backuper(db, cfg, cml)
    return bk.run()
