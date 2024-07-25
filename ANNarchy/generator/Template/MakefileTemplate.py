"""
MAKEFILE templates.

:copyright: Copyright 2013 - now, see AUTHORS.
:license: GPLv2, see LICENSE for details.
"""

# Linux, Seq or OMP
linux_omp_template = """# CMakeLists.txt generated by ANNarchy
cmake_minimum_required(VERSION 3.20)

set(MODULE_NAME "ANNarchyCore%(net_id)s")
set(CMAKE_CXX_COMPILER "%(compiler)s")

project(${MODULE_NAME})

add_custom_command(
    OUTPUT ANNarchyCore%(net_id)s.cpp
    COMMAND "%(cython)s"
    ARGS "-%(py_major)s" "--cplus" "%(cython_ext)s" "-D" "ANNarchyCore%(net_id)s.pyx"
    DEPENDS ANNarchyCore%(net_id)s.pyx
)

# Only affects the C++ compilation!
# Additional paths
include_directories(
    %(python_include)s
    %(numpy_include)s
    %(annarchy_include)s
)
# Additional compiler flags (-fPIC will is added already)
add_compile_options(%(cpu_flags)s -fopenmp -std=c++17)
add_link_options(%(cpu_flags)s -fopenmp -std=c++17)

# Compile source files and generate shared library
add_library(
    # Target name
    ${MODULE_NAME}
    # target is shared library
    SHARED
    # source files (will trigger above command)
    ${MODULE_NAME}.cpp
    ANNarchy.cpp
)

# supress "lib" prefix
set_target_properties(${MODULE_NAME} PROPERTIES PREFIX "")

# After successful compilation move the shared library 
add_custom_command(
    TARGET ${MODULE_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy ${MODULE_NAME}.so ../../
)
"""

# Linux, CUDA
linux_cuda_template = """# Makefile generated by ANNarchy
all:
\t%(cython)s -%(py_major)s --cplus %(cython_ext)s -D ANNarchyCore%(net_id)s.pyx
\t%(gpu_compiler)s %(gpu_flags)s -std=c++14 -c -Xcompiler %(xcompiler_flags)s-std=c++14,-fPIC, ANNarchyKernel.cu -o ANNarchyKernel.o
\t%(compiler)s %(cpu_flags)s -std=c++14 -fPIC -shared \\
        *.cpp ANNarchyKernel.o -o ANNarchyCore%(net_id)s.so \\
        %(python_include)s -I%(numpy_include)s -I%(annarchy_include)s \\
        %(cython_ext)s \\
        %(python_lib)s \\
        %(gpu_ldpath)s \\
        %(python_libpath)s -lcurand -lcudart %(extra_libs)s
\tmv ANNarchyCore%(net_id)s.so ../..

clean:
\trm -rf *.o
\trm -rf *.so
"""

# OSX, with clang, Seq only
osx_clang_template = """# Makefile generated by ANNarchy
all:
\t%(cython)s -%(py_major)s --cplus %(cython_ext)s -D ANNarchyCore%(net_id)s.pyx
\t%(compiler)s -stdlib=libc++ -std=c++14 -dynamiclib -flat_namespace %(cpu_flags)s -fpermissive %(openmp)s \\
        *.cpp -o ANNarchyCore%(net_id)s.so \\
        %(python_include)s -I%(numpy_include)s -I%(annarchy_include)s \\
        %(cython_ext)s \\
        %(python_lib)s \\
        %(python_libpath)s  %(extra_libs)s
\tmv ANNarchyCore%(net_id)s.so ../..

clean:
\trm -rf *.o
\trm -rf *.so
"""

# OSX, with gcc, OpenMP
osx_gcc_template = """# Makefile generated by ANNarchy
all:
\t%(cython)s -%(py_major)s --cplus %(cython_ext)s -D ANNarchyCore%(net_id)s.pyx
\t%(compiler)s -std=c++14 -dynamiclib -flat_namespace %(cpu_flags)s -fpermissive %(openmp)s \\
        *.cpp -o ANNarchyCore%(net_id)s.so \\
        %(python_include)s -I%(numpy_include)s -I%(annarchy_include)s  -I%(thirdparty_include)s \\
        %(cython_ext)s \\
        %(python_lib)s \\
        %(python_libpath)s  %(extra_libs)s
\tmv ANNarchyCore%(net_id)s.so ../..

clean:
\trm -rf *.o
\trm -rf *.so
"""
