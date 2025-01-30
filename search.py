import os
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSearchAPIWrapper

# Load environment variables from .env file
load_dotenv()

def get_search(query: str = "", max_results: int = 1):
    """
    Fetches search results using Google Custom Search JSON API with pagination.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to retrieve (up to 100).
        
    Returns:
        list: A list of search result items.
    """
    if max_results > 100:
        raise ValueError("The Google Custom Search API supports a maximum of 100 results per query.")
    
    search = GoogleSearchAPIWrapper()
    all_results = []
    num_per_request = 10  # Max allowed by API
    for start in range(1, max_results + 1, num_per_request):
        results = search.results(query=query, num_results=num_per_request, search_params={"start": start})
        all_results.extend(results)
        if len(results) < num_per_request:
            break
    
    return all_results


