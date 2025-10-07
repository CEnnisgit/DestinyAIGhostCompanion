import os
import torch
import requests
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from peft import PeftModel

# Assuming the model is fine-tuned and saved as llama-destiny-lora
# If not, this will fail; in practice, you'd run fine_tune_llama.py first

try:
    base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct", torch_dtype=torch.float16)
    model = PeftModel.from_pretrained(base_model, "./llama-destiny-lora")
    tokenizer = AutoTokenizer.from_pretrained("./llama-destiny-lora")
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512)
except Exception as e:
    print(f"Model not found or error: {e}. Using fallback.")
    pipe = None

# Bungie API setup
BUNGIE_API_KEY = os.getenv("BUNGIE_API_KEY", "your_api_key_here")
BUNGIE_BASE_URL = "https://www.bungie.net/Platform"

def call_bungie_api(endpoint, params=None, auth_token=None):
    headers = {"X-API-Key": BUNGIE_API_KEY}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    response = requests.get(f"{BUNGIE_BASE_URL}{endpoint}", headers=headers, params=params)
    if response.status_code == 429:  # Rate limit
        return {"error": "Rate limit exceeded. Retry later."}
    return response.json()

def generate_response(query, user_token=None):
    if not pipe:
        return "Model not loaded. Please fine-tune first."

    # Generate with model - the model now outputs direct Ghost responses
    prompt = f"User: {query}\nGhost:"
    output = pipe(prompt)[0]["generated_text"]

    # Extract the response after "Ghost:"
    if "Ghost:" in output:
        response = output.split("Ghost:")[1].strip()
    else:
        response = output.replace(prompt, "").strip()

    return response

# Example
if __name__ == "__main__":
    print(generate_response("What's happening in Destiny 2 right now?"))