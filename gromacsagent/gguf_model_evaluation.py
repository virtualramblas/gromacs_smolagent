import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# 1) Specify your model and the GGUF filename
model_id = "Qwen/Qwen2.5-3B-Instruct-GGUF" 
gguf_filename = "qwen2.5-3b-instruct-q5_k_m.gguf"  # Local GGUF file that matches your model

# 2) Load tokenizer and model from GGUF
tokenizer = AutoTokenizer.from_pretrained(model_id, gguf_file=gguf_filename)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    gguf_file=gguf_filename,
    dtype=torch.bfloat16,  # Use float32 or float16/bfloat16 as appropriate
    device_map={"": "mps"},
    #offload_folder="../checkpoints"
)

# 3) Prompt and generate
prompt = "Explain how the Qwen model architecture works."
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
