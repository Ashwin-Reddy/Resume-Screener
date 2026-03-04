"""
Resume Screener - A tool for matching resumes against job descriptions.

This module provides functionality to extract information from PDF resumes,
parse job descriptions, and compute compatibility scores using semantic
embeddings and LLM-based explanations.
"""

# Standard Library
import os
import re
from datetime import datetime

# Third-party Libraries
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Gemini API
from google import genai
import fitz  # PyMuPDF


# ==============================
# Configuration & Constants
# ==============================

SIMILARITY_THRESHOLD = 0.65
GEMINI_MODEL = "gemini-3-flash-preview"
MAX_SKILLS_FOR_EXPLANATION = 6


# ==============================
# Model Loading
# ==============================

document_model = SentenceTransformer('all-MiniLM-L6-v2')


# ==============================
# Skill Dictionary & Setup
# ==============================

SKILL_DICTIONARY = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "csharp", "c#",
        "php", "ruby", "go", "rust", "kotlin", "swift", "objective-c", "perl",
        "scala", "groovy", "r", "matlab", "lua", "haskell", "clojure"
    ],
    "Web Frameworks": [
        "django", "flask", "fastapi", "spring", "spring boot", "express",
        "react", "angular", "vue", "nextjs", "next.js", "svelte", "ember",
        "rails", "laravel", "symfony", "asp.net"
    ],
    "Databases": [
        "postgresql", "mysql", "mongodb", "oracle", "sqlite", "redis",
        "cassandra", "dynamodb", "elasticsearch", "memcached", "firebase",
        "mariadb", "sql", "sql server"
    ],
    "Cloud Platforms": [
        "aws", "azure", "gcp", "google cloud", "heroku", "digitalocean",
        "linode", "docker", "kubernetes", "openstack"
    ],
    "DevOps & Tools": [
        "git", "github", "gitlab", "bitbucket", "jenkins", "circleci",
        "travis ci", "gitlab ci", "github actions", "docker", "kubernetes",
        "terraform", "ansible", "linux", "unix", "nginx", "apache"
    ],
    "Data Science & ML": [
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
        "opencv", "nltk", "spacy", "matplotlib", "seaborn", "plotly",
        "jupyter", "jupyter notebook", "nlp"
    ],
    "APIs & Protocols": [
        "rest", "rest api", "graphql", "soap", "json", "xml", "http",
        "websocket", "grpc"
    ],
    "Frontend & UI": [
        "html", "css", "sass", "bootstrap", "tailwind", "webpack", "babel",
        "gulp", "grunt", "npm", "yarn", "pnpm"
    ],
    "Testing": [
        "pytest", "unittest", "jest", "mocha", "jasmine", "rspec",
        "jUnit", "testng", "selenium", "cypress", "postman"
    ],
    "Mobile Development": [
        "react native", "flutter", "xamarin", "swift", "kotlin", "ios",
        "android", "objective-c"
    ],
    "Message Queues": [
        "kafka", "rabbitmq", "activemq", "mqtt", "celery"
    ],
    "Search & Analytics": [
        "elasticsearch", "kibana", "logstash", "splunk", "datadog", "newrelic"
    ],
    "Project Management": [
        "git", "jira", "confluence", "trello", "asana", "monday.com"
    ]
}

# Build skill lookup structures
SKILL_LIST = []  # lowercase skill names for embeddings
SKILL_CATEGORIES = []  # corresponding categories
SKILL_TO_CATEGORY = {}  # quick lookup: skill -> category

for category, skills in SKILL_DICTIONARY.items():
    for skill in skills:
        skill_lower = skill.lower()
        SKILL_LIST.append(skill_lower)
        SKILL_CATEGORIES.append(category)
        SKILL_TO_CATEGORY[skill_lower] = category

# Precompute skill embeddings
skill_embeddings = (
    document_model.encode(SKILL_LIST, convert_to_tensor=True)
    if SKILL_LIST
    else None
)


# ==============================
# Utility Functions
# ==============================

def flatten_skill_dict(skill_dict, limit=None):
    """Flatten a category-organized skill dict into a flat list.

    Args:
        skill_dict: Dict with category keys and skill lists as values.
        limit: Maximum number of skills to return (None for no limit).

    Returns:
        List of unique skill strings (lowercase).
    """
    items = []
    for category, skills in (skill_dict or {}).items():
        for skill in skills:
            if skill and skill not in items:
                items.append(skill)
            if limit and len(items) >= limit:
                return items
    return items


# ==============================
# PDF & Text Processing
# ==============================

def extract_text_from_pdf(file_path):
    """Extract all text from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Concatenated text from all PDF pages.
    """
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_section(text, headers):
    """Extract text from a resume section identified by headers.

    Captures all non-blank lines following a matching header until a blank
    line or another common section header is encountered.

    Args:
        text: The full text to search.
        headers: List of header names or regex patterns to match.

    Returns:
        List of stripped lines from the matched section.
    """
    lines = text.splitlines()
    capture = False
    section_lines = []
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


# ==============================
# Skill Extraction & Matching
# ==============================

def match_candidates_to_skills(candidates, threshold=SIMILARITY_THRESHOLD):
    """Match candidate phrases to known skills using semantic embeddings.

    Args:
        candidates: List of candidate skill phrases.
        threshold: Minimum cosine similarity score to consider a match.

    Returns:
        Dict with category keys and lists of matched skills as values.
    """
    result = {}
    if not candidates or skill_embeddings is None:
        return result

    cand_embeddings = document_model.encode(candidates, convert_to_tensor=True)
    scores = util.cos_sim(cand_embeddings, skill_embeddings)

    for i, cand in enumerate(candidates):
        best_idx = int(np.argmax(scores[i].cpu().numpy()))
        best_score = float(scores[i][best_idx])

        if best_score >= threshold:
            matched_skill = SKILL_LIST[best_idx]
            category = SKILL_CATEGORIES[best_idx]

            if category not in result:
                result[category] = []
            if matched_skill not in result[category]:
                result[category].append(matched_skill)

    return result


def extract_skills_from_resume(text):
    """Extract skills from resume Skills section using semantic matching.

    Args:
        text: Full resume text.

    Returns:
        Dict with skill categories as keys and skill lists as values.
    """
    lines = text.splitlines()
    capture = False
    candidates = []

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


def extract_skills_from_job(text):
    """Extract skills from job description using semantic matching.

    Args:
        text: Job description text.

    Returns:
        Dict with skill categories as keys and skill lists as values.
    """
    parts = re.split(r"[,;\n]+", text)
    candidates = [p.strip() for p in parts if p.strip()]
    return match_candidates_to_skills(candidates)


# ==============================
# Experience Extraction
# ==============================

def normalize_duration(duration_text):
    """Normalize various duration formats to a consistent string.

    Supports:
    - Direct years expression: "6 years", "6 yrs"
    - Date ranges: "Nov 2019 – Present" or "Jan 2020 - March 2023"

    Args:
        duration_text: Raw duration text from resume.

    Returns:
        Normalized duration string (e.g., "4 years" or "2 years 3 months").
    """
    text = duration_text.strip()

    # Direct years expression
    years_match = re.search(r"(\d+)\s*(?:years?|yrs?)", text, re.I)
    if years_match:
        return years_match.group(0)

    def parse_month_year(s):
        """Parse month-year string to datetime object."""
        s = s.strip().replace(',', '')
        for fmt in ("%B %Y", "%b %Y", "%Y"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    # Parse date range
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


def extract_experience_from_resume(text):
    """Extract work experience entries from resume.

    Expects format:
        Organization (Duration)
        Role – Role Name:
        [description lines]

    Args:
        text: Full resume text.

    Returns:
        Dict with "Experience" key containing list of experience dicts.
        Each entry has: Role, Organization, Duration.
    """
    lines = extract_section(text, [r"\bexperience\b", r"\bwork experience\b"])
    experiences = []

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

        # Match: Organization (Duration)
        org_duration_match = re.match(r"^(.*?)\s*\(\s*(.*?)\s*\)$", line)

        if org_duration_match:
            current_org = org_duration_match.group(1).strip()
            raw_duration = org_duration_match.group(2).strip()
            current_duration = normalize_duration(raw_duration)
            i += 1
            continue

        # Match: Role – Role Name:
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


def compute_total_resume_experience(resume_experience_dict):
    """Compute total years of experience from all entries.

    Parses normalized duration strings and sums them.

    Args:
        resume_experience_dict: Dict with "Experience" list.

    Returns:
        Total experience as float (e.g., 4.25 for 4 years 3 months).
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


def extract_required_experience(job_text):
    """Extract minimum years requirement from job description.

    Supports formats:
    - "3 years experience"
    - "3+ years"
    - "3-5 years"
    - "at least 3 years"
    - "minimum three years"

    Args:
        job_text: Job description text.

    Returns:
        Minimum required years as int, or None if not found.
    """
    word_to_num = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15,
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    }
    text = job_text.lower()

    # Pattern 1: Digit-based (3 years, 3+ years, etc.)
    pattern1 = (
        r"(?:minimum|at least|required|minimum of)?\s*(\d+)\s*"
        r"(?:\+|-\d+)?\s*(?:years?|yrs?)"
    )
    match = re.search(pattern1, text, re.I)
    if match:
        return int(match.group(1))

    # Pattern 2: Word-based (three years, five years, etc.)
    word_pattern = "|".join(word_to_num.keys())
    pattern2 = (
        r"(?:minimum|at least|required|minimum of)?\s*("
        + word_pattern + r")\s*(?:years?|yrs?)"
    )
    match = re.search(pattern2, text, re.I)
    if match:
        word = match.group(1).lower()
        return word_to_num.get(word)

    return None


# ==============================
# Project Extraction
# ==============================

def extract_projects_from_resume(text):
    """Extract projects and their technologies from resume.

    Projects are listed under a "Projects" heading; each title typically
    ends with a colon followed by description lines.

    Args:
        text: Full resume text.

    Returns:
        Dict with "Projects" key containing list of project dicts.
        Each entry has: Project Title, Technologies.
    """
    lines = extract_section(text, [r"\bprojects\b"])
    projects = []

    current_title = None
    current_desc = []

    def flush_project():
        nonlocal current_title, current_desc
        if not current_title:
            return

        desc_text = " ".join(current_desc).strip()
        tech_set = set()

        if desc_text:
            # First try exact keyword matching
            for skill in SKILL_LIST:
                if re.search(r"\b" + re.escape(skill) + r"\b", desc_text, re.I):
                    tech_set.add(skill)

            # Fallback to embedding-based matching
            if not tech_set:
                tech_dict = match_candidates_to_skills([desc_text])
                for skills in tech_dict.values():
                    tech_set.update(skills)

        # Canonicalize sql -> sql server
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


# ==============================
# Skill Matching & Scoring
# ==============================

def compute_match(
    resume_skills_dict,
    resume_experience_dict,
    resume_projects_dict,
    job_skills_dict,
    job_description="",
):
    """Compute match score between resume and job description.

    Aggregates all resume information (skills, experience, projects) and
    compares against job requirements. Applies experience-based weighting
    if job description specifies a requirement.

    Args:
        resume_skills_dict: Dict with skill categories as keys.
        resume_experience_dict: Dict with "Experience" list.
        resume_projects_dict: Dict with "Projects" list.
        job_skills_dict: Dict with required skill categories.
        job_description: Raw job description text (optional).

    Returns:
        Tuple of (score, matched_skills_dict, missing_skills_dict).
        Score is a percentage (0-100).
    """
    total_job_skills = sum(len(skills) for skills in job_skills_dict.values())
    if total_job_skills == 0:
        return 0.0, {}, {}

    # Aggregate resume tokens
    resume_skills_lower = set()
    for skills in resume_skills_dict.values():
        resume_skills_lower.update(s.lower() for s in skills)

    for exp in resume_experience_dict.get("Experience", []):
        resume_skills_lower.add(exp.get("Role", "").lower())
        resume_skills_lower.add(exp.get("Organization", "").lower())

    for proj in resume_projects_dict.get("Projects", []):
        for tech in proj.get("Technologies", []):
            resume_skills_lower.add(tech.lower())

    # Count matches
    matched_skills_dict = {}
    matched_count = 0

    for category, skills in job_skills_dict.items():
        matched_in_category = []
        for skill in skills:
            if skill.lower() in resume_skills_lower:
                matched_in_category.append(skill)
                matched_count += 1
        if matched_in_category:
            matched_skills_dict[category] = matched_in_category

    score = (matched_count / total_job_skills * 100) if total_job_skills > 0 else 0.0

    # Compute missing skills
    missing_skills_dict = {}
    for category, skills in job_skills_dict.items():
        missing_in_category = []
        for skill in skills:
            if skill.lower() not in resume_skills_lower:
                missing_in_category.append(skill)
        if missing_in_category:
            missing_skills_dict[category] = missing_in_category

    # Apply experience weighting if applicable
    if job_description:
        try:
            required_exp = extract_required_experience(job_description)
            if required_exp is not None:
                resume_exp = compute_total_resume_experience(resume_experience_dict)
                if resume_exp < required_exp:
                    experience_ratio = resume_exp / required_exp
                    score = score * experience_ratio
        except Exception:
            pass

    return score, matched_skills_dict, missing_skills_dict


# ==============================
# LLM-based Explanation
# ==============================

def generate_llm_explanation(
    match_score,
    matched_skills_dict,
    missing_skills_dict,
    resume_experience_dict,
):
    """Generate professional recruiter-style summary using Gemini LLM.

    If GEMINI_API_KEY is not set or Gemini call fails, returns an error message.

    Args:
        match_score: Computed match percentage.
        matched_skills_dict: Dict of matched skills by category.
        missing_skills_dict: Dict of missing skills by category.
        resume_experience_dict: Dict with "Experience" list.

    Returns:
        Professional one-paragraph summary (string).
    """
    matched_list = flatten_skill_dict(matched_skills_dict, limit=MAX_SKILLS_FOR_EXPLANATION)
    missing_list = flatten_skill_dict(missing_skills_dict, limit=MAX_SKILLS_FOR_EXPLANATION)

    roles = [
        exp.get("Role")
        for exp in resume_experience_dict.get("Experience", [])
        if exp.get("Role")
    ]
    roles_text = ", ".join(roles[:3]) if roles else "roles unavailable"
    total_years = compute_total_resume_experience(resume_experience_dict)

    matched_str = ", ".join(matched_list) if matched_list else "no notable skills"
    missing_str = (
        ", ".join(missing_list) if missing_list else "no critical missing skills"
    )

    prompt = (
        f"You are a professional tech recruiter. Given the following candidate-job "
        f"match data, write one natural paragraph (120-150 words) summarizing the "
        f"candidate's fit, strengths, gaps, and a short recommendation. "
        f"Do not use bullet points or JSON.\n\n"
        f"Match score: {match_score:.1f}%\n"
        f"Matched skills: {matched_str}\n"
        f"Missing skills: {missing_str}\n"
        f"Experience summary: {roles_text}; total experience {total_years:.1f} years.\n\n"
        f"Output: a single professional recruiter-style paragraph "
        f"(no bullets, no JSON)."
    )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "GEMINI_API_KEY not set; cannot call Gemini. "
            "Please set GEMINI_API_KEY in the environment to enable LLM explanations."
        )

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return f"Failed to initialize Gemini client: {e}"

    try:
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        # Extract text from response
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


# ==============================
# Main Execution
# ==============================

if __name__ == "__main__":
    # Load and parse resume
    resume_text = extract_text_from_pdf("resume.pdf")

    resume_skills_dict = extract_skills_from_resume(resume_text)
    resume_experience_dict = extract_experience_from_resume(resume_text)
    resume_projects_dict = extract_projects_from_resume(resume_text)

    print("Resume Skills:", resume_skills_dict)
    print("Resume Experience:", resume_experience_dict)
    print("Resume Projects:", resume_projects_dict)

    # Parse job description
    job_description = """
Looking for a backend developer with 3+ years of experience in Java, C++,
JavaScript, FastAPI, REST APIs, PostgreSQL, AWS, and cloud deployment experience.
    """

    job_skills_dict = extract_skills_from_job(job_description)
    print("Job Skills:", job_skills_dict)

    # Compute match
    match_score, matched_skills_dict, missing_skills_dict = compute_match(
        resume_skills_dict,
        resume_experience_dict,
        resume_projects_dict,
        job_skills_dict,
        job_description,
    )

    # Display diagnostics
    required_exp = extract_required_experience(job_description)
    resume_exp = compute_total_resume_experience(resume_experience_dict)

    print(f"\nResume Total Experience: {resume_exp:.2f} years")

    if required_exp is not None:
        print(f"Job Required Experience: {required_exp} years")
        if resume_exp >= required_exp:
            print("✓ Experience requirement met (no penalty applied)")
        else:
            penalty = (1 - (resume_exp / required_exp)) * 100
            shortfall = required_exp - resume_exp
            print(
                f"✗ Experience shortfall: {shortfall:.2f} years "
                f"(-{penalty:.1f}% penalty)"
            )
    else:
        print("No specific experience requirement found in job description")

    print(f"\nOverall Match Score: {match_score:.2f}%")
    print("\nMatched Skills:", matched_skills_dict)
    print("\nMissing Job Skills:", missing_skills_dict)

    # Generate LLM explanation
    try:
        explanation = generate_llm_explanation(
            match_score,
            matched_skills_dict,
            missing_skills_dict,
            resume_experience_dict,
        )
        print("\nLLM Explanation:\n", explanation)
    except Exception as e:
        print(f"Failed to generate LLM explanation: {e}")