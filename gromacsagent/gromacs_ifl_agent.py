import argparse
import torch
import prompt_utils
from gmx_validation import parse_gromacs_command
from smolagents import (CodeAgent, LiteLLMModel, TransformersModel)

class IFLAgent():
    def __init__(self, args):
        self.args = args
        self.model_id = args.model
        if args.provider == "transformers":
            self.model = TransformersModel(self.model_id,
                                    device_map="auto",
                                    max_new_tokens=200,
                                    torch_dtype=torch.float16,
                                    do_sample=True,
                                    temperature=0.1)
        else:
            self.model = LiteLLMModel(
                    model_id='ollama_chat/' + self.model_id,
                    api_base=args.ollama_api_base,  
                    api_key="",
                    num_ctx=8192,
                    temperature=0.1)
        
        self.manager_agent = CodeAgent(
            tools=[],
            model=self.model,
            managed_agents=[],
        )

    def run_agent(self):
        pdb_file_path = self.args.pdb_file
        force_field = self.args.force_field
        water_model = self.args.water_model
        workspace = self.args.workspace
        box_size = self.args.box_size
        concentration = self.args.concentration
        if self.args.provider == "ollama":
            task_template = prompt_utils.get_ollama_generate_full_gromacs_plan_template(
                pdb_file_path,
                workspace,
                force_field,
                water_model,
                box_size,
                concentration,
            )

            result = self.manager_agent.run(task_template)
            generated_commands = {}
            for cmd in result:
                try:
                    print(f"\nInput: {cmd}")
                    result = parse_gromacs_command(cmd)
                    if result:
                        print(f"Command: {result['command']}")
                        print(f"Options: {result['options']}")
                        
                        if 'validation' in result:
                            print(f"Valid: {result['validation']['valid']}")
                            if result['validation']['warnings']:
                                for warning in result['validation']['warnings']:
                                    print(f"  {warning}")
                            generated_commands.update({cmd: result['validation']['valid']})
                except Exception as e:
                    print(f"Runtime error: {str(e)}")
                    generated_commands.update({cmd: "Valid: False"})
            print(generated_commands)
            

def main():
    parser = argparse.ArgumentParser(description="An AI Multi-Agent that handles Gromacs workflows.")

    parser.add_argument("-pdb_file", type=str, default='', help="The path and name of the starting PDB file.")
    parser.add_argument("-force_field", type=str, default="amber99sb-ildn", help="The force field to use when preparing the simulation files.")
    parser.add_argument("-water_model", type=str, choices=['none', 'spc', 'spce', 'tip3p', 'tip4p', 'tip5p', 'tips3p'],
                        default="tip3p", help="The water model to use.")
    parser.add_argument("-box_size", type=float, default=1.0, help="The size of the simulation box.")
    parser.add_argument("-concentration", type=float, default=0.15, help="The total salt concentration expressed in mol/L")
    parser.add_argument("-workspace", type=str, default=".", help="The directory where to store all the files for a simulation.")
    parser.add_argument("-provider", type=str, choices=["transformers", "ollama"],
                        default="transformers", help="The provider type to use for inference.")
    parser.add_argument("-ollama_api_base", type=str, default="http://localhost:11434",
                        help="The Ollama API base URL.")
    parser.add_argument("-model", type=str,  
                        choices=prompt_utils.get_model_list(), 
                        default="Qwen/Qwen2.5-3B-Instruct", help="The Small Language Model to be used by the agent.")
    parser.add_argument("-telemetry", type=bool, default=False,
                        help="Enables telemetry when set to True. Default is False.")
    parser.add_argument("-telemetry_server_url", type=str, default="http://0.0.0.0:6006/v1/traces",
                        help="The telemetry server URL. This argument is used only when telemetry is enabled")
    parser.add_argument("-structure_id", type=str, default='', help="The id of the structure to download from the Protein Data Bank.")

    args = parser.parse_args()

    agent = IFLAgent(args)
    agent.run_agent()

if __name__ == '__main__':
    main()