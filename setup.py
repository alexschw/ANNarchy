#!/usr/bin/env python

################################################
# Check if the required packages are installed
################################################
from pkg_resources import parse_version

# check python version
import sys
if not sys.version_info[:2] >= (2, 6):
    print('Error : ANNarchy requires at least Python 2.6.')
    exit(0) 

# setuptools
try:
    from setuptools import setup, find_packages
    print('Checking for setuptools... OK')
except:
    print('Checking for setuptools... NO')
    print('Error : Python package "setuptools" is required.')
    print('You can install it from pip or: http://pypi.python.org/pypi/setuptools')
    exit(0)

# sympy
try:
    import sympy
    
    if parse_version(sympy.__version__) > parse_version('0.7.4'):
        print('Checking for sympy... OK')
    else:
        print 'Sympy', sympy.__version__, 'is not sufficient, expected >= 0.7.4' 
except:
    print('Checking for sympy... NO')
    print('Error : Python package "sympy" is required.')
    print('You can install it from pip or: http://www.sympy.org')
    exit(0)
    
# numpy
try:
    import numpy
    print('Checking for numpy... OK')
except:
    print('Checking for numpy... NO')
    print('Error : Python package "numpy" is required.')
    print('You can install it from pip or: http://www.numpy.org')
    exit(0)

# cython
try:
    import cython
    from Cython.Build import cythonize
    print('Checking for cython... OK')

except:
    print('Checking for cython... NO')
    print('Error : Python package "cython" is required.')
    print('You can install it from pip or: http://www.cython.org')
    exit(0)

################################################
# Perform the installation
################################################
print('Installing ANNarchy on your system')

if sys.platform.startswith("linux"):

    setup(  name='ANNarchy',
            version='4.3.4',
            license='GPLv2 or later',
            platforms='GNU/Linux',
            description='Artificial Neural Networks architect',
            long_description='ANNarchy (Artificial Neural Networks architect) is a simulator for distributed rate-coded or spiking neural networks. The core of the library is written in C++ and distributed using openMP. It provides an interface in Python for the definition of the networks.',
            author='Julien Vitay and Helge Uelo Dinkelbach',
            author_email='julien.vitay@informatik.tu-chemnitz.de',
            url='http://www.tu-chemnitz.de/informatik/KI/projects/ANNarchy/index.php',
            packages=find_packages(),
            package_data={'ANNarchy': ['core/cython_ext/*.pxd']},
            ext_modules = cythonize(
                [   "ANNarchy/core/cython_ext/Connector.pyx", 
                    "ANNarchy/core/cython_ext/Coordinates.pyx",
                    "ANNarchy/core/cython_ext/Transformations.pyx"]
            ),
            include_dirs=[numpy.get_include()],
            zip_safe = False
    )

else:
    #   11.02.2015 (hd)
    #
    #   On darwin-based platforms, the distutils package on python 2.x does not work properly. Building of the ext_modules does not link to clang++ instead the 
    #   C compiler is used. As we include e. g. vector classes this is not correct.
    #
    #   As a solution we cythonize *.pyx and compile the resulting *.cpp to the corresponding shared libraries from hand. Afterwords the created libraries are
    #   copied.
    #
    cwd = os.getcwd()
    os.chdir(cwd+"/ANNarchy/core/cython_ext")
    os.system("make clean && make")
    os.chdir(cwd)

    # setup ANNarchy
    setup(  name='ANNarchy',
        version='4.3.4',
        license='GPLv2 or later',
        platforms='GNU/Linux',
        description='Artificial Neural Networks architect',
        long_description='ANNarchy (Artificial Neural Networks architect) is a simulator for distributed rate-coded or spiking neural networks. The core of the library is written in C++ and distributed using openMP. It provides an interface in Python for the definition of the networks.',
        author='Julien Vitay and Helge Uelo Dinkelbach',
        author_email='julien.vitay@informatik.tu-chemnitz.de',
        url='http://www.tu-chemnitz.de/informatik/KI/projects/ANNarchy/index.php',
        packages=find_packages(),
        package_data={'ANNarchy': ['core/cython_ext/*.pxd','core/cython_ext/*.so']},
        include_dirs=[numpy.get_include()],
        zip_safe = False,
)