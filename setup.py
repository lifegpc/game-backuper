# flake8: noqa
import sys
from game_backuper import __version__
if "py2exe" in sys.argv:
    from distutils.core import setup
    import py2exe
    params = {
        "console": [{
            'script': "game_backuper/__main__.py",
            "dest_base": 'game-backuper',
            'version': __version__,
            'product_name': 'game-backuper',
            'product_version': __version__,
            'company_name': 'lifegpc',
            'description': 'A game backuper',
        }],
        "options": {
            "py2exe": {
                "optimize": 2,
                "compressed": 1,
                "excludes": ["pydoc"]
            }
        },
        "zipfile": None,
    }
else:
    from setuptools import setup
    params = {
        "install_requires": ["pyyaml"],
        'entry_points': {
            'console_scripts': ['game-backuper = game_backuper:start']
        },
        "extras_require": {
            "leveldb": "plyvel"
        },
        "python_requires": ">=3.6"
    }
setup(
    name="game-backuper",
    version=__version__,
    url="https://github.com/lifegpc/game-backuper",
    author="lifegpc",
    author_email="g1710431395@gmail.com",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.7",
    ],
    license="GNU General Public License v3 or later",
    description="A game backuper",
    long_description="A game backuper",
    keywords="backup",
    packages=["game_backuper"],
    **params
)
