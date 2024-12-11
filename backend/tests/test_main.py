from fastapi.testclient import TestClient
from backend.database.models import User
from backend.main import app, get_db, extract_text_from_pdf, temp_storage, calculate_fit_score, generate_feedback, tokenize, STOP_WORDS
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
    long_text = "A" * 5001
    long_text_pdf = create_pdf_in_memory(long_text)
    response = client.post(
        "/api/resume-upload",
        files={"file": ("long.pdf", long_text_pdf, "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "File contains more than 5,000 characters."
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
        "job_description": "A"*5001
    }
    response = client.post(
        "/api/job-description",
        json=job_description_payload
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Job description exceeds character limit."
    assert response.json()["status"] == "error"

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

def test_tokenize_basic():
    text = "Hello World!"
    tokens = tokenize(text)
    assert tokens == ["hello", "world"], "Should return lowercase tokens without punctuation."

def test_tokenize_mixed_case():
    text = "PyThOn aNd AWS"
    tokens = tokenize(text)
    assert tokens == ["python", "and", "aws"], "Should normalize all tokens to lowercase."

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

def test_calculate_fit_score_full_match():
    resume_text = (
        "John Doe\n"
        "Experienced Software Engineer with 5 years of experience in Python, AWS, and REST APIs.\n"
        "Skills: Python, AWS, REST APIs, Java, Docker\n"
        "Work Experience:\n"
        " - Developed RESTful APIs in Python.\n"
        " - Managed infrastructure on AWS.\n"
    )
    job_description = (
        "Looking for a software engineer with strong experience in Python, AWS, and REST APIs.\n"
        "Candidates should be proficient in modern cloud technologies and web services."
    )
    score = calculate_fit_score(resume_text, job_description)
    assert score == 100, "All key skills (Python, AWS, REST APIs) should fully match, resulting in 100%."

def test_calculate_fit_score_partial_match():
    resume_text = (
        "Jane Smith\n"
        "Software Developer with experience in Python, Java, and SQL.\n"
        "Familiar with backend development and some AWS knowledge.\n"
        "Projects have involved data pipelines, REST APIs, and microservices.\n"
    )
    job_description = (
        "We are looking for a developer skilled in Python, AWS, and REST APIs.\n"
        "Knowledge of Docker and Kubernetes is a plus."
    )
    score = calculate_fit_score(resume_text, job_description)
    assert score > 0 and score < 100, "Should have a partial match but not full (since other terms might not match)."

def test_calculate_fit_score_no_match():
    resume_text = (
        "Mark Johnson\n"
        "Mobile Developer experienced in Swift and iOS development.\n"
        "Expertise in building native iPhone apps and UI/UX design."
    )
    job_description = (
        "Looking for a software engineer with experience in Python, AWS, and REST APIs.\n"
        "Must be knowledgeable in cloud environments and backend services."
    )
    score = calculate_fit_score(resume_text, job_description)
    assert score == 0, "No shared keywords between resume and job description should yield 0."

def test_calculate_fit_score_empty_input():
    # Empty resume or job description should yield 0
    assert calculate_fit_score("", "some job description") == 0, "Empty resume should yield 0."
    assert calculate_fit_score("some resume text", "") == 0, "Empty job description should yield 0."

def test_generate_feedback_missing_skills():
    resume_text = (
        "Alice Brown\n"
        "Software Engineer with experience in Python and Java.\n"
        "Worked on backend APIs and deployed services to AWS once.\n"
    )
    job_description = (
        "We need a candidate with strong Python, AWS, and REST APIs skills.\n"
        "Should also have some exposure to Docker and CI/CD pipelines."
    )
    feedback = generate_feedback(resume_text, job_description)
    assert "rest_apis" in feedback["missing_keywords"], "REST APIs should be identified as missing."
    assert "cicd_pipelines" in feedback["missing_keywords"], "CI/CD pipelines should be identified as missing."
    assert len(feedback["suggestions"]) >= 2, "At least two suggestions should be provided for the missing keywords."

def test_generate_feedback_no_missing_skills():
    # Let's say we just decide "ci/cd" is the essential skill and "pipelines" is a filler.
    # Add "pipelines" and "software" to STOP_WORDS to remove it from consideration as a skill.
    STOP_WORDS.add("pipelines")
    STOP_WORDS.add("software")
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