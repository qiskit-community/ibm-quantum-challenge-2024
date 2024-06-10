# transpile_parallel.py

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_transpiler_service.transpiler_service import TranspilerService
from qiskit_serverless import get_arguments, save_result, distribute_task, get
from qiskit_ibm_runtime import QiskitRuntimeService
from timeit import default_timer as timer

@distribute_task(target={"cpu": 2})
def transpile_parallel(circuit: QuantumCircuit, config):
    """Distributed transpilation for an abstract circuit into an ISA circuit for a given backend."""
    transpiled_circuit = config.run(circuit)
    return transpiled_circuit


# Get program arguments
arguments = get_arguments()
circuits = arguments.get("circuits")
backend_name = arguments.get("backend_name")

# Get backend
service = QiskitRuntimeService(channel="ibm_quantum")
backend = service.get_backend(backend_name)

# Define Configs
optimization_levels = "# Add your code here"
pass_managers = [generate_preset_pass_manager(optimization_level=level, backend=backend) for level in optimization_levels]

transpiler_services = [
        TranspilerService( "# Add your code here" ),
        TranspilerService( "# Add your code here" ),
    ]

configs = pass_managers + transpiler_services

# Start process 
print("Starting timer")
start = timer()

# run distributed tasks as async function
# we get task references as a return type
sample_task_references = []
for circuit in circuits:
    sample_task_references.append([transpile_parallel(circuit, config) for config in configs])


# now we need to collect results from task references
results = get([task for subtasks in sample_task_references for task in subtasks])

end = timer()

# Record execution time
execution_time_serverless = end-start
print("Execution time: ", execution_time_serverless)

save_result({
    "transpiled_circuits": results,
    "execution_time" : execution_time_serverless
    
})