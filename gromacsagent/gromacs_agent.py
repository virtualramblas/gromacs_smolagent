import sys
import torch
from smolagents import CodeAgent, TransformersModel
from gmxtools import is_gromacs_installed, convert_pdb_to_gromacs, create_index_file, prepare_simulation_files, prepare_and_solvate_box, add_ions

def main():
    if len(sys.argv) != 2:
        print('Usage: python gromacs_agent.py <pdb_file_path>')
    else:
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
        
        pdb_file_path = sys.argv[1]
        user_tasks = [
            "Check if Gromacs in installed.",
            f"Convert the {pdb_file_path} file into Gromacs format.",
            f"Prepare the necessary files for a Gromacs simulation starting from the {pdb_file_path} file. Force field is amber99sb-ildn.",
            f"Prepare a simulation box starting from the {pdb_file_path} file. Force field is amber99sb-ildn. Simulation files must keep the same name as for the PDB file."
        ]
        
        agent.run(user_tasks[1])

if __name__ == '__main__':
    main()