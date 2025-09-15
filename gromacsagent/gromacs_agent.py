import argparse
import os
import torch
import prompt_utils
from opentelemetry.sdk.trace import TracerProvider
from smolagents import CodeAgent, LiteLLMModel, TransformersModel
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from gmxsystools import (is_gromacs_installed, create_index_file, 
                         prepare_system_files, prepare_and_solvate_box, add_ions)
from gmxsimtools import gromacs_energy_minimization, plot_edr_to_png, gromacs_equilibration

class GromacsMainAgent():
    def __init__(self, args):
        self.args = args
        self.model_id = args.model
        if args.provider == "transformers":
            self.model = TransformersModel(self.model_id,
                                    device_map="auto",
                                    max_new_tokens=100,
                                    torch_dtype=torch.float16,
                                    do_sample=True,
                                    temperature=0.1)
        else:
            self.model = LiteLLMModel(
                    model_id='ollama_chat/' + self.model_id,
                    api_base=args.ollama_api_base,  
                    api_key="",
                    num_ctx=8192,
                    temperature=0.1
            )
        self.custom_tools = [is_gromacs_installed, 
                    create_index_file, prepare_system_files,
                    prepare_and_solvate_box, add_ions,
                    gromacs_energy_minimization, plot_edr_to_png,
                    gromacs_equilibration]
        self.agent = CodeAgent(tools=self.custom_tools, model=self.model,
                        additional_authorized_imports=[''],
                        verbosity_level=2, max_steps=4)
        
    def run_agent(self):
        pdb_file_path = self.args.pdb_file
        force_field = self.args.force_field
        water_model = self.args.water_model
        workspace = self.args.workspace
        task = self.args.task
        user_tasks_dict = prompt_utils.get_user_task_dictionary(pdb_file_path,
                                                                workspace,
                                                                force_field,
                                                                water_model)

        task_template = prompt_utils.get_specific_task_template(self.model_id, 
                                                                user_tasks_dict[task],
                                                                False)
        self.agent.run(task_template)
        del self.model

def main():
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    parser = argparse.ArgumentParser(description="An AI Agent that handles Gromacs workflows.")

    parser.add_argument("-pdb_file", type=str, required=True, help="The path and name of the starting PDB file.")
    parser.add_argument("-force_field", type=str, default="amber99sb-ildn", help="The force field to use when preparing the simulation files.")
    parser.add_argument("-water_model", type=str, choices=['none', 'spc', 'spce', 'tip3p', 'tip4p', 'tip5p', 'tips3p'],
                        default="tip3p", help="The water model to use.")
    parser.add_argument("-box_size", type=float, default=1.0, help="The size of the simulation box.")
    parser.add_argument("-concentration", type=float, default=0.15, help="The total salt concentration expressed in mol/L")
    parser.add_argument("-workspace", type=str, default=".", help="The directory where to store all the files for a simulation.")
    parser.add_argument("-task", type=str,  
                        choices=['pulse_check', 'conversion_to_gro', 'prepare_files',
                                 'generate_box', 'add_ions',
                                 'energy_minimization', 'plot_energy'], 
                        default="pulse_check", help="The task for the agent.")
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
    
    args = parser.parse_args()

    if args.telemetry:
        endpoint = args.telemetry_server_url
        trace_provider = TracerProvider()
        trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint)))

        SmolagentsInstrumentor().instrument(tracer_provider=trace_provider)

    agent = GromacsMainAgent(args)
    agent.run_agent()

if __name__ == '__main__':
    main()
