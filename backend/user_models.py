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

class AnalysisPayload(BaseModel):
    resume_text: str = Field(..., max_length=5000, description="Text of uploaded resume")
    job_description: str = Field(..., max_length=5000, description="Job description of desired position")