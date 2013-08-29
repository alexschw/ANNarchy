""" 
Generator.py
"""
import os, sys
import subprocess
import shutil

# ANNarchy core informations
import ANNarchy4.core.Global as Global
from ANNarchy4.core.Variable import Attribute   

def create_includes():
    """
    generate 'Includes.h' containing all generated headers.
    """
    pop_header  = ''
    for pop in Global._populations:
        pop_header += '#include "'+pop.name+'.h"\n'

    proj_header = ''
    for synapse in Global._synapses:
        proj_header += '#include "'+ synapse.generator.proj_class['name'] +'.h"\n'

    header = """#ifndef __ANNARCHY_INCLUDES_H__
#define __ANNARCHY_INCLUDES_H__

// population files
%(pop_header)s
// projection files
%(proj_header)s
#endif
""" % { 'pop_header': pop_header, 'proj_header': proj_header}

    with open(Global.annarchy_dir + '/build/Includes.h', mode = 'w') as w_file:
        w_file.write(header)

def update_annarchy_header(cpp_stand_alone):
    """
    update ANNarchy.h dependent on compilation mode (cpp_stand_alone):
        - True: instantiation of population, projection classes and projection instantiation.
        - False: only projection instantiation.
    """
    code = ''
    with open(Global.annarchy_dir+'/build/ANNarchy.h', mode = 'r') as r_file:
        for a_line in r_file:
            if a_line.find('//AddProjection') != -1:
                if(cpp_stand_alone):
                    for proj in Global.projections_:
                        code += proj.generator.generate_cpp_add()
            elif a_line.find('//AddPopulation') != -1:
                if(cpp_stand_alone):
                    for pop in Global.populations_:
                        code += pop.generator.generate_cpp_add()
                        
            elif a_line.find('//createProjInstance') != -1:
                code += a_line
                code += generate_proj_instance_class()
            else:
                code += a_line

    with open(Global.annarchy_dir+'/build/ANNarchy.h', mode='w') as w_file:
        w_file.write(code)

def generate_proj_instance_class():
    """
    The standard ANNarchy core has no knowledge about the full amount of projection
    classes. On the other hand we want to instantiate the object from there. To achieve this
    we introduce a projection instantiation class, which returns a projections instance corresponding
    to the given ID.
    """
    # single cases
    cases_ptr = ''
    for synapse in Global._synapses:
        cases_ptr += """
        case %(id)s:
            return new %(name)s(pre, post, postNeuronRank, target);

""" % { 'id': synapse.generator.proj_class['ID'], 
        'name': synapse.generator.proj_class['name']
    }

    cases_id = ''
    for synapse in Global._synapses:
        cases_id += """
        case %(id)s:
        #ifdef _DEBUG
            std::cout << "Instantiate name=%(name)s and id=%(id)s" << std::endl;
        #endif
            return new %(name)s(preID, postID, postNeuronRank, target);

""" % { 'id': synapse.generator.proj_class['ID'], 
        'name': synapse.generator.proj_class['name']
    }

    # complete code
    code = """class createProjInstance {
public:
    createProjInstance() {};

    Projection* getInstanceOf(int ID, Population *pre, Population *post, int postNeuronRank, int target) {
        switch(ID) {
            case 0:
                return new Projection(pre, post, postNeuronRank, target);
%(case1)s
            default:
                std::cout << "Unknown typeID" << std::endl;
                return NULL;
        }
    }

    Projection* getInstanceOf(int ID, int preID, int postID, int postNeuronRank, int target) {
        switch(ID) {
            case 0:
                return new Projection(preID, postID, postNeuronRank, target);
%(case2)s
            default:
                std::cout << "Unknown typeID" << std::endl;
                return NULL;
        }
    }

};
""" % { 'case1': cases_ptr, 'case2': cases_id }
    return code

def generate_py_extension():
    """
    Hence the amount of code is higher, we decide to split up the code. Nevertheless cython generates 
    one shared library per .pyx file. To retrieve only one library we need to compile only one .pyx file
    which includes all the others. 
    """
    pop_include = ''
    for pop in Global._populations:
        pop_include += 'include \"'+pop.name+'.pyx\"\n'

    proj_include = ''
    for synapse in Global._synapses:
        proj_include += 'include \"'+synapse.generator.proj_class['name']+'.pyx\"\n'

    code = """include "Network.pyx"
include "Simulation.pyx"

%(pop_inc)s  

include "Projection.pyx"
%(proj_inc)s  

include "Connector.pyx"
""" % { 'pop_inc': pop_include,
        'proj_inc': proj_include }

    with open(Global.annarchy_dir+'/pyx/ANNarchyCython.pyx', mode='w') as w_file:
        w_file.write(code)
        
def folder_management():
    """
    ANNarchy is provided as a python package. For compilation a local folder
    'annarchy' is created in the current working directory.
    """
    if os.path.exists(Global.annarchy_dir):
        shutil.rmtree(Global.annarchy_dir, True)
    
    os.mkdir(Global.annarchy_dir)
    os.mkdir(Global.annarchy_dir+'/pyx')
    os.mkdir(Global.annarchy_dir+'/build')

    sources_dir = os.path.abspath(os.path.dirname(__file__)+'/../data')

    for file in os.listdir(sources_dir):
        if not os.path.isdir(os.path.abspath(sources_dir+'/'+file)):
            shutil.copy(sources_dir+'/'+file, Global.annarchy_dir)
            
    for file in os.listdir(sources_dir+'/cpp'):
        shutil.copy(sources_dir+'/cpp/'+file, # src
                    Global.annarchy_dir+'/build/'+file # dest
                    )
        
    for file in os.listdir(sources_dir+'/pyx'):
        shutil.copy(sources_dir+'/pyx/'+file, #src
                    Global.annarchy_dir+'/pyx/'+file #dest
                    )

    sys.path.append(Global.annarchy_dir)

def code_generation(cpp_stand_alone):
    """
    code generation for each population respectively projection object the user defined. 
    
    After this the ANNarchy main header is expanded by the corresponding headers.
    """
    print '\nGenerate files\n'
    for pop in Global._populations:
        pop.generator.generate()

    #
    # create projection cpp class for each synapse
    for synapse in Global._synapses:
        synapse.generator.generate()

    create_includes()

    update_annarchy_header(cpp_stand_alone)

    generate_py_extension()
    
   
def compile(cpp_stand_alone=False, debug_build=False):
    """
    compilation consists roughly of 3 steps:
    
        a) generate user defined classes and cython wrapper
        b) compile ANNarchyCore
        c) compile ANNarchyCython
        
    after this the cythonized objects are instantiated and available for the user. 
    
    Parameter:
    
    * *cpp_stand_alone*: creates a cpp library solely. It's possible to run the simulation, but no interaction possibilities exist. These argument should be always False.
    * *debug_build*: creates a debug version of ANNarchy, which logs the creation of objects and some other data (by default False).
    """
    print Global.version, 'on', sys.platform, '(', os.name,')'
    
    folder_management()
    
    code_generation(cpp_stand_alone)
    
    #
    # create ANNarchyCore.so and py extensions
    print 'Start compilation ...'
    os.chdir(Global.annarchy_dir)
    
    if sys.platform.startswith('linux'):
        #
        # apply +x lost by copy
        os.system('chmod +x compile*')

        if not debug_build:
            proc = subprocess.Popen(['./compile.sh', 'cpp_stand_alone='+str(cpp_stand_alone)])
            proc.wait()
        else:
            proc = subprocess.Popen(['./compiled.sh', 'cpp_stand_alone='+str(cpp_stand_alone)])
            proc.wait()
        
        os.chdir('..')

        if not cpp_stand_alone:

            #
            # bind the py extensions to the corresponding python objects
            import ANNarchyCython
            for pop in Global._populations:
                pop.cyInstance = eval('ANNarchyCython.py'+
                                  pop.name.capitalize()+'()')
                
                #
                #   extend the population by all cythonized variables
                pop.rate = Attribute('rate')
                pop.rank = Attribute('rank')
                pop.tau = Attribute('tau')
                pop.dt = Attribute('dt')
                
                for var in pop.generator.neuron_variables:
                    if var['name'] in Global._pre_def_neuron:
                        continue
                    
                    cmd = 'pop.'+var['name']+' = Attribute(\''+var['name']+'\')'
                    #print cmd
                    exec(cmd)
    
            #
            # instantiate projections
            for proj in Global._projections:
                proj.connect()                        

        else:
            #abort the application after compile ANNarchyCPP
            print '\nCompilation process of ANNarchyCPP completed successful.\n'
            exit(0)
    
    #
    #    compilation for windows based systems
    #
    else:
        #
        # TODO: 
        # implement multiple compilation modes
        # complete reimplement !!!!!
        print 'compilation under windows currently not supported'
        exit(0)
        
        #proc = subprocess.Popen(['compile.bat'], shell=True)
        #proc.wait()

        #if not cpp_stand_alone:
            #
            # bind the py extensions to the corresponding python objects
        #    import ANNarchyCython
        #    for pop in Global.populations_:
        #        pop.cyInstance = eval('ANNarchyCython.py'+
        #                              pop.name.capitalize()+'()')

                #
                #   extend the population by all cythonized variables
        #        for var in pop.generator.neuron_variables:
        #            if not '_rand_' in var['name']:
        #                cmd = 'pop.'+var['name']+' = Attribute(\''+var['name']+'\')'
                        #print cmd
        #                exec(cmd)
    
            #
            # instantiate projections
        #    for proj in Global.projections_:
        #        try:
        #            proj.connect()                        

        #        except:
        #            print 'Error on instantiation of projection'+str(proj.generator.proj_class['ID'])

        #else:
            #abort the application after compile ANNarchyCPP
        #    exit(0)
        
    print '\nCompilation process done.\n'
    
