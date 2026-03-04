"""Functions related to parsing resume content (PDF/text).

The logic in this module was previously part of ``main.py`` and has been
refactored for easier testing and reuse.  Each public function includes type
hints and a descriptive docstring.
"""
import re
from datetime import datetime
from typing import Dict, List, Any

from backend.utils.skill_dictionary import SKILL_LIST


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file located at ``file_path``.

    Args:
        file_path: Path to the PDF file to read.

    Returns:
        Concatenated text of all pages.
    """
    import fitz  # late import to keep dependencies local to function

    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


# ---------------------------------------------------------------------------
# section extraction helper shared by experience/projects
# ---------------------------------------------------------------------------

def extract_section(text: str, headers: List[str]) -> List[str]:
    """Collect contiguous lines after one of the specified section headers.

    The capture stops when an empty line or a new primary section header is
    encountered.

    Args:
        text: Full resume text to search.
        headers: List of header words or regex fragments to identify the section.

    Returns:
        Lines belonging to the matched section (stripped).
    """
    lines = text.splitlines()
    capture = False
    section_lines: List[str] = []
    header_pattern = re.compile(r"(?:" + "|".join(headers) + r")", re.I)
    boundary_pattern = re.compile(
        r"\b(skills|experience|projects|education|certifications)\b", re.I
    )

    for line in lines:
        if not capture and header_pattern.search(line):
            capture = True
            continue
        if capture:
            if not line.strip():
                break
            if boundary_pattern.search(line):
                break
            section_lines.append(line.strip())

    return section_lines


# ---------------------------------------------------------------------------
# skill extraction
# ---------------------------------------------------------------------------

def extract_skills_from_resume(text: str) -> Dict[str, List[str]]:
    """Parse the "Skills" section of a resume and match phrases to known skills.

    This function isolates the portion of the resume labeled "Skills" and
    delegates the actual semantic matching to the ``matcher`` service.

    Args:
        text: Entire resume text.

    Returns:
        Category-to-skills mapping in lowercase.
    """
    from backend.services.matcher import match_candidates_to_skills

    lines = text.splitlines()
    capture = False
    candidates: List[str] = []

    for line in lines:
        if not capture and re.search(r"\bskills\b", line, re.I):
            capture = True
            continue
        if capture:
            if not line.strip():
                break
            parts = re.split(r"[,;]+", line)
            for part in parts:
                token = part.strip()
                if token:
                    candidates.append(token)

    return match_candidates_to_skills(candidates)


# ---------------------------------------------------------------------------
# experience handling
# ---------------------------------------------------------------------------

def normalize_duration(duration_text: str) -> str:
    """Standardize various resume duration formats to a normalized string.

    Accepts raw snippets like "6 yrs", "Nov 2019 - Present", etc., and
    returns a human-friendly description such as "4 years 3 months".
    """
    text = duration_text.strip()

    years_match = re.search(r"(\d+)\s*(?:years?|yrs?)", text, re.I)
    if years_match:
        return years_match.group(0)

    def parse_month_year(s: str):
        s = s.strip().replace(",", "")
        for fmt in ("%B %Y", "%b %Y", "%Y"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    parts = re.split(r"\s*[–-]\s*", text)
    if len(parts) == 2:
        start_str, end_str = parts
        start_dt = parse_month_year(start_str)
        if re.search(r"present", end_str, re.I):
            end_dt = datetime.today()
        else:
            end_dt = parse_month_year(end_str)

        if start_dt and end_dt and start_dt <= end_dt:
            total_months = (end_dt.year - start_dt.year) * 12 + (
                end_dt.month - start_dt.month
            )
            years = total_months // 12
            months = total_months % 12

            if years > 0 and months > 0:
                return f"{years} years {months} months"
            elif years > 0:
                return f"{years} years"
            else:
                return f"{months} months"

    return text


def extract_experience_from_resume(text: str) -> Dict[str, List[Dict[str, str]]]:
    """Pull out job roles, organizations, and durations from a resume.

    The function looks for a section labeled "Experience" and then iterates
    through the lines attempting to capture entries such as:

        Company Name (Duration)\n
    followed later by a "Role - Title:" line.

    Returns a dictionary containing an "Experience" key with a list of
    individual experience records.
    """
    lines = extract_section(text, [r"\bexperience\b", r"\bwork experience\b"])
    experiences: List[Dict[str, str]] = []

    current_org = ""
    current_duration = ""

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line or line == "·":
            i += 1
            continue

        if re.search(
            r"\b(languages|skills|projects|education|certifications)\b",
            line,
            re.I,
        ):
            break

        org_duration_match = re.match(r"^(.*?)\s*\(\s*(.*?)\s*\)$", line)

        if org_duration_match:
            current_org = org_duration_match.group(1).strip()
            raw_duration = org_duration_match.group(2).strip()
            current_duration = normalize_duration(raw_duration)
            i += 1
            continue

        role_match = re.match(
            r"^Role\s*[–-]\s*(.*?)\s*:?\s*$",
            line,
            re.I,
        )

        if role_match and current_org:
            role = role_match.group(1).strip()
            experiences.append({
                "Role": role,
                "Organization": current_org,
                "Duration": current_duration,
            })

        i += 1

    return {"Experience": experiences}


def compute_total_resume_experience(resume_experience_dict: Dict[str, Any]) -> float:
    """Sum all experience durations (in years) from the parsed resume dict.

    Returns a float representing the total number of years (fractional).
    """
    total_months = 0

    for exp in resume_experience_dict.get("Experience", []):
        duration_str = exp.get("Duration", "").lower()
        if not duration_str:
            continue

        years_match = re.search(r"(\d+)\s*years?", duration_str)
        months_match = re.search(r"(\d+)\s*months?", duration_str)

        years = int(years_match.group(1)) if years_match else 0
        months = int(months_match.group(1)) if months_match else 0

        total_months += years * 12 + months

    return total_months / 12.0


def extract_projects_from_resume(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Identify projects listed on a resume along with their technologies.

    Projects are assumed to be under a "Projects" heading; each project title
    ends with a colon and is followed by descriptive lines that may contain
    technology names.
    """
    from backend.services.matcher import match_candidates_to_skills

    lines = extract_section(text, [r"\bprojects\b"])
    projects: List[Dict[str, Any]] = []

    current_title: str | None = None
    current_desc: List[str] = []

    def flush_project() -> None:
        nonlocal current_title, current_desc
        if not current_title:
            return

        desc_text = " ".join(current_desc).strip()
        tech_set = set()

        if desc_text:
            for skill in SKILL_LIST:
                if re.search(r"\b" + re.escape(skill) + r"\b", desc_text, re.I):
                    tech_set.add(skill)

            if not tech_set:
                tech_dict = match_candidates_to_skills([desc_text])
                for skills in tech_dict.values():
                    tech_set.update(skills)

        # canonical correction
        if "sql" in tech_set:
            tech_set.discard("sql")
            tech_set.add("sql server")

        projects.append({
            "Project Title": current_title,
            "Technologies": list(tech_set),
        })
        current_title = None
        current_desc = []

    for line in lines:
        raw = line.lstrip("· ").strip()
        if not raw:
            continue

        if raw.endswith(":"):
            flush_project()
            title_part = raw[:-1].strip()
            if "–" in title_part:
                title_part = title_part.split("–")[-1].strip()
            current_title = title_part
        else:
            current_desc.append(raw)

    flush_project()
    return {"Projects": projects}
