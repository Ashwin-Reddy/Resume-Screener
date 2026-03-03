import fitz  # PyMuPDF
import re
from datetime import datetime

# Gemini
from google import genai

# semantic embeddings
import numpy as np
from sentence_transformers import SentenceTransformer, util
import os

# load model once
document_model = SentenceTransformer('all-MiniLM-L6-v2')



# Comprehensive skill dictionary organized by categories
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

# Create a mapping from skill name (lowercase) to category for quick lookup
SKILL_TO_CATEGORY = {}
for category, skills in SKILL_DICTIONARY.items():
    for skill in skills:
        SKILL_TO_CATEGORY[skill.lower()] = category

# flatten the skill list and compute embeddings for all known skills
SKILL_LIST = []          # lowercase version used for embedding
SKILL_CATEGORIES = []
for category, skills in SKILL_DICTIONARY.items():
    for skill in skills:
        SKILL_LIST.append(skill.lower())
        SKILL_CATEGORIES.append(category)

# precompute embeddings array
if SKILL_LIST:
    skill_embeddings = document_model.encode(SKILL_LIST, convert_to_tensor=True)
else:
    skill_embeddings = None
# section extraction is now possible in several places

# threshold for semantic matching
SIMILARITY_THRESHOLD = 0.65

# helper for matching candidate phrases to known skills

def match_candidates_to_skills(candidates, threshold=SIMILARITY_THRESHOLD):
    """Return a category-organized dict of skills matching the input candidates.

    Each candidate string is compared against the flattened skill list using
    cosine similarity.  If the best score exceeds *threshold* the corresponding
    skill is recorded under its category.
    """
    result = {}
    if not candidates or skill_embeddings is None:
        return result

    # encode candidate phrases
    cand_embeddings = document_model.encode(candidates, convert_to_tensor=True)
    # compute cosine similarity matrix: candidates x known_skills
    scores = util.cos_sim(cand_embeddings, skill_embeddings)

    for i, cand in enumerate(candidates):
        # find best matching skill index
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



def extract_text_from_pdf(file_path):
    """Read all text from a PDF file using PyMuPDF."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def extract_skills_from_resume(text):
    """Extract candidate tokens from resume and semantically map them to skills.

    The function still locates a "Skills" section and splits the following lines
    on commas/semicolons, but instead of exact string lookups it delegates to
    :func:`match_candidates_to_skills` which uses embeddings.
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


def extract_section(text, headers):
    """Generic helper to capture lines from one of the given section headers.

    *headers* is an iterable of strings or regex patterns. Matching is
    case-insensitive. Once a header is found the function collects all
    subsequent non-blank lines until it encounters either a blank line or
    another common section header (skills, experience, projects, education).
    Returns the raw list of captured lines.
    """
    lines = text.splitlines()
    capture = False
    section_lines = []
    header_pattern = re.compile(r"(?:" + "|".join(headers) + r")", re.I)
    # common boundaries for stopping capture
    boundary_pattern = re.compile(r"\b(skills|experience|projects|education|certifications)\b", re.I)

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


def normalize_duration(duration_text: str) -> str:
    """Normalize various duration formats to a consistent years/months string.

    Rules:
    1. If the text already contains a phrase like "6 years" or "6 yrs",
       return the matched portion unchanged.
    2. If it is a date range ("Nov 2019 – Present" or "Jan 2020 - March 2023"),
       compute the difference from start to end (or current date for Present)
       and express it as "X years" or "X years Y months".
    3. On failure to parse, return the original *duration_text*.

    Supports full and abbreviated month names and both dash types.
    """
    text = duration_text.strip()
    # 1. direct years expression
    years_match = re.search(r"(\d+)\s*(?:years?|yrs?)", text, re.I)
    if years_match:
        return years_match.group(0)

    # helper to parse a month-year string
    def parse_month_year(s: str):
        s = s.strip().replace(',', '')
        for fmt in ("%B %Y", "%b %Y", "%Y"):  # allow bare year as fallback
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    # split on dash or en-dash
    parts = re.split(r"\s*[–-]\s*", text)
    if len(parts) == 2:
        start_str, end_str = parts
        start_dt = parse_month_year(start_str)
        end_str = end_str.strip()
        if re.search(r"present", end_str, re.I):
            end_dt = datetime.today()
        else:
            end_dt = parse_month_year(end_str)
        if start_dt and end_dt:
            # compute total months difference
            total_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
            if total_months < 0:
                return text  # invalid range
            years = total_months // 12
            months = total_months % 12
            if years > 0 and months > 0:
                return f"{years} years {months} months"
            elif years > 0:
                return f"{years} years"
            else:
                return f"{months} months"
    # couldn't parse, return original
    return text


def extract_experience_from_resume(text):
    """
    Extract structured experience entries with Role, Organization, and Duration.
    
    Expected format:
    Organization (Duration)
    Role – Role Name:
    [description lines]
    Role – Another Role:
    [description lines]
    
    Returns a list of dicts with keys: Role, Organization, Duration
    """
    lines = extract_section(text, [r"\bexperience\b", r"\bwork experience\b"])
    experiences = []
    
    current_org = ""
    current_duration = ""
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and bullet points
        if not line or line == "·":
            i += 1
            continue
        
        # Stop if we hit another section header
        if re.search(r"\b(languages|skills|projects|education|certifications)\b", line, re.I):
            break
        
        # Try to match: Organization (Duration)
        org_duration_match = re.match(
            r"^(.*?)\s*\(\s*(.*?)\s*\)$", 
            line
        )
        
        if org_duration_match:
            # Found organization and duration
            current_org = org_duration_match.group(1).strip()
            raw_duration = org_duration_match.group(2).strip()
            current_duration = normalize_duration(raw_duration)
            i += 1
            continue
        
        # Try to match: Role – Role Name: (case insensitive)
        role_match = re.match(
            r"^Role\s*[–-]\s*(.*?)\s*:?\s*$",
            line,
            re.I
        )
        
        if role_match and current_org:
            role = role_match.group(1).strip()
            experiences.append({
                "Role": role,
                "Organization": current_org,
                "Duration": current_duration
            })
        
        i += 1
    
    return {"Experience": experiences}


def extract_projects_from_resume(text):
    """
    Extract project names along with technologies used.
    Projects are listed under a "Projects" heading; each project title
    typically ends with a colon, and the description may span subsequent
    lines until the next bullet/title.
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
            # simple keyword search over known skills
            for skill in SKILL_LIST:
                # match whole word to avoid substrings
                if re.search(r"\b" + re.escape(skill) + r"\b", desc_text, re.I):
                    tech_set.add(skill)
            # fallback to embedding if nothing found
            if not tech_set:
                tech_dict = match_candidates_to_skills([desc_text])
                for skills in tech_dict.values():
                    tech_set.update(skills)
        # canonicalize sql -> sql server
        if "sql" in tech_set:
            tech_set.discard("sql")
            tech_set.add("sql server")
        projects.append({
            "Project Title": current_title,
            "Technologies": list(tech_set)
        })
        current_title = None
        current_desc = []

    for line in lines:
        raw = line.lstrip("· ").strip()
        if not raw:
            continue

        # determine if this line is a project title ending with ':'
        if raw.endswith(":"):
            # start new project, flush previous
            flush_project()
            title_part = raw[:-1].strip()
            # if dash exists in title, take part after dash
            if "–" in title_part:
                title_part = title_part.split("–")[-1].strip()
            current_title = title_part
        else:
            # accumulate description lines
            current_desc.append(raw)
    # flush last project
    flush_project()

    return {"Projects": projects}



def extract_skills_from_job(text):
    """Parse a job description and semantically map phrases to known skills.

    Splits on common delimiters then uses :func:`match_candidates_to_skills`
    for embedding-based matching.
    """
    parts = re.split(r"[,;\n]+", text)
    candidates = [p.strip() for p in parts if p.strip()]

# later on we might add similar helpers for jobs (experience requirements etc.)
    return match_candidates_to_skills(candidates)



def extract_required_experience(job_text: str):
    """Extract the minimum years requirement from job description.

    Supports various formats:
    - "3 years experience"
    - "3+ years"
    - "3-5 years"
    - "at least 3 years"
    - "minimum three years"

    Returns the minimum required years as int, or None if not found.
    """
    # word to number mapping
    word_to_num = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15,
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50
    }

    text = job_text.lower()

    # Pattern 1: digit-based (3 years, 3+ years, 3-5 years, etc.)
    # Match patterns like: "3 years", "3+ years", "3-5 years", "minimum 3 years"
    pattern1 = r"(?:minimum|at least|required|minimum of)?\s*(\d+)\s*(?:\+|-\d+)?\s*(?:years?|yrs?)"
    match = re.search(pattern1, text, re.I)
    if match:
        return int(match.group(1))

    # Pattern 2: word-based (three years, five years, etc.)
    word_pattern = "|".join(word_to_num.keys())
    pattern2 = r"(?:minimum|at least|required|minimum of)?\s*(" + word_pattern + r")\s*(?:years?|yrs?)"
    match = re.search(pattern2, text, re.I)
    if match:
        word = match.group(1).lower()
        return word_to_num.get(word, None)

    return None


def compute_total_resume_experience(resume_experience_dict: dict) -> float:
    """Compute total experience from all resume entries in years (as float).

    Parses normalized duration strings like "4 years" or "2 years 3 months"
    and sums them up.

    Returns total experience as float (e.g., 4.25 for 4 years 3 months).
    """
    total_months = 0

    for exp in resume_experience_dict.get("Experience", []):
        duration_str = exp.get("Duration", "").lower()
        if not duration_str:
            continue

        # Parse "X years Y months" or "X years" or "Y months"
        years_match = re.search(r"(\d+)\s*years?", duration_str)
        months_match = re.search(r"(\d+)\s*months?", duration_str)

        years = int(years_match.group(1)) if years_match else 0
        months = int(months_match.group(1)) if months_match else 0

        total_months += years * 12 + months

    # Convert to years as float
    total_years = total_months / 12.0
    return total_years


def compute_match(resume_skills_dict, resume_experience_dict, resume_projects_dict, job_skills_dict, job_description=""):
    """Compute match between resume (skills/experience/projects) and job description.

    This function aggregates all resume information into a single set of
    lowercase tokens. Experience roles/organizations and project technologies
    are included so that job requirements can be satisfied by those fields as
    well. The job description is expected to have already been parsed into a
    skills dictionary.

    If the job description contains an experience requirement:
    - If resume experience >= required experience: no penalty
    - If resume experience < required experience: score is reduced proportionally

    Args:
        resume_skills_dict: Dict with skill categories as keys
        resume_experience_dict: Dict with "Experience" list
        resume_projects_dict: Dict with "Projects" list
        job_skills_dict: Dict with required skill categories as keys
        job_description: Raw job description text (optional)

    Returns a tuple ``(score, matched_skills_dict, missing_skills_dict)``.
    """
    matched_skills_dict = {}
    total_job_skills = sum(len(skills) for skills in job_skills_dict.values())

    if total_job_skills == 0:
        return 0.0, {}, {}

    # aggregate resume tokens
    resume_skills_lower = set()
    for skills in resume_skills_dict.values():
        resume_skills_lower.update(s.lower() for s in skills)

    # include experience roles/orgs
    for exp in resume_experience_dict.get("Experience", []):
        role = exp.get("Role", "")
        org = exp.get("Organization", "")
        resume_skills_lower.update([role.lower(), org.lower()])

    # include project technologies
    for proj in resume_projects_dict.get("Projects", []):
        for tech in proj.get("Technologies", []):
            resume_skills_lower.add(tech.lower())

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
    missing_skills_dict = {}
    for category, skills in job_skills_dict.items():
        missing_in_category = []
        for skill in skills:
            if skill.lower() not in resume_skills_lower:
                missing_in_category.append(skill)
        if missing_in_category:
            missing_skills_dict[category] = missing_in_category

    # Apply experience weighting if job description contains experience requirement
    if job_description:
        try:
            required_exp = extract_required_experience(job_description)
            if required_exp is not None:
                resume_exp = compute_total_resume_experience(resume_experience_dict)
                if resume_exp < required_exp:
                    # Apply penalty proportionally
                    experience_ratio = resume_exp / required_exp
                    score = score * experience_ratio
        except Exception:
            # Safely ignore any errors during experience extraction
            pass

    return score, matched_skills_dict, missing_skills_dict



# --- LLM explanation helper --------------------------------------------------
def generate_llm_explanation(
    match_score,
    matched_skills_dict,
    missing_skills_dict,
    resume_experience_dict,
):
    """Generate a professional recruiter-style paragraph summarizing fit.

    Uses the `google.generativeai` package with model `gemini-1.5-flash` when an
    API key is available via the `GEMINI_API_KEY` environment variable. If the
    key or package is not available the function returns a concise local
    fallback summary. The returned value is the plain explanation text.
    """

    def _flatten_skill_dict(d, limit=6):
        items = []
        for cat, skills in (d or {}).items():
            for s in skills:
                if s and s not in items:
                    items.append(s)
                if len(items) >= limit:
                    break
            if len(items) >= limit:
                break
        return items

    matched_list = _flatten_skill_dict(matched_skills_dict, limit=6)
    missing_list = _flatten_skill_dict(missing_skills_dict, limit=6)

    # Experience summary: extract roles and compute total years
    roles = [exp.get("Role") for exp in resume_experience_dict.get("Experience", []) if exp.get("Role")]
    roles_text = ", ".join(roles[:3]) if roles else ""
    total_years = compute_total_resume_experience(resume_experience_dict)

    matched_str = ", ".join(matched_list) if matched_list else "no notable skills"
    missing_str = ", ".join(missing_list) if missing_list else "no critical missing skills"

    # concise prompt for the model
    prompt = (
        f"You are a professional tech recruiter. Given the following candidate-job match data,"
        f" write one natural paragraph (120-150 words) summarizing the candidate's fit, strengths, gaps," 
        f" and a short recommendation. Do not use bullet points or JSON.\n\n"
        f"Match score: {match_score:.1f}%\n"
        f"Matched skills: {matched_str}\n"
        f"Missing skills: {missing_str}\n"
        f"Experience summary: {roles_text or 'roles unavailable'}; total experience {total_years:.1f} years.\n\n"
        f"Output: a single professional recruiter-style paragraph (no bullets, no JSON)."
    )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "GEMINI_API_KEY not set; cannot call Gemini. Please set GEMINI_API_KEY in the environment to enable LLM explanations."

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return f"Failed to initialize Gemini client: {e}"

    try:
        resp = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )

        # Robustly extract text from a few possible response shapes
        text = None
        # Pattern 1: resp.outputs or resp.output (list of blocks)
        out = getattr(resp, "outputs", None) or getattr(resp, "output", None)
        if out:
            try:
                # outputs may be list-like of dicts
                first = out[0]
                if isinstance(first, dict):
                    # content may be nested
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

        # Pattern 2: resp.text or resp.output_text
        if not text:
            text = getattr(resp, "text", None) or getattr(resp, "output_text", None)

        # Final fallback: stringify the response
        if not text:
            text = str(resp)

        return text.strip()
    except Exception as e:
        return f"Gemini API call failed: {e}"


# --- main script -------------------------------------------------------------

resume_text = extract_text_from_pdf("resume.pdf")

# extract each section separately
resume_skills_dict = extract_skills_from_resume(resume_text)
resume_experience_dict = extract_experience_from_resume(resume_text)
resume_projects_dict = extract_projects_from_resume(resume_text)

print("Resume Skills:", resume_skills_dict)
print("Resume Experience:", resume_experience_dict)
print("Resume Projects:", resume_projects_dict)

job_description = """
Looking for a backend developer with 3+ years of experience in Java, C++, JavaScript, FastAPI,
REST APIs, PostgreSQL, AWS, and cloud deployment experience.

"""
job_skills_dict = extract_skills_from_job(job_description)
print("Job Skills:", job_skills_dict)

# calculate combined match using all resume information
match_score, matched_skills_dict, missing_skills_dict = compute_match(
    resume_skills_dict,
    resume_experience_dict,
    resume_projects_dict,
    job_skills_dict,
    job_description  # Pass job description for experience-based weighting
)

# Additional diagnostics
required_exp = extract_required_experience(job_description)
resume_exp = compute_total_resume_experience(resume_experience_dict)
print(f"Resume Total Experience: {resume_exp:.2f} years")
if required_exp is not None:
    print(f"Job Required Experience: {required_exp} years")
    if resume_exp >= required_exp:
        print("✓ Experience requirement met (no penalty applied)")
    else:
        penalty = (1 - (resume_exp / required_exp)) * 100
        print(f"✗ Experience shortfall: {required_exp - resume_exp:.2f} years (-{penalty:.1f}% penalty)")
else:
    print("No specific experience requirement found in job description")

print(f"\n Overall Match Score: {match_score:.2f}%")
print("\n Matched Skills:", matched_skills_dict)
print("\n Missing Job Skills:", missing_skills_dict)

# Generate and print a human-readable explanation using the LLM helper
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