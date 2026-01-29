import os
import requests
from ghost.ollama import OllamaClient  # Import for fallback

# Global variables for model
pipe = None
ollama_fallback = None

def load_model():
    """Load the fine-tuned model if available."""
    global pipe, ollama_fallback
    if pipe is not None:
        return pipe

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        from peft import PeftModel

        base_model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Meta-Llama-3-8B-Instruct",
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_8bit=True
        )
        model = PeftModel.from_pretrained(base_model, "./llama-destiny-lora")
        tokenizer = AutoTokenizer.from_pretrained("./llama-destiny-lora")
        # Load chat template if available
        if os.path.exists("./llama-destiny-lora/chat_template.jinja"):
            tokenizer.chat_template = open("./llama-destiny-lora/chat_template.jinja").read()
        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512)
        print("[inference] Fine-tuned model loaded successfully.")
        return pipe
    except Exception as e:
        print(f"[inference] Model not found or error: {e}. Falling back to Ollama.")
        pipe = None
        try:
            ollama_fallback = OllamaClient()
        except Exception as oe:
            print(f"[inference] Ollama fallback also failed: {oe}")
            ollama_fallback = None
        return None

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
    global pipe
    if pipe is None:
        load_model()

    if pipe:
        # Use fine-tuned model
        if "Ghost:" in query:
            prompt = query
        else:
            prompt = f"User: {query}\nGhost:"
        try:
            output = pipe(prompt)[0]["generated_text"]
            if "Ghost:" in output:
                response = output.split("Ghost:")[1].strip()
            else:
                response = output.replace(prompt, "").strip()
            return response
        except Exception as e:
            print(f"[inference] Error generating with fine-tuned model: {e}. Falling back to Ollama.")
            return generate_with_ollama(query, user_token)
    else:
        # Fallback to Ollama
        return generate_with_ollama(query, user_token)

def generate_with_ollama(query, user_token=None):
    """Fallback method using Ollama."""
    global ollama_fallback
    if ollama_fallback:
        try:
            return ollama_fallback.generate(query)
        except Exception as e:
            return f"Error generating response: {e}"
    else:
        return "Both fine-tuned model and Ollama are unavailable. Please check your setup."

# Example
if __name__ == "__main__":
    print(generate_response("What's happening in Destiny 2 right now?"))