import argparse
import torch
from smolagents import CodeAgent, TransformersModel
from gmxtools import is_gromacs_installed, convert_pdb_to_gromacs, create_index_file, prepare_simulation_files, prepare_and_solvate_box, add_ions

def main():
    parser = argparse.ArgumentParser(description="An AI Agent that handles Gromacs workflows.")

    parser.add_argument("-pdb_file", type=str, required=True, help="The path and name of the starting PDB file.")
    parser.add_argument("-force_field", type=str, default="amber99sb-ildn", help="The force field to use when preparing the simulation files.")
    parser.add_argument("-water_model", type=str, choices=['none', 'spc', 'spce', 'tip3p', 'tip4p', 'tip5p', 'tips3p'],
                        default="tip3p", help="The water model to use.")
    parser.add_argument("-box_size", type=float, default=1.0, help="The size of the simulation box.")
    parser.add_argument("-concentration", type=float, default=0.15, help="The total salt concentration expressed in mol/L")
    parser.add_argument("-workspace", type=str, default=".", help="The directory where to store all the files for a simulation.")

    args = parser.parse_args()
    
    model_id = 'Qwen/Qwen2.5-3B-Instruct'
    model = TransformersModel(model_id,
                            device_map="auto",
                            max_new_tokens=1000,
                            torch_dtype=torch.float16,
                            temperature=0.1)

    custom_tools = [is_gromacs_installed, convert_pdb_to_gromacs, 
                    create_index_file, prepare_simulation_files,
                    prepare_and_solvate_box, add_ions]
    agent = CodeAgent(tools=custom_tools, model=model,
                    additional_authorized_imports=[],
                    verbosity_level=2, max_steps=4)
    
    pdb_file_path = args.pdb_file
    force_field = args.force_field
    water_model = args.water_model
    workspace = args.workspace
    user_tasks = [
        "Check if Gromacs in installed.",
        f"Convert the {pdb_file_path} file into Gromacs format. The Workspace is {workspace}",
        f"Prepare the necessary files for a Gromacs simulation starting from the {pdb_file_path} file. Force field is {force_field}. The water model is {water_model}. The Workspace is {workspace}",
        f"Prepare a simulation box starting from the {pdb_file_path} file. Force field is {force_field}. The water model is {water_model}. Simulation files must keep the same name as for the PDB file. The Workspace is {workspace}"
    ]
    
    agent.run(user_tasks[0])

if __name__ == '__main__':
    main()