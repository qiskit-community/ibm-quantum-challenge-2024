import numpy as np
from qiskit import transpile, QuantumCircuit

def version_check():
    import qiskit
    if qiskit.version.VERSION == '1.0.2':
        return print("You have the right version! Enjoy the challenge!")
    else:
        return print("please install right version by copy/paste and execute - %pip install 'qiskit[visualization]' == 1.0.2'")

def transpile_scoring(circ, layout, backend):

    """
    A custom cost function that includes T1 and T2 computed during idle periods

    Parameters:
        circ (QuantumCircuit): circuit of interest
        layouts (list of lists): List of specified layouts
        backend (IBMQBackend): An IBM Quantum backend instance

    Returns:
        float: Fidelity of circ
    """

    fid = 1
    
    touched = set()
    dt = backend.dt
    num_qubits = backend.num_qubits

    error=0
    
    t1s = [backend.qubit_properties(qq).t1 for qq in range(num_qubits)]
    t2s = [backend.qubit_properties(qq).t2 for qq in range(num_qubits)]

    
    for item in circ._data:
        for gate in backend.operation_names:
            if item[0].name == gate:
                if (item[0].name == 'cz') or (item[0].name == 'ecr'):
                    q0 = circ.find_bit(item[1][0]).index
                    q1 = circ.find_bit(item[1][1]).index
                    fid *= 1 - backend.target[item[0].name][(q0, q1)].error
                    touched.add(q0)
                    touched.add(q1)
                elif item[0].name == 'measure':
                    q0 = circ.find_bit(item[1][0]).index
                    fid *= 1 - backend.target[item[0].name][(q0, )].error
                    touched.add(q0)
    
                elif item[0].name == 'delay':
                    q0 = circ.find_bit(item[1][0]).index
                    # Ignore delays that occur before gates
                    # This assumes you are in ground state and errors
                    # do not occur.
                    if q0 in touched:
                        time = item[0].duration * dt
                        fid *= 1-qubit_error(time, t1s[q0], t2s[q0])
                else:
                    q0 = circ.find_bit(item[1][0]).index
                    fid *= 1 - backend.target[item[0].name][(q0, )].error
                    touched.add(q0)

    return fid


def qubit_error(time, t1, t2):
    """Compute the approx. idle error from T1 and T2
    Parameters:
        time (float): Delay time in sec
        t1 (float): T1 time in sec
        t2 (float): T2 time in sec
    Returns:
        float: Idle error
    """
    t2 = min(t1, t2)
    rate1 = 1/t1
    rate2 = 1/t2
    p_reset = 1-np.exp(-time*rate1)
    p_z = (1-p_reset)*(1-np.exp(-time*(rate2-rate1)))/2
    return p_z + p_reset