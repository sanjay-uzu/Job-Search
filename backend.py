import os
import json
import subprocess
from dotenv import load_dotenv
from pathlib import Path

# Import Gemini API
import google.generativeai as genai

# Import OpenAI API (if needed)
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain, ConversationalRetrievalChain

# Import utility functions
from search import get_search
from utils import get_content

# Load environment variables
load_dotenv()

# Set default to Gemini, but allow OpenAI option
USE_OPENAI = False  # Set to True if OpenAI should be used instead of Gemini

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize OpenAI Model & Embeddings if needed
if USE_OPENAI:
    llm = ChatOpenAI(temperature=0, model="gpt-4o")
    embeddings = OpenAIEmbeddings()
else:
    # Gemini Model
    llm = genai.GenerativeModel("gemini-2.0-flash")
    embeddings = None  # Gemini does not require FAISS embeddings

# LaTeX to PDF Conversion
def latex_to_pdf(latex_code, output_pdf="output.pdf"):
    """Converts full LaTeX code into a PDF using pdflatex."""
    tex_filename = "temp_latex.tex"
    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write(latex_code)
    
    try:
        subprocess.run([
            r"C:\Users\sanja\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe",
            "-interaction=nonstopmode", tex_filename
        ], check=True)
        os.rename(tex_filename.replace(".tex", ".pdf"), output_pdf)
    except subprocess.CalledProcessError as e:
        print("Error compiling LaTeX:", e)
    finally:
        for ext in [".aux", ".log", ".out", ".tex"]:
            aux_file = tex_filename.replace(".tex", ext)
            if os.path.exists(aux_file):
                os.remove(aux_file)

# Resume Tailoring Prompt
resume_prompt = ChatPromptTemplate.from_messages([
    ("system", """Tailor this resume to match the job description.
    Modification strength: {strength}/1.0
    Keep LaTeX formatting intact.
    Return ONLY the modified LaTeX code."""), 
    ("human", "Job Description:\n{job_desc}\n\nResume:\n{resume}")
])

def customize_resume(job_desc, resume_text, strength):
    """Process resume customization with Gemini/OpenAI"""
    if USE_OPENAI:
        chain = LLMChain(llm=llm, prompt=resume_prompt)
        response = chain.invoke({
            "job_desc": job_desc[:15000],
            "resume": resume_text[:15000],
            "strength": strength
        })
        return response["text"].strip()
    else:
        response = llm.generate_content([
            {"role": "system", "content": "Tailor this resume to match the job description."},
            {"role": "user", "content": f"Job Description:\n{job_desc}\n\nResume:\n{resume_text}"}
        ])
        return response.text.strip()

# Vector Store Creation
def create_resume_vectorstore(resume_text):
    if USE_OPENAI:
        return FAISS.from_texts([resume_text], embeddings)
    return None  # Gemini does not require FAISS embeddings

def create_jobs_vectorstore(job_descriptions):
    if USE_OPENAI:
        return FAISS.from_texts(job_descriptions, embeddings)
    return None  # Gemini does not require FAISS embeddings

def get_conversation_chain(vectorstore):
    if USE_OPENAI:
        memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
        return ConversationalRetrievalChain.from_llm(
            llm=llm, retriever=vectorstore.as_retriever(), memory=memory
        )
    return None  # Gemini does not require memory chains

# Shortening Prompt for Column Headers
shorten_prompt = ChatPromptTemplate.from_messages([
    ("system", "Convert this question into a 2-4 word column header. Return only the header text."),
    ("human", "{question}")
])

def shorten_question(question_text):
    try:
        if USE_OPENAI:
            chain = LLMChain(llm=llm, prompt=shorten_prompt)
            response = chain.run({"question": question_text})
            return response.strip().strip('"').title()
        else:
            response = llm.generate_content(f"Convert this question into a 2-4 word column header.{question_text}")
            return response.text.strip()
    except Exception as e:
        print(f"Error shortening question: {e}")
        return question_text[:15].strip() + "..."

# Load Questions from JSON
def load_questions():
    try:
        with open('questions.json', 'r') as f:
            questions_data = json.load(f)
            return [
                f"{q['text']} Answer only in {'numbers' if q['type'] == 'numeric' else 'True or False' if q['type'] == 'boolean' else 'as few words as possible'}."
                for q in questions_data
            ]
    except Exception as e:
        print(f"Error loading questions: {e}")
        return []

questions = load_questions()

# Job Processing Function
def process_jobs(query, max_results):
    try:
        results = get_search(query=query, max_results=max_results)
        contents = [(result["link"], get_content(result["link"])) for result in results if result["link"]]
        processed_results = []
        for link, content in contents:
            if not content:
                continue
            job_dict = {"link": link, "answers": [], "raw_content": content[:15000]}
            
            formatted_questions = "\n".join([f"Q{i+1}: {q}" for i, q in enumerate(questions)])
            
            if USE_OPENAI:
                chain = LLMChain(llm=llm, prompt=ChatPromptTemplate.from_messages([
                    ("system", "Answer the following questions based on the job description. Provide answers in the format: Q1: [answer]\nQ2: [answer] ... If no info on the question is found , reply with 'No Info Found' "),
                    ("human", f"Job Description: {content[:15000]}\nQuestions:\n{formatted_questions}")
                ]))
                response = chain.invoke({})
                
                answer_dict = {line.split(": ")[0]: line.split(": ")[1] for line in response["text"].strip().split("\n") if ": " in line}
                job_dict["answers"] = [answer_dict.get(f"Q{i+1}", "No answer") for i in range(len(questions))]
            else:
                response = llm.generate_content(
                    f"Answer the following questions based on the job description. Provide answers in the format: Q1: [answer]\nQ2: [answer] ...\n\nJob Description: {content[:15000]}\nQuestions:\n{formatted_questions}"
                )

                
                answer_dict = {line.split(": ")[0]: line.split(": ")[1] for line in response.text.strip().split("\n") if ": " in line}
                job_dict["answers"] = [answer_dict.get(f"Q{i+1}", "No answer") for i in range(len(questions))]
            
            processed_results.append(job_dict)
        
        return processed_results
    except Exception as e:
        print(f"Error processing jobs: {e}")
        return []


# Apply Filters to Job Results
def apply_filters(results, questions):
    filtered = []
    for job in results:
        valid = True
        for i, answer in enumerate(job['answers']):
            if i >= len(questions):
                continue
            question = questions[i]
            if not question.get('filter'):
                continue
            try:
                if question['type'] == 'numeric' and question['filter']['operator'] != "None":
                    if not answer.strip():
                        valid = False
                        break
                    answer_num = float(answer)
                    if question['filter']['operator'] == ">" and not (answer_num > question['filter']['value']):
                        valid = False
                    elif question['filter']['operator'] == "<" and not (answer_num < question['filter']['value']):
                        valid = False
                elif question['type'] == 'boolean' and question['filter'] != "None":
                    if answer.lower() != question['filter'].lower():
                        valid = False
            except (ValueError, TypeError) as e:
                print(f"Filter error: {e}")
                valid = False
                break
        if valid:
            filtered.append(job)
    return filtered
