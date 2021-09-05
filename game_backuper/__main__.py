from game_backuper.config import Config
from game_backuper.cml import Opts
from game_backuper.db import Db
from game_backuper.backuper import Backuper


def main(cm=None):
    if cm is None:
        import sys
        cm = sys.argv[1:]
    cml = Opts(cm)
    cfg = Config(cml.config_file)
    db = Db(cfg.dest)
    bk = Backuper(db, cfg, cml)
    return bk.run()


if __name__ == "__main__":
    from game_backuper import start
    start()
