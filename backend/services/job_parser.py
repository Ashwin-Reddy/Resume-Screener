"""Utilities to extract information from a job description text."""
import re
from typing import Dict, List, Optional

from backend.services.matcher import match_candidates_to_skills


WORD_TO_NUM = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
}


def extract_skills_from_job(text: str) -> Dict[str, List[str]]:
    """Tokenize a job description and match phrases to known skills.

    Simply splits on commas, semicolons and newlines, then defers to the matcher
    service.
    """
    parts = re.split(r"[,;\n]+", text)
    candidates = [p.strip() for p in parts if p.strip()]
    return match_candidates_to_skills(candidates)


def extract_required_experience(job_text: str) -> Optional[int]:
    """Find the minimum years-of-experience requirement in the text.

    The function attempts several common patterns, both numeric and word-based.
    Returns an integer (years) or ``None`` if no clear requirement is found.
    """
    text = job_text.lower()

    # Pattern 1: Numeric requirement such as "3 years" or "3+ years".
    pattern1 = (
        r"(?:minimum|at least|required|minimum of)?\s*(\d+)\s*"
        r"(?:\+|-\d+)?\s*(?:years?|yrs?)"
    )
    match = re.search(pattern1, text, re.I)
    if match:
        return int(match.group(1))

    # Pattern 2: Word-based numbers
    word_pattern = "|".join(WORD_TO_NUM.keys())
    pattern2 = (
        r"(?:minimum|at least|required|minimum of)?\s*("
        + word_pattern
        + r")\s*(?:years?|yrs?)"
    )
    match = re.search(pattern2, text, re.I)
    if match:
        word = match.group(1).lower()
        return WORD_TO_NUM.get(word)

    return None
