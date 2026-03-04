"""FastAPI application entrypoint for the Resume Screener service.

This replaces the previous script-style logic and exposes a REST endpoint that
accepts a resume PDF and a job description, then returns a compatibility score
with an LLM generated explanation.  The structure follows a clean project
architecture with services, models and configuration separated into their own
modules.

Usage:

    uvicorn main:app --reload

Environment variables:

    GEMINI_API_KEY  - required for generating explanations via Google Gemini.
"""

# Standard library
import os
import shutil
import tempfile
from typing import Any

# Third-party
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import schemas
from .services import resume_parser, job_parser, matcher, llm_explainer


# ---------------------------------------------------------------------------
# application setup
# ---------------------------------------------------------------------------

app = FastAPI()

# allow any origin by default; tighten for production as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Perform one-time initialization such as model loading.

    Importing ``skill_dictionary`` ensures the sentence-transformer model is
    constructed and the skill embeddings are computed once when the app starts.
    """
    # explicit import to trigger module initialization
    from backend.utils import skill_dictionary  # noqa: F401


@app.get("/", response_model=schemas.MessageResponse)
def ping() -> Any:
    """Health check endpoint."""
    return {"message": "Resume Screener API running"}


@app.post(
    "/analyze-resume",
    response_model=schemas.AnalyzeResumeResponse,
)
async def analyze_resume(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
) -> Any:
    """Analyze an uploaded resume against a job description.

    The request must be multipart/form-data with the file and a text field.

    The function saves the uploaded PDF to a temporary file, runs the various
    parsing and matching pipelines, obtains an LLM explanation, and returns a
    structured JSON response.  All errors are converted into HTTP exceptions so
    that the frontend can handle them gracefully.
    """
    tmp_path = None
    try:
        suffix = os.path.splitext(resume_file.filename)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(resume_file.file, tmp)
            tmp_path = tmp.name

        resume_text = resume_parser.extract_text_from_pdf(tmp_path)

        resume_skills = resume_parser.extract_skills_from_resume(resume_text)
        resume_experience = resume_parser.extract_experience_from_resume(resume_text)
        resume_projects = resume_parser.extract_projects_from_resume(resume_text)

        job_skills = job_parser.extract_skills_from_job(job_description)

        match_score, matched_skills, missing_skills = matcher.compute_match(
            resume_skills,
            resume_experience,
            resume_projects,
            job_skills,
            job_description,
        )

        resume_exp_years = round(
            resume_parser.compute_total_resume_experience(resume_experience), 2
        )

        explanation = llm_explainer.generate_llm_explanation(
            match_score,
            matched_skills,
            missing_skills,
            resume_experience,
        )

        return schemas.AnalyzeResumeResponse(
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            resume_experience_years=resume_exp_years,
            explanation=explanation,
        )
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:  # pragma: no cover
                pass
