import fitz  # PyMuPDF
import re

# semantic embeddings
import numpy as np
from sentence_transformers import SentenceTransformer, util

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
            current_duration = org_duration_match.group(2).strip()
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



def compute_skill_match(resume_skills_dict, job_skills_dict):
    """Backward-compatible helper that only considers the explicit skills dict.
    """
    # delegate to new function with empty extras
    return compute_match(resume_skills_dict, {}, {}, job_skills_dict)


def compute_match(resume_skills_dict, resume_experience_dict, resume_projects_dict, job_skills_dict):
    """Compute match between resume (skills/experience/projects) and job skills.

    This function aggregates all resume information into a single set of
    lowercase tokens.  Experience roles/organizations and project technologies
    are included so that job requirements can be satisfied by those fields as
    well.  The job description is expected to have already been parsed into a
    skills dictionary.

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

    return score, matched_skills_dict, missing_skills_dict



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
Looking for a backend developer with Java, C++, JavaScript, FastAPI,
REST APIs, PostgreSQL, AWS, and cloud deployment experience.

"""
job_skills_dict = extract_skills_from_job(job_description)
print("Job Skills:", job_skills_dict)

# calculate combined match using all resume information
match_score, matched_skills_dict, missing_skills_dict = compute_match(
    resume_skills_dict,
    resume_experience_dict,
    resume_projects_dict,
    job_skills_dict
)
print(f"Overall Match Score: {match_score:.2f}%")
print("Matched Skills:", matched_skills_dict)
print("Missing Job Skills:", missing_skills_dict)

