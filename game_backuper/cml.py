from getopt import getopt, GetoptError
from typing import List
from platform import system
if system() == "Windows":
    import os
    DEFAULT_CONFIG = f'{os.environ["APPDATA"]}\\game-backuper.yaml'
else:
    DEFAULT_CONFIG = '/etc/game-backuper.yaml'


class Opts:
    config_file: str = DEFAULT_CONFIG

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
        except GetoptError:
            from traceback import print_exc
            print_exc()
            import sys
            sys.exit(-1)

    def print_help(self):
        print('''game-backuper [options] [game names]''')
