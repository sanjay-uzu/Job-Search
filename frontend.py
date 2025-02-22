import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
from pathlib import Path
from backend import *
import logging
from utils import extract_text_from_pdf, get_embeddings
from sklearn.metrics.pairwise import cosine_similarity

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
    .resume-box {
        border: 2px solid #4a90e2;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
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

st.session_state.resume_vectorstore=None
st.session_state.resume_text=None


# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Navigation")
    # In sidebar section
    if st.button("🛠️ Resume Customizer", use_container_width=True):
        st.session_state.page = 'customizer'
    if st.button("🏠 Main Page", use_container_width=True):
        st.session_state.page = 'main'
    if st.button("❓ Questions Manager", use_container_width=True):
        st.session_state.page = 'questions'
    # In Settings/Filters section
    st.session_state.match_threshold = st.slider(
        "Resume Match Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.65,
        step=0.05
    )

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
# Add to session state initialization
if 'resume_vector' not in st.session_state:
    st.session_state.resume_vector = None

# Add resume uploader to sidebar
with st.sidebar:
    with st.expander("📄 Upload Resume", expanded=True):
        resume_file = st.file_uploader(
            "Upload your resume (PDF)",
            type="pdf",
            key="resume_upload"
        )
        # Resume upload section
        if resume_file:
            with st.spinner("Processing resume..."):
                st.session_state.resume_text = extract_text_from_pdf(resume_file)
                if st.session_state.resume_text:
                    st.session_state.resume_vectorstore = create_resume_vectorstore(st.session_state.resume_text)
                    st.success("Resume processed successfully!")
                    
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
                        print(filtered_results)
                        query_results.extend(filtered_results)
                    
                    # Results processing
                    if query_results:
                        job_descriptions = [job['raw_content'] for job in query_results]
                        jobs_vectorstore = create_jobs_vectorstore(job_descriptions)
                        if st.session_state.resume_vectorstore is not None:
                            conversation_chain = get_conversation_chain(st.session_state.resume_vectorstore)
                        results = []
                        for result in query_results:
                            row = {'Job Link': result['link']}
                            
                            # Add resume match column if resume exists
                            if st.session_state.resume_text is not None:
                                        if USE_OPENAI:
                                            response = conversation_chain({
                                                'question': f"Does this resume match the job: {result['raw_content']} Reply only with yes or no?"
                                            })
                                            row['Match'] = "True" if "yes" in response['answer'].lower() else "False"
                                        else: 
                                            response = llm.generate_content(f"Does this resume match the job description? Reply only with yes or no Resume: {st.session_state.resume_text}\n\nJob Description: {result['raw_content']}"
                                        )
                                            row['Match'] = "True" if "yes" in response.text.lower() else "False"

                            
                            for i, answer in enumerate(result['answers']):
                                row[column_headers[i]] = answer
                            results.append(row)
                        st.session_state.results_df = pd.DataFrame(results)
                    else:
                        st.session_state.results_df = None
            else:
                st.warning("⚠️ Please enter at least one job role")
elif st.session_state.page == 'customizer':
    st.title("📝 Resume Customizer")
    modified_resume=False
    with st.form("resume_customizer"):
        job_link = st.text_input("Job Posting URL")
        resume_content = st.text_area("LaTeX Resume Code", height=300)
        modification_strength = st.slider("Modification Strength", 0.0, 1.0, 0.5)
        submitted=False
        if st.form_submit_button("✨ Customize Resume"):
            with st.spinner("Tailoring resume..."):
                try:
                    submitted=True
                    # Get job description
                    job_desc = get_content(job_link)
                    
                    # Call LLM customization
                    modified_resume = customize_resume(
                        job_desc, 
                        resume_content,
                        modification_strength
                    )
                    
                    st.subheader("Customized Resume")
                    st.code(modified_resume, language="latex")
                    # Generate PDF immediately after submission
                    with st.spinner("Generating PDF..."):
                        try:
                            pdf_bytes = latex_to_pdf(modified_resume)
                            st.session_state.pdf_bytes = pdf_bytes  # Store in session state
                        except Exception as e:
                            st.error(f"PDF generation failed: {str(e)}")
                    # Download button OUTSIDE the form
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")
            

        if st.session_state.get("pdf_bytes"):
            st.download_button(
                label="💾 Download PDF Resume",
                data=st.session_state.pdf_bytes,
                file_name="custom_resume.pdf",
                mime="application/pdf"
            )

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
        # In results display
        # In display section
        if 'Match' in df.columns:
            df['Match'] = df['Match'].apply(
                lambda x: '✅ Match' if x == "True" else '❌ No Match'
            )


        
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