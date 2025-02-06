import streamlit as st
import json
from pathlib import Path
from backend import shorten_question
# Custom CSS styling
st.markdown("""
    <style>
    .filter-control {
        margin-top: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    .question-item {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: white;
    }
    .add-question-btn {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    .questions-page {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'questions' not in st.session_state:
    st.session_state.questions = []

# ========== DATA MANAGEMENT ==========
QUESTIONS_FILE = Path('questions.json')
def load_questions():
    """Load questions from JSON file with validation"""
    try:
        if QUESTIONS_FILE.exists():
            with open(QUESTIONS_FILE, 'r') as f:
                questions = json.load(f)
                # Validate question structure
                return [q for q in questions if 'text' in q and 'type' in q]
        return []
    except Exception as e:
        print(f"Error loading questions: {e}")
        return []

questions = load_questions()

def save_questions(questions):
    """Save questions to JSON file"""
    with open(QUESTIONS_FILE, 'w') as f:
        for question in questions:
            try:
                question["shortened"]
            except:
                question["shortened"]=shorten_question(question["text"])
        json.dump(questions, f, indent=2)

def show_questions_page():
    st.title("📝 Questions Management")
    
    # Initialize questions if not already set
    if 'questions' not in st.session_state or not st.session_state.questions:
        loaded = load_questions()
        if loaded:
            st.session_state.questions = loaded
        else:
            print("not loaded")
            st.session_state.questions = [
                {
                    "text": "What is the salary range?", 
                    "type": "numeric",
                    "filter": {"operator": "None", "value": 0},
                    "shortened":"Salary"
                },
                {
                    "text": "Is remote work available?", 
                    "type": "boolean",
                    "filter": "None",
                    "Shortened": "Remote"
                }
            ]

        # Validate loaded questions
        st.session_state.questions = [
            q for q in st.session_state.questions 
            if 'text' in q and 'type' in q
        ]

    
    with st.container():
        st.markdown("<div class='questions-page'>", unsafe_allow_html=True)
        
        # Question list
        st.subheader("Current Questions")
        for idx, question in enumerate(st.session_state.questions):
            # In the question editing section (inside the loop):
            with st.container():
                st.markdown(f"<div class='question-item'>", unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([5, 2, 2, 1])  # Added column for filters
                
                with col1:
                    new_text = st.text_input(
                        f"Question {idx+1}",
                        value=question.get('text', 'New question'),
                        key=f"q_text_{idx}"
                    )
                with col2:
                    new_type = st.selectbox(
                        "Answer Type",
                        options=["numeric", "boolean", "categorical"],
                        index=["numeric", "boolean", "categorical"].index(question.get('type', 'numeric')),
                        key=f"q_type_{idx}"
                    )
                
                # Add filter controls
                with col3:
                    if new_type == "numeric":
                        filter_op = st.selectbox(
                            "Filter Operator",
                            options=["None", ">", "<"],
                            index=0,
                            key=f"filter_op_{idx}"
                        )
                        filter_val = st.number_input(
                            "Filter Value",
                            value=0,
                            key=f"filter_val_{idx}"
                        )
                        question['filter'] = {"operator": filter_op, "value": filter_val}
                    elif new_type == "boolean":
                        filter_bool = st.selectbox(
                            "Filter Value",
                            options=["None", "True", "False"],
                            index=0,
                            key=f"filter_bool_{idx}"
                        )
                        question['filter'] = filter_bool
                    else:
                        question['filter'] = None
                
                with col4:
                    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
                    if st.button("❌", key=f"remove_{idx}"):
                        del st.session_state.questions[idx]
                        st.rerun()
                
                # Update question in state
                st.session_state.questions[idx] = {
                    "text": new_text,
                    "type": new_type,
                    "filter": question.get('filter', None)
                }
                st.markdown("</div>", unsafe_allow_html=True)

        
        # Add new question
        if st.button("➕ Add New Question", use_container_width=True, key="add_question"):
            st.session_state.questions.append({
                "text": "New question",
                "type": "numeric"
            })
            st.rerun()
        
        # Save controls
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("💾 Save All Questions", use_container_width=True):
                valid = all(q['text'].strip() for q in st.session_state.questions)
                if valid:
                    save_questions(st.session_state.questions)
                    st.success("✅ Questions saved successfully!")
                else:
                    st.error("❌ Please fill in all question texts")
        
        with col2:
            if st.button("🔙 Back to Main Page", use_container_width=True):
                st.session_state.page = 'main'
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
