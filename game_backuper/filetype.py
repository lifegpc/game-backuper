from enum import IntEnum, unique


@unique
class FileType(IntEnum):
    LEVELDB = 0
