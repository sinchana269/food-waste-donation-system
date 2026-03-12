from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
try:
    from .models import UserRole, DonationStatus
except ImportError:
    from models import UserRole, DonationStatus

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str
    name: str
    phone: str
    address: str
    lat: Optional[float] = None
    lon: Optional[float] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_approved_ngo: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class DonationBase(BaseModel):
    food_name: str
    quantity: str
    location: str
    lat: float
    lon: float
    pickup_time: datetime
    expiry_time: datetime
    image_url: Optional[str] = None

class DonationCreate(DonationBase):
    pass

class DonationResponse(DonationBase):
    id: int
    donor_id: int
    status: str
    created_at: datetime
    image_url: Optional[str] = None

    class Config:
        from_attributes = True
