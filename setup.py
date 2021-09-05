# flake8: noqa
import sys
if len(sys.argv) == 2 and sys.argv[1] == "py2exe":
    from distutils.core import setup
    import py2exe
    params = {
        "console": [{
            'script': "game_backuper/__main__.py",
            "dest_base": 'game-backuper'
        }]
    }
else:
    from setuptools import setup
    params = {
        "install_requires": ["pyyaml"],
        'entry_points': {
            'console_scripts': ['game-backuper = game_backuper:main']
        }
    }
setup(
    name="game-backuper",
    version="1.0.0",
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
