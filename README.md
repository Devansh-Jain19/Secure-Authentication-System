# 🛡️ SentinelAuth - Secure Authentication System

A production-grade full-stack authentication system built with **Python (Flask, PyJWT, bcrypt)**, **PostgreSQL / SQLAlchemy**, and a responsive glassmorphic frontend.

---

## 🚀 Features

- **Password Hashing & Encryption**: `bcrypt` with dynamic 12-round salt.
- **JWT Authentication & Rotation**: RFC 7519 compliant JSON Web Tokens (`HS256`) with short-lived Access Tokens (2 hours) and long-lived Refresh Tokens (7 days).
- **Protected Endpoints**: `@token_required` decorator verifying signatures, claims, and token expiration.
- **Role-Based Access Control (RBAC)**: Support for `member` and `admin` roles.
- **Audit & Security Logging**: Tracks registration, logins, failed login attempts, token refreshes, and logouts with IP address and user-agent metadata.
- **Database Support**: PostgreSQL integration with automatic failover to SQLite.
- **Aesthetic Frontend**: Responsive dark glassmorphism UI with real-time server health checks, interactive JWT inspector, token verification, and administrative audit log viewer.

---

## 📁 Project Architecture

```
Ai-Chatbot/
├── backend/
│   ├── app.py             # Flask application & REST API routes
│   ├── config.py          # Environment & database configurations
│   ├── models.py          # SQLAlchemy User & SessionLog models
│   ├── security.py        # bcrypt & PyJWT token utilities
│   ├── requirements.txt   # Backend Python dependencies
│   └── .env               # Environment configuration
├── frontend/
│   ├── index.html         # Main dashboard and login/registration UI
│   ├── css/
│   │   └── style.css      # Modern dark-mode glassmorphic styles
│   ├── js/
│   │   └── app.js         # Frontend authentication & JWT state management
│   └── serve.py           # Python HTTP server for frontend (port 3000)
├── test_flow.py           # Automated end-to-end authentication test suite
└── README.md              # Project documentation
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+
- (Optional) PostgreSQL server

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Run the Backend API (Port 5000)
```bash
cd backend
python app.py
```
Backend health check is accessible at `http://localhost:5000/api/health`.

### 4. Run the Frontend Client (Port 3000)
```bash
cd frontend
python serve.py
```
Open your browser and navigate to **`http://localhost:3000`**.

---

## 🧪 Automated Testing

Run the included end-to-end verification script:
```bash
python test_flow.py
```
This tests:
1. Health check & database connection
2. Secure user login & bcrypt verification
3. Protected endpoint access via `Bearer <JWT>`
4. Refresh token rotation
5. Admin audit log inspection

---

## 🔒 API Endpoints

| Method | Endpoint | Description | Protected |
|---|---|---|---|
| `GET` | `/api/health` | Health & database status | No |
| `POST` | `/api/auth/register` | Register new user with encrypted password | No |
| `POST` | `/api/auth/login` | Authenticate and issue JWT tokens | No |
| `POST` | `/api/auth/refresh` | Rotate access token using refresh token | No |
| `GET` | `/api/auth/profile` | Retrieve authenticated profile | **Yes (Bearer JWT)** |
| `POST` | `/api/auth/logout` | End session & log event | **Yes (Bearer JWT)** |
| `GET` | `/api/admin/users` | List users and view audit trail | **Yes (Admin Only)** |