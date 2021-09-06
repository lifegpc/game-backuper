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

    @staticmethod
    def from_str(v: str) -> IntEnum:
        if isinstance(v, str):
            t = v.lower()
            if t == 'backup':
                return OptAction.BACKUP
            elif t == 'restore':
                return OptAction.RESTORE
        else:
            raise TypeError('Must be str.')


class Opts:
    config_file: str = DEFAULT_CONFIG
    action = OptAction.BACKUP
    programs_list = None

    def __init__(self, cml: List[str]):
        try:
            r = getopt(cml, 'hc:', [])
            for i in r[0]:
                if i[0] == '-h':
                    self.print_help()
                    import sys
                    sys.exit(0)
                elif i[0] == '-c':
                    self.config_file = i[1]
            if len(r[1]) > 0:
                cm = r[1]
                re = OptAction.from_str(cm[0])
                if re is not None:
                    self.action = re
                li = cm if re is None else cm[1:]
                if len(li) > 0:
                    self.programs_list = li
        except GetoptError:
            from traceback import print_exc
            print_exc()
            import sys
            sys.exit(-1)

    def print_help(self):
        print('''game-backuper [options] [backup|restore] [game names]''')
