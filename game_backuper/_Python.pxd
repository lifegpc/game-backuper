cdef extern from "Python.h":
    const char* PyUnicode_AsUTF8(object unicode)
    const char* PyUnicode_AsUTF8AndSize(object unicode, Py_ssize_t *size)
    int PyBytes_AsStringAndSize(object obj, char **buff, Py_ssize_t *length)
    object PyBytes_FromStringAndSize(const char* v, Py_ssize_t le)
