# Smart Job Search Assistant 🔍

A Streamlit-powered application that automates job searching, resume customization, and application filtering using AI (Gemini/OpenAI) and Google Search API.

## Features ✨
- **AI-Powered Job Search**:  
  **-** Multi-platform search (Lever, Greenhouse, LinkedIn, Indeed)  
  **-** Customizable filters for remote work, experience level, salary range  
  **-** Resume matching system using vector embeddings which is more thorough than just keyword matching.

- **Smart Resume Customizer**:  
  **-** LaTeX-based resume tailoring to match job descriptions  
  **-** Adjustable modification strength (0.1-1.0)  
  **-** Instant PDF generation

- **Dynamic Question Management**:  
  **-** Customizable data extraction from jobs
  **-** Automatic answer extraction from job descriptions  
  **-** Filter system for jobs that match your unique requirements

## Project Structure 📁
```
job-search-assistant/
├── frontend.py            # Main Streamlit interface
├── backend.py             # AI processing & business logic
├── search.py              # Google Search API integration
├── utils.py               # PDF/text processing utilities
├── questionpage.py        # Questions management UI
├── questions.json         # Default screening questions
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
└── venv/                  # Virtual environment
```

## Prerequisites ⚙️
- Python 3.10+
- Google Custom Search API key
- Google Gemini API key (or OpenAI API key)
- MikTeX (for PDF generation)

## Setup & Installation 🛠️

### 1. Virtual Environment Setup
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 2. Install Dependencies
```
pip install -r requirements.txt
```

### 3. Configuration
1. Create `.env` file:
```
GOOGLE_CSE_ID=your_cse_id
GOOGLE_API_KEY=your_search_key
GEMINI_API_KEY=your_gemini_key
```

2. Enable Google Custom Search API
3. Install MikTeX for PDF support

## Usage Guide 🚀

### Running the Application
```
streamlit run frontend.py
```

### Basic Workflow
1. **Upload Resume** (PDF format)
2. **Set Search Parameters**:
   - Job roles (up to 5)
   - Target platforms
   - Remote filter
   - Match threshold (0.65 recommended)

3. **Review Results**:
   - Automatic resume matching
   - Company/role insights
   - Direct job posting links

4. **Resume Customization**:
   - Paste LaTeX resume code
   - Input job URL
   - Adjust modification strength
   - Download customized PDF

## API Configuration 🔑
| Service | Documentation | Required Keys |
|---------|---------------|---------------|
| Google Custom Search | [API Docs](https://developers.google.com/custom-search/v1/overview) | `GOOGLE_CSE_ID`<br>`GOOGLE_API_KEY` |
| Google Gemini | [Getting Started](https://ai.google.dev/) | `GEMINI_API_KEY` |
| OpenAI (Alternative) | [API Reference](https://platform.openai.com/docs) | `OPENAI_API_KEY` |

## Advanced Features ⚡
- **Custom Questions**:
  ```
  # Access question manager from sidebar
  # Add/remove screening criteria
  # Modify filter thresholds
  ```
  
- **Search Configuration**:
  ```
  # Modify supported platforms in frontend.py:
  options=["lever.co", "greenhouse.io", "linkedin.com", "indeed.com"]
  ```

- **AI Model Switching**:
  ```
  # In backend.py:
  USE_OPENAI = True  # Switch to GPT-4
  ```

## Troubleshooting 🐛
| Issue | Solution |
|-------|----------|
| PDF Generation Failures | Install [MikTeX](https://miktex.org/download) |
| API Limit Errors | Check quota at [Google Cloud Console](https://console.cloud.google.com/) |
| LaTeX Rendering Issues | Validate LaTeX code at [Overleaf](https://www.overleaf.com/) |

## Contributing 🤝
1. Fork the repository
2. Create feature branch:
   ```
   git checkout -b feature/new-feature
   ```
3. Commit changes:
   ```
   git commit -m 'Add some feature'
   ```
4. Push to branch:
   ```
   git push origin feature/new-feature
   ```
5. Open a Pull Request

## License 📄
MIT License - see [LICENSE](LICENSE) for details

---

**Screenshot** 📸  
![img](https://github.com/user-attachments/assets/bca6ddc7-9f88-4143-95b0-8c4bb1d09507)

```

This README includes:
1. Full dependency setup instructions with venv support
2. API configuration details for all services
3. Visual project structure breakdown
4. Troubleshooting matrix for common issues
5. Contribution guidelines
6. License information
7. Screenshot placeholder for visual reference
8. Comprehensive feature list
9. Usage workflow documentation

To complete setup:
1. Create `requirements.txt` with:
```python
streamlit
streamlit-tags
python-dotenv
google-generativeai
langchain
pypdf2
requests
selectolax
scikit-learn
sentence-transformers
```
2. Add proper screenshots before deployment
3. Update LICENSE file with your preferred terms
