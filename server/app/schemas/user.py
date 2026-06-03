from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    display_name: str | None = Field(default=None, max_length=50)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str | None
    default_department: str | None = None
    default_reporter: str | None = None
    default_payee: str | None = None
    default_bank_account: str | None = None
    default_bank_name: str | None = None

    model_config = {"from_attributes": True}


class UpdateUserDefaultsRequest(BaseModel):
    default_department: str | None = Field(default=None, max_length=100)
    default_reporter: str | None = Field(default=None, max_length=50)
    default_payee: str | None = Field(default=None, max_length=50)
    default_bank_account: str | None = Field(default=None, max_length=30)
    default_bank_name: str | None = Field(default=None, max_length=100)
