from datetime import datetime, timezone
from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    student_id = db.Column(db.String(80), unique=True, nullable=True)
    guardian_phone = db.Column(db.String(40), nullable=True)
    guardian_email = db.Column(db.String(160), nullable=True)
    role = db.Column(db.String(20), default="student", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    topic = db.Column(db.String(120), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    total = db.Column(db.Integer, nullable=False)
    correct = db.Column(db.Integer, nullable=False)
    wrong = db.Column(db.Integer, nullable=False)
    skipped = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(5), nullable=False)
    remark = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(80), nullable=False)
    topic = db.Column(db.String(120), nullable=False)
    question = db.Column(db.Text, nullable=False)
    correct = db.Column(db.Text, nullable=False)
    options_json = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(80), default="local")
