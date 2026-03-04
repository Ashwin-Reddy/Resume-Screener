"""Skill matching and scoring algorithms.

This module performs semantic embedding-based matching between candidate
phrases and the canonical skill set.  It also computes an overall match score
incorporating experience weighting.
"""
from typing import Dict, List, Tuple, Any

import numpy as np
from sentence_transformers import util

from backend.config.settings import settings
from backend.utils.skill_dictionary import (
    SKILL_LIST,
    SKILL_CATEGORIES,
    skill_embeddings,
    document_model,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def flatten_skill_dict(skill_dict: Dict[str, List[str]], limit: int | None = None) -> List[str]:
    """Convert a category-organized skill dict into a flat list.

    ``limit`` may be provided to truncate the resulting list for explanation
    prompts.
    """
    items: List[str] = []
    for category, skills in (skill_dict or {}).items():
        for skill in skills:
            if skill and skill not in items:
                items.append(skill)
            if limit and len(items) >= limit:
                return items
    return items


# ---------------------------------------------------------------------------
# semantic matching
# ---------------------------------------------------------------------------

def match_candidates_to_skills(
    candidates: List[str],
    threshold: float | None = None,
) -> Dict[str, List[str]]:
    """Match a list of candidate strings to the nearest skills.

    ``threshold`` defaults to the value configured in settings.
    Returns a dictionary mapping categories to lists of matched skills.
    """
    result: Dict[str, List[str]] = {}
    if not candidates or skill_embeddings is None:
        return result

    thresh = threshold if threshold is not None else settings.similarity_threshold
    cand_embeddings = document_model.encode(candidates, convert_to_tensor=True)
    scores = util.cos_sim(cand_embeddings, skill_embeddings)

    for i, cand in enumerate(candidates):
        best_idx = int(np.argmax(scores[i].cpu().numpy()))
        best_score = float(scores[i][best_idx])

        if best_score >= thresh:
            matched_skill = SKILL_LIST[best_idx]
            category = SKILL_CATEGORIES[best_idx]

            if category not in result:
                result[category] = []
            if matched_skill not in result[category]:
                result[category].append(matched_skill)

    return result


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------

def compute_match(
    resume_skills_dict: Dict[str, List[str]],
    resume_experience_dict: Dict[str, Any],
    resume_projects_dict: Dict[str, Any],
    job_skills_dict: Dict[str, List[str]],
    job_description: str = "",
) -> Tuple[float, Dict[str, List[str]], Dict[str, List[str]]]:
    """Compute a percentage match between resume and job requirements.

    The raw score is simply the fraction of required job skills that appear in
    the resume (skills, roles, organization names, project technologies).
    If the job description specifies a minimum experience requirement and the
    candidate falls short, the score is penalized proportionally.
    """
    total_job_skills = sum(len(skills) for skills in job_skills_dict.values())
    if total_job_skills == 0:
        return 0.0, {}, {}

    resume_skills_lower = set()
    for skills in resume_skills_dict.values():
        resume_skills_lower.update(s.lower() for s in skills)

    for exp in resume_experience_dict.get("Experience", []):
        resume_skills_lower.add(exp.get("Role", "").lower())
        resume_skills_lower.add(exp.get("Organization", "").lower())

    for proj in resume_projects_dict.get("Projects", []):
        for tech in proj.get("Technologies", []):
            resume_skills_lower.add(tech.lower())

    matched_skills_dict: Dict[str, List[str]] = {}
    matched_count = 0

    for category, skills in job_skills_dict.items():
        matched_in_category: List[str] = []
        for skill in skills:
            if skill.lower() in resume_skills_lower:
                matched_in_category.append(skill)
                matched_count += 1
        if matched_in_category:
            matched_skills_dict[category] = matched_in_category

    score = (matched_count / total_job_skills * 100) if total_job_skills > 0 else 0.0

    missing_skills_dict: Dict[str, List[str]] = {}
    for category, skills in job_skills_dict.items():
        missing_in_category: List[str] = []
        for skill in skills:
            if skill.lower() not in resume_skills_lower:
                missing_in_category.append(skill)
        if missing_in_category:
            missing_skills_dict[category] = missing_in_category

    if job_description:
        try:
            from backend.services.job_parser import extract_required_experience
            from backend.services.resume_parser import compute_total_resume_experience

            required_exp = extract_required_experience(job_description)
            if required_exp is not None:
                resume_exp = compute_total_resume_experience(resume_experience_dict)
                if resume_exp < required_exp:
                    experience_ratio = resume_exp / required_exp
                    score = score * experience_ratio
        except Exception:
            # any failure in parsing experience should not crash the matcher
            pass

    return score, matched_skills_dict, missing_skills_dict
