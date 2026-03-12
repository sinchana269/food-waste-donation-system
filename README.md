# Food Waste Donation Management System (Industrial Edition)

A professional-grade, full-stack application connecting restaurants, households, and NGOs to reduce food waste using AI and secure logistics.

## 🚀 Industrial Features
- **Smart Tech Integration**:
  - **AI Spoilage Prediction**: Uses ambient data to estimate food safety.
  - **QR Verification**: Secure hand-offs between donors and volunteers.
- **Admin Command Center**: Real-time activity logs and environmental impact tracking (CO2 reduction).
- **Public & Private Ecosystem**: Standalone pages for mission awareness and specialized dashboards for all roles.
- **Image Support**: Fully integrated image upload and preview pipeline for donations.
- **Global Map Integration**: Real-time location tracking using Leaflet.js.

## 🛠️ Local Setup Instructions

### 1. Prerequisites
- **Python 3.9+**
- **pip** (Python package manager)

### 2. Installation
```bash
# Clone the repository and navigate to project root
cd backend
pip install fastapi uvicorn sqlalchemy pydantic python-jose[cryptography] passlib[bcrypt] python-multipart email-validator
```

### 3. Instant Demo (Seeding)
To populate the system with realistic data (Users, NGOs, Donations):
```bash
python seed_data.py
```

### 4. Running the System
**Start Backend:**
```bash
uvicorn main:app --reload
```
**Start Frontend:**
Serve the `frontend` directory using any local server (e.g., Live Server in VS Code):
```bash
cd ../frontend
python -m http.server 5500
```

## 🔑 Pre-Seeded Accounts
| Role | Username | Password |
| --- | --- | --- |
| **Admin** | `admin` | `admin123` |
| **Donor** | `hotel_grand` | `donor123` |
| **NGO** | `helping_hands` | `ngo123` |
| **Volunteer** | `john_vol` | `vol123` |

---
*Created by Antigravity for Food Waste Mitigation.*
