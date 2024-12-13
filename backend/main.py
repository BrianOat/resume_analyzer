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
import openai
import re
from collections import Counter
from typing import List, Dict, Set

# For tokenizing 
STOP_WORDS = set([
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'while', 'with', 'is', 'are',
    'was', 'were', 'in', 'on', 'for', 'to', 'of', 'at', 'by', 'from', 'up',
    'down', 'out', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
    'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
    'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', "don't", 'should',
    'now', 'into', 'during', 'before', 'after', 'above', 'below', 'between', 'because',
    'until', 'while', 'about', 'against', 'among', 'through', 'during', 'without',
    'within', 'along', 'following', 'across', 'behind', 'beyond', 'plus', 'is a plus',
    'nice to have', 'preferred', 'desired', 'is a plus', 'would be a plus', 'preferably', 'skill',
    'skills', 'required', 'looking', 'knowledge', 'experience', 'software', 'we', 'skilled', 'familiarity', 'developer', 'desirable',
    'seeking', 'functional', 'collaborate', 'implement', 'cross', 'responsibilities', 'develop', 'engineer', 'proficient', 'teams', 'include',
    'maintain', "requirements", 'requirement', 'other'
])

# For tokenizing
MULTI_WORD_SKILLS = [
    'rest api', 'rest apis', 'machine learning', 'data analysis', 'sql database',
    'project management', 'customer service', 'agile methodology', 'object oriented programming',
    'software development', 'c++', 'c#', 'java', 'python', 'aws', 'docker', 'kubernetes',
    'html5', 'css3', 'javascript', 'react js', 'node js', 'sql server', 'git version control',
    'continuous integration', 'continuous deployment', 'linux administration', 'data structures',
    'network security', 'cloud computing', 'api development', 'unit testing',
    'test driven development', 'behavior driven development', 'user experience', 'ui design',
    'cicd pipelines', 'ngs pipelines', 'automated deployment processes', 'big data technologies',
    'data warehousing', 'database design', 'server side frameworks', 'terraform',
    'ci/cd pipelines', 'node.js', 'express.js', 'ngs data analysis'
]

# Sort multi-word skills by length in descending order to match longer phrases first
# Escape special characters and allow optional non-word characters within multi-word skills
MULTI_WORD_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(skill) for skill in sorted(MULTI_WORD_SKILLS, key=lambda x: -len(x))) + r')\b',
    re.IGNORECASE
)

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

def tokenize(text):
    """
    Tokenizes the input text into normalized tokens, handling multi-word skills.

    This function processes the input text to:
    - Replace multi-word skills with a single token (e.g., "machine learning" becomes "machine_learning").
    - Normalize tokens by converting to lowercase and removing special characters.
    - Remove stop words from the tokenized text.

    Args:
        text (str): The input text to tokenize.

    Returns:
        list: A list of normalized tokens extracted from the input text.
    """
    if not isinstance(text, str):
        return []

    # Replace multi-word skills with underscores
    def replace_multi_word_skills(match):
        return match.group(0).lower().replace(' ', '_').replace('/', '').replace('.', '')
    
    text = MULTI_WORD_PATTERN.sub(replace_multi_word_skills, text)
    
    # Find all word tokens (including those with underscores)
    tokens = re.findall(r'\b\w+\b', text.lower())
    
    # Remove stop words
    tokens = [token for token in tokens if token not in STOP_WORDS]
    
    return tokens

def extract_skills(job_description):
    """
    Extracts required and preferred skills from a job description.

    The function parses the job description text to identify skills listed
    under "Required Skills" and "Preferred Skills" sections. Skills are normalized
    to lowercase and multi-word skills are converted to a single token using underscores.

    Args:
        job_description (str): The job description text to extract skills from.

    Returns:
        tuple: A tuple containing two sets:
            - required_skills (set): A set of skills identified as required.
            - preferred_skills (set): A set of skills identified as preferred.
    """
    required_skills = set()
    preferred_skills = set()

    if not isinstance(job_description, str):
        return required_skills, preferred_skills

    # Split the job description into lines for processing
    lines = job_description.splitlines()

    current_section = None
    section_headers = {
        'required': re.compile(r'^required skills?:?$', re.IGNORECASE),
        'preferred': re.compile(r'^preferred skills?:?$', re.IGNORECASE)
    }

    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        # Check if the line is a section header
        if section_headers['required'].match(line):
            current_section = 'required'
            continue
        elif section_headers['preferred'].match(line):
            current_section = 'preferred'
            continue

        # If within a recognized section, extract skills
        if current_section in ['required', 'preferred']:
            # Remove common bullet points if present
            line = re.sub(r'^[-*•]\s*', '', line)
            # Split skills by commas or semicolons
            skills = re.split(r',|;', line)
            for skill in skills:
                skill = skill.strip().lower()  # Keep multi-word skills as is
                if skill:
                    # Replace multi-word skills with underscores
                    skill_transformed = MULTI_WORD_PATTERN.sub(
                        lambda match: match.group(0).lower().replace(' ', '_').replace('/', '').replace('.', ''),
                        skill
                    )
                    if current_section == 'required':
                        required_skills.add(skill_transformed)
                    elif current_section == 'preferred':
                        preferred_skills.add(skill_transformed)

    return required_skills, preferred_skills


def calculate_fit_score(resume_text, job_description):
    """
    Calculates a fit score based on the match between resume text and job description.

    This function evaluates how well a resume aligns with a job description
    by comparing the extracted skills from both. Required skills contribute 70%
    to the score, while preferred skills contribute 30%.

    Args:
        resume_text (str): The text extracted from the resume.
        job_description (str): The job description text.

    Returns:
        int: A fit score between 0 and 100, representing the degree of match.
    """
    if not isinstance(resume_text, str) or not isinstance(job_description, str):
        return 0

    # Extract required and preferred skills
    required_skills, preferred_skills = extract_skills(job_description)
    print("required skills",required_skills)
    print("preferred skills", preferred_skills)

    if not required_skills and not preferred_skills:
        return 0  # No skills to match

    # Tokenize resume
    resume_tokens = set(tokenize(resume_text))
    print("resume tokens", resume_tokens)

    # Calculate matches
    required_matches = required_skills.intersection(resume_tokens)
    print("required_matches", required_matches)
    preferred_matches = preferred_skills.intersection(resume_tokens)
    print("preferred_matches", preferred_matches)

    # Calculate weighted score
    required_score = (len(required_matches) / len(required_skills)) * 70 if required_skills else 0
    preferred_score = (len(preferred_matches) / len(preferred_skills)) * 30 if preferred_skills else 0

    total_score = required_score + preferred_score
    return min(int(total_score), 100)  # Ensure score does not exceed 100

def generate_feedback(resume_text, job_description):
    """
    Generates actionable feedback on missing skills in the resume.

    This function identifies the skills present in the job description but
    missing from the resume, and provides suggestions on how to improve the resume
    to align better with the job description.

    Args:
        resume_text (str): The text extracted from the resume.
        job_description (str): The job description text.

    Returns:
        dict: A dictionary containing:
            - missing_keywords (list): A list of skills missing from the resume.
            - suggestions (list): Suggestions on how to address the missing skills.
    """
    if not isinstance(resume_text, str) or not isinstance(job_description, str):
        return {"missing_keywords": [], "suggestions": []}
    
    # Extract required and preferred skills
    required_skills, preferred_skills = extract_skills(job_description)
    
    # Tokenize resume
    resume_tokens = set(tokenize(resume_text))
    
    # Identify missing skills
    missing_required = sorted(required_skills - resume_tokens)
    missing_preferred = sorted(preferred_skills - resume_tokens)
    
    missing_keywords = missing_required + missing_preferred
    
    suggestions = []
    for skill in missing_required:
        suggestions.append(f"Include experience with {skill.replace('_', ' ')}.")
    for skill in missing_preferred:
        suggestions.append(f"Add projects demonstrating {skill.replace('_', ' ')}.")
    
    return {
        "missing_keywords": missing_keywords,
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