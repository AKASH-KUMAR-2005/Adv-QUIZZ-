# QuizMaster Pro — Full Stack Advanced

## Stack
- Python Flask REST API
- SQLite database via SQLAlchemy
- JWT authentication
- Werkzeug password hashing
- Open Trivia DB for live questions
- Local academic question bank for technical topics
- Browser OCR can be connected to `/api/scan/match`
- Responsive frontend

## Run
1. Python 3.11+ recommended.
2. `python -m venv .venv`
3. Activate the virtual environment.
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and change SECRET_KEY.
6. `python run.py`
7. Open `http://127.0.0.1:5000/`

For a deployment, serve the frontend through Flask/static or configure the frontend API base URL.

## Demo admin
Username: admin
Password: admin123

Change the password before production.

## Database
SQLite is created automatically as `quizmaster.db`.

Tables:
- users
- attempts
- questions

## Security
Passwords are hashed. JWTs are used for API authorization. Admin routes only expose name, student ID, subject/topic, marks, percentage and date. Guardian contact and password data are not returned by the admin overview.

## Guardian notifications
The backend stores optional guardian contact details. Actual WhatsApp/SMS/email delivery requires a provider such as Twilio/WhatsApp Business or an email service and credentials. The browser must not contain provider secrets.

## OCR / AI
The frontend can use Tesseract.js to extract text. `/api/scan/match` matches scanned concepts against the academic bank. For exact question generation from arbitrary notes, add a server-side AI provider; never expose an AI secret in JavaScript.
