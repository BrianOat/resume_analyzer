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
        if not isinstance(data, str) and len(data.strip()) > 0:
            return ValueError("Input must be non-empty strings.")
        return data
            
        
class OutputData(BaseModel):
    fit_score: int 
    feedback: list[str]
    @staticmethod
    def validate_output(data):
        if not(0 <= data["fit_score"] <= 100):
            raise ValueError("Fit score has to be between 0 and 100.")
        if not isinstance(data["feedback"], list) or not all(isinstance(item, str) for item in data["feedback"]):
            raise ValueError("Feedback has to be a list of strings.")
        return data

class ErrorResponse(BaseModel):
    error: str