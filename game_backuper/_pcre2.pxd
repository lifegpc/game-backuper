from libc.stddef cimport size_t
from libc.stdint cimport uint8_t, uint32_t


cdef extern from "_pcre2.h":
    ctypedef uint8_t PCRE2_UCHAR
    ctypedef const uint8_t* PCRE2_SPTR8
    ctypedef PCRE2_SPTR8 PCRE2_SPTR
    ctypedef size_t PCRE2_SIZE
    ctypedef struct pcre2_compile_context:
        pass
    ctypedef struct pcre2_code:
        pass
    ctypedef struct pcre2_match_data:
        pass
    ctypedef struct pcre2_general_context:
        pass
    ctypedef struct pcre2_match_context:
        pass

    pcre2_code *pcre2_compile(PCRE2_SPTR pattern, PCRE2_SIZE length, uint32_t options, int *errorcode, PCRE2_SIZE *erroroffset, pcre2_compile_context *ccontext)
    void pcre2_code_free(pcre2_code *code)
    int pcre2_get_error_message(int errorcode, PCRE2_UCHAR *buffer, PCRE2_SIZE bufflen)
    PCRE2_SPTR pcre2_get_mark(pcre2_match_data *match_data)
    uint32_t pcre2_get_ovector_count(pcre2_match_data *match_data)
    PCRE2_SIZE *pcre2_get_ovector_pointer(pcre2_match_data *match_data)
    int pcre2_match(const pcre2_code *code, PCRE2_SPTR subject, PCRE2_SIZE length, PCRE2_SIZE startoffset, uint32_t options, pcre2_match_data *match_data, pcre2_match_context *mcontext)
    int pcre2_pattern_info(const pcre2_code *code, uint32_t what, void *where)
    pcre2_match_data *pcre2_match_data_create_from_pattern(const pcre2_code *code, pcre2_general_context *gcontext)
    void pcre2_match_data_free(pcre2_match_data *match_data)
    int pcre2_substring_get_bynumber(pcre2_match_data *match_data, uint32_t number, PCRE2_UCHAR **bufferptr, PCRE2_SIZE *bufflen)
    void pcre2_substring_free(PCRE2_UCHAR *buffer)
    int pcre2_substring_length_bynumber(pcre2_match_data *match_data, uint32_t number, PCRE2_SIZE *length)
    void pcre2_substring_list_free(PCRE2_SPTR *list)
    int pcre2_substring_list_get(pcre2_match_data *match_data, PCRE2_UCHAR ***listptr, PCRE2_SIZE **lengthsptr)
