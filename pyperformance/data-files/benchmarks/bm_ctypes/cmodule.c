#include <Python.h>

#if defined(_WIN32) || defined(__CYGWIN__)
#define EXPORTED_SYMBOL __declspec(dllexport)
#else
#define EXPORTED_SYMBOL
#endif


EXPORTED_SYMBOL
void void_foo_void(void) {

}

EXPORTED_SYMBOL
int int_foo_int(int a) {
    return a + 1;
}

EXPORTED_SYMBOL
void void_foo_int(int a) {

}

EXPORTED_SYMBOL
void void_foo_int_int(int a, int b) {

}

EXPORTED_SYMBOL
void void_foo_int_int_int(int a, int b, int c) {

}

EXPORTED_SYMBOL
void void_foo_int_int_int_int(int a, int b, int c, int d) {

}

EXPORTED_SYMBOL
void void_foo_constchar(const char* str) {

}

PyMODINIT_FUNC
PyInit_cmodule(void) {
  // DELIBERATELY EMPTY

  // This isn't actually a Python extension module (it's used via ctypes), so
  // this entry point function will never be called. However, we are utilizing
  // setuptools to build it, and on Windows, setuptools explicitly passes the
  // flag /EXPORT:PyInit_cmodule, so it must be defined.
  return NULL;
}
