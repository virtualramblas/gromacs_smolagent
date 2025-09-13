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

model_prompt_dict = {
    'Qwen/Qwen2.5-3B-Instruct': get_task_template,
    'Qwen/Qwen2.5-1.5B-Instruct': get_extended_task_template,
    'qwen2.5:3b': get_task_template
}

def get_model_list():
    return model_prompt_dict.keys()

def get_specific_task_template(model_id, task):
    task_template = model_prompt_dict[model_id](task)
    
    return task_template

def get_user_task_dictionary(pdb_file_path, workspace, force_field, water_model):
    user_tasks_dict = {
            "pdb_validation": f"Check if the {str(os.path.abspath(pdb_file_path))} file has a valid PDB structure.",
            "pdb_analysis": f"Analyze the {str(os.path.abspath(pdb_file_path))} file.",
            "pulse_check": "Check if Gromacs in installed.",
            "conversion_to_gro": f"Convert the {pdb_file_path} file into Gromacs format. The Workspace is {workspace}",
            "prepare_files": f"Prepare the necessary files for a Gromacs simulation starting from the {pdb_file_path} file. Force field is {force_field}. The water model is {water_model}. The Workspace is {workspace}",
            "generate_box": f"Prepare a simulation box starting from the {pdb_file_path} file. Force field is {force_field}. The water model is {water_model}. Simulation files must keep the same name as for the PDB file. The Workspace is {workspace}",
            "add_ions": f"Prepare a simulation box starting from the {pdb_file_path} file and add ions once created. Force field is {force_field}. The water model is {water_model}. Any created file must keep the same prefix as for the PDB file. The Workspace is {workspace}",
            "energy_minimization": f"Do energy minimization. The workspace is {workspace}",
            "plot_energy": f"Plot the .edr file in the workspace and save it to PNG. The workspace is {workspace}"
        }
    
    return user_tasks_dict