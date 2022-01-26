from getopt import getopt, GetoptError
from typing import List
from platform import system
from enum import IntEnum, unique
if system() == "Windows":
    import os
    DEFAULT_CONFIG = f'{os.environ["APPDATA"]}\\game-backuper.yaml'
else:
    DEFAULT_CONFIG = '/etc/game-backuper.yaml'


@unique
class OptAction(IntEnum):
    BACKUP = 0
    RESTORE = 1
    LIST = 2
    LIST_LEVELDB_KEY = 3

    @staticmethod
    def from_str(v: str) -> IntEnum:
        if isinstance(v, str):
            t = v.lower()
            if t == 'backup':
                return OptAction.BACKUP
            elif t == 'restore':
                return OptAction.RESTORE
            elif t == 'list':
                return OptAction.LIST
            elif t == 'list_leveldb_key':
                return OptAction.LIST_LEVELDB_KEY
        else:
            raise TypeError('Must be str.')


class Opts:
    config_file: str = DEFAULT_CONFIG
    action = OptAction.BACKUP
    programs_list = None
    optimize_db = False
    change_key = False

    def __init__(self, cml: List[str]):
        try:
            r = getopt(cml, 'hc:', ['help', 'config=', 'optimize-db',
                                    'change-key'])
            for i in r[0]:
                if i[0] == '-h' or i[0] == '--help':
                    self.print_help()
                    import sys
                    sys.exit(0)
                elif i[0] == '-c' or i[0] == '--config':
                    self.config_file = i[1]
                elif i[0] == '--optimize-db':
                    self.optimize_db = True
                elif i[0] == '--change-key':
                    self.change_key = True
            if len(r[1]) > 0:
                cm = r[1]
                re = OptAction.from_str(cm[0])
                if re is not None:
                    self.action = re
                    if re == OptAction.LIST:
                        return
                    elif re == OptAction.LIST_LEVELDB_KEY:
                        if len(cm) == 1:
                            raise GetoptError('list_leveldb_key need at least one db_path.')  # noqa: E501
                        self.programs_list = cm[1:]
                        return
                li = cm if re is None else cm[1:]
                if len(li) > 0:
                    self.programs_list = li
        except GetoptError:
            from traceback import print_exc
            print_exc()
            import sys
            sys.exit(-1)

    def print_help(self):
        print('''game-backuper [options] [backup|restore] [<game names> [...]]
game-backuper [options] list
game-backuper [options] list_leveldb_key [<db_path> [...]]
Options:
    -h, --help          Print help message.
    -c, --config <path> Set config file.
    --optimize-db       Optimize the sqlite3 database
    --change-key        Change encrypt password''')
