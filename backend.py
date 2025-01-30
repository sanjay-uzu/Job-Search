from search import get_search
from utils import get_content
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI  # Updated import
from langchain.prompts import ChatPromptTemplate  # New prompt template

load_dotenv()

# Load questions from a file (shared across searches)
with open('questions.txt', 'r') as f:
    questions = [line.strip() for line in f.readlines()]

# Initialize Chat Model globally to avoid reinitialization overhead
llm = ChatOpenAI(
    temperature=0,
    model="gpt-4o",  # Official model name
)

# Chat-optimized prompt template (shared across searches)
template = ChatPromptTemplate.from_messages([
    ("system", "Answer questions based on the job description."),
    ("human", "Question: {question}\nJob Description: {context}")
])

def process_jobs(query):
    """
    Fetch job postings using a search query and process them with LLM.
    
    Args:
      query (str): The search query.
      
    Returns:
      list[dict]: A list of dictionaries containing job links and answers.
    """
    try:
        # Fetch search results (limit to prevent excessive processing)
        results = get_search(query=query, max_results=5)
        
        # Extract content from each result link
        contents = [(result["link"], get_content(result["link"])) for result in results]
        
        chain = LLMChain(llm=llm, prompt=template)
        
        processed_results = []
        
        for link, content in contents:
            job_dict = {"link": link, "answers": []}
            
            for question in questions:
                response = chain.invoke({
                    "question": question,
                    "context": content[:15000]  # Truncate to prevent token limit errors
                })
                job_dict["answers"].append(response["text"])
            
            processed_results.append(job_dict)
        
        return processed_results
    
    except Exception as e:
        print(f"Error processing jobs: {e}")
        return []
