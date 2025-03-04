from search import get_search
from backend import *
tags=["Computer Vision"]
sites = ["lever.co", "greenhouse.io"]
for tag in tags:
    site_query = " | ".join([f"site:{site}" for site in sites])
    remote_query = " remote"
    full_query = f"{site_query} {tag}{remote_query}"
    # raw_results = process_jobs(full_query, 1)

