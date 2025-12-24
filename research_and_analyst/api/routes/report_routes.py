from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from research_and_analyst.database.db_config import SessionLocal, User, hash_password, verify_password
from research_and_analyst.api.services.report_service import ReportService
import os
import hmac
import hashlib
import base64
import secrets

router = APIRouter()
SESSIONS = {}  # Keep for backward compatibility with non-HF deployments

# Detect if running on Hugging Face Spaces (HTTPS environment)
IS_HF_SPACE = os.getenv("SPACE_ID") is not None or os.getenv("SYSTEM") == "spaces"

# Secret key for signed cookies (use env var or generate random for HF Spaces)
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", secrets.token_hex(32))

def sign_cookie_value(value: str) -> str:
    """Sign a cookie value using HMAC-SHA256"""
    signature = hmac.new(
        SECRET_KEY.encode(),
        value.encode(),
        hashlib.sha256
    ).hexdigest()
    # Return base64 encoded "value.signature"
    signed = f"{value}.{signature}"
    return base64.b64encode(signed.encode()).decode()

def verify_signed_cookie(signed_value: str) -> str:
    """Verify and extract value from signed cookie"""
    try:
        decoded = base64.b64decode(signed_value.encode()).decode()
        value, signature = decoded.rsplit(".", 1)
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            value.encode(),
            hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(signature, expected_sig):
            return value
    except Exception:
        pass
    return None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------ AUTH ROUTES ------------------ #

@router.get("/", response_class=HTMLResponse)
async def show_login(request: Request):
    return request.app.templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()

    if user and verify_password(password, user.password):
        response = RedirectResponse(url="/dashboard", status_code=302)
        
        if IS_HF_SPACE:
            # Use signed cookies for HF Spaces (stateless, works across instances)
            signed_username = sign_cookie_value(username)
            response.set_cookie(
                key="user_session", 
                value=signed_username,
                path="/",
                max_age=3600,  # 1 hour
                httponly=True,
                samesite="lax"
            )
        else:
            # Use in-memory sessions for local/Azure deployment
            session_id = f"{username}_session"
            SESSIONS[session_id] = username
            response.set_cookie(key="session_id", value=session_id)
        
        return response

    return request.app.templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid username or password"},
    )

@router.get("/signup", response_class=HTMLResponse)
async def show_signup(request: Request):
    return request.app.templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup", response_class=HTMLResponse)
async def signup(request: Request, username: str = Form(...), password: str = Form(...)):
    db = next(get_db())
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return request.app.templates.TemplateResponse(
            "signup.html", {"request": request, "error": "Username already exists"}
        )

    hashed_pw = hash_password(password)
    new_user = User(username=username, password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/", status_code=302)

# ------------------ REPORT ROUTES ------------------ #

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    username = None
    
    if IS_HF_SPACE:
        # Verify signed cookie for HF Spaces
        signed_cookie = request.cookies.get("user_session")
        if signed_cookie:
            username = verify_signed_cookie(signed_cookie)
    else:
        # Use in-memory session for local/Azure
        session_id = request.cookies.get("session_id")
        if session_id and session_id in SESSIONS:
            username = SESSIONS[session_id]
    
    if not username:
        return RedirectResponse(url="/")
    
    return request.app.templates.TemplateResponse("dashboard.html", {"request": request, "user": username})

@router.post("/generate_report", response_class=HTMLResponse)
async def generate_report(request: Request, topic: str = Form(...)):
    service = ReportService()
    result = service.start_report_generation(topic, 3)
    thread_id = result["thread_id"] 

    return request.app.templates.TemplateResponse(
        "report_progress.html",
        {
            "request": request,
            "topic": topic,
            "feedback": "",
            "thread_id": thread_id,
        },
    )

@router.post("/submit_feedback", response_class=HTMLResponse)
async def submit_feedback(request: Request, topic: str = Form(...), feedback: str = Form(...), thread_id: str = Form(...)):
    service = ReportService()
    service.submit_feedback(thread_id, feedback)

    # Get latest report status
    result = service.get_report_status(thread_id)
    doc_path = result.get("docx_path")
    pdf_path = result.get("pdf_path")

    return request.app.templates.TemplateResponse(
        "report_progress.html",
        {
            "request": request,
            "topic": topic,
            "feedback": feedback,
            "doc_path": doc_path,
            "pdf_path": pdf_path,
            "thread_id": thread_id,
        },
    )

@router.get("/download/{file_name}", response_class=HTMLResponse)
async def download_report(file_name: str):
    service = ReportService()
    file_response = service.download_file(file_name)
    if file_response:
        return file_response
    return {"error": f"File {file_name} not found"}
