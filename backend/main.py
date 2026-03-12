from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
import random
import datetime
from fastapi.staticfiles import StaticFiles
try:
    from . import models, schemas, auth, database
    from .database import engine, get_db
except ImportError:
    import models, schemas, auth, database
    from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Food Waste Donation Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/predict-spoilage/{donation_id}")
def predict_spoilage(donation_id: int, db: Session = Depends(get_db)):
    donation = db.query(models.Donation).filter(models.Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    # Simple simulated AI logic
    # Higher confidence for shorter time since creation and longer time until expiry
    now = datetime.datetime.utcnow()
    total_duration = (donation.expiry_time - donation.created_at).total_seconds()
    elapsed = (now - donation.created_at).total_seconds()
    
    if elapsed < 0: elapsed = 0
    remaining_ratio = 1 - (elapsed / total_duration) if total_duration > 0 else 0
    
    # Add some "AI" randomness and factor in food name keywords
    confidence = remaining_ratio * 100
    if "cooked" in donation.food_name.lower() or "rice" in donation.food_name.lower():
        confidence -= 10
    
    label = "Safe"
    if confidence < 30: label = "High Risk"
    elif confidence < 60: label = "Moderate Risk"
    
    return {"confidence_score": round(max(0, confidence), 2), "label": label}

def log_action(db: Session, action: str, details: str):
    log = models.AdminLog(action=action, details=details)
    db.add(log)
    db.commit()

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check for duplicate username
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check for duplicate email
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        name=user.name,
        phone=user.phone,
        address=user.address,
        lat=user.lat,
        lon=user.lon
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        log_action(db, "User Registered", f"New user {user.username} joined as {user.role}")
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.put("/users/update", response_model=schemas.UserResponse)
def update_user_profile(
    user_update: schemas.UserCreate, # Using Create schema for simplicity, or could make a partial one
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    current_user.name = user_update.name
    current_user.phone = user_update.phone
    current_user.address = user_update.address
    if user_update.password:
        current_user.hashed_password = auth.get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(current_user)
    log_action(db, "Profile Updated", f"User {current_user.username} updated their profile")
    return current_user

# Donation Endpoints
@app.post("/donations", response_model=schemas.DonationResponse)
def create_donation(
    donation: schemas.DonationCreate, 
    current_user: models.User = Depends(auth.check_role(["donor", "admin"])),
    db: Session = Depends(get_db)
):
    new_donation = models.Donation(
        **donation.dict(),
        donor_id=current_user.id
    )
    db.add(new_donation)
    db.commit()
    db.refresh(new_donation)
    log_action(db, "Donation Posted", f"Donor {current_user.username} posted {donation.food_name}")
    return new_donation

@app.post("/donations/upload-image")
async def upload_image(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, f"{random.randint(1000,9999)}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"image_url": f"/{file_path}"}

@app.get("/donations", response_model=List[schemas.DonationResponse])
def get_donations(db: Session = Depends(get_db)):
    return db.query(models.Donation).filter(models.Donation.status == "available").all()

@app.get("/donations/public", response_model=List[schemas.DonationResponse])
def get_public_donations(db: Session = Depends(get_db)):
    # Same as /donations but explicitly for public view
    return db.query(models.Donation).filter(models.Donation.status == "available").all()

@app.get("/donations/my", response_model=List[schemas.DonationResponse])
def get_my_donations(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Donation).filter(models.Donation.donor_id == current_user.id).all()

@app.post("/donations/{donation_id}/accept")
def accept_donation(
    donation_id: int,
    current_user: models.User = Depends(auth.check_role(["ngo", "admin"])),
    db: Session = Depends(get_db)
):
    donation = db.query(models.Donation).filter(models.Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    if donation.status != "available":
        raise HTTPException(status_code=400, detail="Donation already accepted or unavailable")
    donation.status = "accepted"
    new_request = models.NGORequest(donation_id=donation_id, ngo_id=current_user.id, status="accepted")
    db.add(new_request)
    db.commit()
    log_action(db, "Donation Accepted", f"NGO {current_user.username} accepted donation {donation.food_name}")
    return {"message": "Donation accepted"}

@app.post("/donations/{donation_id}/assign")
def assign_volunteer(
    donation_id: int,
    volunteer_id: int,
    current_user: models.User = Depends(auth.check_role(["ngo", "admin"])),
    db: Session = Depends(get_db)
):
    # Find the accepted request
    request = db.query(models.NGORequest).filter(
        models.NGORequest.donation_id == donation_id,
        models.NGORequest.ngo_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found or not owned by you")
    
    new_assignment = models.VolunteerAssignment(request_id=request.id, volunteer_id=volunteer_id)
    db.add(new_assignment)
    db.commit()
    return {"message": "Volunteer assigned"}

@app.get("/assignments/my", response_model=List[schemas.DonationResponse])
def get_my_assignments(
    current_user: models.User = Depends(auth.check_role(["volunteer"])),
    db: Session = Depends(get_db)
):
    # This is a bit complex due to relations, simplified for now
    assignments = db.query(models.VolunteerAssignment).filter(
        models.VolunteerAssignment.volunteer_id == current_user.id
    ).all()
    
    results = []
    for ass in assignments:
        don = ass.request.donation
        results.append(don)
    return results

@app.post("/assignments/{donation_id}/status")
def update_status(
    donation_id: int,
    status: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    donation = db.query(models.Donation).filter(models.Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    donation.status = status
    db.commit()
    return {"message": f"Status updated to {status}"}

# Admin Endpoints
@app.get("/admin/users")
def get_all_users(current_user: models.User = Depends(auth.check_role(["admin"])), db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.get("/admin/stats")
def get_stats(current_user: models.User = Depends(auth.check_role(["admin"])), db: Session = Depends(get_db)):
    total_donations = db.query(models.Donation).count()
    active_donations = db.query(models.Donation).filter(models.Donation.status == "available").count()
    delivered_donations = db.query(models.Donation).filter(models.Donation.status == "delivered").count()
    total_users = db.query(models.User).count()
    
    # Calculate impact
    # Assuming avg 5kg per donation
    total_kg = delivered_donations * 5
    co2_saved = total_kg * 2.5 # 2.5kg CO2 saved per kg food
    people_served = total_kg * 2 # 2 people per kg (approx)
    
    return {
        "total_donations": total_donations,
        "active_donations": active_donations,
        "total_users": total_users,
        "food_saved_kg": total_kg,
        "co2_saved_kg": round(co2_saved, 2),
        "people_served": people_served
    }

@app.get("/admin/logs")
def get_admin_logs(current_user: models.User = Depends(auth.check_role(["admin"])), db: Session = Depends(get_db)):
    return db.query(models.AdminLog).order_by(models.AdminLog.created_at.desc()).limit(50).all()

@app.post("/admin/approve-ngo/{user_id}")
def approve_ngo(user_id: int, status: int, current_user: models.User = Depends(auth.check_role(["admin"])), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.role != "ngo":
        raise HTTPException(status_code=404, detail="NGO user not found")
    
    user.is_approved_ngo = status
    db.commit()
    log_action(db, "NGO Status Updated", f"Admin {current_user.username} set NGO {user.username} status to {status}")
    return {"message": "NGO status updated"}
