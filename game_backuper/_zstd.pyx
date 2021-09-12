from ._zstd cimport *
from ._Python cimport *
from libc.stdlib cimport malloc, free


cdef void CHECK_ZSTD(size_t i) except *:
    if ZSTD_isError(i):
        raise ValueError(ZSTD_getErrorName(i).decode())


def version():
    cdef const char* v = ZSTD_versionString()
    return v.decode()


def maxCLevel():
    return ZSTD_maxCLevel()


cdef class ZSTDCompressor:
    cdef ZSTD_CCtx* cctx
    cdef void* buffOut
    cdef size_t buffOutSize
    cdef int finish

    def __cinit__(self):
        self.cctx = NULL
        self.buffOut = NULL
        self.buffOutSize = 0

    def __dealloc__(self):
        if self.cctx != NULL:
            ZSTD_freeCCtx(self.cctx)
        if self.buffOut != NULL:
            free(self.buffOut)

    def __init__(self, int compresslevel = 3):
        if compresslevel < 1 or compresslevel > ZSTD_maxCLevel():
            raise ValueError(u'unsupported compresslevel')
        self.finish = 0
        self.cctx = ZSTD_createCCtx()
        if self.cctx == NULL:
            raise MemoryError()
        CHECK_ZSTD(ZSTD_CCtx_setParameter(self.cctx, ZSTD_c_compressionLevel, compresslevel))
        CHECK_ZSTD(ZSTD_CCtx_setParameter(self.cctx, ZSTD_c_checksumFlag, 1))

    def compress(self, bytes inp):
        if self.finish:
            raise ValueError('Compressor has been flushed')
        if self.buffOut == NULL:
            self.buffOutSize = ZSTD_CStreamOutSize()
            self.buffOut = malloc(self.buffOutSize)
            if self.buffOut == NULL:
                raise MemoryError()
        cdef int finished = 0
        cdef ZSTD_outBuffer out
        cdef ZSTD_inBuffer i
        cdef Py_ssize_t si
        cdef size_t remaining
        cdef char* obuf
        if PyBytes_AsStringAndSize(inp, <char**>&i.src, &si) == -1:
            raise ValueError(u'Can not convert object to void*.')
        i.size = si
        i.pos = 0
        b = b''
        while not finished:
            out.dst = self.buffOut
            out.size = self.buffOutSize
            out.pos = 0
            remaining = ZSTD_compressStream2(self.cctx, &out, &i, ZSTD_e_continue)
            CHECK_ZSTD(remaining)
            obuf = <char*> out.dst
            b += PyBytes_FromStringAndSize(obuf, out.pos)
            finished = i.pos == i.size
        return b

    def flush(self):
        if self.finish:
            raise ValueError('Repeated call to flush()')
        if self.buffOut == NULL:
            self.finish = 1
            return b''
        cdef int finished = 0
        cdef ZSTD_outBuffer out
        cdef ZSTD_inBuffer i
        cdef char* obuf
        i.src = NULL
        i.size = 0
        i.pos = 0
        b = b''
        while not finished:
            out.dst = self.buffOut
            out.size = self.buffOutSize
            out.pos = 0
            remaining = ZSTD_compressStream2(self.cctx, &out, &i, ZSTD_e_end)
            CHECK_ZSTD(remaining)
            obuf = <char*> out.dst
            b += PyBytes_FromStringAndSize(obuf, out.pos)
            finished = remaining == 0
        self.finish = 1
        return b


cdef class ZSTDDecompressor:
    cdef ZSTD_DCtx* dctx
    cdef int finish
    cdef object _buff
    cdef int need_inp
    cdef void* buffOut
    cdef size_t buffOutSize
    cdef object _unused_data

    def __cinit__(self):
        self.dctx = NULL
        self._buff = b''
        self._unused_data = b''
        self.buffOut = NULL
        self.buffOutSize = 0

    def __dealloc__(self):
        if self.dctx != NULL:
            ZSTD_freeDCtx(self.dctx)
        if self.buffOut != NULL:
            free(self.buffOut)

    def __init__(self):
        self.dctx = ZSTD_createDCtx()
        if self.dctx == NULL:
            raise MemoryError()
        self.finish = 0
        self.need_inp = 1

    def decompress(self, bytes data, Py_ssize_t max_length = -1):
        if not self.need_inp:
            self.need_inp = 1
            tmp = self._buff
            self._buff = b''
            if self.finish:
                print(data)
                self._unused_data += data
            return tmp
        if self.finish:
            raise EOFError('End of stream already reached')
        if self.buffOut == NULL:
            self.buffOutSize = ZSTD_DStreamOutSize()
            self.buffOut = malloc(self.buffOutSize)
            if self.buffOut == NULL:
                raise MemoryError()
        if self.need_inp:
            b = b''
        else:
            b = self._buff
            self._buff = b''
        cdef int finished = 0
        cdef ZSTD_inBuffer i
        cdef ZSTD_outBuffer out
        cdef size_t ret
        cdef Py_ssize_t si
        cdef char* obuf
        if PyBytes_AsStringAndSize(data, <char**>&i.src, &si) == -1:
            raise ValueError(u'Can not convert object to void*.')
        i.size = si
        i.pos = 0
        while not finished:
            out.dst = self.buffOut
            out.size = self.buffOutSize
            out.pos = 0
            ret = ZSTD_decompressStream(self.dctx, &out, &i)
            CHECK_ZSTD(ret)
            obuf = <char*> out.dst
            b += PyBytes_FromStringAndSize(obuf, out.pos)
            self.finish = ret == 0
            finished = out.pos < out.size
        if self.finish and i.pos < i.size:
            obuf = (<char*> i.src) + i.pos
            self._unused_data = PyBytes_FromStringAndSize(obuf, i.size - i.pos)
        if max_length == 1 or len(b) <= max_length:
            return b
        else:
            self._buff = b[max_length:]
            self.need_inp = 0
            return b[:max_length]

    @property
    def eof(self):
        return True if self.finish else False

    @property
    def unused_data(self):
        return self._unused_data

    @property
    def needs_input(self):
        return True if self.need_inp else False
