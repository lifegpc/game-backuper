from hashlib import sha512 as _sha512
from base64 import b85encode
from typing import BinaryIO


def sha512(b: BinaryIO):
    s = _sha512()
    t = b.read(1024)
    while len(t) > 0:
        s.update(t)
        t = b.read(1024)
    return b85encode(s.digest()).decode()
