def get_model_list():
    return ['Qwen/Qwen2.5-3B-Instruct', 'Qwen/Qwen2.5-1.5B-Instruct']

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

def get_user_task_dictionary(pdb_file_path, workspace, force_field, water_model):
    user_tasks_dict = {
            "pulse_check": "Check if Gromacs in installed.",
            "conversion_to_gro": f"Convert the {pdb_file_path} file into Gromacs format. The Workspace is {workspace}",
            "prepare_files": f"Prepare the necessary files for a Gromacs simulation starting from the {pdb_file_path} file. Force field is {force_field}. The water model is {water_model}. The Workspace is {workspace}",
            "generate_box": f"Prepare a simulation box starting from the {pdb_file_path} file. Force field is {force_field}. The water model is {water_model}. Simulation files must keep the same name as for the PDB file. The Workspace is {workspace}",
            "add_ions": f"Prepare a simulation box starting from the {pdb_file_path} file and add ions once created. Force field is {force_field}. The water model is {water_model}. Any created file must keep the same prefix as for the PDB file. The Workspace is {workspace}",
            "energy_minimization": f"Do energy minimization. The workspace is {workspace}",
            "plot_energy": f"Plot the .edr file in the workspace and save it to PNG. The workspace is {workspace}"
        }
    
    return user_tasks_dict