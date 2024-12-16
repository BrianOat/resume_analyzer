from fastapi.testclient import TestClient
from backend.database.models import User
from backend.main import app, get_db, extract_text_from_pdf, temp_storage, calculate_fit_score, generate_feedback, tokenize, STOP_WORDS, extract_skills
from unittest.mock import MagicMock
import pytest
import os
from io import BytesIO
import jwt
import bcrypt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader

"""
Setup and helper
"""
client = TestClient(app)

mock_session = MagicMock()
def override_get_db():
    try:
        yield mock_session
    finally:
        pass
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def mock_db_session():
    return mock_session

@pytest.fixture
def clear_temp_storage():
    temp_storage.clear()
    yield
    temp_storage.clear()

register_payload_1 = {
    "email": "test@example.com",
    "password": "securePassword123",
    "username": "testuser"
}

analysis_payload = {
        "resume_text": "I am an experienced software engineer with Python expertise.", 
        "job_description": "Looking for a Python developer with API design experience."
}
def create_pdf_in_memory(text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, text)
    c.save()
    buffer.seek(0)
    return buffer

"""
Tests
"""
def test_register_success(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    response = client.post("/api/register", json=register_payload_1)
    assert response.status_code == 201
    assert response.json() == {"message": "User registered"}

def test_register_duplicate(mock_db_session):
    existing_user = User(email="test@example.com", username="testuser", hashed_password="hashedpassword123")
    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_user
    client.post("/api/register", json=register_payload_1)
    response = client.post("/api/register", json=register_payload_1)
    assert response.status_code == 400
    assert response.json() == {"error": "Username or email already registered"}

def test_register_missing_field():
    payload = {
        "email": "incomplete@example.com",
        "password": "pass123"
        # Missing "username" field
    }
    response = client.post("/api/register", json=payload)
    assert response.status_code == 422  # Unprocessable Entity for validation error

def test_login_success(mock_db_session):
    mock_password = "hashedpassword123"
    mock_hashed_password = bcrypt.hashpw(mock_password.encode('utf-8'), bcrypt.gensalt())
    existing_user = User(email="test@example.com", username="testuser", hashed_password=mock_hashed_password)
    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_user
    mock_db_session.users[existing_user.email].hashed_password = existing_user.hashed_password
    login_payload = {
            "email": "test@example.com",
            "password": "hashedpassword123"
    }
    response = client.post("/api/login", json=login_payload)
    secret = os.getenv('secret')
    algorithm = os.getenv('algorithm')
    assert response.status_code == 200
    data = response.json()
    generated_token = data["token"]
    decoded_token = jwt.decode(generated_token, secret, algorithms=[algorithm])
    assert decoded_token["email"] == login_payload["email"]

def test_login_fail(mock_db_session):
    mock_password = "hashedpassword123"
    mock_hashed_password = bcrypt.hashpw(mock_password.encode('utf-8'), bcrypt.gensalt())
    existing_user = User(email="test@example.com", username="testuser", hashed_password=mock_hashed_password)
    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_user
    mock_db_session.users[existing_user.email].hashed_password = existing_user.hashed_password
    login_payload = {
            "email": "test@example.com",
            "password": "superWrongPassword123",
    }
    response = client.post("/api/login", json=login_payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "Email or password is not recognized"

def test_login_nonexistent_user(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    payload = {
        "email": "nonexistent@example.com", 
        "password": register_payload_1["password"]
    }
    response = client.post("/api/login", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "Email or password is not recognized"

def test_successful_resume_upload():
    file_content = create_pdf_in_memory("Hello World")
    response = client.post(
        "/api/resume-upload",
        files={"file": ("test.pdf", file_content, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Resume uploaded successfully."
    assert response.json()["status"] == "success"

def test_fail_resume_upload_invalid_file_type():
    file_content = BytesIO(b"This is not a valid PDF file.")
    response = client.post(
        "/api/resume-upload",
        files={"file": ("test.txt", file_content, "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Invalid file type. Only PDF files are allowed."
    assert response.json()["status"] == "error"

def test_fail_resume_upload_oversized_file():
    oversized_file = BytesIO(b"A" * (2 * 1024 * 1024 + 1))
    response = client.post(
        "/api/resume-upload",
        files={"file": ("large.pdf", oversized_file, "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "File size exceeds the 2MB limit."
    assert response.json()["status"] == "error"

def test_fail_resume_upload_exceeds_character_limit():
    long_text = "A" * 10001
    long_text_pdf = create_pdf_in_memory(long_text)
    response = client.post(
        "/api/resume-upload",
        files={"file": ("long.pdf", long_text_pdf, "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "File contains more than 10,000 characters."
    assert response.json()["status"] == "error"

def test_sucessful_job_description_upload():
    job_description_payload = {
        "job_description": "This is a test job description"
    }
    response = client.post(
        "/api/job-description",
        json=job_description_payload
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Job description submitted successfully."
    assert response.json()["status"] == "success"

def test_fail_job_description_upload_invalid_length():
    job_description_payload = {
        "job_description": "A"*10001
    }
    response = client.post(
        "/api/job-description",
        json=job_description_payload
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Job description exceeds character limit."
    assert response.json()["status"] == "error"

def test_nlp_analyze_success():

    response = client.post("api/analyze", json=analysis_payload)
    assert response.status_code == 200
    assert "fit_score" in response.json()
    assert "feedback" in response.json()
    assert isinstance(response.json()["feedback"], list)

def test_nlp_analyze_invalid_type():
    payload = {
        "resume_text": ['This is an invalid data type.'],
        "job_description": 490
    }
    response = client.post("api/analyze", json=payload)
    assert response.status_code == 400
    assert response.json()["error"] == "Validation error with input. Please try again. Input must be non-empty string."
    assert response.json()["status"]

def test_nlp_analyze_exceeds_length():
    payload = {
        "resume_text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "job_description": "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    }
    response = client.post("api/analyze", json=payload)
    assert response.status_code == 400
    assert response.json()["error"] == "Validation error with input. Please try again. Input exceeds 10,000 characters."
    assert response.json()["status"]

def test_nlp_analyze_empty():
    payload = {
        "resume_text": "",
        "job_description":""
    }
    response = client.post("api/analyze", json=payload)
    assert response.status_code == 400
    assert response.json()["error"] == "Validation error with input. Please try again. Input must be non-empty string."
    assert response.json()["status"]


def test_extract_text_from_pdf_success():
    sample_pdf_valid = create_pdf_in_memory("Hello World")
    text = extract_text_from_pdf(sample_pdf_valid)
    assert text.strip() == "Hello World", f"Unexpected text extracted: {text}"

def test_extract_text_from_pdf_empty():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.save()
    buffer.seek(0)
    sample_pdf_empty = buffer
    text = extract_text_from_pdf(sample_pdf_empty)
    assert text == "", f"Unexpected text extracted: {text}"

def test_extract_text_from_pdf_whitespace_cleanup():
    sample_pdf_with_whitespace = create_pdf_in_memory("Hello   World")
    text = extract_text_from_pdf(sample_pdf_with_whitespace)
    assert text.strip() == "Hello World", f"Unexpected text extracted: {text}"

def test_extract_text_from_pdf_invalid_pdf():
    invalid_pdf = BytesIO(b"This is not valid PDF content")
    with pytest.raises(ValueError) as excinfo:
        extract_text_from_pdf(invalid_pdf)
    assert "Failed to extract text from PDF" in str(excinfo.value)

def test_data_insertion_and_retrieval(clear_temp_storage):
    file_content = create_pdf_in_memory("Resume text here")
    response = client.post(
        "/api/resume-upload",
        files={"file": ("resume.pdf", file_content, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Resume uploaded successfully."
    session_id = next(iter(temp_storage))
    assert session_id in temp_storage 
    assert "resume_text" in temp_storage[session_id]
    assert temp_storage[session_id]["resume_text"] == "Resume text here"
    job_description_payload = {"job_description": "Job description here"}
    job_response = client.post("/api/job-description", json=job_description_payload)
    assert job_response.status_code == 200
    assert job_response.json()["message"] == "Job description submitted successfully."
    assert "job_description" in temp_storage[session_id]
    assert temp_storage[session_id]["job_description"] == "Job description here"

# TOKENIZATION TESTS 

def test_tokenize_basic():
    text = "Hello World!"
    tokens = tokenize(text)
    assert tokens == ["hello", "world"], "Should return lowercase tokens without punctuation."

def test_tokenize_mixed_case():
    text = "PyThOn aNd AWS"
    tokens = tokenize(text)
    assert tokens == ["python", "aws"], "Should normalize all tokens to lowercase and remove stop words."

def test_tokenize_punctuation():
    text = "Python, AWS, REST APIs!"
    tokens = tokenize(text)
    assert "python" in tokens
    assert "aws" in tokens
    assert "rest_apis" in tokens
    assert len(tokens) == 3, "Should strip punctuation and combine multi-word phrases into single tokens."

def test_tokenize_empty_string():
    text = ""
    tokens = tokenize(text)
    assert tokens == [], "Empty input should return an empty list."

# EXTRACT TESTS

def test_extract_skills_with_sections():
    job_description = """
    Required Skills:
    - Python
    - AWS
    - REST APIs

    Preferred Skills:
    - Docker
    - Kubernetes
    - CI/CD Pipelines
    """
    expected_required = {"python", "aws", "rest_apis"}
    expected_preferred = {"docker", "kubernetes", "cicd_pipelines"}
    extracted_required, extracted_preferred = extract_skills(job_description)
    assert extracted_required == expected_required
    assert extracted_preferred == expected_preferred

def test_extract_skills_with_comma_separated():
    job_description = """
    Required Skills:
    Python, AWS, REST APIs

    Preferred Skills:
    Docker, Kubernetes, CI/CD Pipelines
    """
    expected_required = {"python", "aws", "rest_apis"}
    expected_preferred = {"docker", "kubernetes", "cicd_pipelines"}
    extracted_required, extracted_preferred = extract_skills(job_description)
    assert extracted_required == expected_required
    assert extracted_preferred == expected_preferred

def test_extract_skills_mixed_bullets_and_commas():
    job_description = """
    Required Skills:
    - Python
    - AWS, REST APIs

    Preferred Skills:
    Docker, Kubernetes
    - CI/CD Pipelines
    """
    expected_required = {"python", "aws", "rest_apis"}
    expected_preferred = {"docker", "kubernetes", "cicd_pipelines"}
    extracted_required, extracted_preferred = extract_skills(job_description)
    assert extracted_required == expected_required
    assert extracted_preferred == expected_preferred

def test_extract_skills_missing_sections():
    job_description = """
    Responsibilities:
    - Develop software solutions.
    - Collaborate with teams.

    Qualifications:
    - Bachelor's degree in Computer Science.
    """
    expected_required = set()
    expected_preferred = set()
    extracted_required, extracted_preferred = extract_skills(job_description)
    assert extracted_required == expected_required
    assert extracted_preferred == expected_preferred

def test_extract_skills_empty_job_description():
    job_description = ""
    expected_required = set()
    expected_preferred = set()
    extracted_required, extracted_preferred = extract_skills(job_description)
    assert extracted_required == expected_required
    assert extracted_preferred == expected_preferred

def test_extract_skills_non_string_input():
    job_description = None
    expected_required = set()
    expected_preferred = set()
    extracted_required, extracted_preferred = extract_skills(job_description)
    assert extracted_required == expected_required
    assert extracted_preferred == expected_preferred

def test_extract_skills_case_insensitivity():
    job_description = """
    REQUIRED SKILLS:
    - Python
    - AWS

    preferred skills:
    - Docker
    - Kubernetes
    """
    expected_required = {"python", "aws"}
    expected_preferred = {"docker", "kubernetes"}
    extracted_required, extracted_preferred = extract_skills(job_description)
    assert extracted_required == expected_required
    assert extracted_preferred == expected_preferred

def test_extract_skills_with_multiple_spaces():
    job_description = """
    Required Skills:
    -  Python
    - AWS
        - REST APIs

    Preferred Skills:
    - Docker
      - Kubernetes
    - CI/CD Pipelines
    """
    expected_required = {"python", "aws", "rest_apis"}
    expected_preferred = {"docker", "kubernetes", "cicd_pipelines"}
    extracted_required, extracted_preferred = extract_skills(job_description)
    assert extracted_required == expected_required
    assert extracted_preferred == expected_preferred

# FIT SCORE CALCULATION TESTS

def test_calculate_fit_score_full_match():
    resume_text = (
        "John Doe\n"
        "Experienced Software Engineer with 5 years of experience in Python, AWS, and REST APIs.\n"
        "Skills: Python, AWS, REST APIs, Java, Docker\n"
        "Work Experience:\n"
        "- Developed RESTful APIs in Python.\n"
        "- Managed infrastructure on AWS.\n"
    )
    job_description = (
        "Looking for a software engineer with strong experience in Python, AWS, and REST APIs.\n"
        "Candidates should be proficient in modern cloud technologies and web services.\n\n"
        "Required Skills:\n"
        "- Python\n"
        "- AWS\n"
        "- REST APIs\n\n"
        "Preferred Skills:\n"
        "- Docker"
    )
    score = calculate_fit_score(resume_text, job_description)
    assert 95 <= score <= 100, "All key skills (Python, AWS, REST APIs) should fully match, resulting in near 100%."

def test_calculate_fit_score_partial_match():
    resume_text = (
        "Jane Smith\n"
        "Software Developer with experience in Python, Java, and SQL.\n"
        "Familiar with backend development and some AWS knowledge.\n"
        "Projects have involved data pipelines, REST APIs, and microservices.\n"
    )
    job_description = (
        "We are looking for a developer skilled in Python, AWS, and REST APIs.\n"
        "Knowledge of Docker and Kubernetes is a plus.\n\n"
        "Required Skills:\n"
        "- Python\n"
        "- AWS\n"
        "- REST APIs\n\n"
        "Preferred Skills:\n"
        "- Docker\n"
        "- Kubernetes"
    )
    score = calculate_fit_score(resume_text, job_description)
    assert 0 < score < 100, "Should have a partial match but not full (since some skills are missing)."

def test_calculate_fit_score_no_match():
    resume_text = (
        "Mark Johnson\n"
        "Mobile Developer experienced in Swift and iOS development.\n"
        "Expertise in building native iPhone apps and UI/UX design."
    )
    job_description = (
        "Looking for a software engineer with experience in Python, AWS, and REST APIs.\n"
        "Must be knowledgeable in cloud environments and backend services."
        "Required Skills:\n"
        "- Python\n"
        "- REST APIs\n"
        "- AWS\n\n"
        "Preferred Skills:\n"
        "- GCP\n"
        "- AWS\n"
        "- Azure"
    )
    score = calculate_fit_score(resume_text, job_description)
    assert score == 0, "No shared keywords between resume and job description should yield 0."

def test_calculate_fit_score_empty_input():
    assert calculate_fit_score("", "Some job description") == 0, "Empty resume should yield 0."
    assert calculate_fit_score("Some resume text", "") == 0, "Empty job description should yield 0."
    assert calculate_fit_score("", "") == 0, "Both resume and job description empty should yield 0."

def test_calculate_fit_score_with_extra_skills():
    resume_text = (
        "Samuel Lee\n"
        "Data Analyst with expertise in Python, R, SQL, Tableau, and Excel.\n"
        "Experience in data visualization and statistical analysis."
    )
    job_description = (
        "Required Skills:\n"
        "- Python\n"
        "- SQL\n\n"
        "Preferred Skills:\n"
        "- R\n"
        "- Tableau\n"
        "- Power BI"
    )
    score = calculate_fit_score(resume_text, job_description)
    # Required: Python, SQL => 2/2 matched
    # Preferred: R, Tableau, Power BI => 2/3 matched
    expected_score = int((2 / 2) * 70 + (2 / 3) * 30)  # 70 + 20 = 90
    assert score == expected_score, f"Expected {expected_score}, got {score}"

def test_calculate_fit_score_bioinformatics():
    resume_text = (
        "John Doe\n"
        "Bioinformatics graduate with experience in analyzing NGS data, writing scripts, and performing statistical analyses.\n"
        "Skills: Python, R, NGS_pipelines, data_visualization, machine_learning, QC Measures, Collaboration, Script\n"
        "Experience:\n"
        "- Assisted in analyzing NGS data using established pipelines.\n"
        "- Performed QC measures for sequencing data.\n"
        "- Collaborated with researchers on sequencing data interpretation.\n"
    )
    job_description = (
        "As a Bioinformatics Assistant II, you will be trained in the analysis and interpretation of next-generation sequencing (NGS) data, "
        "originating from mouse experiments of cancer metastasis as well as patients, under the guidance of postdoctoral scientists and bioinformaticians.\n"
        "Responsibilities:\n"
        "- Learn and assist in analyzing sequencing data using established pipelines\n"
        "- Learn and perform appropriate QC measures\n"
        "- Learn and develop/benchmark new tools for sequencing data analysis\n"
        "- Assist and collaborate with internal and external researchers in interpretation of sequencing data\n"
        "- Other responsibilities, as assigned\n\n"
        "Required Skills:\n"
        "- NGS Pipelines\n"
        "- Sequencing Data\n"
        "- QC Measures\n"
        "- Collaboration\n"
        "- Code\n"
        "- Script\n\n"
        "Preferred Skills:\n"
        "- Statistics\n"
        "- Machine Learning\n"
    )

    # Calculate the score
    score = calculate_fit_score(resume_text, job_description)

    assert score >=50, f"Expected a good match, got {score}"


# FEEDBACK GENERATION TESTS

def test_generate_feedback_missing_skills():
    resume_text = (
        "Alice Brown\n"
        "Software Engineer with experience in Python and Java.\n"
        "Worked on backend APIs and deployed services to AWS once.\n"
    )
    job_description = (
        "We need a candidate with strong Python, AWS, and REST APIs skills.\n"
        "Should also have some exposure to Docker and CI/CD pipelines.\n\n"
        "Required Skills:\n"
        "- Python\n"
        "- AWS\n"
        "- REST APIs\n\n"
        "Preferred Skills:\n"
        "- Docker\n"
        "- CI/CD pipelines"
    )
    feedback = generate_feedback(resume_text, job_description)
    assert "rest_apis" in feedback["missing_keywords"], "REST APIs should be identified as missing."
    assert "docker" in feedback["missing_keywords"], "Docker should be identified as missing."
    assert "cicd_pipelines" in feedback["missing_keywords"], "CI/CD pipelines should be identified as missing."
    assert len(feedback["suggestions"]) >= 3, "At least three suggestions should be provided for the missing keywords."

def test_generate_feedback_no_missing_skills():
    resume_text = (
        "Chris Green\n"
        "Full-stack Engineer experienced in Python, AWS, and REST APIs.\n"
        "Familiar with Docker, Kubernetes, and CI/CD pipelines.\n"
    )
    job_description = (
        "Looking for a software engineer experienced in Python, AWS, and REST APIs.\n"
        "Familiarity with Docker and CI/CD pipelines is a plus."
    )
    feedback = generate_feedback(resume_text, job_description)
    assert len(feedback["missing_keywords"]) == 0, "No missing keywords should be found."
    assert len(feedback["suggestions"]) == 0, "No suggestions should be provided if nothing is missing."

def test_generate_feedback_all_skills_present():
    resume_text = (
        "Alex Johnson\n"
        "Full-stack Developer with expertise in JavaScript, React, Node.js, TypeScript, and GraphQL.\n"
        "Experience in building scalable web applications."
    )
    job_description = (
        "Looking for a developer proficient in JavaScript, React, and Node.js.\n"
        "Knowledge of TypeScript and GraphQL is desirable."
    )
    feedback = generate_feedback(resume_text, job_description)
    assert len(feedback["missing_keywords"]) == 0, "No missing keywords should be found."
    assert len(feedback["suggestions"]) == 0, "No suggestions should be provided if nothing is missing."

def test_generate_feedback_all_skills_missing():
    resume_text = (
        "Emily Davis\n"
        "Marketing Specialist with experience in SEO, content creation, and social media management."
    )
    job_description = (
        "Seeking a software engineer with skills in Python, AWS, and REST APIs.\n"
        "Familiarity with Docker and Kubernetes is a plus.\n\n"
        "Required Skills:\n"
        "- Python\n"
        "- AWS\n"
        "- REST APIs\n\n"
        "Preferred Skills:\n"
        "- Docker\n"
        "- Kubernetes"
    )
    feedback = generate_feedback(resume_text, job_description)
    expected_missing = {"python", "aws", "rest_apis", "docker", "kubernetes"}
    assert set(feedback["missing_keywords"]) == expected_missing, f"Expected missing_keywords {expected_missing}, got {feedback['missing_keywords']}"
    assert len(feedback["suggestions"]) == len(expected_missing), "Suggestions should be provided for all missing keywords."

def test_generate_feedback_with_partial_matches():
    resume_text = (
        "Olivia Martinez\n"
        "Data Scientist with experience in Python and R.\n"
        "Worked on data visualization and machine learning projects.\n"
    )
    job_description = (
        "Looking for a data scientist skilled in Python, R, SQL, and machine learning.\n"
        "Experience with big data technologies and data warehousing is a plus.\n\n"
        "Required Skills:\n"
        "- Python\n"
        "- R\n"
        "- SQL\n"
        "- Machine Learning\n\n"
        "Preferred Skills:\n"
        "- Big Data Technologies\n"
        "- Data Warehousing"
    )
    feedback = generate_feedback(resume_text, job_description)
    expected_missing = {"sql", "big_data_technologies", "data_warehousing"}
    assert set(feedback["missing_keywords"]) == expected_missing, f"Expected missing_keywords {expected_missing}, got {feedback['missing_keywords']}"
    assert len(feedback["suggestions"]) == len(expected_missing), "Suggestions should be provided for all missing keywords."

def test_generate_feedback_with_synonyms_and_variations():
    resume_text = (
        "Daniel Wilson\n"
        "DevOps Engineer with expertise in CI/CD, Kubernetes, and AWS.\n"
        "Experience in infrastructure as code and automated deployments.\n"
    )
    job_description = (
        "Seeking a DevOps Engineer proficient in Continuous Integration and Continuous Deployment (CI/CD), AWS, and Kubernetes.\n"
        "Familiarity with Terraform and automated deployment processes is desirable.\n\n"
        "Required Skills:\n"
        "- Continuous Integration\n"
        "- Continuous Deployment\n"
        "- AWS\n"
        "- Kubernetes\n\n"
        "Preferred Skills:\n"
        "- Terraform\n"
        "- Automated Deployment Processes"
    )
    feedback = generate_feedback(resume_text, job_description)
    expected_missing = {"terraform", 'continuous_deployment', 'continuous_integration', 'automated_deployment_processes'}
    assert set(feedback["missing_keywords"]) == expected_missing, f"Expected missing_keywords {expected_missing}, got {feedback['missing_keywords']}"
    assert len(feedback["suggestions"]) == len(expected_missing), "Suggestions should be provided for all missing keywords."


def test_generate_feedback_no_job_skills():
    resume_text = (
        "Michael Scott\n"
        "Regional Manager with extensive experience in sales and customer relations."
    )
    job_description = ""
    feedback = generate_feedback(resume_text, job_description)
    assert feedback["missing_keywords"] == [], "Empty job description should result in no missing keywords."
    assert feedback["suggestions"] == [], "Empty job description should result in no suggestions."

def test_generate_feedback_no_resume_skills():
    resume_text = ""
    job_description = (
        "Looking for a software engineer with experience in Python, AWS, and REST APIs.\n"
        "Familiarity with Docker and Kubernetes is a plus.\n\n"
        "Required Skills:\n"
        "- Python\n"
        "- AWS\n"
        "- REST APIs\n\n"
        "Preferred Skills:\n"
        "- Docker\n"
        "- Kubernetes"
    )
    feedback = generate_feedback(resume_text, job_description)
    expected_missing = {"python", "aws", "rest_apis", "docker", "kubernetes"}
    assert set(feedback["missing_keywords"]) == expected_missing, f"Expected missing_keywords {expected_missing}, got {feedback['missing_keywords']}"
    assert len(feedback["suggestions"]) == len(expected_missing), "Suggestions should be provided for all missing keywords."

def test_generate_feedback_empty_inputs():
    resume_text = ""
    job_description = ""
    feedback = generate_feedback(resume_text, job_description)
    assert feedback["missing_keywords"] == [], "Both resume and job description empty should yield no missing keywords."
    assert feedback["suggestions"] == [], "Both resume and job description empty should yield no suggestions."

""" def test_fit_score_endpoint_valid_payload():
    with patch("app.calculate_fit_score", return_value=95) as mock_fit_score, \
         patch("app.generate_feedback", return_value={"suggestions": [], "missing_keywords": []}) as mock_feedback, \
         patch("app.analyze_text", return_value={"feedback": []}) as mock_analysis:
        
        temp_storage = {
            "test_session": {
                "resume_text": "Experienced Software Engineer skilled in Python, AWS, and REST APIs.",
                "job_description": "Required: Python, AWS, REST APIs; Preferred: Docker, CI/CD"
            }
        }

        response = client.post("/api/fit-score")
        assert response.status_code == 200
        data = response.json()
        assert data["fit_score"] == 95
        assert data["feedback"] == []
        assert data["matched_skills"] == ["python", "aws", "rest_apis"]

        mock_fit_score.assert_called_once()
        mock_feedback.assert_called_once()
        mock_analysis.assert_called_once() """

def test_fit_score_endpoint_missing_resume():
    temp_storage = {
        "test_session": {
            "job_description": "Required: Python, AWS, REST APIs; Preferred: Docker, CI/CD"
        }
    }

    response = client.post("/api/fit-score")
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "Resume or job description not provided."

def test_fit_score_endpoint_missing_job_description():
    temp_storage = {
        "test_session": {
            "resume_text": "Experienced Software Engineer skilled in Python, AWS, and REST APIs."
        }
    }

    response = client.post("/api/fit-score")
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "Resume or job description not provided."

def test_fit_score_endpoint_empty_inputs():
    temp_storage = {
        "test_session": {
            "resume_text": "",
            "job_description": ""
        }
    }

    response = client.post("/api/fit-score")
    assert response.status_code == 400

def test_fit_score_endpoint_oversized_inputs():
    large_text = "a" * 100001 

    temp_storage = {
        "test_session": {
            "resume_text": large_text,
            "job_description": large_text
        }
    }

    response = client.post("/api/fit-score")
    assert response.status_code == 400