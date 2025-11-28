import os

def get_task_template(user_task):
    return f"""
            You have smolagents tools at your disposal to solve the following coding task:
            {user_task}
    Follow these rules regarding tool calls:
    1. ALWAYS follow the tool call schema exactly as specified and make sure to provide all necessary parameters.
    2. ALWAYS call only the provided tools.
    3. NEVER do unhautorized Python imports.
    4. Provide only valid Python code to the answer.
        """

def get_extended_task_template(user_task):
    return f"""
            You are an expert molecular dynamics (MD) assistant that helps run GROMACS simulations.
            Your primary goal is to guide the user through setting up and running MD simulations.
            You have access to various functions (tools) to interact with GROMACS and manage simulations.
            You have to solve the following coding task:
            {user_task}
    Follow these rules regarding tool calls:
    1. ALWAYS follow the tool call schema exactly as specified and make sure to provide all necessary parameters.
    2. ALWAYS call only the provided tools.
    3. NEVER do unhautorized Python imports.
    4. Provide only valid Python code to the answer.
        """

def get_multi_agent_task_template(user_task):
    return f"""
            You have agents at your disposal to solve the following coding task:
            {user_task}
    Follow these rules regarding agent orchestration:
    1. ALWAYS follow a plan exactly as specified and make sure to provide all necessary parameters.
    2. ALWAYS call only the managed agents.
    3. Managed agents can use only the tools they are authorized to use.
    4. NEVER do unhautorized Python imports.
        """

model_prompt_dict = {
    'Qwen/Qwen2.5-3B-Instruct': [get_task_template, get_multi_agent_task_template],
    'Qwen/Qwen2.5-1.5B-Instruct': [get_extended_task_template],
    'qwen2.5:3b': [get_task_template, get_multi_agent_task_template]
}

def get_model_list():
    return model_prompt_dict.keys()

def get_specific_task_template(model_id, task, is_multi_agent=True):
    if is_multi_agent:
        task_template_idx = 1
    else:
        task_template_idx = 0
    task_template = model_prompt_dict[model_id][task_template_idx](task)
    
    return task_template

def get_user_task_dictionary(pdb_file_path, workspace, force_field, water_model, box_size, concentration, structure_id):
    file_name_with_extension = os.path.basename(pdb_file_path)
    output_prefix, _ = os.path.splitext(file_name_with_extension) 
    gro_file = f"{output_prefix}.gro"
    gro_solvated_file = f"{output_prefix}_solv.gro"
    top_file = f"{output_prefix}.top" 
    user_tasks_dict = {
            "pdb_validation": f"Check if the {str(os.path.abspath(pdb_file_path))} file has a valid PDB structure.",
            "pdb_download": f"Complete only the following task and don't do anything else when completed: Download a structure from the Protein Data Bank. The structure id is {structure_id}. The Workspace is {workspace}",
            "pdb_analysis": f"Analyze the {str(os.path.abspath(pdb_file_path))} file.",
            "remove_water": f"Complete only the following task and don't do anything else when completed: Remove water molecules from the {pdb_file_path} PDB file. The Workspace is {workspace}",
            "pulse_check": "Check if Gromacs in installed.",
            "conversion_to_gro": f"Convert the {pdb_file_path} file into Gromacs format. The Workspace is {workspace}",
            "prepare_files": f"Complete only the following task and don't do anything else when completed: Create the system configuration files. The PDB file path is {pdb_file_path}. The output prefix is {output_prefix}. Force field is {force_field}. The water model is {water_model}. The Workspace is {workspace}",
            "generate_box": f"Complete only the following task and don't do anything else when completed: Prepare a simulation box. The GRO file is {gro_file}. The topology file is {top_file}. The out prefix is {output_prefix}. The box size is {box_size}. The Workspace is {workspace}",
            "add_ions": f"Complete only the following task and don't do anything else when completed: add ions. The GRO file is {gro_solvated_file}. The topology file is {top_file}. The out prefix is {output_prefix}. Concentration is {concentration}. The Workspace is {str(os.path.abspath(workspace))}",
            "energy_minimization": f"Complete only the following task and don't do anything else when completed: Execute energy minimization. Use the simulation box in the workspace. The prefix is em. The Workspace is {str(os.path.abspath(workspace))}",
            "plot_energy": f"Plot the .edr file in the workspace and save it to PNG. The workspace is {workspace}"
        }
    
    return user_tasks_dict

def get_ollama_user_task_dictionary(pdb_file_path, workspace, force_field, water_model, box_size, concentration, structure_id):
    file_name_with_extension = os.path.basename(pdb_file_path)
    output_prefix, _ = os.path.splitext(file_name_with_extension) 
    gro_file = f"{output_prefix}.gro"
    gro_solvated_file = f"{output_prefix}_solv.gro"
    top_file = f"{output_prefix}.top" 
    user_tasks_dict = {
            "pdb_validation": f"Check if the {str(os.path.abspath(pdb_file_path))} file has a valid PDB structure.",
            "pdb_download": f"Complete only the following task and don't do anything else when completed: Download a structure from the Protein Data Bank. The structure id is {structure_id}. The Workspace is {workspace}",
            "pdb_analysis": f"Analyze the {str(os.path.abspath(pdb_file_path))} file.",
            "remove_water": f"Complete only the following task and don't do anything else when completed: Remove water molecules from the {pdb_file_path} PDB file. The Workspace is {workspace}",
            "pulse_check": "Check if Gromacs in installed.",
            "conversion_to_gro": f"Convert the {pdb_file_path} file into Gromacs format. The Workspace is {workspace}",
            "prepare_files": f"Complete only the following task and don't do anything else when completed: Create the necessary system files for Gromacs starting from the {pdb_file_path} file. Output prefix is the name of the PDB file. Force field is {force_field}. The water model is {water_model}. The Workspace is {workspace}",
            "generate_box": f"Complete only the following task and don't do anything else when completed: Prepare a simulation box. The GRO file is {gro_file}. The topology file is {top_file}. The out prefix is {output_prefix}. The box size is {box_size}. The Workspace is {workspace}",
            "add_ions": f"Complete only the following task and don't do anything else when completed: add ions. The GRO file is {gro_solvated_file}. The topology file is {top_file}. The out prefix is {output_prefix}. Concentration is {concentration}. The Workspace is {workspace}",
            "energy_minimization": f"Complete only the following task and don't do anything else when completed: Do energy minimization. The prefix is em. The Workspace is {workspace}",
            "plot_energy": f"Plot the .edr file in the workspace and save it to PNG. The workspace is {workspace}"
        }
    
    return user_tasks_dict

def get_final_answer_prompt_template():
    return "Based on the above, please provide an answer to the given task. Always answer in user-readable text, don't use json."

def get_ollama_generate_full_gromacs_plan_template(pdb_file_path, workspace, force_field, water_model, box_size, concentration):
    file_name_with_extension = os.path.basename(pdb_file_path)
    output_prefix, _ = os.path.splitext(file_name_with_extension) 
    
    return f"""
            You are an expert molecular dynamics (MD) assistant that helps setting GROMACS simulations.
            Your primary goal is to guide the user through setting up and running MD simulations.
            Your main task is to provide the correct sequence of GROMACS commands to setup and execute system preparation and simulation, given the following:
            The input PDB file is {pdb_file_path}. Force field is {force_field}. The water model is {water_model}. The box size is {box_size}. Concentration is {concentration}. The output prefix is {output_prefix}. The Workspace is {workspace}
    Follow these rules:
    1. USE ONLY the values specified above. Don't provide different values.
    2. ALWAYS refer to valid GROMACS CLI tools and arguments.
    3. ALWAYS follow the expected GROMACS simulation execution order.
    4. Don't execute the generated commands. 
    5. Return the commands in the form of a Python list.
        """