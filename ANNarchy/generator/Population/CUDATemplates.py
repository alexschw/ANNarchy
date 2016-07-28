"""

    CUDATemplates.py

    This file is part of ANNarchy.

    Copyright (C) 2016-2018  Julien Vitay <julien.vitay@gmail.com>,
    Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ANNarchy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
library_header = """#pragma once
extern double dt;
extern long int t;

// RNG - defined in ANNarchy.cu
extern long seed;
extern void init_curand_states( int N, curandState* states, unsigned long seed );

%(include_additional)s
%(extern_global_operations)s
%(struct_additional)s

///////////////////////////////////////////////////////////////
// Main Structure for the population of id %(id)s (%(name)s)
///////////////////////////////////////////////////////////////
struct PopStruct%(id)s{
    int size; // Number of neurons
    bool _active; // Allows to shut down the whole population
    cudaStream_t stream; // assigned stream for concurrent kernel execution ( CC > 2.x )

    // Access functions used by cython wrapper
    int get_size() { return size; }
    bool is_active() { return _active; }
    void set_active(bool val) { _active = val; }
%(declare_spike_arrays)s
    // Neuron specific parameters and variables
%(declare_parameters_variables)s
%(declare_delay)s
%(declare_additional)s
    // Access methods to the parameters and variables
%(access_parameters_variables)s

    // Method called to initialize the data structures
    void init_population() {
        size = %(size)s;
        _active = true;
%(init_parameters_variables)s
%(init_spike)s
%(init_delay)s
%(init_additional)s
    }

    // Method called to reset the population
    void reset() {
%(reset_spike)s
%(reset_delay)s
%(reset_additional)s
    }

    // Method to draw new random numbers
    void update_rng() {
%(update_rng)s
    }

    // Method to enqueue output variables in case outgoing projections have non-zero delay
    void update_delay() {
%(update_delay)s
    }

    // Main method to update neural variables
    void update() {
%(update_variables)s
    }

    %(stop_condition)s
};
"""

population_header = """#pragma once
extern double dt;
extern long int t;

// RNG - defined in ANNarchy.cu
extern long seed;
extern void init_curand_states( int N, curandState* states, unsigned long seed );

%(include_additional)s
%(extern_global_operations)s
%(struct_additional)s

///////////////////////////////////////////////////////////////
// Main Structure for the population of id %(id)s (%(name)s)
///////////////////////////////////////////////////////////////
struct PopStruct%(id)s{
    int size; // Number of neurons
    bool _active; // Allows to shut down the whole population
    cudaStream_t stream; // assigned stream for concurrent kernel execution ( CC > 2.x )

    // Access functions used by cython wrapper
    int get_size() { return size; }
    bool is_active() { return _active; }
    void set_active(bool val) { _active = val; }
%(declare_spike_arrays)s
    // Neuron specific parameters and variables
%(declare_parameters_variables)s
%(declare_delay)s
%(declare_additional)s
    // Access methods to the parameters and variables
%(access_parameters_variables)s

    // Method called to initialize the data structures
    void init_population() {
        size = %(size)s;
        _active = true;
%(init_parameters_variables)s
%(init_spike)s
%(init_delay)s
%(init_additional)s
    }

    // Method called to reset the population
    void reset() {
%(reset_spike)s
%(reset_delay)s
%(reset_additional)s
    }

    // Method to draw new random numbers
    void update_rng() {
%(update_rng)s
    }

    // Method to enqueue output variables in case outgoing projections have non-zero delay
    void update_delay() {
%(update_delay)s
    }

    // Main method to update neural variables
    void update() {
%(update_variables)s
    }

    %(stop_condition)s
};
"""

# c like definition of neuron attributes, whereas 'local' is used if values can vary across
# neurons, consequently 'global' is used if values are common to all neurons.Currently two
# types of sets are defined: openmp and cuda. In cuda case additional 'dirty' flags are
# created.
#
# Parameters:
#
#    type: data type of the variable (double, float, int ...)
#    name: name of the variable
#    attr_type: either 'variable' or 'parameter'
#
attribute_decl = {
    'local': """
    // Local parameter %(name)s
    std::vector< %(type)s > %(name)s;
    %(type)s *gpu_%(name)s;
    bool %(name)s_dirty;
""",
    'global': """
    // Global parameter %(name)s
    %(type)s  %(name)s ;
"""
}

# c like definition of accessors for neuron attributes, whereas 'local' is used if values can vary
# across neurons, consequently 'global' is used if values are common to all neurons. Currently two
# types of sets are defined: openmp and cuda. In cuda case additional 'dirty' flags are created for
# each variable (set to true, in case of setters).
#
# Parameters:
#
#    type: data type of the variable (double, float, int ...)
#    name: name of the variable
#    attr_type: either 'variable' or 'parameter'
#
attribute_acc = {
    'local':
"""
    // Local %(attr_type)s %(name)s
    std::vector< %(type)s > get_%(name)s() { return %(name)s; }
    %(type)s get_single_%(name)s(int rk) { return %(name)s[rk]; }
    void set_%(name)s(std::vector< %(type)s > val) { %(name)s = val; %(name)s_dirty = true; }
    void set_single_%(name)s(int rk, %(type)s val) { %(name)s[rk] = val; %(name)s_dirty = true; }
""",
    'global':
"""
    // Global %(attr_type)s %(name)s
    %(type)s get_%(name)s() { return %(name)s; }
    void set_%(name)s(%(type)s val) { %(name)s = val; }
"""
}


# Initialization of parameters due to the init_population method.
#
# Parameters:
#
#    name: name of the variable
#    init: initial value
attribute_cpp_init = {
    'local':
"""
        // Local %(attr_type)s %(name)s
        %(name)s = std::vector<%(type)s>(size, %(init)s);
        cudaMalloc(&gpu_%(name)s, size * sizeof(double));
        cudaMemcpy(gpu_%(name)s, %(name)s.data(), size * sizeof(double), cudaMemcpyHostToDevice);
""",
    'global':
"""
        // Global %(attr_type)s %(name)s
        %(name)s = %(init)s;
"""
}

attribute_delayed = {
   'local': """
    gpu_delayed_%(var)s = std::deque< double* >(%(delay)s, NULL);
    for ( int i = 0; i < %(delay)s; i++ )
        cudaMalloc( (void**)& gpu_delayed_%(var)s[i], sizeof(double) * size);
""",
    'global': "//TODO: implement code template",
    'reset' : """
    for ( int i = 0; i < gpu_delayed_%(var)s.size(); i++ ) {
        cudaMemcpy( gpu_delayed_%(var)s[i], gpu_%(var)s, sizeof(double) * size, cudaMemcpyDeviceToDevice );
    }
"""
}
# Definition for the usage of CUDA device random
# number generators
#
# Parameters:
#
#    rd_name:
#    rd_update:
curand = {
    'local': {
        'decl': """
    curandState* gpu_%(rd_name)s;
""",
        'init': """
        cudaMalloc((void**)&gpu_%(rd_name)s, size * sizeof(curandState));
        init_curand_states( size, gpu_%(rd_name)s, seed );
#ifdef _DEBUG
        cudaError_t err = cudaGetLastError();
        if ( err != cudaSuccess )
            std::cout << "pop%(id)s - init_population: " << cudaGetErrorString(err) << std::endl;
#endif
"""
    },
    'global': {
        'decl': """
    curandState* gpu_%(rd_name)s;
""",
        'init': """
        cudaMalloc((void**)&gpu_%(rd_name)s, sizeof(curandState));
        init_curand_states( 1, gpu_%(rd_name)s, seed );
#ifdef _DEBUG
        cudaError_t err = cudaGetLastError();
        if ( err != cudaSuccess )
            std::cout << "pop%(id)s - init_population: " << cudaGetErrorString(err) << std::endl;
#endif
"""
    }
}

rate_psp = {
   'decl': """
    std::vector<double> _sum_%(target)s;
    double* gpu__sum_%(target)s;
""",
   'init': """
        // Post-synaptic potential
        _sum_%(target)s = std::vector<double>(size, 0.0);
        cudaMalloc((void**)&gpu__sum_%(target)s, size * sizeof(double));
        cudaMemcpy(gpu__sum_%(target)s, _sum_%(target)s.data(), size * sizeof(double), cudaMemcpyHostToDevice);
"""
}

spike_specific = {
    'declare_spike': """
    // Structures for managing spikes
    std::vector<long int> last_spike;
    long int* gpu_last_spike;
    std::vector<int> spiked;
    int* gpu_spiked;
    unsigned int num_events;
    unsigned int* gpu_num_events;
""",
    'init_spike': """
        // Spiking variables
        spiked = std::vector<int>();
        cudaMalloc((void**)&gpu_spiked, size * sizeof(int)); // we can't reallocate dynamically on the device, therefore we allocate max. possible request

        last_spike = std::vector<long int>(size, -10000L);
        cudaMalloc((void**)&gpu_last_spike, size * sizeof(long int));
        cudaMemcpy(gpu_last_spike, last_spike.data(), size * sizeof(long int), cudaMemcpyHostToDevice);

        cudaMalloc((void**)&gpu_num_events, sizeof(unsigned int));
        num_events = 0;
        cudaMemcpy(gpu_num_events, &num_events, sizeof(unsigned int), cudaMemcpyHostToDevice);
""",
    'declare_refractory': """
    // Refractory period
    std::vector<int> refractory;
    int *gpu_refractory;
    bool refractory_dirty;
    std::vector<int> refractory_remaining;
    int *gpu_refractory_remaining;""",
    'init_refractory': """
        // Refractory period
        refractory = std::vector<int>(size, 0);
        cudaMalloc((void**)&gpu_refractory, size * sizeof(int));
        refractory_remaining = std::vector<int>(size, 0);
        cudaMemcpy(gpu_refractory, refractory.data(), size * sizeof(int), cudaMemcpyHostToDevice);
        refractory_dirty = false;
        cudaMalloc((void**)&gpu_refractory_remaining, size * sizeof(int));
        cudaMemcpy(gpu_refractory_remaining, refractory_remaining.data(), size * sizeof(int), cudaMemcpyHostToDevice); 
""",
    'init_event-driven': """
        last_spike = std::vector<long int>(size, -10000L);
""",
    'reset_spike': """
        spiked.clear();
        last_spike.clear();
        last_spike = std::vector<long int>(size, -10000L);
""",
    'reset_refractory': """
        refractory_remaining.clear();
        refractory_remaining = std::vector<int>(size, 0);
        cudaMemcpy(gpu_refractory_remaining, refractory_remaining.data(), size * sizeof(int), cudaMemcpyHostToDevice);
""",
    'pyx_wrapper': """
    # Refractory period
    cpdef np.ndarray get_refractory(self):
        return pop%(id)s.refractory
    cpdef set_refractory(self, np.ndarray value):
        pop%(id)s.refractory = value
        pop%(id)s.refractory_dirty = True
"""
}

population_update_kernel=\
"""
// gpu device kernel for population %(id)s
__global__ void cuPop%(id)s_step(%(default)s%(refrac)s%(tar)s%(var)s%(par)s)
{
    int i = threadIdx.x + blockDim.x * blockIdx.x;

    // Updating global variables of population %(id)s
%(global_eqs)s

    // Updating local variables of population %(id)s
    while ( i < %(pop_size)s )
    {
%(local_eqs)s

        i += blockDim.x * gridDim.x;
    }
}
"""

population_update_call=\
"""
    // Updating the local and global variables of population %(id)s
    if ( pop%(id)s._active ) {
        int nb = ceil ( double( pop%(id)s.size ) / (double)__pop%(id)s__ );

        cuPop%(id)s_step<<< nb, __pop%(id)s__ >>>(
              /* default arguments */
              %(default)s
              /* refractoriness (only spike) */
              %(refrac)s
              /* targets (only rate) */
              %(tar)s
              /* kernel gpu arrays */
              %(var)s
              /* kernel constants */
              %(par)s );
    }

#ifdef _DEBUG
    cudaError_t err_pop_step_%(id)s = cudaGetLastError();
    if(err_pop_step_%(id)s != cudaSuccess)
        std::cout << "pop0_step: " << cudaGetErrorString(err_pop_step_%(id)s) << std::endl;
#endif
"""

spike_gather_kernel=\
"""
// gpu device kernel for population %(id)s
__global__ void cuPop%(id)s_spike_gather( %(default)s%(refrac)s%(args)s )
{
    int i = threadIdx.x;
    *num_events = 0;
    __syncthreads();

    // Updating local variables of population %(id)s
    while ( i < %(pop_size)s )
    {
%(spike_gather)s

        i += blockDim.x;
    }
}
"""

spike_gather_call =\
"""
    // Check if neurons emit a spike in population %(id)s
    if ( pop%(id)s._active ) {
        cuPop%(id)s_spike_gather<<< 1, __pop%(id)s__ >>>(
              /* default arguments */
              %(default)s
              /* refractoriness */
              %(refrac)s
              /* other variables */
              %(args)s );
    }

    // update event counter
    cudaMemcpy(&pop%(id)s.num_events, pop%(id)s.gpu_num_events, sizeof(int), cudaMemcpyDeviceToHost);

#ifdef _DEBUG
    cudaError_t err_pop_spike_gather_%(id)s = cudaGetLastError();
    if(err_pop_spike_gather_%(id)s != cudaSuccess)
        std::cout << "pop0_spike_gather: " << cudaGetErrorString(err_pop_spike_gather_%(id)s) << std::endl;
#endif
"""

#
# Final dictionary
cuda_templates = {
    'header': library_header,
    'population_header': population_header,
    'attr_decl': attribute_decl,
    'attr_acc': attribute_acc,
    'attribute_cpp_init': attribute_cpp_init,
    'attribute_delayed': attribute_delayed,
    'rng': curand,

    'rate_psp': rate_psp,
    'spike_specific': spike_specific
}