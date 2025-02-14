from pathlib import Path
from search import get_search
from utils import get_content
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI  # Updated import
from langchain.prompts import ChatPromptTemplate  # New prompt template
import json
from langchain.prompts import ChatPromptTemplate

# Add this with other prompt templates
shorten_prompt = ChatPromptTemplate.from_messages([
    ("system", "Convert this question into a 2-4 word column header. Return only the header text."),
    ("human", "{question}")
])

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
def apply_filters(results, questions):
    """Apply filters to the results based on question configurations"""
    filtered = []
    
    for job in results:
        valid = True
        for i, answer in enumerate(job['answers']):
            # Add bounds checking for questions list
            if i >= len(questions):
                continue  # Skip if there are more answers than questions
                
            question = questions[i]
            if not question.get('filter'):
                continue
                
            try:
                if question['type'] == 'numeric':
                    if question['filter']['operator'] == "None":
                        continue
                    # Handle empty/non-numeric answers
                    if not answer.strip():
                        valid = False
                        break
                    answer_num = float(answer)
                    if question['filter']['operator'] == ">":
                        if not (answer_num > question['filter']['value']):
                            valid = False
                    elif question['filter']['operator'] == "<":
                        if not (answer_num < question['filter']['value']):
                            valid = False
                            
                elif question['type'] == 'boolean':
                    if question['filter'] == "None":
                        continue
                    # Handle case-insensitive comparison
                    if answer.lower() != question['filter'].lower():
                        valid = False
                        
            except (ValueError, TypeError) as e:
                print(f"Filter error: {e}")
                valid = False
                break
                
        if valid:
            filtered.append(job)
            
    return filtered


# Replace the questions loading with this code
def load_questions():
    """Load questions from JSON file with formatting"""
    try:
        with open('questions.json', 'r') as f:
            questions_data = json.load(f)
            formatted_questions = []
            for q in questions_data:
                base_question = q['text']
                if q['type'] == 'numeric':
                    formatted_questions.append(f"{base_question} Answer only in numbers.")
                elif q['type'] == 'boolean':
                    formatted_questions.append(f"{base_question} Answer only in True or False.")
                elif q['type'] == 'categorical':
                    formatted_questions.append(f"{base_question} Answer in as few words as possible.")
                else:
                    formatted_questions.append(base_question)
            return formatted_questions
    except Exception as e:
        print(f"Error loading questions: {e}")
        return [
            "What is the salary range? Answer only in numbers.",
            "Is remote work available? Answer only in True or False."
        ]

# Update the initialization
questions = load_questions()

def process_jobs(query,max_results):
    """
    Fetch job postings using a search query and process them with LLM.
    
    Args:
      query (str): The search query.
      
    Returns:
      list[dict]: A list of dictionaries containing job links and answers.
    """
    
    
    try:
        # Fetch search results (limit to prevent excessive processing)

        results = get_search(query=query, max_results=max_results)
        
        # r=[]
        # for result in results:
        #     if result["link"]==None:
        #         print("none here")
        #         continue
        #     r.append(result)
        # results=r
        # Extract content from each result link
        contents = [(result["link"], get_content(result["link"])) for result in results]
        
        chain = LLMChain(llm=llm, prompt=template)
    
        processed_results = []
        for link, content in contents:
            if content is None:
                continue
                
            job_dict = {
                "link": link,
                "answers": [],
                "raw_content": content[:15000]  # Keep original content for matching
            }
            
            
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

def shorten_question(question_text):
    try:
        chain = LLMChain(llm=llm, prompt=shorten_prompt)
        response = chain.run({"question": question_text})
        print(f"Shortened '{question_text}' to '{response}'")  # Debug print
        return response.strip().strip('"').title()
    except Exception as e:
        print(f"Error shortening question: {e}")
        return question_text[:15].strip() + "..."
