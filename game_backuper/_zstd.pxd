from libc.stddef cimport size_t


cdef extern from "zstd.h":
    ctypedef struct ZSTD_CCtx:
        pass
    ctypedef ZSTD_CCtx ZSTD_CStream
    ctypedef enum ZSTD_EndDirective:
        ZSTD_e_continue = 0
        ZSTD_e_flush = 1
        ZSTD_e_end = 2
    cdef struct ZSTD_inBuffer_s:
        const void* src
        size_t size
        size_t pos
    ctypedef ZSTD_inBuffer_s ZSTD_inBuffer
    cdef struct ZSTD_outBuffer_s:
        void* dst
        size_t size
        size_t pos
    ctypedef ZSTD_outBuffer_s ZSTD_outBuffer
    ctypedef enum ZSTD_cParameter:
        ZSTD_c_compressionLevel
        ZSTD_c_checksumFlag
    ctypedef struct ZSTD_DCtx:
        pass
    ctypedef ZSTD_DCtx ZSTD_DStream

    const char* ZSTD_versionString()
    unsigned ZSTD_isError(size_t code)
    const char* ZSTD_getErrorName(size_t code)
    int ZSTD_maxCLevel()
    ZSTD_CCtx* ZSTD_createCCtx()
    size_t ZSTD_freeCCtx(ZSTD_CCtx* cctx)
    ZSTD_CStream* ZSTD_createCStream()
    size_t ZSTD_freeCStream(ZSTD_CStream* zcs)
    size_t ZSTD_initCStream(ZSTD_CStream* zcs, int compressionLevel)
    size_t ZSTD_CCtx_setParameter(ZSTD_CCtx* cctx, ZSTD_cParameter param, int value)
    size_t ZSTD_CStreamInSize()
    size_t ZSTD_CStreamOutSize()
    size_t ZSTD_DStreamInSize()
    size_t ZSTD_DStreamOutSize()
    size_t ZSTD_compressStream2(ZSTD_CCtx* cctx, ZSTD_outBuffer* output, ZSTD_inBuffer* inp, ZSTD_EndDirective endOp)
    ZSTD_DCtx* ZSTD_createDCtx()
    size_t ZSTD_freeDCtx(ZSTD_DCtx* dctx)
    size_t ZSTD_decompressStream(ZSTD_DStream* zds, ZSTD_outBuffer* output, ZSTD_inBuffer* inp)
