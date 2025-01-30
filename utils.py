import requests
from selectolax.parser import HTMLParser
def get_html(url):
    headers = {
        'User-Agent': 'Chrome/125.0.0.0 (Windows NT 10.0; Win64 x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None





def extract_main_content(html):
    tree = HTMLParser(html)
    
    # Remove non-content elements
    for tag in tree.css('script, style, nav, footer, header, aside'):
        tag.decompose()
    
    # Focus on content-rich elements
    content = []
    for node in tree.css('article, main, .content, p, div[itemprop="articleBody"]'):
        content.append(node.text(separator='\n'))
    
    return '\n\n'.join(content)

def get_content(url):
    html=get_html(url)
    return extract_main_content(html)
