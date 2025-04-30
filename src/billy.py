import requests
import json

def query_ollama(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "mistral:7b-instruct-v0.3-q4_0",
        "prompt": prompt,
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
    prompt = "Hello, I am Billy. How can I assist you today?"
    response = query_ollama(prompt)
    print(f"Billy: {response}")
