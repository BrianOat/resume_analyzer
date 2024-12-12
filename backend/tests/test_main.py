from fastapi.testclient import TestClient
from backend.database.models import User
from backend.main import app, get_db, extract_text_from_pdf, temp_storage
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