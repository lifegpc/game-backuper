from ._pcre2 cimport *
from ._Python cimport *
from enum import IntFlag
from libc.stdlib cimport malloc, free
from libc.string cimport strcpy
from cpython.mem cimport PyMem_Free
try:
    from functools import cached_property
except ImportError:
    cached_property = property


cdef extern from "_pcre2.h":
    const uint32_t _PCRE2_ANCHORED "PCRE2_ANCHORED"
    const uint32_t _PCRE2_ALLOW_EMPTY_CLASS "PCRE2_ALLOW_EMPTY_CLASS"
    const uint32_t _PCRE2_ALT_BSUX "PCRE2_ALT_BSUX"
    const uint32_t _PCRE2_ALT_CIRCUMFLEX "PCRE2_ALT_CIRCUMFLEX"
    const uint32_t _PCRE2_ALT_VERBNAMES "PCRE2_ALT_VERBNAMES"
    const uint32_t _PCRE2_AUTO_CALLOUT "PCRE2_AUTO_CALLOUT"
    const uint32_t _PCRE2_CASELESS "PCRE2_CASELESS"
    const uint32_t _PCRE2_COPY_MATCHED_SUBJECT "PCRE2_COPY_MATCHED_SUBJECT"
    const uint32_t _PCRE2_DOLLAR_ENDONLY "PCRE2_DOLLAR_ENDONLY"
    const uint32_t _PCRE2_DOTALL "PCRE2_DOTALL"
    const uint32_t _PCRE2_DUPNAMES "PCRE2_DUPNAMES"
    const uint32_t _PCRE2_ENDANCHORED "PCRE2_ENDANCHORED"
    const uint32_t _PCRE2_EXTENDED "PCRE2_EXTENDED"
    const uint32_t _PCRE2_FIRSTLINE "PCRE2_FIRSTLINE"
    const uint32_t _PCRE2_LITERAL "PCRE2_LITERAL"
    const uint32_t _PCRE2_MATCH_INVALID_UTF "PCRE2_MATCH_INVALID_UTF"
    const uint32_t _PCRE2_MATCH_UNSET_BACKREF "PCRE2_MATCH_UNSET_BACKREF"
    const uint32_t _PCRE2_MULTILINE "PCRE2_MULTILINE"
    const uint32_t _PCRE2_NEVER_BACKSLASH_C "PCRE2_NEVER_BACKSLASH_C"
    const uint32_t _PCRE2_NEVER_UCP "PCRE2_NEVER_UCP"
    const uint32_t _PCRE2_NEVER_UTF "PCRE2_NEVER_UTF"
    const uint32_t _PCRE2_NOTBOL "PCRE2_NOTBOL"
    const uint32_t _PCRE2_NOTEOL "PCRE2_NOTEOL"
    const uint32_t _PCRE2_NOTEMPTY "PCRE2_NOTEMPTY"
    const uint32_t _PCRE2_NOTEMPTY_ATSTART "PCRE2_NOTEMPTY_ATSTART"
    const uint32_t _PCRE2_NO_AUTO_CAPTURE "PCRE2_NO_AUTO_CAPTURE"
    const uint32_t _PCRE2_NO_AUTO_POSSESS "PCRE2_NO_AUTO_POSSESS"
    const uint32_t _PCRE2_NO_DOTSTAR_ANCHOR "PCRE2_NO_DOTSTAR_ANCHOR"
    const uint32_t _PCRE2_NO_JIT "PCRE2_NO_JIT"
    const uint32_t _PCRE2_NO_START_OPTIMIZE "PCRE2_NO_START_OPTIMIZE"
    const uint32_t _PCRE2_NO_UTF_CHECK "PCRE2_NO_UTF_CHECK"
    const uint32_t _PCRE2_PARTIAL_HARD "PCRE2_PARTIAL_HARD"
    const uint32_t _PCRE2_PARTIAL_SOFT "PCRE2_PARTIAL_SOFT"
    const uint32_t _PCRE2_UCP "PCRE2_UCP"
    const uint32_t _PCRE2_UNGREEDY "PCRE2_UNGREEDY"
    const uint32_t _PCRE2_USE_OFFSET_LIMIT "PCRE2_USE_OFFSET_LIMIT"
    const uint32_t _PCRE2_UTF "PCRE2_UTF"
    const size_t PCRE2_ZERO_TERMINATED
    const int PCRE2_ERROR_NOMEMORY
    const int PCRE2_ERROR_UNSET
    const int PCRE2_INFO_NAMECOUNT
    const int PCRE2_INFO_NAMEENTRYSIZE
    const int PCRE2_INFO_NAMETABLE


class Option(IntFlag):
    PCRE2_ANCHORED = _PCRE2_ANCHORED
    PCRE2_ALLOW_EMPTY_CLASS = _PCRE2_ALLOW_EMPTY_CLASS
    PCRE2_ALT_BSUX = _PCRE2_ALT_BSUX
    PCRE2_ALT_CIRCUMFLEX = _PCRE2_ALT_CIRCUMFLEX
    PCRE2_ALT_VERBNAMES = _PCRE2_ALT_VERBNAMES
    PCRE2_AUTO_CALLOUT = _PCRE2_AUTO_CALLOUT
    PCRE2_CASELESS = _PCRE2_CASELESS
    PCRE2_DOLLAR_ENDONLY = _PCRE2_DOLLAR_ENDONLY
    PCRE2_DOTALL = _PCRE2_DOTALL
    PCRE2_DUPNAMES = _PCRE2_DUPNAMES
    PCRE2_ENDANCHORED = _PCRE2_ENDANCHORED
    PCRE2_EXTENDED = _PCRE2_EXTENDED
    PCRE2_FIRSTLINE = _PCRE2_FIRSTLINE
    PCRE2_LITERAL = _PCRE2_LITERAL
    PCRE2_MATCH_INVALID_UTF = _PCRE2_MATCH_INVALID_UTF
    PCRE2_MATCH_UNSET_BACKREF = _PCRE2_MATCH_UNSET_BACKREF
    PCRE2_MULTILINE = _PCRE2_MULTILINE
    PCRE2_NEVER_BACKSLASH_C = _PCRE2_NEVER_BACKSLASH_C
    PCRE2_NEVER_UCP = _PCRE2_NEVER_UCP
    PCRE2_NEVER_UTF = _PCRE2_NEVER_UTF
    PCRE2_NO_AUTO_CAPTURE = _PCRE2_NO_AUTO_CAPTURE
    PCRE2_NO_AUTO_POSSESS = _PCRE2_NO_AUTO_POSSESS
    PCRE2_NO_DOTSTAR_ANCHOR = _PCRE2_NO_DOTSTAR_ANCHOR
    PCRE2_NO_START_OPTIMIZE = _PCRE2_NO_START_OPTIMIZE
    PCRE2_NO_UTF_CHECK = _PCRE2_NO_UTF_CHECK
    PCRE2_UCP = _PCRE2_UCP
    PCRE2_UNGREEDY = _PCRE2_UNGREEDY
    PCRE2_USE_OFFSET_LIMIT = _PCRE2_USE_OFFSET_LIMIT
    PCRE2_UTF = _PCRE2_UTF


class MatchOption(IntFlag):
    PCRE2_ANCHORED = _PCRE2_ANCHORED
    PCRE2_COPY_MATCHED_SUBJECT = _PCRE2_COPY_MATCHED_SUBJECT
    PCRE2_ENDANCHORED = _PCRE2_ENDANCHORED
    PCRE2_NOTBOL = _PCRE2_NOTBOL
    PCRE2_NOTEOL = _PCRE2_NOTEOL
    PCRE2_NOTEMPTY = _PCRE2_NOTEMPTY
    PCRE2_NOTEMPTY_ATSTART = _PCRE2_NOTEMPTY_ATSTART
    PCRE2_NO_JIT = _PCRE2_NO_JIT
    PCRE2_NO_UTF_CHECK = _PCRE2_NO_UTF_CHECK
    PCRE2_PARTIAL_HARD = _PCRE2_PARTIAL_HARD
    PCRE2_PARTIAL_SOFT = _PCRE2_PARTIAL_SOFT


cdef class Match:
    cdef pcre2_match_data* data
    cdef object inp
    cdef object r
    def __cinit__(self):
        self.data = NULL

    def __dealloc__(self):
        if self.data != NULL:
            pcre2_match_data_free(self.data)
            self.data = NULL

    def __getitem__(self, uint32_t i):
        if self.data == NULL:
            raise ValueError(u'No matched data.')
        cdef uint32_t count = pcre2_get_ovector_count(self.data)
        if count <= 0:
            raise ValueError(u'No match')
        if i >= count:
            raise IndexError(u'No such group')
        cdef PCRE2_UCHAR *buf
        cdef PCRE2_SIZE le
        cdef PCRE2_UCHAR* errbuf
        cdef size_t errsize = sizeof(PCRE2_UCHAR) * 1024
        cdef int re = pcre2_substring_get_bynumber(self.data, i, &buf, &le)
        if re == 0:
            s = buf.decode()
            pcre2_substring_free(buf)
            return s
        elif re == PCRE2_ERROR_UNSET:
            return None
        elif re == PCRE2_ERROR_NOMEMORY:
            raise MemoryError()
        else:
            errbuf = <PCRE2_UCHAR*> malloc(errsize)
            if errbuf == NULL:
                raise MemoryError()
            s = None
            if pcre2_get_error_message(re, errbuf, errsize) > 0:
                s = errbuf.decode()
            free(errbuf)
            raise ValueError(s if s else u'Can not get substring.')

    def __init__(self, unicode inp, r):
        self.inp = inp
        self.r = r

    def end(self) -> int:
        if self.data == NULL:
            raise ValueError(u'No matched data.')
        cdef uint32_t count = pcre2_get_ovector_count(self.data)
        if count <= 0:
            raise ValueError(u'No match')
        cdef PCRE2_SIZE* vect = pcre2_get_ovector_pointer(self.data)
        return vect[1]

    @cached_property
    def endpos(self) -> int:
        return self.end()

    def group(self) -> str:
        if self.data == NULL:
            raise ValueError(u'No matched data.')
        cdef uint32_t count = pcre2_get_ovector_count(self.data)
        if count <= 0:
            raise ValueError(u'No match')
        cdef PCRE2_UCHAR *buf
        cdef PCRE2_SIZE le
        cdef PCRE2_UCHAR* errbuf
        cdef size_t errsize = sizeof(PCRE2_UCHAR) * 1024
        cdef int re = pcre2_substring_get_bynumber(self.data, 0, &buf, &le)
        if re == 0:
            s = buf.decode()
            pcre2_substring_free(buf)
            return s
        elif re == PCRE2_ERROR_NOMEMORY:
            raise MemoryError()
        else:
            errbuf = <PCRE2_UCHAR*> malloc(errsize)
            if errbuf == NULL:
                raise MemoryError()
            s = None
            if pcre2_get_error_message(re, errbuf, errsize) > 0:
                s = errbuf.decode()
            free(errbuf)
            raise ValueError(s if s else u'Can not get substring.')

    def groupdict(self):
        if self.data == NULL:
            raise ValueError(u'No matched data.')
        cdef uint32_t count = pcre2_get_ovector_count(self.data)
        if count <= 0:
            raise ValueError(u'No match')
        cdef PCRE2_UCHAR **li
        cdef re = pcre2_substring_list_get(self.data, &li, NULL)
        if re == PCRE2_ERROR_NOMEMORY:
            raise MemoryError()
        elif re != 0:
            raise ValueError(u'Unexpected error')
        d = {}
        cdef size_t i = 1
        t = self.r.namedtable()
        while li[i] != NULL:
            if i not in t:
                i += 1
                continue
            if li[i][0] == 0 and pcre2_substring_length_bynumber(self.data, i, NULL) != 0:
                if t[i] not in d:
                    d[t[i]] = None
            else:
                if t[i] not in d or d[t[i]] is None:
                    d[t[i]] = li[i].decode()
            i += 1
        while i < count:
            if i in t:
                if t[i] not in d:
                    d[t[i]] = None
            i += 1
        pcre2_substring_list_free(li)
        return d

    def groups(self):
        if self.data == NULL:
            raise ValueError(u'No matched data.')
        cdef uint32_t count = pcre2_get_ovector_count(self.data)
        if count <= 0:
            raise ValueError(u'No match')
        cdef PCRE2_UCHAR **li
        cdef re = pcre2_substring_list_get(self.data, &li, NULL)
        if re == PCRE2_ERROR_NOMEMORY:
            raise MemoryError()
        elif re != 0:
            raise ValueError(u'Unexpected error')
        cdef size_t i = 1
        l = []
        while li[i] != NULL:
            if li[i][0] == 0 and pcre2_substring_length_bynumber(self.data, i, NULL) != 0:
                l.append(None)
            else:
                l.append(li[i].decode())
            i += 1
        while i < count:
            l.append(None)
            i += 1
        pcre2_substring_list_free(li)
        return tuple(l)

    @cached_property
    def lastgroup(self) -> str:
        regs = self.regs
        cdef uint32_t le = len(regs)
        cdef uint32_t i = le - 1
        while i >= 0:
            if regs[i][0] == -1:
                i -= 1
                continue
            break
        if i == 0:
            return None
        t = self.r.namedtable()
        if i in t:
            return t[i]

    @cached_property
    def lastindex(self) -> int:
        if self.data == NULL:
            raise ValueError(u'No matched data.')
        cdef uint32_t count = pcre2_get_ovector_count(self.data)
        if count <= 0:
            raise ValueError(u'No match')
        return count - 1

    @cached_property
    def pos(self) -> int:
        return self.start()

    @cached_property
    def re(self):
        return self.r

    @cached_property
    def regs(self):
        if self.data == NULL:
            raise ValueError(u'No matched data.')
        cdef uint32_t count = pcre2_get_ovector_count(self.data)
        if count <= 0:
            raise ValueError(u'No match')
        cdef PCRE2_SIZE* vect = pcre2_get_ovector_pointer(self.data)
        l = []
        cdef uint32_t i = 0
        while i < count:
            if vect[i * 2] == <PCRE2_SIZE> -1:
                l.append((-1, -1))
            else:
                l.append((vect[i * 2], vect[i * 2 + 1]))
            i += 1
        return tuple(l)

    def span(self) -> (int, int):
        if self.data == NULL:
            raise ValueError(u'No matched data.')
        cdef uint32_t count = pcre2_get_ovector_count(self.data)
        if count <= 0:
            raise ValueError(u'No match')
        cdef PCRE2_SIZE* vect = pcre2_get_ovector_pointer(self.data)
        return (vect[0], vect[1])

    def start(self) -> int:
        if self.data == NULL:
            raise ValueError(u'No matched data.')
        cdef uint32_t count = pcre2_get_ovector_count(self.data)
        if count <= 0:
            raise ValueError(u'No match')
        cdef PCRE2_SIZE* vect = pcre2_get_ovector_pointer(self.data)
        return vect[0]

    @cached_property
    def string(self) -> str:
        return self.inp

    cdef set_data(self, pcre2_match_data* data):
        if data == NULL:
            raise ValueError(u'data is NULL.')
        self.data = data


cdef class PCRE2:
    cdef pcre2_code* code
    def __cinit__(self):
        self.code = NULL

    def __dealloc__(self):
        if self.code != NULL:
            pcre2_code_free(self.code)
            self.code = NULL

    def __init__(self, unicode inp, opt: Option = None):
        if inp is None:
            raise ValueError(u'Empty pattern.')
        cdef uint32_t opts = _PCRE2_UTF | _PCRE2_ALT_BSUX
        cdef int err
        cdef PCRE2_SIZE erroffset
        cdef PCRE2_UCHAR* errbuf
        cdef size_t errsize = sizeof(PCRE2_UCHAR) * 1024
        if isinstance(opt, Option):
            opts = opt.value
        elif isinstance(opt, int):
            opts = opt
        cdef pcre2_code* re = pcre2_compile(<PCRE2_SPTR>PyUnicode_AsUTF8(inp),
                                            PCRE2_ZERO_TERMINATED, opts, &err,
                                            &erroffset, NULL)
        if re is NULL:
            errbuf = <PCRE2_UCHAR*> malloc(errsize)
            if errbuf == NULL:
                raise MemoryError()
            s = None
            if pcre2_get_error_message(err, errbuf, errsize) > 0:
                s = u"Error at offset %d: %s" % (erroffset, errbuf.decode())
            free(errbuf)
            raise ValueError(s if s else u'Not invalid')
        self.code = re

    def match(self, unicode inp, opt: MatchOption = None, PCRE2_SIZE startoffset = 0, int search_only = 0) -> Match:
        if inp is None:
            raise ValueError(u'Empty input.')
        if self.code == NULL:
            raise ValueError(u'pattern is NULL.')
        cdef uint32_t opts = 0
        if isinstance(opt, MatchOption):
            opts = opt.value
        elif isinstance(opt, int):
            opts = opt
        cdef pcre2_match_data* data = pcre2_match_data_create_from_pattern(self.code, NULL)
        cdef PCRE2_UCHAR* errbuf
        cdef size_t errsize = sizeof(PCRE2_UCHAR) * 1024
        if data == NULL:
            raise MemoryError()
        cdef int re = pcre2_match(self.code, <PCRE2_SPTR>PyUnicode_AsUTF8(inp),
                                  PCRE2_ZERO_TERMINATED, startoffset, opts, data, NULL)
        if re <= 0:
            pcre2_match_data_free(data)
            data = NULL
            if re == -1:  # No match
                if search_only:
                    return False
                else:
                    return None
            elif re == 0:
                raise ValueError(u'The vector of offsets is too small')
            else:
                errbuf = <PCRE2_UCHAR*> malloc(errsize)
                if errbuf == NULL:
                    raise MemoryError()
                s = None
                if pcre2_get_error_message(re, errbuf, errsize) > 0:
                    s = errbuf.decode()
                free(errbuf)
                raise ValueError(s if s else u'Can not match')
        if search_only:
            pcre2_match_data_free(data)
            return True
        m = Match(inp, self)
        m.set_data(data)
        return m

    def namedtable(self):
        if self.code == NULL:
            raise ValueError(u'pattern is NULL.')
        cdef uint32_t count
        cdef uint32_t ensize
        if pcre2_pattern_info(self.code, PCRE2_INFO_NAMECOUNT, &count) != 0:
            raise ValueError(u'Can not get namedtable')
        if pcre2_pattern_info(self.code, PCRE2_INFO_NAMEENTRYSIZE, &ensize) != 0:
            raise ValueError(u'Can not get namedtable')
        if count <= 0 or ensize <= 0:
            raise ValueError(u'Can not get namedtable')
        cdef PCRE2_SPTR buf
        if pcre2_pattern_info(self.code, PCRE2_INFO_NAMETABLE, &buf) != 0:
            raise ValueError(u'Can not get namedtable')
        cdef uint32_t i = 0
        cdef size_t ind = 0
        cdef char* tmp = <char*> malloc(ensize)
        if tmp == NULL:
            raise MemoryError()
        d = {}
        while i < count:
            ind = i * ensize
            strcpy(tmp, <char*>buf + ind + 2)
            d[buf[ind] * 256 + buf[ind + 1]] = tmp.decode()
            i += 1
        free(tmp)
        return d
