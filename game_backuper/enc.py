from base64 import b85decode, b85encode
from collections import namedtuple
from io import RawIOBase
from os import PathLike, remove, urandom
from os.path import exists, getsize
from typing import Union
from zlib import crc32
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from game_backuper.compress import (
    CompressConfig,
    CompressMethod,
    compress_info,
)
from game_backuper.file import File, hydrate_file_if_needed, mkdir_for_file


_MODE_CLOSED = 0
_MODE_READ = 1
_MODE_WRITE = 3
_EncrpytStats = namedtuple('EncryptStats', ['key', 'iv', 'crc32', 'x_compress_type', 'compressed_size'])  # noqa: E501


class EncryptStats(_EncrpytStats):
    @property
    def compressed(self):
        return self.x_compress_type is not None

    @property
    def compress_type(self):
        return CompressMethod(self.x_compress_type)


class DecryptException(Exception):
    pass


class EncFile(RawIOBase):
    def __enter__(self):
        return self

    def __exit__(self, type, val, tb):
        if not self.closed:
            self.close()

    def __init__(self, fn, mode: str, salt: Union[bytes, str],
                 key: Union[bytes, str] = None, iv: Union[bytes, str] = None,
                 length: int = None, crc32: Union[str, int] = None,
                 compress: CompressConfig = None):
        self._fp = None
        self._mode = _MODE_CLOSED
        if mode in ["", "r", "rb"]:
            mode = "rb"
            mode_code = _MODE_READ
        elif mode in ["w", "wb"]:
            mode = "wb"
            mode_code = _MODE_WRITE
        elif mode in ["x", "xb"]:
            mode = "xb"
            mode_code = _MODE_WRITE
        elif mode in ["a", "ab"]:
            mode = "ab"
            mode_code = _MODE_WRITE
        if isinstance(fn, (str, bytes, PathLike)):
            self._fp = open(fn, mode)
            self._mode = mode_code
        else:
            raise TypeError('filename must be str, bytes or PathLike.')
        if self._mode == _MODE_WRITE:
            self._key = urandom(32)
            self._iv = urandom(16)
            self._cipher = Cipher(algorithms.AES(self._key), modes.CBC(self._iv))  # noqa: E501
            self._enc = self._cipher.encryptor()
            self._crc32 = 0
            if compress is not None:
                self._compressor = compress.compressor(self)
                if self._compressor is None:
                    raise NotImplementedError('Unsupported compression type.')
            else:
                self._compressor = None
        if isinstance(salt, str):
            self._salt = b85decode(salt)
        else:
            self._salt = salt
        if self._mode == _MODE_READ:
            if isinstance(key, str):
                key = b85decode(key)
            if isinstance(iv, str):
                iv = b85decode(iv)
            if key is None or len(key) != 32:
                raise ValueError('A 256-bit key is required.')
            self._key = key
            if iv is None or len(iv) != 16:
                raise ValueError('A 128-bit initialization_vector is required.')  # noqa: E501
            self._iv = iv
            self._cipher = Cipher(algorithms.AES(self.key), modes.CBC(self._iv))  # noqa: E501
            self._dec = self._cipher.decryptor()
            if length is None or not isinstance(length, int):
                raise ValueError("data's length is needed.")
            self._length = length
            self._buf = b''
            self._eof = False
            if crc32:
                if isinstance(crc32, str):
                    self._crc32 = int(crc32, 16)
                else:
                    self._crc32 = crc32
                self._crc32_checked = False
            else:
                self._crc32 = None
            self._decompressor = None
            if compress:
                self._decompressor = compress.decompressor(self)
                if self._decompressor is None:
                    raise NotImplementedError('Unsupported compression type.')
                self._debuf = b''
        self._pos = 0
        self._crc_size = algorithms.AES.block_size * 8
        self._flushing = False

    def _check_not_closed(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")

    def close(self):
        if self._mode == _MODE_CLOSED:
            return
        try:
            if self._mode == _MODE_READ:
                if hasattr(self._decompressor, 'close'):
                    self._decompressor.write_to_file = False
                    self._decompressor.close()
                    self._decompressor.write_to_file = True
            if self._mode == _MODE_WRITE:
                if hasattr(self._compressor, 'close'):
                    self._compressor.write_to_file = False
                    self._compressor.close()
                    self._compressor.write_to_file = True
                elif self._compressor:
                    d = self._compressor.flush()
                    if d:
                        length = len(d)
                        if self._pos < self._crc_size:
                            le = min(length, self._crc_size - self._pos)
                            self._crc32 = crc32(d[:le], self._crc32)
                        self._fp.write(self._enc.update(d))
                        self._pos += length
                if self._pos % algorithms.AES.block_size != 0:
                    self._fp.write(self._enc.update(b"\x00" * (algorithms.AES.block_size - (self._pos % algorithms.AES.block_size))))  # noqa: E501
                self._fp.write(self._enc.finalize())
        finally:
            self._fp.close()
            self._dec = None
            self._enc = None
            self._cipher = None
            self._fp = None
            self._mode = _MODE_CLOSED

    @property
    def closed(self):
        return self._mode == _MODE_CLOSED

    def check_crc32(self):
        while len(self._buf) < self._crc_size:
            if not self.__read():
                break
        if crc32(self._buf[:min(self._crc_size, self._length)]) == self._crc32:
            return True
        else:
            return False

    @property
    def crc32(self):
        return '{:08x}'.format(self._crc32)

    def __decompress(self):
        if len(self._buf) == 0:
            return False
        if self._decompressor:
            le = min(len(self._buf), self._length - self._pos)
            if le == 0 or (hasattr(self._decompressor, "eof") and self._decompressor.eof):  # noqa: E501
                return False
            self._debuf += self._decompressor.decompress(self._buf[:le])
            self._pos += le
            self._buf = self._buf[le:]
            return True
        return False

    @property
    def eof(self):
        return self._pos >= self._length

    def fileno(self):
        self._check_not_closed()
        return self._fp.fileno()

    def flush(self) -> None:
        if self._flushing:
            return
        self._flushing = True
        self._check_not_closed()
        if hasattr(self._compressor, 'write_to_file'):
            self._compressor.write_to_file = False
            self._compressor.flush()
            self._compressor.write_to_file = True
        self._fp.flush()
        self._flushing = False

    def readable(self):
        self._check_not_closed()
        return self._mode == _MODE_READ

    def __read(self):
        data = self._fp.read(algorithms.AES.block_size)
        if not data:
            if not self._eof:
                self._buf += self._dec.finalize()
                self._eof = True
            else:
                return False
        else:
            self._buf += self._dec.update(data)
        return True

    def read(self, size: int = -1):
        if not self.readable():
            raise ValueError('File is not readable.')
        if self._crc32 is not None and not self._crc32_checked:
            if not self.check_crc32():
                raise DecryptException("crc32 check failed.")
            self._crc32_checked = True
        if size < 0:
            return self.readall()
        if self._decompressor and hasattr(self._decompressor, 'write_to_file') and self._decompressor.write_to_file:  # noqa: E501
            self._decompressor.write_to_file = False
            d = self._decompressor.read(size)
            self._decompressor.write_to_file = True
            return d
        if self._decompressor and not hasattr(self._decompressor, 'write_to_file'):  # noqa: E501
            if not size or (self.eof and len(self._debuf) == 0):
                return b""
            while True:
                if not self.__read():
                    self.__decompress()
                    break
                if not self.__decompress():
                    break
                if size <= len(self._debuf):
                    data = self._debuf[:size]
                    self._debuf = self._debuf[size:]
                    return data
            d = self._debuf[:size]
            self._debuf = self._debuf[size:]
            return d
        if not size or self.eof:
            return b""
        size = min(size, self._length - self._pos)
        if size <= len(self._buf):
            data = self._buf[:size]
            self._buf = self._buf[size:]
            self._pos += size
            return data
        while True:
            if not self.__read():
                break
            if size <= len(self._buf):
                data = self._buf[:size]
                self._buf = self._buf[size:]
                self._pos += size
                return data
        self._pos += min(len(self._buf), size)
        d = self._buf[:size]
        self._buf = self._buf[size:]
        return d

    def readinto(self, b):
        with memoryview(b) as view, view.cast("B") as byte_view:
            data = self.read(len(byte_view))
            byte_view[:len(data)] = data
        return len(data)

    def tell(self):
        return self._pos

    def writable(self):
        self._check_not_closed()
        return self._mode == _MODE_WRITE

    def write(self, data):
        if not self.writable():
            raise ValueError("File was not opened for writing")
        if isinstance(data, bytes):
            length = len(data)
        elif isinstance(data, str):
            data = data.encode()
            length = len(data)
        elif isinstance(data, bytearray):
            data = bytes(data)
            length = len(data)
        else:
            data = memoryview(data)
            length = data.nbytes
            data = data.tobytes()
        if self._compressor:
            if hasattr(self._compressor, 'write_to_file'):
                if self._compressor.write_to_file:
                    self._compressor.write_to_file = False
                    self._compressor.compress(data)
                    self._compressor.write_to_file = True
                    return
            else:
                data = self._compressor.compress(data)
                length = len(data)
        if self._pos < self._crc_size:
            le = min(length, self._crc_size - self._pos)
            self._crc32 = crc32(data[:le], self._crc32)
        self._fp.write(self._enc.update(data))
        self._pos += length

    @property
    def key(self):
        if len(self._salt) < 32:
            self._salt = self._salt + b'\x00' * (32 - len(self._salt))
        return bytes(a ^ b for a, b in zip(self._salt, self._key))

    @property
    def iv(self):
        return self._iv


def encrypt_file(src: str, dest: str, f: File, name: str, prog: str, c: CompressConfig = None):  # noqa: E501
    if exists(dest):
        remove(dest)
    mkdir_for_file(dest)
    cs = 4096 if c is None else c.chunk_size
    with open(src, 'rb') as s:
        with EncFile(dest, 'wb', f.hash, compress=c) as t:
            a = s.read(cs)
            while a != b'':
                t.write(a)
                a = s.read(cs)
            del a
        stats = EncryptStats(b85encode(t.key).decode(), b85encode(t.iv).decode(), t.crc32, c._method.value if c else None, t.tell() if c else None)  # noqa: E501
    i = compress_info(f.size, getsize(dest))
    if c is None:
        print(f'{prog}: Encrypted {src}({name}) -> {dest} ({i})')
    else:
        print(f'{prog}: Compressed and encrypted {src}({name}) -> {dest} ({i})')  # noqa: E501
    return stats


def decrypt_file(src: str, dest: str, f: File, name: str, prog: str, c: CompressConfig = None):  # noqa: E501
    if not f.encrypted:
        raise ValueError('File is not encrypted.')
    hydrate_file_if_needed(src)
    if exists(dest):
        remove(dest)
    mkdir_for_file(dest)
    cs = 4096 if c is None else c.chunk_size
    with EncFile(src, 'rb', f.hash, f.key, f.iv, f.encrypt_file_size, f.crc32, c) as s:  # noqa: E501
        with open(dest, 'wb') as t:
            a = s.read(cs)
            while a != b'':
                t.write(a)
                a = s.read(cs)
            del a
    i = compress_info(f.size, getsize(src))
    if c is None:
        print(f'{prog}: Decrypted {src}({name}) -> {dest} ({i})')
    else:
        print(f'{prog}: Decrypted and decompressed {src}({name}) -> {dest} ({i})')  # noqa: E501
