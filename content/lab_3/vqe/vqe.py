from qiskit_aer import AerSimulator
import logging
from typing import Optional
import time
import numpy as np
from scipy.optimize import minimize

from qiskit import QuantumCircuit
from qiskit_ibm_runtime import (
    EstimatorV2 as Estimator,
    SamplerV2 as Sampler,
    QiskitRuntimeService,
    Session,
)
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_serverless import (
    distribute_task,
    get_arguments,
    get,
    save_result,
)

def run(params, ansatz, hamiltonian, estimator, callback_dict):
    """Return callback function that uses Estimator instance,
    and stores intermediate values into a dictionary.

    Parameters:
        params (ndarray): Array of ansatz parameters
        ansatz (QuantumCircuit): Parameterized ansatz circuit
        hamiltonian (SparsePauliOp): Operator representation of Hamiltonian
        estimator (Estimator): Estimator primitive instance
        callback_dict (dict): Mutable dict for storing values

    Returns:
        Callable: Callback function object
    """
    result = estimator.run([(ansatz, [hamiltonian], [params])]).result()
    energy = result[0].data.evs[0]
    
    # Keep track of the number of iterations
    callback_dict["iters"] += 1
    # Set the prev_vector to the latest one
    callback_dict["prev_vector"] = params
    # Compute the value of the cost function at the current vector
    callback_dict["cost_history"].append(energy)
    # Grab the current time
    current_time = time.perf_counter()
    # Find the total time of the execute (after the 1st iteration)
    if callback_dict["iters"] > 1:
        callback_dict["_total_time"] += current_time - callback_dict["_prev_time"]
    # Set the previous time to the current time
    callback_dict["_prev_time"] = current_time
    # Compute the average time per iteration and round it
    time_str = (
        round(callback_dict["_total_time"] / (callback_dict["iters"] - 1), 2)
        if callback_dict["_total_time"]
        else "-"
    )
    # Print to screen on single line
    print(
        "Iters. done: {} [Avg. time per iter: {}]".format(
            callback_dict["iters"], time_str
        ),
        end="\r",
        flush=True,
    )
    
    return energy, result


def cost_func(*args, **kwargs):
    """Return estimate of energy from estimator

    Parameters:
        params (ndarray): Array of ansatz parameters
        ansatz (QuantumCircuit): Parameterized ansatz circuit
        hamiltonian (SparsePauliOp): Operator representation of Hamiltonian
        estimator (Estimator): Estimator primitive instance

    Returns:
        float: Energy estimate
    """
    energy, result = run(*args, **kwargs)
    return energy


def run_vqe(initial_parameters, ansatz, operator, estimator, method):
    callback_dict = {
        "prev_vector": None,
        "iters": 0,
        "cost_history": [],
        "_total_time": 0,
        "_prev_time": None,
    }
   
    result = minimize(
        cost_func,
        initial_parameters,
        args=(ansatz, operator, estimator, callback_dict),
        method=method,
    )
    return result, callback_dict


if __name__ == "__main__":
    arguments = get_arguments()

    service = arguments.get("service")

    ansatz = arguments.get("ansatz")
    operator = arguments.get("operator")
    method = arguments.get("method", "COBYLA")
    initial_parameters = arguments.get("initial_parameters")
        
    if initial_parameters is None:
        initial_parameters = 2 * np.pi * np.random.rand(ansatz.num_parameters)

    
    if service:
        backend = service.least_busy(operational=True, simulator=False)
    else:
        backend = AerSimulator(method='density_matrix')
        
    if initial_parameters is None:
        initial_parameters = 2 * np.pi * np.random.rand(ansatz.num_parameters)
    
    if service:
        with Session(service=service, backend=backend) as session:
            estimator = Estimator(session=session)
            vqe_result, callback_dict = run_vqe(
                initial_parameters=initial_parameters,
                ansatz=ansatz,
                operator=operator,
                estimator=estimator,
                method=method,
            )
    else:
        estimator = Estimator(backend=backend)
        vqe_result, callback_dict = run_vqe(
            initial_parameters=initial_parameters,
            ansatz=ansatz,
            operator=operator,
            estimator=estimator,
            method=method,
        )
    
    
    save_result(
        {
            "optimal_point": vqe_result.x.tolist(),
            "optimal_value": vqe_result.fun,
            "optimizer_time": callback_dict.get("_total_time", 0),
             "iters": callback_dict["iters"],
            "cost_history" : callback_dict["cost_history"]
        }
    )
