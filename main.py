from search import get_search
from utils import get_content
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI  # Updated import
from langchain.prompts import ChatPromptTemplate  # New prompt template

load_dotenv()

# 1. Search setup
query = "site:lever.co | site:greenhouse.io Data Analyst Intern"
results = get_search(query=query, max_results=1)
contents = [(result["link"], get_content(result["link"])) for result in results]

# 2. Load questions
with open('questions.txt', 'r') as f:
    questions = [line.strip() for line in f.readlines()]

# 3. Initialize Chat Model
llm = ChatOpenAI(
    temperature=0,
    model="gpt-4o",  # Official model name
)

# 4. Chat-optimized prompt template
template = ChatPromptTemplate.from_messages([
    ("system", "Answer questions based on the job description."),
    ("human", "Question: {question}\nJob Description: {context}")
])

def process_jobs(job_tuples):
    results = []
    chain = LLMChain(llm=llm, prompt=template)
    
    for link, content in job_tuples:
        job_dict = {"link": link, "answers": []}
        
        for question in questions:
            response = chain.invoke({
                "question": question,
                "context": content[:15000]  # Truncate to prevent token limit errors
            })
            job_dict["answers"].append(response["text"])
        
        results.append(job_dict)
    
    return results

re=process_jobs(contents)
for r in re:
    print(r["link"],r["answers"][1])
