import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
from pathlib import Path
from backend import *
import logging
# Page configuration
st.set_page_config(page_title="Job Search Assistant", layout="wide")
logging.basicConfig(level=logging.INFO)
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
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'search_triggered' not in st.session_state:
    st.session_state.search_triggered = False
# Add this line to initialize questions
if 'questions' not in st.session_state:
    st.session_state.questions = []


# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Navigation")
    
    if st.button("🏠 Main Page", use_container_width=True):
        st.session_state.page = 'main'
    if st.button("❓ Questions Manager", use_container_width=True):
        st.session_state.page = 'questions'
    
    if st.session_state.page == 'main':
        with st.expander("🔧 Settings/Filters", expanded=True):
            st.session_state.max_results = st.slider("Max Results", 1, 100, 1)
            st.session_state.include_remote = st.checkbox("Remote Positions", True)
        
        with st.expander("🌐 Search Sites", expanded=True):
            st.session_state.sites = st.multiselect(
                "Select platforms:",
                options=["lever.co", "greenhouse.io", "linkedin.com", "indeed.com"],
                default=["lever.co", "greenhouse.io"]
            )

# ========== MAIN CONTENT ==========
if 'results_df' in st.session_state and st.session_state.results_df is not None:
    print("DataFrame Columns:", st.session_state.results_df.columns)

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
                with st.spinner("🔍 Searching job postings..."):
                    # Generate column headers
                    column_headers = []
                    with open('questions.json', 'r') as f:
                        questions_data = json.load(f)
                        
                        for question in questions_data:
                            
                            column_headers.append(question["shortened"])
                    
                    st.session_state.column_headers = column_headers
                    query_results = []
                    for tag in tags:
                        site_query = " | ".join([f"site:{site}" for site in st.session_state.sites])
                        remote_query = " remote" if st.session_state.include_remote else ""
                        full_query = f"{site_query} {tag}{remote_query}"
                        raw_results = process_jobs(full_query, st.session_state.max_results)
                        
                        # Apply filters
                        filtered_results = apply_filters(raw_results, st.session_state.questions)
                        query_results.extend(filtered_results)
                    
                    if query_results:
                        results = []
                        for result in query_results:
                            row = {'Job Link': result['link']}
                           
                            for i, answer in enumerate(result['answers']):
                                row[column_headers[i]]= answer
                                
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
        
        # Copy DataFrame and check for 'Job Link'
        df = st.session_state.results_df.copy()
        if 'Job Link' in df.columns:
            def make_clickable(link):
                return f'<a href="{link}" target="_blank" style="color: #4a90e2; text-decoration: none;">🔗 View Posting</a>'
            
            df['Job Link'] = df['Job Link'].apply(make_clickable)
        

        
        # Display DataFrame
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
    from questionpage import show_questions_page
    show_questions_page()