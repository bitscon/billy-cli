import requests
import json
from config import Config

def query_ollama(prompt, include_memory=False, memory_category=None):
    """Query the Ollama API for a response."""
    config = Config()
    url = "http://localhost:11434/api/generate"
    tone_instruction = f"Respond in a {config.TONE} tone."
    
    from database import get_memory_context, get_documentation
    memory_context = get_memory_context(memory_category) if include_memory else ""
    doc_context = ""
    docs = get_documentation(prompt)
    if docs:
        doc_context = "\nRelevant Documentation:\n" + "\n".join([f"{doc['title']}: {doc['content'][:200]}" for doc in docs])
    full_prompt = f"{tone_instruction}\n{memory_context}\n{doc_context}\nUser: {prompt}"
    
    payload = {
        "model": "mistral:7b-instruct-v0.3-q4_0",
        "prompt": full_prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return json.loads(response.text)["response"]
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Request failed: {str(e)}"