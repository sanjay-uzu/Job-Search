import requests
from selectolax.parser import HTMLParser
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def extract_text_from_pdf(file):
    """Extract text from uploaded PDF file"""
    try:
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def get_embeddings(text):
    """Generate embeddings using sentence transformer"""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(text, convert_to_tensor=False)

def get_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
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
    if html==None:
        return None
    return extract_main_content(html)

