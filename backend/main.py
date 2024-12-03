from fastapi import FastAPI, Response, status, UploadFile, Depends
from sqlalchemy.orm import Session
import os 
import io 
import bcrypt
import jwt
import datetime
from fastapi.middleware.cors import CORSMiddleware
from database import models
from user_models import RegisterPayload, LoginPayload, JobDescriptionPayload
from PyPDF2 import PdfReader
import uuid

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

import openai
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