import requests
import json
import os
from googlesearch import search

# Load configuration
with open("src/config.json", "r") as config_file:
    config = json.load(config_file)
    TONE = config["tone"]

def load_memory():
    if os.path.exists("src/memory.json"):
        with open("src/memory.json", "r") as f:
            return json.load(f)
    return []

def save_memory(prompt, response, category="general"):
    memory = load_memory()
    memory.append({"prompt": prompt, "response": response, "category": category})
    with open("src/memory.json", "w") as f:
        json.dump(memory, f, indent=4)

def get_memory_context(category=None):
    memory = load_memory()
    if not memory:
        return "No past interactions."
    context = "\nPast interactions:\n"
    for entry in memory:
        if category is None or entry["category"] == category:
            context += f"[{entry['category']}] User: {entry['prompt']}\nBilly: {entry['response']}\n"
    return context if context != "\nPast interactions:\n" else f"No past interactions for category '{category}'."

def web_search(query, num_results=3):
    try:
        results = []
        for url in search(query, num_results=num_results):
            results.append(url)
        return "\n".join([f"- {url}" for url in results])
    except Exception as e:
        return f"Web search failed: {str(e)}"

def query_ollama(prompt, include_memory=False, memory_category=None):
    url = "http://localhost:11434/api/generate"
    # Add tone and memory context to the prompt
    tone_instruction = f"Respond in a {TONE} tone."
    memory_context = get_memory_context(memory_category) if include_memory else ""
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

        # Determine category based on input
        category = "general"
        if "code" in user_input.lower() or "write a" in user_input.lower():
            category = "coding"
        elif "search for" in user_input.lower():
            category = "research"

        # Check if user wants to include memory
        include_memory = False
        memory_category = None
        if "recall" in user_input.lower():
            include_memory = True
            if "coding" in user_input.lower():
                memory_category = "coding"
            elif "research" in user_input.lower():
                memory_category = "research"
            user_input = user_input.replace("recall coding", "").replace("recall research", "").replace("recall past", "").strip()

        # Handle web search
        web_results = ""
        if "search for" in user_input.lower():
            search_query = user_input.replace("search for", "").strip()
            web_results = web_search(search_query)
            user_input = f"{user_input}\nWeb search results:\n{web_results}"

        # Query Ollama
        response = query_ollama(user_input, include_memory, memory_category)
        print(f"Billy: {response}")

        # Save the interaction to memory
        save_memory(user_input, response, category)
