import requests
import json
import os

# Load configuration
with open("src/config.json", "r") as config_file:
    config = json.load(config_file)
    TONE = config["tone"]

def load_memory():
    if os.path.exists("src/memory.json"):
        with open("src/memory.json", "r") as f:
            return json.load(f)
    return []

def save_memory(prompt, response):
    memory = load_memory()
    memory.append({"prompt": prompt, "response": response})
    with open("src/memory.json", "w") as f:
        json.dump(memory, f, indent=4)

def get_memory_context():
    memory = load_memory()
    if not memory:
        return "No past interactions."
    context = "\nPast interactions:\n"
    for entry in memory:
        context += f"User: {entry['prompt']}\nBilly: {entry['response']}\n"
    return context

def query_ollama(prompt, include_memory=False):
    url = "http://localhost:11434/api/generate"
    # Add tone and memory context to the prompt
    tone_instruction = f"Respond in a {TONE} tone."
    memory_context = get_memory_context() if include_memory else ""
    full_prompt = f"{tone_instruction}\n{memory_context}\nUser: {prompt}"
    
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

if __name__ == "__main__":
    while True:
        # Get user input
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        # Check if user wants to include memory
        include_memory = "recall past" in user_input.lower()
        if include_memory:
            user_input = user_input.replace("recall past", "").strip()
        
        # Query Ollama
        response = query_ollama(user_input, include_memory)
        print(f"Billy: {response}")
        
        # Save the interaction to memory
        save_memory(user_input, response)
