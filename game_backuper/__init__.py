from game_backuper.__main__ import main


def start():
    import sys
    try:
        sys.exit(main())
    except Exception:
        sys.exit(-1)
