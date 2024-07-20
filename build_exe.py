from version import version, dversion
from py2exe import freeze

freeze(
    console=[{
        'script': "game_backuper/__main__.py",
        "dest_base": 'game-backuper',
        'version_info': {
            'version': version,
            'product_name': 'game-backuper',
            'product_version': dversion,
            'company_name': 'lifegpc',
            'description': 'A game backuper',
            'copyright': 'Copyright (C) 2021-2024 lifegpc'
        },
    }],
    options={
        "optimize": 2,
        "compressed": 1,
        "excludes": ["doctest", "pydoc", "unittest"],
        "includes": ["cryptography.utils", "_cffi_backend", "sqlite3.dump"]
    },
    zipfile=None,
)
