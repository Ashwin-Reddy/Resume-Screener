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
        "mariadb", "sql server"
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
        "jupyter", "jupyter notebook"
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



def extract_skills_from_job(text):
    """Parse a job description and semantically map phrases to known skills.

    Splits on common delimiters then uses :func:`match_candidates_to_skills`
    for embedding-based matching.
    """
    parts = re.split(r"[,;\n]+", text)
    candidates = [p.strip() for p in parts if p.strip()]
    return match_candidates_to_skills(candidates)



def compute_skill_match(resume_skills_dict, job_skills_dict):
    """Compute skill match between resume and job requirements.
    
    Args:
        resume_skills_dict: Dictionary with categories as keys and skill lists as values
        job_skills_dict: Dictionary with categories as keys and skill lists as values
    
    Returns:
        Tuple of (match_score, matched_skills_dict) where matched_skills_dict shows
        which skills matched in each category.
    """
    matched_skills_dict = {}
    total_job_skills = sum(len(skills) for skills in job_skills_dict.values())
    
    if total_job_skills == 0:
        return 0.0, {}
    
    # Create sets of lowercase skill names for comparison
    resume_skills_lower = set()
    for skills in resume_skills_dict.values():
        resume_skills_lower.update(s.lower() for s in skills)
    
    matched_count = 0
    # Check which job skills are in resume
    for category, skills in job_skills_dict.items():
        matched_in_category = []
        for skill in skills:
            if skill.lower() in resume_skills_lower:
                matched_in_category.append(skill)
                matched_count += 1
        if matched_in_category:
            matched_skills_dict[category] = matched_in_category
    
    score = (matched_count / total_job_skills * 100) if total_job_skills > 0 else 0.0
    # identify missing job skills as well
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
resume_skills_dict = extract_skills_from_resume(resume_text)
print("Resume Skills:", resume_skills_dict)

job_description = """
Looking for a backend developer with Java, C++, JavaScript, FastAPI,
REST APIs, PostgreSQL, AWS, and cloud deployment experience.
"""
job_skills_dict = extract_skills_from_job(job_description)
print("Job Skills:", job_skills_dict)

match_score, matched_skills_dict, missing_skills_dict = compute_skill_match(resume_skills_dict, job_skills_dict)
print(f"Skill Match Score: {match_score:.2f}%")
print("Matched Skills:", matched_skills_dict)
print("Missing Job Skills:", missing_skills_dict)

