from setuptools import setup, Extension

# Compile the C shared object containing functions to call through ctypes. It
# isn't technically a Python C extension, but this is the easiest way to build
# it in a cross-platform way.

setup(
    name="pyperformance_bm_ctypes",
    ext_modules=[Extension("bm_ctypes.cmodule", sources=["cmodule.c"])],
    package_dir={"bm_ctypes": "src"},
)
