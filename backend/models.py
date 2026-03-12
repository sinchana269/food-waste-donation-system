from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
try:
    from .database import Base
except ImportError:
    from database import Base
import datetime
import enum

class UserRole(enum.Enum):
    DONOR = "donor"
    NGO = "ngo"
    VOLUNTEER = "volunteer"
    ADMIN = "admin"

class DonationStatus(enum.Enum):
    AVAILABLE = "available"
    ACCEPTED = "accepted"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    EXPIRED = "expired"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default=UserRole.DONOR.value)
    name = Column(String)
    phone = Column(String)
    address = Column(Text)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    is_approved_ngo = Column(Integer, default=0) # For NGOs: 0=Pending, 1=Approved, -1=Rejected

    donations = relationship("Donation", back_populates="donor")
    assignments = relationship("VolunteerAssignment", back_populates="volunteer")

class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    donor_id = Column(Integer, ForeignKey("users.id"))
    food_name = Column(String)
    quantity = Column(String)
    location = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    pickup_time = Column(DateTime)
    expiry_time = Column(DateTime)
    image_url = Column(String, nullable=True)
    status = Column(String, default=DonationStatus.AVAILABLE.value)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    donor = relationship("User", back_populates="donations")
    request = relationship("NGORequest", back_populates="donation", uselist=False)

class NGORequest(Base):
    __tablename__ = "ngo_requests"

    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(Integer, ForeignKey("donations.id"))
    ngo_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending") # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    donation = relationship("Donation", back_populates="request")
    assignment = relationship("VolunteerAssignment", back_populates="request", uselist=False)

class VolunteerAssignment(Base):
    __tablename__ = "volunteer_assignments"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("ngo_requests.id"))
    volunteer_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="assigned") # assigned, picked_up, delivered
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    request = relationship("NGORequest", back_populates="assignment")
    volunteer = relationship("User", back_populates="assignments")

class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
