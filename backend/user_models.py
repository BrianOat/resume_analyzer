from pydantic import BaseModel, Field

class BaseUserPayload(BaseModel):
    email: str
    password: str

class RegisterPayload(BaseUserPayload):
    username: str

class LoginPayload(BaseUserPayload):
    pass

class JobDescriptionPayload(BaseModel):
   job_description: str

class InputData(BaseModel):
    resume_text: str
    job_description: str
    @staticmethod
    def validate_length(data):
        if len(data) > 10000:
            raise ValueError("Input exceeds 10,000 characters.")
        return data
    @staticmethod
    def is_valid(data):
        if not isinstance(data, str) or len(data.strip()) == 0:
            raise ValueError("Input must be non-empty string.")
        return data
            
class FeedbackItem(BaseModel):
    category:str
    text:str
class OutputData(BaseModel):
    fit_score: int 
    feedback: list[FeedbackItem]
    @staticmethod
    def validate_output(data):
        if not(0 <= data.fit_score <= 100):
            raise ValueError("Fit score must be between 0 and 100.")
        return data

class ErrorResponse(BaseModel):
    error: str