import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
from backend import process_jobs
from pathlib import Path

# Page configuration
st.set_page_config(page_title="Job Search Assistant", layout="wide")

# Custom CSS styling
st.markdown("""
    <style>
    .css-1vq4p4l {
        padding: 1rem;
        border-radius: 0.5rem;
        background: #f8f9fa;
    }
    .stTags {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 0.5rem;
    }
    .tag {
        background: #4a90e2 !important;
        color: white !important;
        border-radius: 15px;
        padding: 2px 10px;
        margin: 2px;
    }
    .tag-remove {
        color: white !important;
    }
    .stDataFrame {
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    table thead th {
        background: linear-gradient(145deg, #6c5ce7, #4a90e2) !important;
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
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'search_triggered' not in st.session_state:
    st.session_state.search_triggered = False

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Navigation")
    
    # Page selection buttons
    if st.button("🏠 Main Page", use_container_width=True):
        st.session_state.page = 'main'
    if st.button("❓ Questions Editor", use_container_width=True):
        st.session_state.page = 'questions'
    
    # Settings/Filters (only shown on main page)
    if st.session_state.page == 'main':
        with st.expander("🔧 Settings/Filters", expanded=True):
            st.session_state.max_results = st.slider("Max Results per Query", 1, 20, 10)
            st.session_state.include_remote = st.checkbox("Include Remote Positions", True)
            st.session_state.salary_range = st.slider("Minimum Salary (USD)", 50000, 200000, 100000, 10000)
        
        with st.expander("🌐 Search Sites", expanded=True):
            st.session_state.sites = st.multiselect(
                "Select platforms:",
                options=["lever.co", "greenhouse.io", "linkedin.com", "indeed.com", "glassdoor.com"],
                default=["lever.co", "greenhouse.io"]
            )

# ========== MAIN CONTENT ==========
if st.session_state.page == 'main':
    st.title("🔍 Smart Job Search Assistant")
    
    # Tag input section
    with st.container():
        st.subheader("Add Job Roles")
        tags = st_tags(
            label='',
            text='Press enter to add more',
            value=[],
            suggestions=['Data Scientist', 'ML Engineer', 'Product Manager'],
            maxtags=5,
            key='job_tags'
        )
    
    # Search button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🚀 Start Search", use_container_width=True):
            if len(tags) > 0:
                st.session_state.search_triggered = True
                with st.spinner("🔍 Searching across platforms..."):
                    query_results = []
                    for tag in tags:
                        site_query = " | ".join([f"site:{site}" for site in st.session_state.sites])
                        remote_query = " remote" if st.session_state.include_remote else ""
                        full_query = f"{site_query} {tag}{remote_query}"
                        query_results.extend(process_jobs(full_query))
                    
                    if query_results:
                        results = []
                        for result in query_results:
                            row = {'Job Link': result['link']}
                            row.update({f"Q{i+1}": answer for i, answer in enumerate(result['answers'])})
                            results.append(row)
                        st.session_state.results_df = pd.DataFrame(results)
                    else:
                        st.session_state.results_df = None
            else:
                st.warning("⚠️ Please enter at least one job role")
    
    # Display results
    if st.session_state.search_triggered:
        if 'results_df' in st.session_state and st.session_state.results_df is not None:
            st.subheader("📊 Search Results")
            
            def make_clickable(link):
                return f'<a href="{link}" target="_blank" style="color: #4a90e2; text-decoration: none;">🔗 View Posting</a>'
            
            df = st.session_state.results_df.copy()
            df['Job Link'] = df['Job Link'].apply(make_clickable)
            
            st.write(
                df.to_html(escape=False, index=False),
                unsafe_allow_html=True
            )
            
            if st.button("🔄 New Search"):
                st.session_state.search_triggered = False
                del st.session_state.results_df
                st.rerun()
        else:
            st.error("❌ No results found. Please adjust your search criteria.")

elif st.session_state.page == 'questions':
    st.title("📝 Questions Editor")
    
    with st.container():
        st.markdown("<div class='questions-page'>", unsafe_allow_html=True)
        
        # Load existing questions
        questions_file = Path('questions.txt')
        if questions_file.exists():
            current_questions = questions_file.read_text()
        else:
            current_questions = "What are the key responsibilities?\nWhat are the required qualifications?\nWhat is the salary range?"
        
        new_questions = st.text_area(
            "Edit your analysis questions (one per line):",
            value=current_questions,
            height=400,
            key="questions_editor"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("💾 Save Changes", use_container_width=True):
                questions_file.write_text(new_questions)
                st.success("✅ Questions saved successfully!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("🔙 Back to Main Page"):
        st.session_state.page = 'main'
        st.rerun()
