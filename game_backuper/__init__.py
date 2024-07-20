__version__ = "1.0.0"
import sys
from platform import system
if system() == 'Windows' and sys.version_info.minor > 7:
    from os import add_dll_directory, environ, getcwd
    from os.path import dirname, isdir
    add_dll_directory(dirname(sys.executable))
    add_dll_directory(getcwd())
    for i in environ['PATH'].split(";"):
        add_dll_directory(i)
    for i in sys.path:
        if isdir(i):
            add_dll_directory(i)


from game_backuper.main import main


def start():
    try:
        sys.exit(main())
    except Exception:
        from traceback import print_exc
        print_exc()
        sys.exit(-1)
