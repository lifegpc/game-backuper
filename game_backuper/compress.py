try:
    from bz2 import BZ2File
    have_bz2 = True
except ImportError:
    have_bz2 = False
try:
    from gzip import GzipFile
    have_gzip = True
except ImportError:
    have_gzip = False
try:
    from lzma import LZMAFile
    have_lzma = True
except ImportError:
    have_lzma = False
try:
    from lzip import (
        FileEncoder as LZIPFileEncoder,
        decompress_file_iter as LZIP_decompress_file_iter,
    )
    have_lzip = True
except ImportError:
    have_lzip = False
from enum import IntEnum, unique
try:
    from functools import cached_property
except ImportError:
    cached_property = property
from os.path import exists, isfile, getsize
from os import remove


@unique
class CompressMethod(IntEnum):
    BZIP2 = 0
    GZIP = 1
    LZMA = 2
    LZIP = 3

    @staticmethod
    def from_str(v: str) -> IntEnum:
        if isinstance(v, str):
            t = v.lower()
            if t == 'bzip2':
                return CompressMethod.BZIP2
            elif t == "gzip":
                return CompressMethod.GZIP
            elif t == "lzma":
                return CompressMethod.LZMA
            elif t == "lzip":
                return CompressMethod.LZIP
        else:
            raise TypeError('Must be str.')


class CompressConfig:
    def __init__(self, method: str, level: int = None):
        self._method = CompressMethod.from_str(method)
        if self._method is None:
            raise ValueError('Unknown compress method.')
        if self._method == CompressMethod.BZIP2:
            if not have_bz2:
                raise NotImplementedError("bzip2 not supported.")
            if level is None:
                self._level = 9
            else:
                if isinstance(level, int) and level >= 1 and level <= 9:
                    self._level = level
                else:
                    raise ValueError('bzip2: compress_level should be 1-9.')
            self._ext = ".bz2"
        elif self._method == CompressMethod.GZIP:
            if not have_gzip:
                raise NotImplementedError("gzip not supported.")
            if level is None:
                self._level = 9
            else:
                if isinstance(level, int) and level >= 0 and level <= 9:
                    self._level = level
                else:
                    raise ValueError('gzip: compress_level should be 0-9.')
            self._ext = '.gz'
        elif self._method == CompressMethod.LZMA:
            if not have_lzma:
                raise NotImplementedError("lzma not supported.")
            if level is None:
                self._level = 6
            else:
                if isinstance(level, int) and level >= 0 and level <= 9:
                    self._level = level
                else:
                    raise ValueError('lzma: compress_level should be 0-9.')
            self._ext = ".xz"
        elif self._method == CompressMethod.LZIP:
            if not have_lzip:
                raise NotImplementedError("lzip not supported.")
            if level is None:
                self._level = 6
            else:
                if isinstance(level, int) and level >= 0 and level <= 9:
                    self._level = level
                else:
                    raise ValueError('lzip: compress_level should be 0-9.')
            self._ext = ".lz"
        self._chunk_size = 1048576

    def __repr__(self):
        t = type(self)
        return f"<{t.__module__}.{t.__qualname__} object at {hex(id(self))}; method={repr(self._method)}, level={repr(self._level)}, ext={repr(self._ext)}>"  # noqa: E501

    @cached_property
    def chunk_size(self) -> int:
        return self._chunk_size

    @cached_property
    def ext(self) -> str:
        return self._ext

    @cached_property
    def level(self) -> int:
        return self._level

    @cached_property
    def method(self) -> CompressMethod:
        return self._method


supported_exts = []
if have_bz2:
    supported_exts.append('.bz2')
if have_gzip:
    supported_exts.append('.gz')
if have_lzma:
    supported_exts.append('.xz')
if have_lzip:
    supported_exts.append('.lz')


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', ' Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def compress_info(ori: int, re: int):
    return f"{sizeof_fmt(ori)} -> {sizeof_fmt(re)} ({re/ori*100:.2f}%)"


def compress(src: str, dest: str, c: CompressConfig, name: str, prog: str):
    exts = [''] + supported_exts.copy()
    exts.remove(c.ext)
    fn = dest + c.ext
    cs = c.chunk_size
    if exists(fn):
        remove(fn)
    if c.method == CompressMethod.BZIP2:
        with open(src, 'rb') as t:
            with BZ2File(fn, 'wb', compresslevel=c.level) as f:
                a = t.read(cs)
                while a != b'':
                    f.write(a)
                    a = t.read(cs)
                del a
    elif c.method == CompressMethod.GZIP:
        with open(src, 'rb') as t:
            with GzipFile(fn, 'wb', compresslevel=c.level) as f:
                a = t.read(cs)
                while a != b'':
                    f.write(a)
                    a = t.read(cs)
                del a
    elif c.method == CompressMethod.LZMA:
        with open(src, 'rb') as t:
            with LZMAFile(fn, 'wb', preset=c.level) as f:
                a = t.read(cs)
                while a != b'':
                    f.write(a)
                    a = t.read(cs)
                del a
    elif c.method == CompressMethod.LZIP:
        with open(src, 'rb') as t:
            with LZIPFileEncoder(fn, c.level) as f:
                a = t.read(cs)
                while a != b'':
                    f.compress(a)
                    a = t.read(cs)
                del a
    i = compress_info(getsize(src), getsize(fn))
    print(f'{prog}: Compressed {src}({name}) -> {fn} ({i})')
    del i
    for i in exts:
        f = dest + i
        if exists(f) and isfile(f):
            remove(f)
            print(f'{prog}: Removed {f}({name})')


def decompress(src: str, dest: str, c: CompressConfig, name: str, prog: str):
    fn = src + c.ext
    if exists(dest):
        remove(dest)
    cs = c.chunk_size
    if c.method == CompressMethod.BZIP2:
        with BZ2File(fn, 'rb') as f:
            with open(dest, 'wb') as t:
                a = f.read(cs)
                while a != b'':
                    t.write(a)
                    a = f.read(cs)
                del a
    elif c.method == CompressMethod.GZIP:
        with GzipFile(fn, 'rb') as f:
            with open(dest, 'wb') as t:
                a = f.read(cs)
                while a != b'':
                    t.write(a)
                    a = f.read(cs)
                del a
    elif c.method == CompressMethod.LZMA:
        with LZMAFile(fn, 'rb') as f:
            with open(dest, 'wb') as t:
                a = f.read(cs)
                while a != b'':
                    t.write(a)
                    a = f.read(cs)
                del a
    elif c.method == CompressMethod.LZIP:
        with open(dest, 'wb') as t:
            f = LZIP_decompress_file_iter(fn, chunk_size=cs)
            for a in f:
                t.write(a)
            del a
    i = compress_info(getsize(dest), getsize(fn))
    print(f'{prog}: Decompressed {fn}({name}) -> {dest} ({i})')
