import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///quizmaster.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    from .routes import api
    app.register_blueprint(api, url_prefix="/api")

    with app.app_context():
        from .models import User, Attempt, Question
        db.create_all()
        seed_admin()
    return app

def seed_admin():
    from .models import User
    from werkzeug.security import generate_password_hash
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin123")
    if not User.query.filter_by(username=username).first():
        db.session.add(User(
            username=username,
            password_hash=generate_password_hash(password),
            role="admin",
            name="Administrator"
        ))
        db.session.commit()
