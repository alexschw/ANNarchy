#
#
#    ANNarchy-4 NeuralField
#
#
from ANNarchy4 import *

setup(verbose=True)
#
# Define the neuron classes
#
Input = Neuron(   
    tau = 1.0,
    noise = Variable(eq=Uniform(0,1)),
    baseline = Variable(init = 0.0),
    mp = Variable(eq = "tau * dmp / dt + mp = baseline + noise"),
    rate = Variable(eq = "rate = pos(mp)"),
    order = ['mp','rate'] 
)

Focus = Neuron( 
    tau = 20.0,
    noise = 0.0,
    baseline = Variable(init=0.0),
    threshold_min = 0.0,
    threshold_max = 1.0,
    mp = Variable(eq = "tau * dmp / dt + mp = sum(exc) - sum(inh) + baseline + noise"),
    rate = Variable(eq = "rate = if mp > threshold_max then threshold_max else pos(mp)", init = 0.0),
    order = ['mp', 'rate']
)

InputPop = Population((20,20), Input)
FocusPop = Population((20,20), Focus)

Proj1 = Projection( 
    pre = InputPop, 
    post = FocusPop, 
    target = 'exc', 
    connector = One2One( weights=1.0 )
)
                    
Proj2 = Projection(
    pre = FocusPop, 
    post = FocusPop, 
    target = 'inh', 
    connector = DoG( 
                   weights=Uniform(0.0,0.1), 
                   amp_pos=0.2, 
                   sigma_pos=0.1, 
                   amp_neg=0.1, 
                   sigma_neg=0.7 
                ) 
)

# Main program
if __name__ == "__main__":

    # Analyse and compile everything, initialize the parameters/variables...
    compile()    

    import pyximport; pyximport.install()
    import BubbleWorld
    
    BubbleWorld.run(InputPop, FocusPop)
