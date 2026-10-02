import json, os, random, requests
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Attempt
from .auth import make_token, login_required, admin_required

api = Blueprint("api", __name__)

LOCAL = [
 {"subject":"C","topic":"pointers","question":"Which operator obtains the address of a variable in C?","correct":"&","options":["*","&","%","->"]},
 {"subject":"C++","topic":"inheritance","question":"Which feature allows a C++ class to derive from another class?","correct":"Inheritance","options":["Compilation","Inheritance","Casting","Tokenization"]},
 {"subject":"Java","topic":"inheritance","question":"Which keyword creates a subclass relationship in Java?","correct":"extends","options":["implements","extends","inherits","super"]},
 {"subject":"Python","topic":"data types","question":"Which Python collection is immutable?","correct":"tuple","options":["list","tuple","set","dictionary"]},
 {"subject":"DBMS","topic":"sql","question":"Which SQL command retrieves rows from a table?","correct":"SELECT","options":["GET","SELECT","READ","FETCH"]},
 {"subject":"Operating System","topic":"memory","question":"Which technique divides memory into fixed-size pages?","correct":"Paging","options":["Spooling","Paging","Caching","Segmentation"]},
 {"subject":"Computer Networks","topic":"dns","question":"Which protocol translates domain names to IP addresses?","correct":"DNS","options":["DHCP","DNS","FTP","SMTP"]},
 {"subject":"Computer Architecture","topic":"alu","question":"Which unit performs arithmetic and logical operations?","correct":"ALU","options":["CU","ALU","Cache","Register"]},
 {"subject":"Data Structures","topic":"stack","question":"Which principle does a stack follow?","correct":"LIFO","options":["FIFO","LIFO","Priority","Random"]},
 {"subject":"Web Technology","topic":"html","question":"Which HTML element creates the largest heading?","correct":"h1","options":["h6","head","h1","header"]},
]

def grade(p):
    if p >= 90: return "A+", "Outstanding performance!"
    if p >= 80: return "A", "Excellent work!"
    if p >= 70: return "B", "Good job — keep improving."
    if p >= 60: return "C", "Good attempt — revise weak areas."
    if p >= 50: return "D", "Keep practicing."
    return "F", "Review the study material and try again."

@api.get("/health")
def health():
    return jsonify({"ok": True, "service": "QuizMaster Pro API"})

@api.post("/auth/student/register")
def register_student():
    d = request.json or {}
    name, sid, password = d.get("name","").strip(), d.get("student_id","").strip(), d.get("password","")
    if not name or not sid or not password:
        return jsonify({"error":"Name, student ID and password are required"}), 400
    if User.query.filter((User.student_id == sid) | (User.username == sid)).first():
        return jsonify({"error":"Student ID already exists"}), 409
    u = User(username=sid, student_id=sid, name=name,
             guardian_phone=d.get("guardian_phone"),
             guardian_email=d.get("guardian_email"),
             password_hash=generate_password_hash(password), role="student")
    db.session.add(u); db.session.commit()
    return jsonify({"token":make_token(u),"user":{"id":u.id,"name":u.name,"student_id":u.student_id,"role":u.role}})

@api.post("/auth/login")
def login():
    d = request.json or {}
    u = User.query.filter_by(username=d.get("username","")).first()
    if not u or not check_password_hash(u.password_hash, d.get("password","")):
        return jsonify({"error":"Invalid credentials"}), 401
    return jsonify({"token":make_token(u),"user":{"id":u.id,"name":u.name,"student_id":u.student_id,"role":u.role}})

@api.get("/me")
@login_required
def me(user):
    return jsonify({"id":user.id,"name":user.name,"student_id":user.student_id,"role":user.role,
                    "guardian_phone":user.guardian_phone,"guardian_email":user.guardian_email})

@api.put("/me/guardian")
@login_required
def guardian(user):
    d=request.json or {}
    user.guardian_phone=d.get("guardian_phone")
    user.guardian_email=d.get("guardian_email")
    db.session.commit()
    return jsonify({"ok":True})

@api.get("/questions")
@login_required
def questions(user):
    amount=min(max(int(request.args.get("amount",20)),1),50)
    difficulty=request.args.get("difficulty","medium")
    category=request.args.get("category","computer")
    topic=request.args.get("topic","")
    result=[]
    try:
        params={"amount":amount,"difficulty":difficulty,"type":"multiple","encode":"url3986"}
        if category=="computer": params["category"]=18
        r=requests.get(os.getenv("OPEN_TRIVIA_API","https://opentdb.com/api.php"),params=params,timeout=8)
        data=r.json()
        if data.get("response_code")==0:
            from urllib.parse import unquote
            for q in data.get("results",[]):
                opts=[unquote(q["correct_answer"])] + [unquote(x) for x in q["incorrect_answers"]]
                random.shuffle(opts)
                result.append({"question":unquote(q["question"]),"correct":unquote(q["correct_answer"]),"options":opts,"topic":topic or "general"})
    except Exception:
        pass
    # Technical local bank fills the gap
    matches=[x for x in LOCAL if not topic or topic.lower() in (x["topic"]+" "+x["subject"]).lower()]
    pool=(matches or LOCAL)[:]
    random.shuffle(pool)
    for x in pool:
        if len(result)>=amount: break
        result.append({**x,"options":random.sample(x["options"],len(x["options"]))})
    random.shuffle(result)
    return jsonify({"questions":result[:amount],"source":"OpenTDB + local academic bank"})

@api.post("/attempts")
@login_required
def save_attempt(user):
    d=request.json or {}
    total=int(d.get("total",0)); correct=int(d.get("correct",0))
    if total<=0 or correct<0 or correct>total: return jsonify({"error":"Invalid score"}),400
    wrong=int(d.get("wrong",total-correct)); skipped=int(d.get("skipped",0))
    pct=round(correct/total*100,2); g,remark=grade(pct)
    a=Attempt(user_id=user.id,category=d.get("category",""),topic=d.get("topic",""),
              difficulty=d.get("difficulty","medium"),total=total,correct=correct,
              wrong=wrong,skipped=skipped,percentage=pct,grade=g,remark=remark)
    db.session.add(a); db.session.commit()
    return jsonify({"id":a.id,"percentage":pct,"grade":g,"remark":remark})

@api.get("/attempts/mine")
@login_required
def mine(user):
    rows=Attempt.query.filter_by(user_id=user.id).order_by(Attempt.created_at.desc()).all()
    return jsonify({"attempts":[serialize_attempt(x) for x in rows]})

def serialize_attempt(a):
    return {"id":a.id,"category":a.category,"topic":a.topic,"difficulty":a.difficulty,
            "total":a.total,"correct":a.correct,"wrong":a.wrong,"skipped":a.skipped,
            "percentage":a.percentage,"grade":a.grade,"remark":a.remark,
            "created_at":a.created_at.isoformat()}

@api.get("/admin/overview")
@admin_required
def admin_overview(user):
    rows=Attempt.query.order_by(Attempt.created_at.desc()).all()
    ids={a.user_id for a in rows}
    users=User.query.filter_by(role="student").all()
    return jsonify({"attempts":len(rows),"students":len(users),
                    "average":round(sum(a.percentage for a in rows)/len(rows),2) if rows else 0,
                    "results":[{"name":next((u.name for u in users if u.id==a.user_id),"Student"),
                               "student_id":next((u.student_id for u in users if u.id==a.user_id),""),
                               "subject":a.category,"topic":a.topic,"mark":f"{a.correct}/{a.total}",
                               "percentage":a.percentage,"date":a.created_at.isoformat()} for a in rows[:200]]})

@api.post("/scan/match")
@login_required
def scan_match(user):
    text=(request.json or {}).get("text","").lower()
    found=[]
    for x in LOCAL:
        if x["topic"].lower() in text or x["subject"].lower() in text:
            found.append(x)
    return jsonify({"matched_questions":found,"note":"Exact AI generation from arbitrary notes requires a secure server-side AI provider key."})
