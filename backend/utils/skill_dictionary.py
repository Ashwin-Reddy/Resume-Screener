"""Skill dictionary, embedding setup, and utilities.

This module centralizes the master skill list and computes embeddings using a
sentence-transformer model. Loading happens at import time so that the model is
initialized once when the application starts.
"""
from typing import Dict, List, Tuple

from sentence_transformers import SentenceTransformer

from backend.config.settings import settings

# Skill categories keyed to lists of skill keywords.
SKILL_DICTIONARY: Dict[str, List[str]] = {
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

# Flatten dictionary to lists used for embedding lookup.
SKILL_LIST: List[str] = []
SKILL_CATEGORIES: List[str] = []
SKILL_TO_CATEGORY: Dict[str, str] = {}

for category, skills in SKILL_DICTIONARY.items():
    for skill in skills:
        skill_lower = skill.lower()
        SKILL_LIST.append(skill_lower)
        SKILL_CATEGORIES.append(category)
        SKILL_TO_CATEGORY[skill_lower] = category

# Load sentence transformer model once.
document_model: SentenceTransformer = SentenceTransformer(
    settings.sentence_model_name
)

# Precompute skill embeddings if list is non‑empty.
skill_embeddings = (
    document_model.encode(SKILL_LIST, convert_to_tensor=True)
    if SKILL_LIST
    else None
)
