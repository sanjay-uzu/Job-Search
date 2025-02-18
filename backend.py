from pathlib import Path
from search import get_search
from utils import get_content
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI  # Updated import
from langchain.prompts import ChatPromptTemplate  # New prompt template
import json
from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain


import subprocess
import tempfile
import os
import aspose.pdf as ap
import tempfile
import uuid
import subprocess
import os

def latex_to_pdf(latex_code, output_pdf="output.pdf"):
    """
    Converts full LaTeX code into a PDF using pdflatex.
    """
    tex_filename = "temp_latex.tex"

    # Step 1: Write LaTeX code to a .tex file
    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write(latex_code)

    # Step 2: Compile LaTeX using pdflatex
    try:
        subprocess.run([r"C:\Users\sanja\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe", "-interaction=nonstopmode", tex_filename], check=True)
        print("PDF generated successfully.")

        # Rename and move the output PDF
        generated_pdf = tex_filename.replace(".tex", ".pdf")
        os.rename(generated_pdf, output_pdf)
        print(f"PDF saved as: {output_pdf}")

    except subprocess.CalledProcessError as e:
        print("Error compiling LaTeX:", e)

    # Step 3: Clean up auxiliary files
    for ext in [".aux", ".log", ".out"]:
        aux_file = tex_filename.replace(".tex", ext)
        if os.path.exists(aux_file):
            os.remove(aux_file)

    # Remove the temporary .tex file
    os.remove(tex_filename)


# Add new prompt template
resume_prompt = ChatPromptTemplate.from_messages([
    ("system", """Tailor this resume to match the job description.
     Modification strength: {strength}/1.0
     Keep LaTeX formatting intact.
     Return ONLY the modified LaTeX code."""),
    ("human", "Job Description:\n{job_desc}\n\nResume:\n{resume}")
])

def customize_resume(job_desc, resume_text, strength):
    """Process resume customization with LLM"""
    chain = LLMChain(
        llm=ChatOpenAI(temperature=0.7, model="gpt-4"),
        prompt=resume_prompt
    )
    
    response = chain.invoke({
        "job_desc": job_desc[:15000],
        "resume": resume_text[:15000],
        "strength": strength
    })
    
    return response["text"].strip("``````").strip()


# Initialize embeddings
embeddings = OpenAIEmbeddings()

def create_resume_vectorstore(resume_text):
    """Create vector store from resume text"""
    return FAISS.from_texts([resume_text], embeddings)

def create_jobs_vectorstore(job_descriptions):
    """Create vector store from job descriptions"""
    return FAISS.from_texts(job_descriptions, embeddings)

def get_conversation_chain(vectorstore):
    """Create conversation chain with memory"""
    llm = ChatOpenAI(temperature=0.7, model="gpt-4")
    memory = ConversationBufferMemory(
        memory_key='chat_history', 
        return_messages=True
    )
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        memory=memory
    )


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
