cdef extern from "Python.h":
    void Py_INCREF(object o)
    void Py_DECREF(object o) 
    const char* PyUnicode_AsUTF8(object unicode)
    const char* PyUnicode_AsUTF8AndSize(object unicode, Py_ssize_t *size)
