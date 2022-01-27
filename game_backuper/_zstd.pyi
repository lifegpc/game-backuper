def version() -> str: ...
def maxCLevel() -> int: ...
class ZSTDCompressor:  # noqa: E302
    def __init__(self, compresslevel: int = 3): ...
    def compress(self, inp: bytes) -> bytes: ...
    def flush(self) -> bytes: ...
class ZSTDDecompressor:  # noqa: E302
    def __init__(self): ...
    def decompress(self, data: bytes, max_length: int = -1) -> bytes: ...
    @property
    def eof(self) -> bool: ...
    @property
    def unused_data(self) -> bytes: ...
    @property
    def needs_input(self) -> bool: ...
