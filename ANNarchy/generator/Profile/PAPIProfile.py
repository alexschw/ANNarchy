"""
:copyright: Copyright 2013 - now, see AUTHORS.
:license: GPLv2, see LICENSE for details.
"""

from ANNarchy.core import Global

from .ProfileGenerator import ProfileGenerator
from .ProfileTemplate import profile_base_template, papi_profile_template, papi_profile_header

class PAPIProfile(ProfileGenerator):
    """
    Extent the generated code by profiling annotations.
    """
    def __init__(self, annarchy_dir, net_id):
        ProfileGenerator.__init__(self, annarchy_dir, net_id)

        Global._warning("The PAPI profiling is deprecated. Please use the CPP11Profile instead.")

    def generate(self):
        """
        Generate Profiling class code, called from Generator instance.
        """
        # Generate header for profiling
        with open(self.annarchy_dir+'/generate/net'+str(self._net_id)+'/Profiling.h', 'w') as ofile:
            ofile.write(self._generate_header())

    def generate_body_dict(self):
        """
        Creates a dictionary, contain profile code snippets.
        """
        body_dict = {
            'prof_include': papi_profile_template['include'],
            'prof_step_pre': papi_profile_template['step_pre'],
            'prof_step_post': papi_profile_template['step_post'],
            'prof_run_pre': papi_profile_template['run_pre'],
            'prof_run_post': papi_profile_template['run_post'],
            'prof_proj_psp_pre': papi_profile_template['proj_psp_pre'],
            'prof_proj_psp_post': papi_profile_template['proj_psp_post'],
            'prof_neur_step_pre': papi_profile_template['neur_step_pre'],
            'prof_neur_step_post': papi_profile_template['neur_step_post']
        }
        return body_dict

    def generate_init_population(self, pop):
        """
        Generate initialization code for population
        """
        declare = """
    Measurement* measure_step;
"""
        init = """        // Profiling
        measure_step = Profiling::get_instance()->register_function("pop", "%(name)s", "step");
""" % {'name': pop.name}

        return declare, init

    def generate_init_projection(self, proj):
        """
        Generate initialization code for projection
        """
        declare = """
    Measurement* measure_psp;
    Measurement* measure_step;
"""
        init = """        // Profiling
        measure_psp = Profiling::get_instance()->register_function("proj", "proj%(id_proj)s", "psp");
        measure_step = Profiling::get_instance()->register_function("proj", "proj%(id_proj)s", "step");
""" % {'id_proj': proj.id}

        return declare, init

    def annotate_computesum_rate(self, proj, code):
        """
        annotate the computesum compuation code
        """
        prof_begin = papi_profile_template['compute_psp']['before']
        prof_end = papi_profile_template['compute_psp']['after']

        prof_code = """
        // first run, measuring average time
        %(prof_begin)s
%(code)s
        %(prof_end)s
""" % {
        'code': code,
        'prof_begin': prof_begin,
        'prof_end': prof_end
        }

        return prof_code

    def annotate_computesum_spiking(self, proj, code):
        """
        annotate the computesum compuation code
        """
        prof_begin = papi_profile_template['compute_psp']['before'] % {'name': 'proj'+str(proj.id)}
        prof_end = papi_profile_template['compute_psp']['after'] % {'name': 'proj'+str(proj.id)}

        prof_code = """
        // first run, measuring average time
        %(prof_begin)s
%(code)s
        %(prof_end)s
""" % {'code': code,
       'prof_begin': prof_begin,
       'prof_end': prof_end
       }
        return prof_code

    def annotate_update_synapse(self, proj, code):
        """
        annotate the update synapse code, generated by ProjectionGenerator.update_synapse()
        """
        prof_begin = papi_profile_template['update_synapse']['before']
        prof_end = papi_profile_template['update_synapse']['after']

        prof_code = """
// first run, measuring average time
%(prof_begin)s
%(code)s
%(prof_end)s
""" % {'code': code,
       'prof_begin': prof_begin,
       'prof_end': prof_end
       }

        return prof_code

    def annotate_update_neuron(self, pop, code):
        """
        annotate the update neuron code
        """
        prof_begin = papi_profile_template['update_neuron']['before'] % {'name': pop.name}
        prof_end = papi_profile_template['update_neuron']['after'] % {'name': pop.name}

        prof_code = """
        // first run, measuring average time
        %(prof_begin)s
%(code)s
        %(prof_end)s
""" % {'code': code,
       'prof_begin': prof_begin,
       'prof_end': prof_end
       }
        return prof_code

    def _generate_header(self):
        """
        generate Profiling.h
        """
        config_xml = """
        _out_file << "  <config>" << std::endl;
        _out_file << "    <paradigm>%(paradigm)s</paradigm>" << std::endl;
        _out_file << "    <num_threads>%(num_threads)s</num_threads>" << std::endl;
        _out_file << "  </config>" << std::endl;
        """ % {
            'paradigm': Global.config["paradigm"],
            'num_threads': Global.config["num_threads"]
        }

        timer_import = "#include <papi.h>"
        timer_start = "long_long _profiler_start;"
        timer_init = """
        // initialize PAPI
        if (PAPI_library_init(PAPI_VER_CURRENT) != PAPI_VER_CURRENT)
            exit(1);

        _profiler_start = PAPI_get_real_usec();
"""

        config = Global.config["paradigm"] + '_'  + str(Global.config["num_threads"]) + 'threads'
        return profile_base_template % {
            'timer_import': timer_import,
            'timer_start_decl': timer_start,
            'timer_init': timer_init,
            'config': config,
            'result_file': "results_%(config)s.xml" % {'config':config} if Global.config['profile_out'] == None else Global.config['profile_out'],
            'config_xml': config_xml,
            'measurement_class': papi_profile_header
        }
