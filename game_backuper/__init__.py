from game_backuper.main import main


def start():
    import sys
    try:
        sys.exit(main())
    except Exception:
        sys.exit(-1)
