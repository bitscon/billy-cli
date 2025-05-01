import logging
from googlesearch import search
from database import save_documentation

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename="billy.log", format="%(asctime)s %(levelname)s:%(message)s")

def web_search(query, num_results=3):
    """Perform a web search and save results to documentation."""
    try:
        results = []
        for url in search(query, num_results=num_results):
            results.append(url)
            save_documentation(f"Web Search: {query}", f"Found at {url}", "online", url)
        result_str = "\n".join([f"- {url}" for url in results])
        logging.info(f"Web search completed for query '{query}': {len(results)} results found")
        return result_str if result_str else "No search results found."
    except Exception as e:
        logging.error(f"Web search failed: {str(e)}")
        return f"Web search failed: {str(e)}"