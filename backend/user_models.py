from pydantic import BaseModel

class BaseUserPayload(BaseModel):
    email: str
    password: str

class RegisterPayload(BaseUserPayload):
    username: str

class LoginPayload(BaseUserPayload):
    pass

class JobDescriptionPayload(BaseModel):
   job_description: str
