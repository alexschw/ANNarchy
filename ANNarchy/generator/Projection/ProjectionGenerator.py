#===============================================================================
#
#     ProjectionGenerator.py
#
#     This file is part of ANNarchy.
#
#     Copyright (C) 2016-2018  Julien Vitay <julien.vitay@gmail.com>,
#     Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     ANNarchy is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#===============================================================================
from ANNarchy.core import Global
from ANNarchy.core.PopulationView import PopulationView
from ANNarchy.core import Random as ANNRandom
from ANNarchy.extensions.convolution import Transpose

# Useful functions
from ANNarchy.generator.Utils import tabify

class ProjectionGenerator(object):
    """
    Abstract definition of a ProjectionGenerator.
    """
    def __init__(self, profile_generator, net_id):
        """
        Initialization of the class object and store some ids.
        """
        super(ProjectionGenerator, self).__init__()

        self._prof_gen = profile_generator
        self._net_id = net_id

        self._templates = {}
        self._template_ids = {}
        self._connectivity_class = None

        self._cpp_patterns = ["Random", "Random Convergent"]

    def header_struct(self, proj, annarchy_dir):
        """
        Generate and store the projection code in a single header file. The
        name is defined as
        proj%(id)s.hpp.

        Parameters:

            proj: Projection object
            annarchy_dir: working directory

        Returns:

            (str, str): include directive, pointer definition

        Templates:

            header_struct: basic template

        """
        raise NotImplementedError

    def creating(self, proj):
        "Implemented by child class"
        raise NotImplementedError

    def pruning(self, proj):
        "Implemented by child class"
        raise NotImplementedError

    def _computesum_rate(self, proj):
        "Implemented by child class"
        raise NotImplementedError

    def _computesum_spiking(self, proj):
        "Implemented by child class"
        raise NotImplementedError

    def _configure_template_ids(self, proj):
        """
        This function should be called before any other method of the
        Connectivity class is called, as the templates are adapted.
        """
        raise NotImplementedError

    def _select_sparse_matrix_format(self, proj):
        """
        The sparse matrix format determines the fundamental structure for
        connectivity representation. It depends on the model type as well
        as hardware paradigm.

        Returns (str1, str2, bool):

            * str1:     sparse matrix format declaration
            * str2:     sparse matrix format arguments if needed (e. g. sizes)
            * bool:     if the matrix is a complete (True) or sliced matrix (False)
        """
        if Global.config["structural_plasticity"] and proj._storage_format != "lil":
            raise Global.InvalidConfiguration("Structural plasticity is only allowed for LIL format.")

        if proj.synapse_type.type == "rate":
            # Sanity check
            if proj._storage_order == "pre_to_post":
                Global.CodeGeneratorException("    The storage_order 'pre_to_post' is invalid for rate-coded synapses (Projection: "+proj.name+")")

            # Check for the provided format + paradigm
            # combination if it's availability

            if proj._storage_format == "lil":
                if Global._check_paradigm("openmp"):
                    if Global.config['num_threads'] == 1:
                        sparse_matrix_format = "LILMatrix<int>"
                        single_matrix = True
                    else:
                        sparse_matrix_format = "LILMatrix<int>"
                        single_matrix = True
                elif Global._check_paradigm("cuda"):
                    sparse_matrix_format = "LILMatrixCUDA<int>"
                    single_matrix = True
                else:
                    Global.CodeGeneratorException("    No implementation assigned for rate-coded synapses using LIL and paradigm="+str(Global.config['paradigm'])+" (Projection: "+proj.name+")")

            elif proj._storage_format == "coo":
                if Global._check_paradigm("openmp"):
                    if Global.config['num_threads'] == 1:
                        sparse_matrix_format = "COOMatrix<int>"
                        single_matrix = True
                    else:
                        sparse_matrix_format = "COOMatrix<int>"
                        single_matrix = True

                elif Global._check_paradigm("cuda"):
                    sparse_matrix_format = "COOMatrixCUDA"
                    single_matrix = True

                else:
                    Global.CodeGeneratorException("    No implementation assigned for rate-coded synapses using COO and paradigm="+str(Global.config['paradigm'])+" (Projection: "+proj.name+")")                

            elif proj._storage_format == "csr":
                sparse_matrix_format = "CSRMatrix <int>" if Global._check_paradigm("openmp") else "CSRMatrixCUDA"
                single_matrix = True

            elif proj._storage_format == "ell":
                sparse_matrix_format = "ELLMatrix<int>"
                single_matrix = True

            elif proj._storage_format == "hyb":
                sparse_matrix_format = "HYBMatrix<int, true>"
                single_matrix = True

            else:
                Global.CodeGeneratorException("    No implementation assigned for rate-coded synapses using '"+proj._storage_format+"' storage format (Projection: "+proj.name+")")

        elif proj.synapse_type.type == "spike":
            # Check for the provided format + paradigm
            # combination if it's availability

            if proj._storage_format == "lil":
                if proj._storage_order == "pre_to_post":
                    Global.CodeGeneratorException("    The storage_order 'pre_to_post' is invalid for LIL representations (Projection: "+proj.name+")")

                if Global._check_paradigm("openmp"):
                    if Global.config['num_threads'] == 1 or proj._no_split_matrix:
                        sparse_matrix_format = "LILInvMatrix<int>"
                        single_matrix = True
                    else:
                        sparse_matrix_format = "ParallelLIL<LILInvMatrix<int>, int>"
                        single_matrix = False

                elif Global._check_paradigm("cuda"):
                    sparse_matrix_format = "LILInvMatrixCUDA <int>"
                    single_matrix = True

                else:
                    Global.CodeGeneratorException("    No implementation assigned for spiking synapses using LIL and paradigm="+str(Global.config['paradigm'])+ " (Projection: "+proj.name+")")

            elif proj._storage_format == "csr":
                if proj._storage_order == "post_to_pre":
                    if Global.config['num_threads'] == 1:
                        sparse_matrix_format = "CSRCMatrix <int>"
                        single_matrix = True
                    else:
                        sparse_matrix_format = "CSRCMatrix <int>"
                        single_matrix = True

                else:
                    if Global.config['num_threads'] == 1:
                        sparse_matrix_format = "CSRCMatrixT <int>"
                        single_matrix = True
                    else:
                        sparse_matrix_format = "CSRCMatrixTOMP <int>"
                        single_matrix = False

            else:
                Global.CodeGeneratorException("    No implementation assigned for spiking synapses using '"+proj._storage_format+"' storage format (Projection: "+proj.name+")")

        else:
            Global.CodeGeneratorException("    Invalid synapse type " + proj.synapse_type.type)

        # HD (6th Oct 2020)
        # Currently I unified this by flipping the dimensions in CSRCMatrixT in the C++ code
        sparse_matrix_args = " %(post_size)s, %(pre_size)s" % {
            'pre_size': proj.pre.population.size if isinstance(proj.pre, PopulationView) else proj.pre.size,
            'post_size': proj.post.population.size if isinstance(proj.post, PopulationView) else proj.post.size
        }

        if Global.config['verbose']:
            print("Selected", sparse_matrix_format, "(", sparse_matrix_args, ")", "for projection ", proj.name, "and single_matrix =", single_matrix )

        return sparse_matrix_format, sparse_matrix_args, single_matrix

    def _connectivity_init(self, proj, sparse_matrix_format, sparse_matrix_args):
        """
        Each of the pre-defined pattern requires probably different initialization values.
        If no C++ implementation for a pattern is available a default construction from
        LIL is set.
        """
        #
        # Define the correct projection init code
        if proj.connector_name == "Random":
            connector_call = """
    void fixed_probability_pattern(std::vector<int> post_ranks, std::vector<int> pre_ranks, double p, double w_dist_arg1, double w_dist_arg2, double d_dist_arg1, double d_dist_arg2, bool allow_self_connections) {
        static_cast<%(sparse_format)s*>(this)->fixed_probability_pattern(post_ranks, pre_ranks, p, allow_self_connections, rng%(rng_idx)s%(num_threads)s);

%(init_weights)s
%(init_delays)s
    }
"""
        elif proj.connector_name == "Random Convergent":
            connector_call = """
    void fixed_number_pre_pattern(std::vector<int> post_ranks, std::vector<int> pre_ranks, unsigned int nnz_per_row, double w_dist_arg1, double w_dist_arg2, double d_dist_arg1, double d_dist_arg2) {
        static_cast<%(sparse_format)s*>(this)->fixed_number_pre_pattern(post_ranks, pre_ranks, nnz_per_row, rng%(rng_idx)s%(num_threads)s);

%(init_weights)s
%(init_delays)s
    }
"""
        else:
            connector_call = """
    void init_from_lil( std::vector<int> &row_indices,
                        std::vector< std::vector<int> > &column_indices,
                        std::vector< std::vector<double> > &values,
                        std::vector< std::vector<int> > &delays) {
        static_cast<%(sparse_format)s*>(this)->init_matrix_from_lil(row_indices, column_indices%(add_args)s%(num_threads)s);

%(init_weights)s
%(init_delays)s

    #ifdef _DEBUG_CONN
        static_cast<%(sparse_format)s*>(this)->print_data_representation();
    #endif
    }
"""

        return connector_call

    def _declaration_accessors(self, proj, single_matrix):
        """
        Generate declaration and accessor code for variables/parameters of the projection.

        Returns:
            (dict, str): first return value contain declaration code and last one the accessor code.

            The declaration dictionary has the following fields:
                delay, event_driven, rng, parameters_variables, additional, cuda_stream
        """
        # create the code for non-specific projections
        declare_event_driven = ""
        declare_rng = ""
        declare_additional = ""

        # Delays
        if proj.max_delay > 1:
            if proj.uniform_delay > 1 :
                key_delay = "uniform"
            else:
                if Global._check_paradigm("cuda"):
                    Global.CodeGeneratorException("Non-uniform delays on rate-coded or spiking synapses are not available for CUDA devices.")

                if proj.synapse_type.type == "rate":
                    key_delay = "nonuniform_rate_coded"
                else:
                    key_delay = "nonuniform_spiking"

            declare_delay = self._templates['delay'][key_delay]['declare']
            init_delay = self._templates['delay'][key_delay]['init']
        else:
            declare_delay = ""
            init_delay = ""

        # Code for declarations and accessors
        declare_parameters_variables, accessor = self._generate_default_get_set(proj, single_matrix)

        # If no psp is defined, it's event-driven
        has_event_driven = False
        for var in proj.synapse_type.description['variables']:
            if var['method'] == 'event-driven':
                has_event_driven = True
                break
        if has_event_driven:
            declare_event_driven = self._templates['event_driven']['declare']

        # Arrays for the random numbers
        if len(proj.synapse_type.description['random_distributions']) > 0:
            declare_rng += """
    // Random numbers
"""
            for rd in proj.synapse_type.description['random_distributions']:
                declare_rng += self._templates['rng'][rd['locality']]['decl'] % {
                    'rd_name' : rd['name'],
                    'type': rd['ctype'],
                    'float_prec': Global.config['precision'],
                    'template': rd['template'] % {'float_prec':Global.config['precision']}
                }

        # Structural plasticity
        if Global.config['structural_plasticity']:
            declare_parameters_variables += self._header_structural_plasticity(proj)

        # Specific projections can overwrite
        if 'declare_parameters_variables' in proj._specific_template.keys():
            declare_parameters_variables = proj._specific_template['declare_parameters_variables']
        if 'access_parameters_variables' in proj._specific_template.keys():
            accessor = proj._specific_template['access_parameters_variables']
        if 'declare_rng' in proj._specific_template.keys():
            declare_rng = proj._specific_template['declare_rng']
        if 'declare_event_driven' in proj._specific_template.keys():
            declare_event_driven = proj._specific_template['declare_event_driven']
        if 'declare_additional' in proj._specific_template.keys():
            declare_additional = proj._specific_template['declare_additional']

        # Finalize the declarations
        declaration = {
            'declare_delay': declare_delay,
            'init_delay': init_delay,            
            'event_driven': declare_event_driven,
            'rng': declare_rng,
            'parameters_variables': declare_parameters_variables,
            'additional': declare_additional
        }

        return declaration, accessor

    def _generate_default_get_set(self, proj, single_matrix):
        """
        Instead of generating a code block with get/set for each variable we generate a common
        function which receives the name of the variable.
        """
        accessor_template = """
    std::vector<std::vector<double>> get_local_attribute_all(std::string name) {
%(local_get1)s

        // should not happen
        std::cerr << "ProjStruct%(id_proj)s::get_local_attribute_all: " << name << " not found" << std::endl;
        return std::vector<std::vector<double>>();
    }

    std::vector<double> get_local_attribute_row(std::string name, int rk_post) {
%(local_get2)s

        // should not happen
        std::cerr << "ProjStruct%(id_proj)s::get_local_attribute_row: " << name << " not found" << std::endl;
        return std::vector<double>();
    }

    double get_local_attribute(std::string name, int rk_post, int rk_pre) {
%(local_get3)s

        // should not happen
        std::cerr << "ProjStruct%(id_proj)s::get_local_attribute: " << name << " not found" << std::endl;
        return 0.0;
    }

    void set_local_attribute_all(std::string name, std::vector<std::vector<double>> value) {
%(local_set1)s
    }

    void set_local_attribute_row(std::string name, int rk_post, std::vector<double> value) {
%(local_set2)s
    }

    void set_local_attribute(std::string name, int rk_post, int rk_pre, double value) {
%(local_set3)s
    }

    std::vector<double> get_semiglobal_attribute_all(std::string name) {
%(semiglobal_get1)s

        // should not happen
        std::cerr << "ProjStruct%(id_proj)s::get_semiglobal_attribute_all: " << name << " not found" << std::endl;
        return std::vector<double>();
    }

    double get_semiglobal_attribute(std::string name, int rk_post) {
%(semiglobal_get2)s

        // should not happen
        std::cerr << "ProjStruct%(id_proj)s::get_semiglobal_attribute: " << name << " not found" << std::endl;
        return 0.0;
    }

    void set_semiglobal_attribute_all(std::string name, std::vector<double> value) {
%(semiglobal_set1)s
    }

    void set_semiglobal_attribute(std::string name, int rk_post, double value) {
%(semiglobal_set2)s
    }

    double get_global_attribute(std::string name) {
%(global_get)s

        // should not happen
        std::cerr << "ProjStruct%(id_proj)s::get_global_attribute: " << name << " not found" << std::endl;
        return 0.0;
    }

    void set_global_attribute(std::string name, double value) {
%(global_set)s
    }
"""

        declare_parameters_variables = ""

        # Attribute accessors/declarators
        local_attribute_get1 = ""
        local_attribute_get2 = ""
        local_attribute_get3 = ""
        local_attribute_set1 = ""
        local_attribute_set2 = ""
        local_attribute_set3 = ""
        semiglobal_attribute_get1 = ""
        semiglobal_attribute_get2 = ""
        semiglobal_attribute_set1 = ""
        semiglobal_attribute_set2 = ""
        global_attribute_get = ""
        global_attribute_set = ""

        # The transpose projection contains synapse parameters, but needs to ignore them ...
        if isinstance(proj, Transpose):
            final_code = accessor_template %{
                'local_get1' : local_attribute_get1,
                'local_get2' : local_attribute_get2,
                'local_get3' : local_attribute_get3,
                'local_set1' : local_attribute_set1,
                'local_set2' : local_attribute_set2,
                'local_set3' : local_attribute_set3,
                'semiglobal_get1' : semiglobal_attribute_get1,
                'semiglobal_get2' : semiglobal_attribute_get2,
                'semiglobal_set1' : semiglobal_attribute_set1,
                'semiglobal_set2' : semiglobal_attribute_set2,
                'global_get' : global_attribute_get,
                'global_set' : global_attribute_set,
                'id_proj': proj.id
            }

            return "", final_code

        # choose templates dependend on the paradigm
        if single_matrix:
            decl_template = self._templates['attribute_decl']
        else:
            decl_template = self._templates['attribute_sliced_matrix_decl']

        attributes = []
        # Parameters
        for var in proj.synapse_type.description['parameters'] + proj.synapse_type.description['variables']:
            # Avoid doublons
            if var['name'] in attributes:
                continue

            locality = var['locality']

            # Special case for single weights
            if var['name'] == "w" and proj._has_single_weight():
                locality = 'global'

            # For GPUs we need to tell GPU that this variable need to be updated
            if Global._check_paradigm("cuda"):
                dirty_flag = "%(name)s_dirty = true;" % {'name': var['name']}
            else:
                dirty_flag = ""

            # code ids
            ids = {
                'type' : var['ctype'],
                'name': var['name'],
                'attr_type': 'parameter',
                'dirty_flag': dirty_flag
            }
            
            #
            # Local variables can be vec[vec[d]], vec[d] or d
            if locality == "local":
                local_attribute_get1 += """
        if ( name.compare("%(name)s") == 0 ) {
            return get_matrix_variable_all<%(type)s>(%(name)s);
        }
""" % ids
                local_attribute_set1 += """
        if ( name.compare("%(name)s") == 0 ) {
            update_matrix_variable_all<%(type)s>(%(name)s, value);
            %(dirty_flag)s
        }
""" % ids
                local_attribute_get2 += """
        if ( name.compare("%(name)s") == 0 ) {
            return get_matrix_variable_row<%(type)s>(%(name)s, rk_post);
        }
""" % ids
                local_attribute_set2 += """
        if ( name.compare("%(name)s") == 0 ) {
            update_matrix_variable_row<%(type)s>(%(name)s, rk_post, value);
            %(dirty_flag)s
        }
""" % ids
                local_attribute_get3 += """
        if ( name.compare("%(name)s") == 0 ) {
            return get_matrix_variable<%(type)s>(%(name)s, rk_post, rk_pre);
        }
""" % ids
                local_attribute_set3 += """
        if ( name.compare("%(name)s") == 0 ) {
            update_matrix_variable<%(type)s>(%(name)s, rk_post, rk_pre, value);
            %(dirty_flag)s
        }
""" % ids

            #
            # Semiglobal variables can be vec[d] or d
            elif locality == "semiglobal":
                semiglobal_attribute_get1 = """
        if ( name.compare("%(name)s") == 0 ) {
            return get_vector_variable_all<%(type)s>(%(name)s);
        }
""" % ids
                semiglobal_attribute_get2 = """
        if ( name.compare("%(name)s") == 0 ) {
            return get_vector_variable<%(type)s>(%(name)s, rk_post);
        }
""" % ids
                semiglobal_attribute_set1 = """
        if ( name.compare("%(name)s") == 0 ) {
            update_vector_variable_all<%(type)s>(%(name)s, value);
            %(dirty_flag)s
        }
""" % (ids)
                semiglobal_attribute_set2 = """
        if ( name.compare("%(name)s") == 0 ) {
            update_vector_variable<%(type)s>(%(name)s, rk_post, value);
            %(dirty_flag)s
        }
""" % (ids)

            #
            # Global variables are only d
            else:
                global_attribute_get += """
        if ( name.compare("%(name)s") == 0 ) {
            return %(name)s;
        }
""" % ids
                global_attribute_set += """
        if ( name.compare("%(name)s") == 0 ) {
            %(name)s = value;
            %(dirty_flag)s
        }
""" % ids

            declare_parameters_variables += decl_template[locality] % ids
            attributes.append(var['name'])


        # build up the final codes
        final_code = accessor_template %{
            'local_get1' : local_attribute_get1,
            'local_get2' : local_attribute_get2,
            'local_get3' : local_attribute_get3,
            'local_set1' : local_attribute_set1,
            'local_set2' : local_attribute_set2,
            'local_set3' : local_attribute_set3,
            'semiglobal_get1' : semiglobal_attribute_get1,
            'semiglobal_get2' : semiglobal_attribute_get2,
            'semiglobal_set1' : semiglobal_attribute_set1,
            'semiglobal_set2' : semiglobal_attribute_set2,
            'global_get' : global_attribute_get,
            'global_set' : global_attribute_set,
            'id_proj': proj.id
        }

        return declare_parameters_variables, final_code

    @staticmethod
    def _get_attr_and_type(proj, name):
        """
        Small helper function, used for instance in self.update_spike_neuron().

        For a given variable name, the data container is searched and checked,
        whether it is a local or global variable, a random variable or a
        variable related to global operations.

        **Hint**:

        Returns (None, None) by default, if none of this cases is true, indicating
        an error in code generation procedure.
        """
        desc = proj.synapse_type.description
        for attr in desc['parameters']:
            if attr['name'] == name:
                return 'var', attr

        for attr in desc['variables']:
            if attr['name'] == name:
                return 'par', attr

        for attr in desc['random_distributions']:
            if attr['name'] == name:
                return 'rand', attr

        return None, None

    def _header_structural_plasticity(self, proj):
        "Implemented by child class"
        raise NotImplementedError

    def _init_parameters_variables(self, proj, single_spmv_matrix):
        """
        Generate initialization code for variables / parameters of the
        projection *proj*.

        Returns 3 values:

            ret1 (str): weight initialization
            ret2 (str): delay initialization
            ret3 (str): other initializations (e. g. event-driven)
        """
        # Is it a specific projection?
        if 'init_parameters_variables' in proj._specific_template.keys():
            return proj._specific_template['init_parameters_variables']

        # Learning by default
        code = ""
        weight_code = ""

        # choose initialization templates based on chosen paradigm
        attr_init_tpl = self._templates['attribute_cpp_init']

        attributes = []

        # Initialize parameters
        for var in proj.synapse_type.description['parameters'] + proj.synapse_type.description['variables']:
            # Avoid doublons
            if var['name'] in attributes:
                continue

            if var['name'] == 'w':
                if var['locality'] == "global" or proj._has_single_weight():
                    if proj.connector_name in self._cpp_patterns:
                        weight_code = tabify("w = w_dist_arg1;", 2)
                    else:
                        weight_code = tabify("w = values[0][0];", 2)
                    
                elif var['locality'] == "local":
                    if proj.connector_name in self._cpp_patterns:   # Init weights in CPP
                        if proj.connector_weight_dist == None:
                            init_code = self._templates['attribute_cpp_init']['local'] % {
                                'init': 'w_dist_arg1',
                                'type': var['ctype'],
                                'attr_type': 'parameter' if var in proj.synapse_type.description['parameters'] else 'variable',
                                'name': var['name']
                            }
                        elif isinstance(proj.connector_weight_dist, ANNRandom.Uniform):
                            if single_spmv_matrix:
                                init_code = "w = init_matrix_variable_uniform<%(float_prec)s>(w_dist_arg1, w_dist_arg2, rng[0]);"
                            else:
                                init_code = "w = init_matrix_variable_uniform<%(float_prec)s>(w_dist_arg1, w_dist_arg2, rng);"
                        elif isinstance(proj.connector_weight_dist, ANNRandom.Normal):
                            if single_spmv_matrix:
                                init_code = "w = init_matrix_variable_normal<%(float_prec)s>(w_dist_arg1, w_dist_arg2, rng[0]);"
                            else:
                                init_code = "w = init_matrix_variable_normal<%(float_prec)s>(w_dist_arg1, w_dist_arg2, rng);"
                        else:
                            raise NotImplementedError( str(type(proj.connector_weight_dist)) + " is not available.")

                        if Global._check_paradigm("cuda"):
                            init_code += "\ngpu_w = init_matrix_variable_gpu<%(float_prec)s>(w);"

                        weight_code = tabify(init_code % {'float_prec': Global.config['precision']}, 2)

                    else:   # Init_from_lil
                        init = 'false' if var['ctype'] == 'bool' else ('0' if var['ctype'] == 'int' else '0.0')
                        weight_code = attr_init_tpl[var['locality']] % {
                            'id': proj.id,
                            'id_post': proj.post.id,
                            'name': var['name'],
                            'type': var['ctype'],
                            'init': init,
                            'attr_type': 'parameter' if var in proj.synapse_type.description['parameters'] else 'variable',
                            'float_prec': Global.config['precision']
                        }                        
                        weight_code += tabify("update_matrix_variable_all<%(float_prec)s>(w, values);" % {'float_prec': Global.config['precision']}, 2)

                else:
                    raise NotImplementedError
            else:
                init = 'false' if var['ctype'] == 'bool' else ('0' if var['ctype'] == 'int' else '0.0')
                code += attr_init_tpl[var['locality']] % {
                    'id': proj.id,
                    'id_post': proj.post.id,
                    'name': var['name'],
                    'type': var['ctype'],
                    'init': init,
                    'attr_type': 'parameter' if var in proj.synapse_type.description['parameters'] else 'variable',
                    'float_prec': Global.config['precision']
                }

            attributes.append(var['name'])

        # Initialize delays differs for construction from LIL or CPP inited patterns
        if proj.max_delay > 1:
            # uniform delay
            if proj.connector_delay_dist == None:
                if proj.connector_name in self._cpp_patterns:
                    delay_code = tabify("delay = d_dist_arg1;", 2)
                else:
                    delay_code = self._templates['delay']['uniform']['init']

            # non-uniform delay
            elif isinstance(proj.connector_delay_dist, ANNRandom.Uniform):
                if proj.connector_name in self._cpp_patterns:
                    rng_init = "rng[0]" if single_spmv_matrix else "rng"
                    delay_code = tabify("""
delay = init_matrix_variable_discrete_uniform<int>(d_dist_arg1, d_dist_arg2, %(rng_init)s);
max_delay = -1;""" % {'id_pre': proj.pre.id, 'rng_init': rng_init}, 2)
                else:
                    id_pre = proj.pre.id if not isinstance(proj.pre, PopulationView) else proj.pre.population.id
                    if proj.synapse_type.type == "rate":
                        delay_code = self._templates['delay']['nonuniform_rate_coded']['init'] % {'id_pre': id_pre}
                    else:
                        delay_code = self._templates['delay']['nonuniform_spiking']['init'] % {'id_pre': id_pre}
            else:
                raise NotImplementedError( str(type(proj.connector_weight_dist)) + " is not available.")
        else:
            delay_code = ""

        # If no psp is defined, it's event-driven
        has_event_driven = False
        for var in proj.synapse_type.description['variables']:
            if var['method'] == 'event-driven':
                has_event_driven = True
                break
        if has_event_driven:
            code += self._templates['event_driven']['cpp_init']

        # Pruning
        if Global.config['structural_plasticity']:
            if 'pruning' in proj.synapse_type.description.keys():
                code += """
        // Pruning
        _pruning = false;
        _pruning_period = 1;
        _pruning_offset = 0;
"""
            if 'creating' in proj.synapse_type.description.keys():
                code += """
        // Creating
        _creating = false;
        _creating_period = 1;
        _creating_offset = 0;
"""

        return weight_code, delay_code, code

    def _init_random_distributions(self, proj):
        "Implemented by child class"
        raise NotImplementedError

    def _local_functions(self, proj):
        "Implemented by child class"
        raise NotImplementedError

    def _post_event(self, proj):
        "Implemented by child class"
        raise NotImplementedError

    def _update_random_distributions(self, proj):
        "Implemented by child class"
        raise NotImplementedError

    def _update_synapse(self, proj):
        "Implemented by child class"
        raise NotImplementedError

    def _determine_size_in_bytes(self, proj):
        """
        Generate code template to determine size in bytes for the C++ object *proj*. Please note, that this contain only
        default elementes (parameters, variables). User defined elements, parallelization support data structures or similar
        are not considered.

        Consequently implementing generators should extent the resulting code template. This is done by the 'size_in_bytes'
        field in the _specific_template dictionary.
        """
        if 'size_in_bytes' in proj._specific_template.keys():
            return proj._specific_template['size_in_bytes']

        from ANNarchy.generator.Utils import tabify
        code = ""

        # Connectivity
        sparse_matrix_format, _, _ = self._select_sparse_matrix_format(proj)
        code += """
// connectivity
size_in_bytes += static_cast<%(spm)s*>(this)->size_in_bytes();
""" % {'spm': sparse_matrix_format}

        # Other variables
        for attr in proj.synapse_type.description['variables']+proj.synapse_type.description['parameters']:
            ids = {'ctype': attr['ctype'], 'name': attr['name'], 'locality': attr['locality']}

            if attr in proj.synapse_type.description['parameters']:
                code += "// %(locality)s parameter %(name)s\n" % ids
            else:
                code += "// %(locality)s variable %(name)s\n" % ids

            if attr['name'] == "w" and proj._has_single_weight():
                code += "size_in_bytes += sizeof(%(ctype)s);\t// %(name)s\n" % ids
                continue

            if attr['locality'] == "global":
                code += "size_in_bytes += sizeof(%(ctype)s);\t// %(name)s\n" % ids
            elif attr['locality'] == "semiglobal":
                code += "size_in_bytes += sizeof(%(ctype)s) * %(name)s.capacity();\n" % ids
            else:
                if proj._storage_format == "lil":
                    code += """size_in_bytes += sizeof(%(ctype)s) * %(name)s.capacity();
for(auto it = %(name)s.begin(); it != %(name)s.end(); it++)
    size_in_bytes += (it->capacity()) * sizeof(%(ctype)s);\n""" % ids
                elif proj._storage_format == "csr":
                    code += """size_in_bytes += sizeof(%(ctype)s) * %(name)s.capacity();""" % ids
                elif proj._storage_format == "hyb":
                    code += """size_in_bytes += (%(name)s.ell.capacity()) * sizeof(%(ctype)s);\n""" % ids
                    code += """size_in_bytes += (%(name)s.coo.capacity()) * sizeof(%(ctype)s);\n""" % ids
                else:
                    # TODO: sanity check???
                    pass

        code = tabify(code, 2)
        return code

    def _clear_container(self, proj):
        """
        Generate code template to destroy allocated container of the C++ object *proj*.

        User defined elements, parallelization support data structures or similar are not considered. Consequently
        implementing generators should extent the resulting code template.
        """
        from ANNarchy.generator.Utils import tabify
        code = ""

        # Variables
        code += "// Variables\n"
        for attr in proj.synapse_type.description['variables']:
            # HD: clear alone does not deallocate, it only resets size.
            #     So we need to call shrink_to_fit afterwards.
            ids = {'ctype': attr['ctype'], 'name': attr['name']}
            code += "%(name)s.clear();\n" % ids
            code += "%(name)s.shrink_to_fit();\n" % ids

        code = tabify(code, 2)
        return "" #code


######################################
### Code generation
######################################
def get_bounds(param):
    """
    Analyses the bounds of a variables used in pre- and post-spike
    statements in a synapse description and returns a code template.
    """
    code = ""
    for bound, val in param['bounds'].items():
        if bound == "init":
            continue

        # Min-Max bounds
        code += """if(%(var)s%(index)s %(operator)s %(val)s)
    %(var)s%(index)s = %(val)s;
""" % {
        'index': "%(local_index)s",
        'var' : param['name'],
        'val' : val,
        'operator': '<' if bound == 'min' else '>'
      }
    return code
