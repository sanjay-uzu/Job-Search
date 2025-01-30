from search import get_search

query = "What is prompt engineering?"
results = get_search(query=query, max_results=101)  
print(len(results))