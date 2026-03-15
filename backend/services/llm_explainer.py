"""Module responsible for generating recruiter-style explanations via Gemini.

The heavy lifting remains in ``main.py`` previously but has been abstracted here
for clarity and reuse.  This module references configuration settings and the
skill matcher to build prompts.
"""
import os
from typing import Dict, List, Any

from backend.config.settings import settings
from backend.services.matcher import flatten_skill_dict


def generate_llm_explanation(
    match_score: float,
    matched_skills_dict: Dict[str, List[str]],
    missing_skills_dict: Dict[str, List[str]],
    resume_experience_dict: Dict[str, Any],
) -> str:
    """Produce a one‑paragraph summary using the Gemini LLM.

    If the GEMINI_API_KEY is missing or the API call fails the function will
    return an informative error string rather than raising.
    """
    missing_list = flatten_skill_dict(missing_skills_dict, limit=settings.max_skills_for_explanation)

    roles = [
        exp.get("Role")
        for exp in resume_experience_dict.get("Experience", [])
        if exp.get("Role")
    ]
    roles_text = ", ".join(roles[:3]) if roles else "roles unavailable"

    missing_str = (
        ", ".join(missing_list) if missing_list else "no critical missing skills"
    )

    prompt = (
        f"You are a professional tech recruiter. Given the following candidate-job "
        f"match data, write one natural paragraph (120-150 words) summarizing the "
        f"candidate's fit, strengths, gaps, and a short recommendation. "
        f"Do not use bullet points or JSON.\n\n"
        f"Match score: {match_score:.1f}%\n"
        f"Missing skills: {missing_str}\n"
        f"Experience summary: {roles_text}.\n\n"
        f"Output: a single professional recruiter-style paragraph "
        f"(no bullets, no JSON)."
    )

    api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "GEMINI_API_KEY not set; cannot call Gemini. "
            "Please set GEMINI_API_KEY in the environment to enable LLM explanations."
        )

    try:
        from google import genai
    except ImportError as e:
        return f"Gemini SDK not available: {e}"

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return f"Failed to initialize Gemini client: {e}"

    try:
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        text = None
        out = getattr(resp, "outputs", None) or getattr(resp, "output", None)

        if out:
            try:
                first = out[0]
                if isinstance(first, dict):
                    content = first.get("content") or first.get("text")
                    if isinstance(content, list) and content:
                        c0 = content[0]
                        if isinstance(c0, dict) and "text" in c0:
                            text = c0["text"]
                        elif isinstance(c0, str):
                            text = c0
                    elif isinstance(content, str):
                        text = content
                else:
                    text = str(first)
            except Exception:
                text = None

        if not text:
            text = (
                getattr(resp, "text", None)
                or getattr(resp, "output_text", None)
                or str(resp)
            )

        return text.strip()
    except Exception as e:
        return f"Gemini API call failed: {e}"
