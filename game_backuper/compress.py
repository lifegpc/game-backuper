try:
    from bz2 import BZ2File, BZ2Compressor, BZ2Decompressor
    have_bz2 = True
except ImportError:
    have_bz2 = False
try:
    from gzip import GzipFile
    have_gzip = True
except ImportError:
    have_gzip = False
try:
    from lzma import LZMAFile, LZMACompressor, LZMADecompressor
    have_lzma = True
except ImportError:
    have_lzma = False
try:
    from lzip import (
        FileEncoder as LZIPFileEncoder,
        decompress_file_iter as LZIP_decompress_file_iter,
        level_to_dictionary_size_and_match_len_limit as lzip_level_dict,
    )
    from lzip_extension import (
        Decoder as LZIPDecoder,
        Encoder as LZIPEncoder,
    )
    have_lzip = True
except ImportError:
    have_lzip = False
try:
    from game_backuper.zstd import (
        ZSTDCompressor,
        ZSTDDecompressor,
        ZSTDFile,
        MAX_COMPRESS_LEVEL as ZSTD_MAX,
    )
    have_zstd = True
except ImportError:
    have_zstd = False
try:
    from snappy import (
        StreamCompressor as Snappy_Compressor,
        StreamDecompressor as Snappy_Decompressor,
    )
    have_snappy = True
except ImportError:
    have_snappy = False
try:
    from brotli import (
        Compressor as BrotliCompressor,
        Decompressor as BrotliDecompressor,
    )
    have_brotli = True
except ImportError:
    have_brotli = False
from enum import IntEnum, unique
try:
    from functools import cached_property
except ImportError:
    cached_property = property
from os.path import exists, isfile, getsize
from os import remove
from game_backuper.file import mkdir_for_file, hydrate_file_if_needed


if have_gzip:
    class GZCompressor:
        def __init__(self, compress_level: int = 9, file_obj=None):
            self.write_to_file = True
            self._fileobj = file_obj
            self._level = compress_level
            self._f = None

        def close(self):
            if self._f is None:
                return
            self._f.close()

        def compress(self, data: bytes) -> bytes:
            if self._f is None:
                self._f = GzipFile(mode="wb", compresslevel=self._level, fileobj=self._fileobj)  # noqa: E501
            self._f.write(data)
            return b''

        def flush(self) -> bytes:
            self._f.flush()
            return b''

    class GZDecompressor:
        def __init__(self, file_obj=None):
            self.write_to_file = True
            self._fileobj = file_obj
            self._f = None

        def close(self):
            if self._f is None:
                return
            self._f.close()

        def read(self, len: int) -> bytes:
            if self._f is None:
                self._f = GzipFile(mode="rb", fileobj=self._fileobj)
            return self._f.read(len)

if have_lzip:
    class LZIPCompressor:
        def __init__(self, level: int = 6):
            d = lzip_level_dict[level]
            self._encoder = LZIPEncoder(d[0], d[1], 1 << 51)

        def compress(self, data: bytes) -> bytes:
            return self._encoder.compress(data)

        def flush(self) -> bytes:
            return self._encoder.finish()

    class LZIPDecompressor:
        def __init__(self):
            self._decoder = LZIPDecoder(1)

        def decompress(self, data: bytes) -> bytes:
            return self._decoder.decompress(data)

        @property
        def eof(self):
            return False

if have_brotli:
    class BrotliCompressor2:
        def __init__(self, *k, **kw):
            self._c = BrotliCompressor(*k, **kw)

        def compress(self, data: bytes) -> bytes:
            return self._c.process(data)

        def flush(self) -> bytes:
            return self._c.finish()

    class BrotliDecompressor2:
        def __init__(self, *k, **kw) -> None:
            self._c = BrotliDecompressor(*k, **kw)

        def decompress(self, data: bytes) -> bytes:
            return self._c.process(data)

        @property
        def eof(self):
            return self._c.is_finished()


@unique
class CompressMethod(IntEnum):
    BZIP2 = 0
    GZIP = 1
    LZMA = 2
    LZIP = 3
    ZSTD = 4
    SNAPPY = 5
    BROTLI = 6

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
            elif t == "zstd":
                return CompressMethod.ZSTD
            elif t == "snappy":
                return CompressMethod.SNAPPY
            elif t == "brotli":
                return CompressMethod.BROTLI
        else:
            raise TypeError('Must be str.')

    def to_str(self) -> str:
        return {
            CompressMethod.BZIP2: 'bzip2',
            CompressMethod.GZIP: 'gzip',
            CompressMethod.LZMA: 'lzma',
            CompressMethod.LZIP: 'lzip',
            CompressMethod.ZSTD: 'zstd',
            CompressMethod.SNAPPY: 'snappy',
            CompressMethod.BROTLI: 'brotli',
        }[self]


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
        elif self._method == CompressMethod.ZSTD:
            if not have_zstd:
                raise NotImplementedError("zstd not supported.")
            if level is None:
                self._level = 3
            else:
                if isinstance(level, int) and level >= 0 and level <= ZSTD_MAX:
                    self._level = level
                else:
                    raise ValueError(f'zstd: compress_level should be 0-{ZSTD_MAX}.')  # noqa: E501
            self._ext = ".zst"
        elif self._method == CompressMethod.SNAPPY:
            if not have_snappy:
                raise NotImplementedError("snappy not supported.")
            self._level = None
            self._ext = ".snappy"
        elif self._method == CompressMethod.BROTLI:
            if not have_brotli:
                raise NotImplementedError("brotli not supported.")
            if level is None:
                self._level = None
            else:
                if isinstance(level, int) and level >= 0 and level <= 11:
                    self._level = level
                else:
                    raise ValueError('brotli: compress_level should be 0-11.')
            self._ext = '.br'
        self._chunk_size = 131072

    def __repr__(self):
        t = type(self)
        return f"<{t.__module__}.{t.__qualname__} object at {hex(id(self))}; method={repr(self._method)}, level={repr(self._level)}, ext={repr(self._ext)}>"  # noqa: E501

    def compressor(self, fileobj):
        if self._method == CompressMethod.BZIP2:
            return BZ2Compressor(self._level)
        elif self._method == CompressMethod.GZIP:
            return GZCompressor(self._level, fileobj)
        elif self._method == CompressMethod.LZMA:
            return LZMACompressor(preset=self._level)
        elif self._method == CompressMethod.LZIP:
            return LZIPCompressor(self._level)
        elif self._method == CompressMethod.ZSTD:
            return ZSTDCompressor(self._level)
        elif self._method == CompressMethod.SNAPPY:
            return Snappy_Compressor()
        elif self._method == CompressMethod.BROTLI:
            c = {}
            if self._level is not None:
                c['quality'] = self._level
            return BrotliCompressor2(**c)

    def decompressor(self, fileobj):
        if self._method == CompressMethod.BZIP2:
            return BZ2Decompressor()
        elif self._method == CompressMethod.GZIP:
            return GZDecompressor(fileobj)
        elif self._method == CompressMethod.LZMA:
            return LZMADecompressor()
        elif self._method == CompressMethod.LZIP:
            return LZIPDecompressor()
        elif self._method == CompressMethod.ZSTD:
            return ZSTDDecompressor()
        elif self._method == CompressMethod.SNAPPY:
            return Snappy_Decompressor()
        elif self._method == CompressMethod.BROTLI:
            return BrotliDecompressor2()

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
if have_zstd:
    supported_exts.append('.zst')
if have_snappy:
    supported_exts.append('.snappy')
if have_brotli:
    supported_exts.append('.br')


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', ' Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def compress_info(ori: int, re: int):
    if ori == 0:
        return f"{sizeof_fmt(ori)} -> {sizeof_fmt(re)} ({float('inf')})"
    return f"{sizeof_fmt(ori)} -> {sizeof_fmt(re)} ({re/ori*100:.2f}%)"


def compress(src: str, dest: str, c: CompressConfig, name: str, prog: str):
    exts = [''] + supported_exts.copy()
    exts.remove(c.ext)
    fn = dest + c.ext
    cs = c.chunk_size
    if exists(fn):
        remove(fn)
    mkdir_for_file(fn)
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
    elif c.method == CompressMethod.ZSTD:
        with open(src, 'rb') as t:
            with ZSTDFile(fn, 'wb', compresslevel=c.level) as f:
                a = t.read(cs)
                while a != b'':
                    f.write(a)
                    a = t.read(cs)
                del a
    elif c.method == CompressMethod.SNAPPY:
        with open(src, 'rb') as t:
            with open(fn, 'wb') as f:
                o = Snappy_Compressor()
                a = t.read(cs)
                while a != b'':
                    b = o.compress(a)
                    f.write(b)
                    a = t.read(cs)
                del a, b, o
    elif c.method == CompressMethod.BROTLI:
        k = {}
        if c.level is not None:
            k['quality'] = c.level
        with open(src, 'rb') as t:
            with open(fn, 'wb') as f:
                o = BrotliCompressor(**k)
                a = t.read(cs)
                while a != b'':
                    b = o.process(a)
                    f.write(b)
                    a = t.read(cs)
                f.write(o.finish())
                del a, b, o
        del k
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
    hydrate_file_if_needed(fn)
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
    elif c.method == CompressMethod.ZSTD:
        with ZSTDFile(fn, 'rb') as f:
            with open(dest, 'wb') as t:
                a = f.read(cs)
                while a != b'':
                    t.write(a)
                    a = f.read(cs)
                del a
    elif c.method == CompressMethod.SNAPPY:
        with open(fn, 'rb') as f:
            with open(dest, 'wb') as t:
                o = Snappy_Decompressor()
                a = f.read(cs)
                while a != b'':
                    b = o.decompress(a)
                    t.write(b)
                    a = f.read(cs)
                o.flush()
                del a, b, o
    elif c.method == CompressMethod.BROTLI:
        with open(fn, 'rb') as f:
            with open(dest, 'wb') as t:
                o = BrotliDecompressor()
                a = f.read(cs)
                while a != b'':
                    b = o.process(a)
                    t.write(b)
                    a = f.read(cs)
                if not o.is_finished():
                    raise ValueError('Read all datas from file but seems not finished.')  # noqa: E501
                del a, b, o
    i = compress_info(getsize(dest), getsize(fn))
    print(f'{prog}: Decompressed {fn}({name}) -> {dest} ({i})')
