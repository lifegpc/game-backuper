from game_backuper.compress import CompressConfig
from game_backuper.enc import DecryptException, EncFile
from os import urandom, remove
from hashlib import sha512
from zlib import crc32


datalen = 4096
data = urandom(datalen)
a = sha512()
a.update(data)
with EncFile('a.txt', 'wb', a.digest()) as f:
    f.write(data)
    key = f.key
    iv = f.iv
    crc = f.crc32
    print(crc)
    crc2 = '{:08x}'.format(crc32(data[:1024]))
    print(crc2)
    assert crc == crc2
with EncFile('a.txt', 'rb', a.digest(), key, iv, datalen, crc) as f:
    d = f.read()
    assert d == data
with EncFile('a.txt', 'rb', b'', key, iv, datalen, crc) as f:
    try:
        d = f.read()
        assert False
    except DecryptException:
        pass
remove('a.txt')
with EncFile('a.txt', 'wb', b'', compress=CompressConfig('gzip', 9)) as f:
    f.write(data)
    f.flush()
    key = f.key
    iv = f.iv
le = f.tell()
crc = f.crc32
with EncFile('a.txt', 'rb', b'', key, iv, le, crc, compress=CompressConfig('gzip')) as f:  # noqa: E501
    assert data == f.read()
remove('a.txt')
with EncFile('a.txt', 'wb', b'', compress=CompressConfig('bzip2', 1)) as f:
    f.write(data)
    f.flush()
    key = f.key
    iv = f.iv
le = f.tell()
crc = f.crc32
with EncFile('a.txt', 'rb', b'', key, iv, le, crc, CompressConfig('bzip2', 1)) as f:  # noqa: E501
    assert data == f.read()
remove('a.txt')
with EncFile('a.txt', 'wb', b'', compress=CompressConfig('lzma', 1)) as f:
    f.write(data)
    f.flush()
    key = f.key
    iv = f.iv
le = f.tell()
crc = f.crc32
with EncFile('a.txt', 'rb', b'', key, iv, le, crc, CompressConfig('lzma', 1)) as f:  # noqa: E501
    assert data == f.read()
remove('a.txt')
with EncFile('a.txt', 'wb', b'', compress=CompressConfig('lzip', 1)) as f:
    f.write(data)
    f.flush()
    key = f.key
    iv = f.iv
le = f.tell()
crc = f.crc32
with EncFile('a.txt', 'rb', b'', key, iv, le, crc, CompressConfig('lzip', 1)) as f:  # noqa: E501
    assert data == f.read()
remove('a.txt')
with EncFile('a.txt', 'wb', b'', compress=CompressConfig('zstd', 1)) as f:
    f.write(data)
    f.flush()
    key = f.key
    iv = f.iv
le = f.tell()
crc = f.crc32
with EncFile('a.txt', 'rb', b'', key, iv, le, crc, CompressConfig('zstd', 1)) as f:  # noqa: E501
    assert data == f.read()
remove('a.txt')
with EncFile('a.txt', 'wb', b'', compress=CompressConfig('snappy', 1)) as f:
    f.write(data)
    f.flush()
    key = f.key
    iv = f.iv
le = f.tell()
crc = f.crc32
with EncFile('a.txt', 'rb', b'', key, iv, le, crc, CompressConfig('snappy', 1)) as f:  # noqa: E501
    assert data == f.read()
remove('a.txt')
with EncFile('a.txt', 'wb', b'', compress=CompressConfig('brotli', 1)) as f:
    f.write(data)
    f.flush()
    key = f.key
    iv = f.iv
le = f.tell()
crc = f.crc32
with EncFile('a.txt', 'rb', b'', key, iv, le, crc, CompressConfig('brotli', 1)) as f:  # noqa: E501
    assert data == f.read()
remove('a.txt')
