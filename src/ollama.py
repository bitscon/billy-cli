import requests
import json
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename="billy.log", format="%(asctime)s %(levelname)s:%(message)s")

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
    full_prompt = f"{tone_instruction}\n{memory_context}\n{doc_context}\n{prompt}"
    
    payload = {
        "model": "mistral:7b-instruct-v0.3-q4_0",
        "prompt": full_prompt,
        "stream": False
    }
    try:
        logging.debug(f"Sending prompt to Ollama: {full_prompt}")
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = json.loads(response.text)["response"]
            logging.debug(f"Ollama response: {result}")
            return result
        else:
            error_msg = f"Error: {response.status_code} - {response.text}"
            logging.error(error_msg)
            return error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        logging.error(error_msg)
        return error_msg