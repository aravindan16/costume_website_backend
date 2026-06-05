from pydantic import BaseModel, Field

class SignupRequest(BaseModel):
    name: str = Field(min_length=2)
    phone: str = Field(min_length=7)
    email: str = Field(min_length=5)
    password: str = Field(min_length=6)

class LoginRequest(BaseModel):
    email: str = Field(min_length=5)
    password: str = Field(min_length=6)

class FavoriteRequest(BaseModel):
    user_id: str
    product_id: str

class GoogleAuthRequest(BaseModel):
    token: str

class UpdateProfileRequest(BaseModel):
    name: str = Field(min_length=2)
    phone: str
    address: str
