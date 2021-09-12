try:
    from game_backuper._zstd import (
        ZSTDCompressor,
        ZSTDDecompressor,
        maxCLevel,
    )
    have_zstd = True
except ImportError:
    have_zstd = False
if have_zstd:
    from builtins import open as _builtin_open
    from _compression import BaseStream, DecompressReader
    import os
    import io

    _MODE_CLOSED = 0
    _MODE_READ = 1
    _MODE_WRITE = 3
    MAX_COMPRESS_LEVEL = maxCLevel()

    class ZSTDFile(BaseStream):
        def __init__(self, filename, mode="r", *, compresslevel=3):
            self._fp = None
            self._closefp = False
            self._mode = _MODE_CLOSED
            if not (1 <= compresslevel <= MAX_COMPRESS_LEVEL):
                raise ValueError(f"compresslevel must be between 1 and {MAX_COMPRESS_LEVEL}")  # noqa: E501
            if mode in ("", "r", "rb"):
                mode = "rb"
                mode_code = _MODE_READ
            elif mode in ("w", "wb"):
                mode = "wb"
                mode_code = _MODE_WRITE
                self._compressor = ZSTDCompressor(compresslevel)
            elif mode in ("x", "xb"):
                mode = "xb"
                mode_code = _MODE_WRITE
                self._compressor = ZSTDCompressor(compresslevel)
            elif mode in ("a", "ab"):
                mode = "ab"
                mode_code = _MODE_WRITE
                self._compressor = ZSTDCompressor(compresslevel)
            else:
                raise ValueError("Invalid mode: %r" % (mode,))
            if isinstance(filename, (str, bytes, os.PathLike)):
                self._fp = _builtin_open(filename, mode)
                self._closefp = True
                self._mode = mode_code
            else:
                raise TypeError("filename must be a str, bytes, file or PathLike object")  # noqa: E501
            if self._mode == _MODE_READ:
                raw = DecompressReader(self._fp, ZSTDDecompressor,
                                       trailing_error=OSError)
                self._buffer = io.BufferedReader(raw)
            else:
                self._pos = 0

        def close(self):
            if self._mode == _MODE_CLOSED:
                return
            try:
                if self._mode == _MODE_READ:
                    self._buffer.close()
                elif self._mode == _MODE_WRITE:
                    self._fp.write(self._compressor.flush())
                    self._compressor = None
            finally:
                try:
                    if self._closefp:
                        self._fp.close()
                finally:
                    self._fp = None
                    self._closefp = False
                    self._mode = _MODE_CLOSED
                    self._buffer = None

        @property
        def closed(self):
            return self._mode == _MODE_CLOSED

        def fileno(self):
            self._check_not_closed()
            return self._fp.fileno()

        def seekable(self):
            return self.readable() and self._buffer.seekable()

        def readable(self):
            self._check_not_closed()
            return self._mode == _MODE_READ

        def writable(self):
            self._check_not_closed()
            return self._mode == _MODE_WRITE

        def peek(self, n=0):
            self._check_can_read()
            return self._buffer.peek(n)

        def read(self, size=-1):
            self._check_can_read()
            return self._buffer.read(size)

        def read1(self, size=-1):
            self._check_can_read()
            if size < 0:
                size = io.DEFAULT_BUFFER_SIZE
            return self._buffer.read1(size)

        def readinto(self, b):
            self._check_can_read()
            return self._buffer.readinto(b)

        def readline(self, size=-1):
            if not isinstance(size, int):
                if not hasattr(size, "__index__"):
                    raise TypeError("Integer argument expected")
                size = size.__index__()
            self._check_can_read()
            return self._buffer.readline(size)

        def __iter__(self):
            self._check_can_read()
            return self._buffer.__iter__()

        def readlines(self, size=-1):
            if not isinstance(size, int):
                if not hasattr(size, "__index__"):
                    raise TypeError("Integer argument expected")
                size = size.__index__()
            self._check_can_read()
            return self._buffer.readlines(size)

        def write(self, data):
            self._check_can_write()
            if isinstance(data, (bytes, bytearray)):
                length = len(data)
            else:
                data = memoryview(data)
                length = data.nbytes
            compressed = self._compressor.compress(data)
            self._fp.write(compressed)
            self._pos += length
            return length

        def writelines(self, seq):
            return BaseStream.writelines(self, seq)

        def seek(self, offset, whence=io.SEEK_SET):
            self._check_can_seek()
            return self._buffer.seek(offset, whence)

        def tell(self):
            self._check_not_closed()
            if self._mode == _MODE_READ:
                return self._buffer.tell()
            return self._pos

    def open(filename, mode="rb", compresslevel=3, encoding=None, errors=None, newline=None):  # noqa: E501
        if "t" in mode:
            if "b" in mode:
                raise ValueError("Invalid mode: %r" % (mode,))
        else:
            if encoding is not None:
                raise ValueError("Argument 'encoding' not supported in binary mode")  # noqa: E501
            if errors is not None:
                raise ValueError("Argument 'errors' not supported in binary mode")  # noqa: E501
            if newline is not None:
                raise ValueError("Argument 'newline' not supported in binary mode")  # noqa: E501

        bz_mode = mode.replace("t", "")
        binary_file = ZSTDFile(filename, bz_mode, compresslevel=compresslevel)

        if "t" in mode:
            return io.TextIOWrapper(binary_file, encoding, errors, newline)
        else:
            return binary_file
