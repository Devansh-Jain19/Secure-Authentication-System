import os
import re
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from models import init_db, get_db, User, SessionLog, active_db_engine
from security import hash_password, verify_password, generate_tokens, decode_token, token_required

app = Flask(__name__)
app.config.from_object(Config)

# Enable Cross-Origin Resource Sharing with support for modern frontend ports
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Initialize database schema
init_db()

def log_session_event(db, user_id, username, event_type):
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "127.0.0.1"
        ua = request.headers.get("User-Agent", "Unknown Browser")
        log_entry = SessionLog(
            user_id=user_id,
            username=username,
            event_type=event_type,
            ip_address=ip[:50],
            user_agent=ua[:255]
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error logging session event: {e}")

@app.teardown_appcontext
def remove_session(exception=None):
    from models import SessionLocal
    if SessionLocal:
        SessionLocal.remove()

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "service": "Secure Authentication API",
        "version": "1.0.0",
        "db_engine": active_db_engine,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "member")
    if role not in ["member", "admin"]:
        role = "member"

    # Input validation
    if not username or len(username) < 3 or len(username) > 30:
        return jsonify({"status": "error", "message": "Username must be between 3 and 30 characters."}), 400
    
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not email or not re.match(email_regex, email):
        return jsonify({"status": "error", "message": "Please provide a valid email address."}), 400

    if not password or len(password) < 8:
        return jsonify({"status": "error", "message": "Password must be at least 8 characters long."}), 400

    db = get_db()
    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        if existing_user.username == username:
            return jsonify({"status": "error", "message": "Username is already registered."}), 409
        return jsonify({"status": "error", "message": "Email is already registered."}), 409

    try:
        pw_hash = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=pw_hash,
            role=role,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        log_session_event(db, new_user.id, new_user.username, "REGISTER")

        # Automatically produce JWT session upon successful registration
        tokens = generate_tokens(new_user.id, new_user.username, new_user.role)
        return jsonify({
            "status": "success",
            "message": "User account created successfully with encrypted credentials.",
            "user": new_user.to_dict(),
            "tokens": tokens
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": f"Failed to register user: {str(e)}"}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = (data.get("identifier") or "").strip() # can be email or username
    password = data.get("password") or ""

    if not identifier or not password:
        return jsonify({"status": "error", "message": "Identifier and password are required."}), 400

    db = get_db()
    user = db.query(User).filter((User.username == identifier) | (User.email == identifier.lower())).first()

    if not user:
        return jsonify({"status": "error", "message": "Invalid username/email or password."}), 401

    if not user.is_active:
        return jsonify({"status": "error", "message": "Account has been deactivated. Please contact support."}), 403

    if not verify_password(password, user.password_hash):
        log_session_event(db, user.id, user.username, "FAILED_LOGIN")
        return jsonify({"status": "error", "message": "Invalid username/email or password."}), 401

    try:
        user.last_login = datetime.datetime.utcnow()
        db.commit()

        log_session_event(db, user.id, user.username, "LOGIN")
        tokens = generate_tokens(user.id, user.username, user.role)

        return jsonify({
            "status": "success",
            "message": "Authentication successful.",
            "user": user.to_dict(),
            "tokens": tokens
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": f"Login processing error: {str(e)}"}), 500

@app.route("/api/auth/refresh", methods=["POST"])
def refresh():
    data = request.get_json() or {}
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"status": "error", "message": "Refresh token is required."}), 400

    payload, err = decode_token(refresh_token)
    if err or not payload:
        return jsonify({"status": "error", "message": err}), 401

    if payload.get("type") != "refresh":
        return jsonify({"status": "error", "message": "Supplied token is not a refresh token."}), 401

    user_id = int(payload.get("sub"))
    db = get_db()
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return jsonify({"status": "error", "message": "User session no longer valid."}), 401

    log_session_event(db, user.id, user.username, "REFRESH")
    tokens = generate_tokens(user.id, user.username, user.role)
    return jsonify({
        "status": "success",
        "message": "Access token refreshed successfully.",
        "tokens": tokens
    }), 200

@app.route("/api/auth/profile", methods=["GET"])
@token_required
def profile():
    current_user_claims = request.current_user
    db = get_db()
    user = db.query(User).filter(User.id == int(current_user_claims.get("sub"))).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found."}), 404

    return jsonify({
        "status": "success",
        "user": user.to_dict(),
        "token_claims": current_user_claims
    }), 200

@app.route("/api/auth/logout", methods=["POST"])
@token_required
def logout():
    current_user_claims = request.current_user
    db = get_db()
    log_session_event(db, int(current_user_claims.get("sub")), current_user_claims.get("username"), "LOGOUT")
    return jsonify({
        "status": "success",
        "message": "User successfully logged out. Session closed."
    }), 200

@app.route("/api/admin/users", methods=["GET"])
@token_required
def get_all_users():
    current_user_claims = request.current_user
    if current_user_claims.get("role") != "admin":
        return jsonify({"status": "error", "message": "Access restricted to administrators only."}), 403

    db = get_db()
    users = db.query(User).order_by(User.id.desc()).all()
    session_logs = db.query(SessionLog).order_by(SessionLog.id.desc()).limit(20).all()

    return jsonify({
        "status": "success",
        "users": [u.to_dict() for u in users],
        "audit_logs": [log.to_dict() for log in session_logs]
    }), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print(f"\n=======================================================")
    print(f"[SECURE AUTH] Backend running on port {port}")
    print(f"[SECURE AUTH] API Health URL: http://localhost:{port}/api/health")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
