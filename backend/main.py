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
from openai import OpenAI
import json

resume_file_content = io.BytesIO()

temp_storage = {}

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
        if current_char_count > 10000:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
                "error": "File contains more than 10,000 characters.",
                "status": "error",
                "exceeded_by": current_char_count - 10000
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
    try:
      job_description = payload.job_description
      job_description.strip()
      max_char_count = 10000
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

        # Validating input
        InputData.is_valid(resume_text)
        InputData.is_valid(job_description)
        InputData.validate_length(resume_text)
        InputData.validate_length(job_description)

        # Construct prompt for NLP API call:
        openai.api_key = os.getenv('gpt_key')
        prompt = (
            "You are a career coach. Based on the given resume and job description, "
            "evaluate the fit and provide specific feedback for improvement.\n\n"
            f"Resume:\n{resume_text}\n\n"
            f"Job Description:\n{job_description}\n\n"
            "Provide:\n1. A fit score (0-100).\n"
            "2. Feedback as a JSON array where each element is an object with "
            "'category' and 'text' fields. Categories should be one of 'skills', 'experience', or 'formatting', "
            "based on the type of improvement suggested. The 'text' should be a concise improvement suggestion.\n\n"
            "Example:\n"
            "{\n"
            "  \"fit_score\": 85,\n"
            "  \"feedback\": [\n"
            "    { \"category\": \"skills\", \"text\": \"Include experience with AWS services.\" },\n"
            "    { \"category\": \"experience\", \"text\": \"Add projects demonstrating REST API development.\" }\n"
            "  ]\n"
            "}"
        )
        # Making a request to OpenAI API
        analysis = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
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
                                    "type": "object",
                                    "properties": {
                                        "category": {
                                            "type": "string",
                                            "description": "Category of the feedback: skills, experience, or formatting"
                                        },
                                        "text": {
                                            "type": "string",
                                            "description": "The feedback text"
                                        }
                                    },
                                    "required": ["category", "text"]
                                }
                            }
                        },
                        "required": ["fit_score", "feedback"],
                        "additionalProperties": False
                    }
                }
            }
        )

        # Extract relevant fields
        raw_response = analysis.choices[0].message.content

        if not raw_response.strip():
            raise ValueError("NLP API returned an empty response.")

        # Attempt to parse response as JSON
        try:
            parsed_response = json.loads(raw_response)
        except json.JSONDecodeError:
            raise ValueError(f"Response is not in JSON format: {raw_response}")

        fit_score = parsed_response['fit_score']
        feedback = parsed_response['feedback']

        # Validate output data structure
        if not isinstance(fit_score, int) or not isinstance(feedback, list):
            raise ValueError("NLP API response has invalid 'fit_score' or 'feedback' format.")

        # Additional validation checks if needed
        for f_item in feedback:
            if 'category' not in f_item or 'text' not in f_item:
                raise ValueError("Each feedback item must contain 'category' and 'text' fields.")

        # Map parsed data to OutputData (assuming you adjust OutputData accordingly)
        # If OutputData still expects just a list of strings, you'll need to update it.
        output = {
            "fit_score": fit_score,
            "feedback": feedback
        }

        response.status_code = status.HTTP_200_OK
        return output
    except openai.APIError as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": f"Unable to process the request due to OpenAI API: {str(e)}", "status": "error"}
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": f"Validation error with input. Please try again. {str(e)}", "status": "error"}
    except Exception as e:
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