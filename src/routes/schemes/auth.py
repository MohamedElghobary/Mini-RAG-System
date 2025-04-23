from pydantic import BaseModel

class UserSignup(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithProject(BaseModel):
    access_token: str
    token_type: str = "bearer"
    project_id: str
