# ANNarchy 

[![DOI](https://zenodo.org/badge/57382690.svg)](https://zenodo.org/badge/latestdoi/57382690)


ANNarchy (Artificial Neural Networks architect) is a parallel and hybrid simulator for distributed rate-coded or spiking neural networks. The core of the library is written in C++ and distributed using openMP or CUDA. It provides an interface in Python for the definition of the networks. It is released under the [GNU GPL v2 or later](http://www.gnu.org/licenses/gpl.html).

* Source code: [github.com/ANNarchy/ANNarchy](https://github.com/ANNarchy/ANNarchy)
* Documentation: [annarchy.github.io](https://annarchy.github.io)
* Forum: [google forum](https://groups.google.com/forum/#!forum/annarchy)
* Bug reports and feature requests: [Issue Tracker](https://github.com/ANNarchy/ANNarchy/issues).

### Citation

If you use ANNarchy for your research, we would appreciate if you cite the following paper:

> Vitay J, Dinkelbach HÜ and Hamker FH (2015). ANNarchy: a code generation approach to neural simulations on parallel hardware. *Frontiers in Neuroinformatics* 9:19. [doi:10.3389/fninf.2015.00019](http://dx.doi.org/10.3389/fninf.2015.00019)

### Authors

* Julien Vitay (julien.vitay@informatik.tu-chemnitz.de).
* Helge Ülo Dinkelbach (helge-uelo.dinkelbach@informatik.tu-chemnitz.de).
* Fred Hamker (fred.hamker@informatik.tu-chemnitz.de).

## Installation

Using pip, you can install the latest stable release:

```
pip install ANNarchy
```

See <https://annarchy.github.io/Installation.html> for further instructions.

## Platforms

* GNU/Linux
* MacOS X

## Dependencies

* python >= 3.10 with development files
* g++ >= 7.4 or clang++ >= 3.4
* Cython >= 3.0
* numpy >= 1.13
* sympy >= 1.11
* scipy >= 1.9
* matplotlib >= 3.0
 
Recommended:

* lxml
* pandoc 
* tensorboardX
* tensorflow
