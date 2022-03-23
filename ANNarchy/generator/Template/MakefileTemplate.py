# Linux, Seq or OMP
linux_omp_template = """# Makefile generated by ANNarchy
all:
\t%(cython)s -%(py_major)s --cplus %(cython_ext)s -D ANNarchyCore%(net_id)s.pyx
\t%(compiler)s %(cpu_flags)s -std=c++14 -fPIC -shared %(openmp)s \\
        *.cpp  %(add_sources)s -o ANNarchyCore%(net_id)s.so \\
        %(python_include)s -I%(numpy_include)s -I%(annarchy_include)s \\
        %(cython_ext)s \\
        %(python_lib)s \\
        %(python_libpath)s %(extra_libs)s
\tmv ANNarchyCore%(net_id)s.so ../..

clean:
\trm -rf *.o
\trm -rf *.so
"""

# Linux, CUDA
linux_cuda_template = """# Makefile generated by ANNarchy
all:
\t%(cython)s -%(py_major)s --cplus %(cython_ext)s -D ANNarchyCore%(net_id)s.pyx
\t%(gpu_compiler)s %(gpu_flags)s -std=c++14 -c -Xcompiler -std=c++14,-fPIC, ANNarchyDevice.cu -o ANNarchyDevice.o
\t%(gpu_compiler)s %(cuda_gen)s %(gpu_flags)s -Xcompiler %(cpu_flags)s-std=c++14,-fPIC,-shared \\
        ANNarchyHost.cu *.cpp ANNarchyDevice.o -o ANNarchyCore%(net_id)s.so \\
        %(python_include)s -I%(numpy_include)s -I%(annarchy_include)s \\
        %(cython_ext)s \\
        %(python_lib)s \\
        %(gpu_ldpath)s \\
        %(python_libpath)s %(extra_libs)s
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
        %(python_include)s -I%(numpy_include)s -I%(annarchy_include)s \\
        %(cython_ext)s \\
        %(python_lib)s \\
        %(python_libpath)s  %(extra_libs)s
\tmv ANNarchyCore%(net_id)s.so ../..

clean:
\trm -rf *.o
\trm -rf *.so
"""
