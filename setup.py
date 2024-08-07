# flake8: noqa
import sys
from version import version
from setuptools import setup, Extension
try:
    from Cython.Build import cythonize
except ImportError:
    def cythonize(li):
        return []

ext_modules = []
if '--without-pcre2' in sys.argv:
    sys.argv.remove('--without-pcre2')
else:
    ext_modules.append(Extension("game_backuper._pcre2", ["game_backuper/_pcre2.pyx"], libraries=["pcre2-8"]))
if '--without-zstd' in sys.argv:
    sys.argv.remove('--without-zstd')
else:
    ext_modules.append(Extension("game_backuper._zstd", ["game_backuper/_zstd.pyx"], libraries=["zstd"]))

setup(
    name="game-backuper",
    version=version,
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
    ext_modules=cythonize(ext_modules, compiler_directives={'language_level': "3"}),
    install_requires=["pyyaml"],
    entry_points={
        'console_scripts': ['game-backuper = game_backuper:start']
    },
    extras_require={
        "leveldb": "plyvel",
        "lzip": "lzip",
        "snappy": "python-snappy",
        "brotli": "brotli",
    },
    python_requires=">=3.6"
)
