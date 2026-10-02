from functools import wraps
from flask import request, jsonify
import jwt, os
from .models import User

def make_token(user):
    return jwt.encode({"uid": user.id, "role": user.role}, os.getenv("SECRET_KEY", "dev-change-me"), algorithm="HS256")

def current_user():
    h = request.headers.get("Authorization", "")
    if not h.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(h[7:], os.getenv("SECRET_KEY", "dev-change-me"), algorithms=["HS256"])
        return User.query.get(payload["uid"])
    except Exception:
        return None

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        return fn(user, *args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(user, *args, **kwargs)
    return wrapper
