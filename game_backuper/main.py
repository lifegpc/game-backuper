from game_backuper.config import Config
from game_backuper.cml import Opts
from game_backuper.db import Db
from game_backuper.backuper import Backuper
from os import makedirs
from os.path import exists


def main(cm=None):
    if cm is None:
        import sys
        cm = sys.argv[1:]
    cml = Opts(cm)
    cfg = Config(cml.config_file)
    if not exists(cfg.dest):
        makedirs(cfg.dest)
    db = Db(cfg.dest, cml.optimize_db)
    bk = Backuper(db, cfg, cml)
    return bk.run()
