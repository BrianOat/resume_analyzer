from fastapi import FastAPI, Response, status, UploadFile, Depends
from sqlalchemy.orm import Session
import os 
import io 
import bcrypt
import jwt
import datetime
from fastapi.middleware.cors import CORSMiddleware
from database import models
from user_models import RegisterPayload, LoginPayload, JobDescriptionPayload, InputData, OutputData
from PyPDF2 import PdfReader
import uuid
import openai
import re
from collections import Counter
from openai import OpenAI
import json

resume_file_content = io.BytesIO()

temp_storage = {}


# Note that STOP_WORDS is for the functions for calculating fit score and generating feedback
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if", "in", "into",
    "is", "it", "its", "of", "on", "or", "such", "that", "the", "their", "there",
    "these", "they", "this", "to", "was", "will", "with", "you", "your", "looking",
    "strong", "experience", "candidates", "should", "be", "proficient", "modern",
    "cloud", "technologies", "web", "services", "familiarity", "plus"
}

# Note that MULTI_WORD_SKILLS is for the tokenize() function
MULTI_WORD_SKILLS = {
    # Software/Web Development
    "rest apis": "rest_apis",
    "rest api": "rest_api",
    "ci/cd pipelines": "cicd_pipelines",
    "ci/cd": "cicd",
    "web development": "web_development",
    "front end": "front_end",
    "back end": "back_end",
    "full stack": "full_stack",
    "microservices architecture": "microservices_architecture",
    "distributed systems": "distributed_systems",
    "cloud computing": "cloud_computing",
    "cloud infrastructure": "cloud_infrastructure",
    "container orchestration": "container_orchestration",
    "infrastructure as code": "infrastructure_as_code",
    "configuration management": "configuration_management",
    "secret management": "secret_management",
    "identity and access management": "identity_and_access_management",
    "high availability": "high_availability",
    "load balancing": "load_balancing",
    "api gateway": "api_gateway",

    # Data Science / ML / AI
    "machine learning": "machine_learning",
    "deep learning": "deep_learning",
    "natural language processing": "natural_language_processing",
    "natural language generation": "natural_language_generation",
    "data science": "data_science",
    "data visualization": "data_visualization",
    "big data": "big_data",
    "etl pipelines": "etl_pipelines",
    "time series analysis": "time_series_analysis",
    "computer vision": "computer_vision",
    "reinforcement learning": "reinforcement_learning",
    "generative adversarial networks": "generative_adversarial_networks",
    "graph neural networks": "graph_neural_networks",
    "transformer models": "transformer_models",

    # Cybersecurity / Low-Level
    "cyber security": "cyber_security",
    "penetration testing": "penetration_testing",
    "threat analysis": "threat_analysis",
    "digital forensics": "digital_forensics",
    "reverse engineering": "reverse_engineering",
    "vulnerability assessment": "vulnerability_assessment",
    "risk management": "risk_management",
    "regulatory compliance": "regulatory_compliance",
    "incident response": "incident_response",

    # Embedded / Systems Programming
    "linux kernel driver development": "linux_kernel_driver_development",
    "embedded systems": "embedded_systems",
    "high performance computing": "high_performance_computing",

    # DevOps / Methodologies
    "project management": "project_management",
    "product management": "product_management",
    "quality assurance": "quality_assurance",
    "business analysis": "business_analysis",
    "test driven development": "test_driven_development",
    "behavior driven development": "behavior_driven_development",
    "continuous integration": "continuous_integration",
    "continuous deployment": "continuous_deployment",
    "devops pipelines": "devops_pipelines",
    "agile methodology": "agile_methodology",
    "scrum master": "scrum_master",
    "user experience design": "user_experience_design",
    "responsive design": "responsive_design",
    "root cause analysis": "root_cause_analysis",
    "static code analysis": "static_code_analysis",
    "dynamic code analysis": "dynamic_code_analysis",
    "automated testing": "automated_testing",
    "pair programming": "pair_programming",
    "peer code review": "peer_code_review"
}

app = FastAPI()

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    """
    Root endpoint to check the server status.

    Returns:
        dict: A welcome message.
    """
    return {"message": "Hello World"}

@app.post("/api/register")
async def register(payload: RegisterPayload, response: Response, db: Session = Depends(get_db)):
    """
      Register account from the given payload.
      
      Args:
        payload (RegisterPayload): The payload containing email, password, username
        response (Response): The FastAPI Response object for setting the status code
        db (Session): A database connection?
      Returns:
        dict: A JSON response with a status message.
      """
    email = payload.email
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
      response.status_code = status.HTTP_400_BAD_REQUEST
      return {"error": "Username or email already registered"}
    else:
      username = payload.username
      password = payload.password
      bytes = password.encode('utf-8') 
      salt = bcrypt.gensalt() 
      hashed_password = bcrypt.hashpw(bytes, salt) 
      user = models.User(email=email, username=username, hashed_password=hashed_password)
      db.add(user)
      db.commit()
      response.status_code = status.HTTP_201_CREATED
      return {"message": "User registered"}
  
@app.post("/api/login")
async def login(payload: LoginPayload, response: Response, db: Session = Depends(get_db)):
    """
      Register account from the given payload.
      
      Args:
        payload (LoginPayload): The payload containing email, password
        response (Response): The FastAPI Response object for setting the status code

      Returns:
        dict: A JSON response with token if succesful otherwise a status message.
      """
    email = payload.email
    password = payload.password
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user and bcrypt.checkpw(password.encode('utf-8'), db.query(models.User).filter(models.User.email == email).first().hashed_password):
      secret = os.getenv('secret')
      algorithm = os.getenv('algorithm')
      payload = {
          "email" : email,
          "exp" : (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).timestamp()
      }
      jwt_token = jwt.encode(payload, secret, algorithm)
      response.status_code = status.HTTP_200_OK
      return {"token": jwt_token}
    else:
      response.status_code = status.HTTP_400_BAD_REQUEST
      return {"error": "Email or password is not recognized"}

@app.post("/api/resume-upload")
async def resume_upload(file: UploadFile, response: Response):
    """
    Upload and process a resume file, validating its type and size.

    Args:
        file (UploadFile): The uploaded resume file.
        response (Response): The FastAPI Response object for setting the status code.

    Returns:
        dict: A JSON response with status and processing results.
    """
    max_file_size = 2 * 1024 * 1024
    allowed_types = ["application/pdf"]

    # Validate file type
    if file.content_type not in allowed_types:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Invalid file type. Only PDF files are allowed.", "status": "error"}

    # Read file content
    file_content = await file.read()
    if len(file_content) > max_file_size:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "File size exceeds the 2MB limit.", "status": "error"}

    # Extract and validate text
    try:
        text = extract_text_from_pdf(io.BytesIO(file_content))
        current_char_count = len(text)
        if current_char_count > 5000:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
                "error": "File contains more than 5,000 characters.",
                "status": "error",
                "exceeded_by": current_char_count - 5000
            }
        
        #Create a session ID to store data
        session_id = str(uuid.uuid4())
        temp_storage[session_id] = {"resume_text": text}

        response.status_code = status.HTTP_200_OK
        return {
            "message": "Resume uploaded successfully.",
            "status": "success",
            "character_count": current_char_count,
            "session_id": session_id
        }
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": f"Error processing PDF: {str(e)}", "status": "error"}
      
@app.post("/api/job-description")
async def job_description_upload(payload: JobDescriptionPayload, response: Response):
    """
    Upload and validate a job description, associating it with the current session.

    Args:
        payload (JobDescriptionPayload): The payload containing the job description text.
        response (Response): The FastAPI Response object for setting the status code.

    Returns:
        dict: A JSON response indicating success or error.
    """
    try:
      job_description = payload.job_description
      job_description.strip()
      max_char_count = 5000
      if len(job_description) <= max_char_count:
        session_id = next(iter(temp_storage), None)
        if session_id:
           temp_storage[session_id]["job_description"] = job_description
           response.status_code = status.HTTP_200_OK
           return {
               "message": "Job description submitted successfully.",
               "status": "success"
           }
        else:
          response.status_code = status.HTTP_400_BAD_REQUEST
          return {
            "error": "No resume uploaded.",
            "status": "error"
          }
      else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "error": "Job description exceeds character limit.",
            "status": "error"
        }
    except Exception as e: 
      return {"error": str(e)}

@app.post("/api/analyze")
async def analyze_text(payload: InputData, response: Response):
  """
    Send uploaded resume and job description to NLP API.
    
    Args:
      payload (InputData): The payload containing resume text, job description in standardized input data structure
      response (Response): The FastAPI Response object for setting the status code

    Returns:
      OutputData: standardized output data structure for fit score and feedback if succesful otherwise an error status message.
  """
  
  try:
    resume_text = payload.resume_text.strip()
    job_description = payload.job_description.strip()

    #Validating input
    InputData.is_valid(resume_text)
    InputData.is_valid(job_description)
    InputData.validate_length(resume_text)
    InputData.validate_length(job_description)
    
    #Construct prompt for NLP API call:
    openai.api_key = os.getenv('gpt_key')
    prompt = (
            "You are a career coach. Based on the given resume and job description, "
            "evaluate the fit and provide specific feedback for improvement.\n\n"
            f"Resume:\n{resume_text}\n\n"
            f"Job Description:\n{job_description}\n\n"
            "Provide:\n1. A fit score (0-100).\n"
            "2. Feedback on how the resume can be improved to better fit the job description in a concise list of strings."
        )
    #Making a request to OpenAI API
    analysis = openai.chat.completions.create(
      model= "gpt-4o-mini",
      messages= [{"role": "user", "content": prompt}], 
      response_format={
         "type": "json_schema", 
         "json_schema": {
            "name": "resume_analysis", 
            "schema": {
               "type": "object",
               "properties": {
                  "fit_score": {
                    "description": "A score representing how well the resume fits the job description.",
                    "type": "integer", 
                    "minimum": 0,
                    "maximum": 100
                  }, 
                  "feedback": {
                    "description": "List of feedback points on how the user can improve their resume.",
                    "type": "array", 
                    "items": {
                      "type": "string"
                    }
                  }
               }, 
               "required": ["fit_score", "feedback"],
               "additionalProperties": False
            }
         }
      }
    )

    #Extract relevant fields
    raw_response = analysis.choices[0].message.content
    # Log raw response for debugging
    #print("Raw response:", raw_response)

    # Handle empty responses
    if not raw_response.strip():
      raise ValueError("NLP API returned an empty response.")

    # Attempt to parse response as JSON
    try:
      parsed_response = json.loads(raw_response)
    except json.JSONDecodeError:
      raise ValueError(f"Response is not in JSON format: {raw_response}")

    #Parse relevant values from raw_response after converting to dict
    fit_score = parsed_response['fit_score']
    feedback = parsed_response['feedback']

    #Handle malformed/missing fields
    if not fit_score or not feedback:
      return ValueError("NLP API response missing fit score and/or feedback fields.")
    #Convert to fit_score to percentage
    # if fit_score.isInstance(fit_score, float) and fit_score <= 1:
    #   fit_score=round(fit_score * 100)
    
    #Map parsed data to OutputData
    output = OutputData(
      fit_score = fit_score,
      feedback = feedback
    )
    #print("Fit Score:", output.fit_score)
    #print("Feedback:", output.feedback)
    
    #Validate output data
    OutputData.validate_output(output)

    response.status_code = status.HTTP_200_OK
    return output
  
  except openai.APIError as e:
    #catch openAI API errors
    response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return {"error": f"Unable to process the request due to OpenAI API: {str(e)}", "status": "error"}
  except ValueError as e:
    #catch validation errors from standardized input/output data structures
    response.status_code = status.HTTP_400_BAD_REQUEST
    return {"error": f"Validation error with input. Please try again. {str(e)}", "status": "error"}
  except Exception as e:
    #catch other unexpected errors
    response.status_code = status.HTTP_400_BAD_REQUEST
    return {"error": f"Unable to process the request. Please try again later: {str(e)}", "status": "error"}

def extract_text_from_pdf(file):
    """
    Extract text from a PDF file and clean up unnecessary line breaks and whitespace.

    Args:
        file: The PDF file to extract text from.
    
    Returns:
        str: The cleaned text extracted from the PDF.
    """
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""  # Handle cases where text extraction might return None
        return " ".join(text.split())  # Remove extraneous whitespace
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
def preprocess_text(text: str) -> str:
    """
    Preprocess the input text by replacing known multi-word skill phrases with single-token forms.
    The replacement is done case-insensitively, ensuring that variations in capitalization do not
    affect the ability to recognize these terms.

    Args:
        text (str): The original text to preprocess.

    Returns:
        str: The preprocessed text with multi-word skills replaced by single tokens.
    """
    for phrase, token in MULTI_WORD_SKILLS.items():
        # Use word boundaries (\b) to ensure whole phrase matches only.
        pattern = r'\b' + re.escape(phrase) + r'\b'
        text = re.sub(pattern, token, text, flags=re.IGNORECASE)

    return text

def tokenize(text: str):
    """
    Normalize text by converting to lowercase, removing punctuation, and splitting into words.

    Args:
        text (str): Input text.

    Returns:
        list: List of normalized tokens (words).
    """
    text = preprocess_text(text)  # Preprocess to handle multi-word phrases
    return re.findall(r'\b\w+\b', text.lower()) if text else []

def calculate_fit_score(resume_text: str, job_description: str) -> int:
    """
    Calculate the fit score between a resume and a job description based on keyword matching.

    Args:
        resume_text (str): The text of the resume.
        job_description (str): The text of the job description.

    Returns:
        int: Fit score as a percentage (0-100).
    """
    # Tokenize
    resume_tokens = [token for token in tokenize(resume_text) if token not in STOP_WORDS]
    job_tokens = [token for token in tokenize(job_description) if token not in STOP_WORDS]

    # Count matches
    resume_counter = Counter(resume_tokens)
    job_counter = Counter(job_tokens)

    matches = sum((resume_counter & job_counter).values())
    total_keywords = len(job_tokens)

    return int((matches / total_keywords) * 100) if total_keywords > 0 else 0

def generate_feedback(resume_text: str, job_description: str):
    """
    Generate feedback on missing keywords in a resume compared to a job description.

    Args:
        resume_text (str): The text of the resume.
        job_description (str): The text of the job description.

    Returns:
        dict: Feedback including matched and missing keywords, and improvement suggestions.
    """
    # Tokenize
    resume_tokens = {token for token in tokenize(resume_text) if token not in STOP_WORDS}
    job_tokens = {token for token in tokenize(job_description) if token not in STOP_WORDS}

    matched_keywords = resume_tokens.intersection(job_tokens)
    missing_keywords = job_tokens.difference(resume_tokens)

    suggestions = [
        f"Consider adding details or experience related to '{keyword}' in your resume."
        for keyword in missing_keywords
    ]

    return {
        "matched_keywords": list(matched_keywords),
        "missing_keywords": list(missing_keywords),
        "suggestions": suggestions
    }

@app.post("/api/fit-score")
async def fit_score_endpoint(response: Response):
    """
    Endpoint to calculate fit score and provide feedback based on resume and job description.

    It retrieves the resume and job description from the temporary storage, calculates
    the fit score using `calculate_fit_score` and generates feedback using `generate_feedback`.

    Args:
        response (Response): The FastAPI Response object for setting the status code.

    Returns:
        dict: A JSON response containing the fit score, matched keywords, missing keywords,
              and suggestions, or an error message if something goes wrong.
    """
    try:
        session_id = next(iter(temp_storage), None)
        if not session_id or "resume_text" not in temp_storage[session_id] or "job_description" not in temp_storage[session_id]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "Resume or job description not provided.", "status": "error"}

        resume_text = temp_storage[session_id]["resume_text"]
        job_description = temp_storage[session_id]["job_description"]

        fit_score = calculate_fit_score(resume_text, job_description)
        feedback = generate_feedback(resume_text, job_description)

        response.status_code = status.HTTP_200_OK
        return {
            "message": "Fit score calculated successfully.",
            "status": "success",
            "fit_score": fit_score,
            "matched_keywords": feedback["matched_keywords"],
            "missing_keywords": feedback["missing_keywords"],
            "suggestions": feedback["suggestions"]
        }
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e), "status": "error"}

openai.api_key = os.getenv('gpt_key')
def test():
  # Define the model and input
  response = openai.chat.completions.create(
    model= "gpt-4o-mini",
    messages= [{ "role": "user", "content": "Say this is a test" }]
  )

  # Print the response
  print(response)

test()
