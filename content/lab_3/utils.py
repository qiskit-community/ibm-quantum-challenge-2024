
def plot_execution_times(execution_time_serverless, execution_time_local):
    """
    Plots a comparison of execution times between serverless and local executions.

    Parameters:
    execution_time_serverless (int): Execution time for serverless execution.
    execution_time_local (int): Execution time for local execution.
    """
    # Create labels for the x-axis
    labels = ['Serverless', 'Local']
    
    # Execution times
    execution_times = [execution_time_serverless, execution_time_local]
    
    # Plotting
    plt.figure(figsize=(8, 6))
    bars = plt.bar(labels, execution_times, color=['skyblue', 'orange'])
    
    # Add annotations to display the execution times on the bars
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 1, f'{bar.get_height()}', 
                 ha='center', va='bottom', color='black')
    
    # Adding labels and title
    plt.xlabel('Execution Type')
    plt.ylabel('Execution Time (seconds)')
    plt.title('Comparison of Execution Times: Serverless vs Local')
    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

import matplotlib.pyplot as plt

def process_transpiled_circuits(configs, result):
    """
    Processes transpiled circuits, plots the depths for each configuration chunk, and stores the best circuits.

    Parameters:
    configs (list): List of configuration dictionaries.
    result (dict): Dictionary containing transpiled circuits.

    Returns:
    best_circuits (list): List of best transpiled circuits.
    best_depths (list): List of depths of the best transpiled circuits.
    best_methods (list): List of methods used to obtain the best depths.
    """
    # Helper function to create configuration names
    def get_config_name(config):
        if 'service' in config:
            return f"TranspilerService(ai={config['ai']}, optimization_level={config['optimization_level']})"
        else:
            return f"PassManager(optimization_level={config['optimization_level']})"

    # Generate the full list of configurations to match the number of transpiled circuits
    full_configs = configs * (len(result) // len(configs))

    # Number of results to process in each chunk
    chunk_size = 5

    # Lists to store the best circuits, depths, and methods
    best_circuits = []
    best_depths = []
    best_methods = []

    # Process each chunk of results
    for chunk_start in range(0, len(result), chunk_size):
        chunk_end = chunk_start + chunk_size
        current_chunk = result[chunk_start:chunk_end]
        current_configs = full_configs[chunk_start:chunk_end]

        depths = [transpiled_circuit.depth() for transpiled_circuit in current_chunk]
        config_names = [get_config_name(config) for config in current_configs]
        
        # Find the index of the minimum depth
        min_depth_index = depths.index(min(depths))
        
        # Store the best circuit, depth, and method
        best_circuit = current_chunk[min_depth_index]
        best_depth = depths[min_depth_index]
        best_method = config_names[min_depth_index]
        best_circuits.append(best_circuit)
        best_depths.append(best_depth)
        best_methods.append(best_method)
        
        # Plotting
        plt.figure(figsize=(12, 8))
        bars = plt.bar(range(len(depths)), depths, tick_label=config_names, color='skyblue')
        
        # Highlight the bar with the minimum depth
        bars[min_depth_index].set_color('green')
        
        # Add annotations to highlight the minimum depth
        for i, bar in enumerate(bars):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 1, f'{bar.get_height()}', 
                     ha='center', va='bottom', color='black')
        
        plt.xlabel('Configuration')
        plt.ylabel('Transpiled Circuit Depth')
        plt.title(f'Transpiled result for circuit {chunk_start // chunk_size}')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()
    
    return best_circuits, best_depths, best_methods
