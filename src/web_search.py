from googlesearch import search
from database import save_documentation

def web_search(query, num_results=3):
    """Perform a web search and save results to documentation."""
    try:
        results = []
        for url in search(query, num_results=num_results):
            results.append(url)
            save_documentation(f"Web Search: {query}", f"Found at {url}", "online", url)
        return "\n".join([f"- {url}" for url in results])
    except Exception as e:
        return f"Web search failed: {str(e)}"
