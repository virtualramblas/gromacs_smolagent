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
                                    max_new_tokens=600,
                                    dtype=torch.float16,
                                    do_sample=True,
                                    temperature=0.1)
        else:
            self.model = LiteLLMModel(
                    model_id='ollama_chat/' + self.model_id,
                    api_base=args.ollama_api_base,  
                    api_key="",
                    num_ctx=8192*2,
                    temperature=0.1)
        
        self.manager_agent = CodeAgent(
            tools=[],
            model=self.model,
            managed_agents=[],
            max_steps=2,
        )
        
        self.manager_agent.prompt_templates["final_answer"]["post_messages"] = prompt_utils.get_final_answer_prompt_template()

    def run_agent(self):
        MAX_RETRIES = 3
        feedback_history = []
        all_commands_valid = False
        final_generated_commands = []
        pdb_file_path = self.args.pdb_file
        force_field = self.args.force_field
        water_model = self.args.water_model
        workspace = self.args.workspace
        box_size = self.args.box_size
        concentration = self.args.concentration
        for retry_count in range(MAX_RETRIES):
            print("""\nAttempt {{retry_count + 1}}/{{MAX_RETRIES}}""")
            if self.args.provider == "ollama":
                base_task_template = prompt_utils.get_ollama_generate_full_gromacs_plan_template(
                    pdb_file_path,
                    workspace,
                    force_field,
                    water_model,
                    box_size,
                    concentration,
                )
            else:
                base_task_template = prompt_utils.get_generate_full_gromacs_plan_template(
                    pdb_file_path,
                    workspace,
                    force_field,
                    water_model,
                    box_size,
                    concentration,
                )

            current_task_template = base_task_template
            if feedback_history:
                feedback_str = """\n\nPrevious attempt failed with the following validation errors/warnings. Please correct the commands:
"""
                for fb in feedback_history:
                    feedback_str += f"- {fb}\n"
                current_task_template += feedback_str

            generated_cmds_list = self.manager_agent.run(current_task_template)
            current_attempt_valid = True
            current_attempt_feedback = []
            temp_generated_commands = []
            for cmd in generated_cmds_list:
                print(f"""\nInput: {cmd}""")
                if not isinstance(cmd, str):
                    current_attempt_valid = False
                    current_attempt_feedback.append(f"""Command '{cmd}' is not a string.""")
                    continue
                parsed_cmd_result = parse_gromacs_command(cmd)
                if parsed_cmd_result is not None:
                    print(f"""Command: {parsed_cmd_result["command"]}""")
                    print(f"""Options: {parsed_cmd_result["options"]}""")

                    if "validation" in parsed_cmd_result:
                        print(f"""Valid: {parsed_cmd_result["validation"]["valid"]}""")
                        if parsed_cmd_result["validation"]["warnings"]:
                            for warning in parsed_cmd_result["validation"]["warnings"]:
                                print(f"  {warning}")

                        if not parsed_cmd_result["validation"]["valid"] or parsed_cmd_result["validation"]["warnings"]:
                            current_attempt_valid = False
                            validation_issues = []
                            if not parsed_cmd_result["validation"]["valid"]:
                                validation_issues.append("Invalid syntax/structure")
                            validation_issues.extend(parsed_cmd_result["validation"]["warnings"])
                            current_attempt_feedback.append(f"""Command '{cmd}' validation issues: { ', '.join(validation_issues)} """)
                        else:
                            temp_generated_commands.append(cmd)
                else:
                    current_attempt_valid = False
                    current_attempt_feedback.append(f"""Command '{cmd}' failed parsing.""")

            if current_attempt_valid:
                all_commands_valid = True
                final_generated_commands = temp_generated_commands
                print("""\nAll generated commands for this attempt are valid.""")
                break
            else:
                print("""\nGenerated commands for this attempt failed validation. Retrying...""")
                feedback_history.extend(current_attempt_feedback)

        if all_commands_valid:
            print("""\nSuccessfully generated valid Gromacs commands:""")
            for cmd in final_generated_commands:
                print(cmd)
        else:
            print(f"""\nFailed to generate valid Gromacs commands after {{MAX_RETRIES}} attempts.""")
            print("""Last generated commands had issues:""")
            for fb in feedback_history:
                print(f"- {fb}")
            
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