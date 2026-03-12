import sys
import os
import datetime

# Add the backend directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import models
import auth
from database import SessionLocal, engine

def seed():
    # Create tables if they don't exist
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if we already have data
    if db.query(models.User).filter(models.User.username == "admin").first():
        print("Database already seeded.")
        return

    print("Seeding database...")

    # 1. Create Users
    users = [
        ("admin", "admin@foodwaste.org", "admin", "System Administrator", "admin123"),
        ("hotel_grand", "donations@grandhotel.com", "donor", "The Grand Hotel", "donor123"),
        ("helping_hands", "contact@helpinghands.ngo", "ngo", "Helping Hands NGO", "ngo123"),
        ("john_vol", "john@volunteer.com", "volunteer", "John Doe", "vol123"),
    ]

    for username, email, role, name, password in users:
        hashed = auth.get_password_hash(password)
        user = models.User(
            username=username,
            email=email,
            role=role,
            name=name,
            hashed_password=hashed,
            phone="1234567890",
            address="123 City Street",
            lat=12.9716,
            lon=77.5946,
            is_approved_ngo=1 if role == "ngo" else 0
        )
        db.add(user)
    
    db.commit()
    donor = db.query(models.User).filter(models.User.username == "hotel_grand").first()

    # 2. Create Sample Donations
    donations = [
        ("Fresh Biryani", "10 kg", "Grand Hotel Main Kitchen", 5, 24),
        ("Breads and Pastries", "5 kg", "Hotel Bakery", 2, 48),
        ("Cooked Vegetable Curry", "8 kg", "Grand Hotel Hall B", 1, 12),
    ]

    for food, qty, loc, pickup_h, expiry_h in donations:
        now = datetime.datetime.utcnow()
        don = models.Donation(
            food_name=food,
            quantity=qty,
            location=loc,
            lat=12.9716 + (0.01 * pickup_h), # Slight offset
            lon=77.5946 + (0.01 * pickup_h),
            pickup_time=now + datetime.timedelta(hours=pickup_h),
            expiry_time=now + datetime.timedelta(hours=expiry_h),
            donor_id=donor.id,
            status="available"
        )
        db.add(don)
    
    db.commit()
    
    # 3. Add an Admin Log
    log = models.AdminLog(
        action="System Seeded",
        details="Initial sample data populated by system administrator."
    )
    db.add(log)
    db.commit()

    print("Database seeding complete!")
    print("Logins: admin/admin123, hotel_grand/donor123, helping_hands/ngo123, john_vol/vol123")

if __name__ == "__main__":
    seed()
