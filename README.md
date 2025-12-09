# ATF CyberX - Team C

AI-based cyber-defense platform for detecting phishing emails and deepfake voice calls.

## 📋 Project Overview

ATF CyberX is an MVP (Minimum Viable Product). The platform provides:
- **Phishing Email Detection**: Analyze email content for phishing threats
- **Deepfake Voice Detection**: Analyze audio files for voice manipulation
- **Risk Assessment**: Returns risk scores (0-100) with human-readable explanations
- **Scan History**: Stores all scans in a SQLite database

## What We've Built So Far

### ✅ Completed (Initial Setup)
1. **Project Structure**: Complete folder structure for backend and frontend
2. **Backend Foundation**:
   - Pydantic schemas for request/response validation ✅
   - Configuration files ready ✅
   - Clean file structure with placeholders for:
     - Database models (email_scan.py, voice_scan.py)
     - CRUD operations (crud_email.py, crud_voice.py)
     - ML models (phishing_model.py, deepfake_model.py)

3. **Frontend Foundation**:
   - React app with routing (Phishing, Voice, History pages) ✅
   - Navigation bar with ATF CyberX branding ✅
   - API client setup with Axios ✅
   - Common UI components (RiskBadge, Loader, ErrorAlert) ✅
   - Phishing form components (EmailForm, PhishingResultCard) ✅
   - Phishing scan hook (usePhishingScan) ✅
   - Responsive styling ✅



### 🚧 To Be Completed (Team Tasks)
- **Backend Database Layer**:
  - Implement EmailScan and VoiceScan models
  - Implement CRUD operations for email and voice scans
  - Set up database session and initialization
  
- **Backend ML Layer**:
  - Implement PhishingModel with detection logic
  - Implement DeepfakeModel with audio analysis
  
- **Backend Services Layer**:
  - Implement phishing_service.py
  - Implement voice_service.py
  - Implement explanation_service.py
  
- **Backend API Layer**:
  - Implement API routes (phishing, voice, health endpoints)
  - Create FastAPI main application setup
  
- **Frontend Components**:
  - Build AudioUpload component
  - Build VoiceResultCard component
  
- **Frontend State Management**:
  - ~~Create usePhishingScan hook~~ ✅ DONE
  - Create useVoiceScan hook
  - Connect frontend to backend APIs
  
- **Testing**:
  - Backend unit tests
  - Frontend component tests
  - End-to-end integration tests

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  Pages: Phishing | Voice | History                          │
│  Components: Forms | Results | Common UI                    │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────┼───────────────────────────────────────┐
│                 Backend (FastAPI)                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ API Routes │→ │  Services  │→ │ ML Models  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│                       ↓                                      │
│                  ┌────────────┐                             │
│                  │  Database  │                             │
│                  │  (SQLite)  │                             │
│                  └────────────┘                             │
└──────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework with automatic API docs
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **SQLite**: Lightweight embedded database
- **Python 3.9+**

### Frontend
- **React 18**: UI component library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication

## 📁 Project Structure

```
dec25_intern_C_security/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # API routes (TO DO)
│   │   │   ├── routes_phishing.py
│   │   │   ├── routes_voice.py
│   │   │   └── routes_health.py
│   │   ├── core/                # Configuration ✅
│   │   │   ├── config.py
│   │   │   └── logging_config.py
│   │   ├── db/                  # Database layer (TO DO)
│   │   │   ├── session.py       # Setup database connection
│   │   │   ├── crud_email.py    # Implement CRUD operations
│   │   │   └── crud_voice.py    # Implement CRUD operations
│   │   ├── ml/                  # ML models (TO DO)
│   │   │   ├── phishing_model.py    # Implement detection logic
│   │   │   └── deepfake_model.py    # Implement audio analysis
│   │   ├── models/              # SQLAlchemy models (TO DO)
│   │   │   ├── email_scan.py    # Define EmailScan model
│   │   │   └── voice_scan.py    # Define VoiceScan model
│   │   ├── schemas/             # Pydantic schemas ✅
│   │   │   ├── common.py
│   │   │   ├── phishing.py
│   │   │   └── voice.py
│   │   ├── services/            # Business logic (TO DO)
│   │   │   ├── phishing_service.py
│   │   │   ├── voice_service.py
│   │   │   └── explanation_service.py
│   │   ├── utils/               # Utilities (TO DO)
│   │   │   ├── text_utils.py
│   │   │   └── audio_utils.py
│   │   └── main.py              # FastAPI app (TO DO)
│   ├── tests/                   # Tests (TO DO)
│   ├── requirements.txt         # Python dependencies ✅
│   └── Dockerfile               # Docker config ✅
│
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client ✅
│   │   │   ├── client.ts
│   │   │   ├── phishingApi.ts
│   │   │   └── voiceApi.ts
│   │   ├── components/          # UI components
│   │   │   ├── layout/          # Layout ✅
│   │   │   │   ├── Navbar.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── common/          # Common components ✅
│   │   │   │   ├── RiskBadge.tsx
│   │   │   │   ├── Loader.tsx
│   │   │   │   └── ErrorAlert.tsx
│   │   │   ├── phishing/        # Phishing components ✅
│   │   │   │   ├── EmailForm.tsx
│   │   │   │   └── PhishingResultCard.tsx
│   │   │   └── voice/           # Voice components (TO DO)
│   │   │       ├── AudioUpload.tsx
│   │   │       └── VoiceResultCard.tsx
│   │   ├── hooks/               # Custom hooks
│   │   │   ├── usePhishingScan.ts    # ✅ Complete
│   │   │   └── useVoiceScan.ts       # TO DO
│   │   ├── pages/               # Pages ✅
│   │   │   ├── PhishingPage.tsx
│   │   │   ├── VoicePage.tsx
│   │   │   └── HistoryPage.tsx
│   │   ├── router/              # Routing ✅
│   │   │   └── index.tsx
│   │   ├── styles/              # Styles ✅
│   │   │   └── global.css
│   │   ├── App.tsx              # Root component ✅
│   │   └── main.tsx             # Entry point ✅
│   ├── index.html               # HTML template ✅
│   ├── package.json             # Dependencies ✅
│   └── vite.config.ts           # Vite config ✅
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- Node.js 16 or higher
- npm or yarn

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend (once main.py is completed):
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The app will be available at: http://localhost:3000

## 📝 How the System Works

### Phishing Detection Flow
1. User enters email details (subject, sender, body, URLs) in the frontend form
2. Frontend sends POST request to `/api/v1/phishing/analyze`
3. Backend service:
   - Calls ML model to analyze email content
   - Calculates risk score (0-100)
   - Determines risk level (low/medium/high)
   - Generates human-readable explanation
   - Saves scan to database
4. Frontend displays results with color-coded risk badge

### Voice Analysis Flow
1. User uploads audio file in the frontend
2. Frontend sends multipart/form-data to `/api/v1/voice/analyze`
3. Backend service:
   - Processes audio file
   - Calls ML model to detect deepfake
   - Calculates deepfake score (0-100)
   - Determines risk level
   - Generates explanation
   - Saves scan to database
4. Frontend displays results with risk assessment

### Database Schema

**email_scans table:**
- id (primary key)
- subject
- sender
- body_hash
- risk_score (0-100)
- risk_level (low/medium/high)
- explanation
- highlights (JSON array)
- created_at

**voice_scans table:**
- id (primary key)
- file_hash
- file_path
- deepfake_score (0-100)
- risk_level (low/medium/high)
- explanation
- created_at

## 👥 Team Collaboration Guide

### Dividing Work Among 4 Team Members

**Person 1: Backend Database & Models**
- Implement database models (email_scan.py, voice_scan.py)
- Implement CRUD operations (crud_email.py, crud_voice.py)
- Set up database session (session.py)
- Implement ML models (phishing_model.py, deepfake_model.py)

**Person 2: Backend Services & API Routes**
- Implement services layer (phishing_service.py, voice_service.py, explanation_service.py)
- Implement API routes (routes_phishing.py, routes_voice.py, routes_health.py)
- Create FastAPI main.py setup

**Person 3: Frontend Forms & Components**
- Implement voice components (AudioUpload.tsx, VoiceResultCard.tsx)
- Implement voice hook (useVoiceScan.ts)

**Person 4: Integration & Testing**
- Connect frontend to backend APIs
- Write backend tests
- Write frontend tests
- End-to-end testing
- Help with integration issues

### Git Workflow

1. **Pull latest changes** before starting work:
```bash
git pull origin main
```

2. **Create a branch** for your feature:
```bash
git checkout -b feature/your-feature-name
```

3. **Commit your changes**:
```bash
git add .
git commit -m "Description of changes"
```

4. **Push to GitHub**:
```bash
git push origin feature/your-feature-name
```

5. **Create Pull Request** on GitHub for team review

### Avoiding Merge Conflicts
- Each person works on different files
- Communicate before editing shared files
- Pull latest changes frequently
- Commit small, focused changes

## 📚 Key Concepts

### CRUD Operations
CRUD = Create, Read, Update, Delete
- Functions that interact with the database
- Located in `backend/app/db/crud_*.py`
- Example: `create_email_scan()`, `get_email_scans()`

### Pydantic Schemas
- Define the structure of API requests and responses
- Provide automatic validation
- Located in `backend/app/schemas/`

### ML Models (Placeholder)
- Currently use simple heuristics
- Will be replaced with real trained models later
- Located in `backend/app/ml/`

### Risk Levels
- **Low**: score < 30 (green badge)
- **Medium**: 30 ≤ score < 70 (yellow badge)
- **High**: score ≥ 70 (red badge)

## 🔍 Testing the Application

### Test Backend API (once completed)
```bash
# Health check
curl http://localhost:8000/health

# Test phishing analysis
curl -X POST http://localhost:8000/api/v1/phishing/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Urgent: Verify your account",
    "body": "Click here to verify",
    "sender": "noreply@suspicious.com",
    "urls": ["http://suspicious.com"]
  }'
```

### Test Frontend
1. Open http://localhost:3000
2. Navigate to Phishing Detection page
3. Fill out the email form with test data:
   - Subject: "Urgent: Verify your account"
   - Sender: "noreply@suspicious.com"
   - Body: "Click here to verify your account immediately"
   - URLs: "http://suspicious.com/verify"
4. Click "Analyze Email"
5. Note: Backend must be running for results to display

## 📖 API Documentation
Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🎯 Next Steps

### Phase 1: Backend Foundation
1. **Implement Database Models**
   - Complete email_scan.py with SQLAlchemy model
   - Complete voice_scan.py with SQLAlchemy model
   - Set up database session in session.py

2. **Implement CRUD Operations**
   - Complete crud_email.py functions
   - Complete crud_voice.py functions

3. **Implement ML Models**
   - Complete phishing_model.py with detection logic
   - Complete deepfake_model.py with audio analysis

### Phase 2: Backend Services & API
4. **Complete Backend Services**
   - Implement phishing_service.py
   - Implement voice_service.py
   - Implement explanation_service.py

5. **Complete API Routes**
   - Implement routes_phishing.py
   - Implement routes_voice.py
   - Implement routes_health.py

6. **Setup FastAPI App**
   - Complete main.py
   - Register routes
   - Configure CORS

### Phase 3: Frontend Components
7. **Complete Frontend Forms**
   - ~~Build EmailForm component~~ ✅ DONE
   - ~~Build PhishingResultCard component~~ ✅ DONE
   - ~~Create usePhishingScan hook~~ ✅ DONE
   - Build AudioUpload component
   - Build VoiceResultCard component
   - Create useVoiceScan hook

### Phase 4: Integration & Testing
9. **Integration Testing**
   - Connect frontend to backend
   - Test end-to-end flows
   - Fix any issues

## 🐛 Troubleshooting

### Backend Issues
- **Import errors**: Make sure you're in the virtual environment
- **Database errors**: Delete the SQLite file and restart
- **Port already in use**: Change port in uvicorn command

### Frontend Issues
- **Module not found**: Run `npm install` again
- **Port 3000 in use**: Change port in vite.config.ts
- **API connection failed**: Make sure backend is running on port 8000

## Team Communication

- Keep each other updated on progress
- Ask for help when stuck
- Review each other's code
- Test integration points together


---

**Team C - December 2025 Internship**


