from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional


class WidgetCreate(BaseModel):
    widget_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    fields: List[str] = Field(..., min_length=1, max_length=10)
    button_text: str = Field(..., min_length=1, max_length=50)


class WidgetResponse(BaseModel):
    id: str
    widget_type: str
    title: str
    description: Optional[str]
    fields: List[str]
    button_text: str
    is_active: bool

    class Config:
        from_attributes = True

class TenantSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


class TenantLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str

class SubmissionCreate(BaseModel):
    widget_id: str
    data: dict
    website: Optional[str] = None  # honeypot field — insaan ise khali chorega


class SubmissionResponse(BaseModel):
    id: str
    widget_id: str
    data: dict
    country: Optional[str] = None
    city: Optional[str] = None
    is_spam: bool

    class Config:
        from_attributes = True