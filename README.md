# AI Resume Screener

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2+-61dafb.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-7.3+-646cff.svg)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An AI-powered resume screening system that analyzes candidate resumes against job descriptions using semantic skill matching and large language models, generating compatibility scores, skill gap analysis, and recruiter-style explanations.

## 🚀 Features

- **PDF Resume Parsing**: Extract text, skills, experience, and projects from PDF resumes
- **Semantic Skill Matching**: Uses advanced sentence-transformer models for accurate skill recognition and matching
- **Intelligent Scoring**: Computes match percentages based on required vs. matched skills, with experience-based penalties
- **AI-Powered Explanations**: Generates professional recruiter-style explanations using Google Gemini LLM
- **Modern Web Interface**: Clean, responsive React frontend with real-time analysis
- **RESTful API**: FastAPI backend for easy integration and scalability
- **Comprehensive Skill Database**: Pre-trained on industry-standard skills across multiple categories

## 🏗️ Architecture

The application follows a microservices architecture with clear separation of concerns:

- **Backend (Python/FastAPI)**: Handles PDF processing, AI analysis, and API endpoints
- **Frontend (React/Vite)**: Provides an intuitive user interface for resume uploads and results visualization
- **AI Services**: Integrates with Google Gemini for natural language explanations and sentence-transformers for semantic matching

## 🛠️ Tech Stack

### Backend
- **Python 3.10+**
- **FastAPI** - High-performance web framework
- **PyMuPDF** - PDF text extraction
- **Sentence Transformers** - Semantic embedding and similarity matching
- **Google Generative AI** - LLM-powered explanations
- **NumPy** - Numerical computations
- **Pydantic** - Data validation and settings

### Frontend
- **React 18+** - Modern JavaScript library
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API communication
- **Recharts** - Data visualization components

## 📋 Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- Google Gemini API key (for AI explanations)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Ashwin-Reddy/resume-screener.git
cd resume-screener
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment Variables
Create a `.env` file in the backend directory:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

#### Run the Backend
```bash
cd backend
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`

### 3. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Run the Frontend
```bash
npm run dev
```
The application will be available at `http://localhost:5173`

## 📖 Usage

1. **Upload Resume**: Select a PDF resume file using the upload interface
2. **Enter Job Description**: Paste the complete job description in the text area
3. **Analyze**: Click the "Analyze" button to process the resume
4. **Review Results**:
   - **Match Score**: Percentage compatibility with the job requirements
   - **Missing Skills**: Skills required by the job but not found in the resume
   - **AI Explanation**: Professional assessment of the candidate's fit

## 🔧 API Documentation

### Endpoints

#### `GET /`
Health check endpoint.

**Response:**
```json
{
  "message": "Resume Screener API running"
}
```

#### `POST /analyze-resume`
Analyze a resume against a job description.

**Request:**
- Content-Type: `multipart/form-data`
- `resume_file`: PDF file (required)
- `job_description`: Text string (required)

**Response:**
```json
{
  "match_score": 85.5,
  "missing_skills": {
    "Programming Languages": ["Java", "C++"],
    "Databases": ["PostgreSQL"]
  },
  "explanation": "This candidate demonstrates strong Python and JavaScript skills..."
}
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Sentence Transformers** for semantic similarity matching
- **Google Gemini** for AI-powered explanations
- **FastAPI** community for the excellent web framework
- **React** ecosystem for modern frontend development

## 📞 Support

If you encounter any issues or have questions:

- Open an issue on GitHub
- Check the API documentation
- Review the setup instructions

---

**Built with ❤️ using FastAPI and React**</content>
