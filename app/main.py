from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal
from app import models, schemas
from app import auth
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app import enrichment
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Response

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # abhi ke liye sab allow, baad mein specific origins rakhenge
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
security = HTTPBearer()


def get_current_tenant(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = auth.decode_access_token(token)
        return payload["tenant_id"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
def send_confirmation_notification(widget_title: str, data: dict):
    raise ConnectionError("Simulated email service failure")
    print(f"[EMAIL SENT] New submission on '{widget_title}': {data}")

@app.get("/")
def home():
    return {"message": "Widget platform is running!"}


@app.post("/widgets", response_model=schemas.WidgetResponse)
def create_widget(
    widget: schemas.WidgetCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
):
    new_widget = models.Widget(
        tenant_id=tenant_id,
        widget_type=widget.widget_type,
        title=widget.title,
        description=widget.description,
        fields=widget.fields,
        button_text=widget.button_text,
    )
    db.add(new_widget)
    db.commit()
    db.refresh(new_widget)
    return new_widget


@app.get("/widgets", response_model=list[schemas.WidgetResponse])
def list_widgets(db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    return db.query(models.Widget).filter(models.Widget.tenant_id == tenant_id).all()


@app.get("/widgets/{widget_id}", response_model=schemas.WidgetResponse)
def get_widget(widget_id: str, db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    widget = db.query(models.Widget).filter(
        models.Widget.id == widget_id,
        models.Widget.tenant_id == tenant_id
    ).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget

@app.post("/auth/signup", response_model=schemas.Token)
def signup(tenant: schemas.TenantSignup, db: Session = Depends(get_db)):
    existing = db.query(models.Tenant).filter(models.Tenant.email == tenant.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_tenant = models.Tenant(
        email=tenant.email,
        password_hash=auth.hash_password(tenant.password),
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    token = auth.create_access_token({"tenant_id": new_tenant.id})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/login", response_model=schemas.Token)
def login(tenant: schemas.TenantLogin, db: Session = Depends(get_db)):
    existing = db.query(models.Tenant).filter(models.Tenant.email == tenant.email).first()
    if not existing or not auth.verify_password(tenant.password, existing.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth.create_access_token({"tenant_id": existing.id})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/submissions", response_model=schemas.SubmissionResponse)
@limiter.limit("5/minute")
@app.post("/submissions", response_model=schemas.SubmissionResponse)
@limiter.limit("5/minute")
def create_submission(request: Request, submission: schemas.SubmissionCreate, db: Session = Depends(get_db)):
    widget = db.query(models.Widget).filter(models.Widget.id == submission.widget_id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    is_spam = bool(submission.website)
    visitor_ip = request.client.host
    geo_data = enrichment.enrich_ip(visitor_ip)

    new_submission = models.Submission(
        widget_id=widget.id,
        tenant_id=widget.tenant_id,
        data=submission.data,
        ip_address=visitor_ip,
        country=geo_data.get("country"),
        city=geo_data.get("city"),
        is_spam=is_spam,
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    try:
        send_confirmation_notification(widget.title, submission.data)
    except Exception as e:
        print(f"Side effect failed (submission still saved): {e}")

    return new_submission

@app.get("/widgets/{widget_id}/submissions", response_model=list[schemas.SubmissionResponse])
def get_widget_submissions(
    widget_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
):
    widget = db.query(models.Widget).filter(
        models.Widget.id == widget_id,
        models.Widget.tenant_id == tenant_id
    ).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    submissions = db.query(models.Submission).filter(
        models.Submission.widget_id == widget_id
    ).all()
    return submissions


@app.get("/widgets/{widget_id}/stats")
def get_widget_stats(
    widget_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
):
    widget = db.query(models.Widget).filter(
        models.Widget.id == widget_id,
        models.Widget.tenant_id == tenant_id
    ).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    submissions = db.query(models.Submission).filter(
        models.Submission.widget_id == widget_id
    ).all()

    total = len(submissions)
    spam_count = sum(1 for s in submissions if s.is_spam)
    countries = {}
    for s in submissions:
        if s.country:
            countries[s.country] = countries.get(s.country, 0) + 1

    return {
        "total_submissions": total,
        "spam_count": spam_count,
        "genuine_count": total - spam_count,
        "by_country": countries,
    }

@app.get("/widgets/{widget_id}/config")
def get_widget_config(widget_id: str, db: Session = Depends(get_db)):
    widget = db.query(models.Widget).filter(
        models.Widget.id == widget_id,
        models.Widget.is_active == True
    ).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    response_data = {
        "id": widget.id,
        "widget_type": widget.widget_type,
        "title": widget.title,
        "description": widget.description,
        "fields": widget.fields,
        "button_text": widget.button_text,
        "version": widget.version,
    }
    return JSONResponse(
        content=response_data,
        headers={"Cache-Control": "public, max-age=60"}
    )

@app.put("/widgets/{widget_id}", response_model=schemas.WidgetResponse)
def update_widget(
    widget_id: str,
    widget_update: schemas.WidgetCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
):
    widget = db.query(models.Widget).filter(
        models.Widget.id == widget_id,
        models.Widget.tenant_id == tenant_id
    ).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    widget.widget_type = widget_update.widget_type
    widget.title = widget_update.title
    widget.description = widget_update.description
    widget.fields = widget_update.fields
    widget.button_text = widget_update.button_text
    widget.version += 1  # cache-busting ke liye version badha diya

    db.commit()
    db.refresh(widget)
    return widget


@app.delete("/widgets/{widget_id}")
def delete_widget(
    widget_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
):
    widget = db.query(models.Widget).filter(
        models.Widget.id == widget_id,
        models.Widget.tenant_id == tenant_id
    ).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    db.delete(widget)
    db.commit()
    return {"message": "Widget deleted successfully"}

@app.get("/widgets/{widget_id}/embed")
def get_embed_snippet(
    widget_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
):
    widget = db.query(models.Widget).filter(
        models.Widget.id == widget_id,
        models.Widget.tenant_id == tenant_id
    ).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    snippet = f'<script src="http://127.0.0.1:8000/widget.js?id={widget.id}"></script>'
    return {"embed_code": snippet}

@app.get("/widget.js")
def serve_widget_script():
    js_code = """
(function() {
    const script = document.currentScript;
    const widgetId = new URL(script.src).searchParams.get('id');
    const apiBase = new URL(script.src).origin;

    fetch(apiBase + '/widgets/' + widgetId + '/config')
        .then(res => res.json())
        .then(config => renderWidget(config));

    function renderWidget(config) {
        const wrapper = document.createElement('div');
        wrapper.style.cssText = 'display:flex; justify-content:center; font-family: Inter, sans-serif;';

        const container = document.createElement('div');
        container.style.cssText = 'border:1px solid #D8DEDC; padding:24px; border-radius:12px; max-width:340px; width:100%; background:white; box-shadow:0 4px 16px rgba(0,0,0,0.06);';

        let html = '<h3 style="font-family: \\'Space Grotesk\\', sans-serif; font-size:20px; margin:0 0 6px; color:#0B1220;">' + config.title + '</h3>';
        if (config.description) html += '<p style="color:#6B7280; font-size:14px; margin:0 0 16px;">' + config.description + '</p>';

        config.fields.forEach(field => {
            html += '<input type="text" data-field="' + field + '" placeholder="' + field.charAt(0).toUpperCase() + field.slice(1) + '" style="display:block; margin-bottom:12px; padding:10px 12px; width:100%; box-sizing:border-box; border:1px solid #D8DEDC; border-radius:6px; font-family:inherit; font-size:14px;">';
        });

        html += '<button id="widget-submit-btn" style="padding:12px 20px; background:#0EA5A5; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:600; font-size:14px; width:100%;">' + config.button_text + '</button>';
        html += '<p id="widget-result" style="font-size:13px; margin-top:10px; color:#0B7A7A;"></p>';

        container.innerHTML = html;
        wrapper.appendChild(container);
        script.parentNode.insertBefore(wrapper, script);

        container.querySelector('#widget-submit-btn').addEventListener('click', function() {
            const data = {};
            container.querySelectorAll('[data-field]').forEach(input => {
                data[input.getAttribute('data-field')] = input.value;
            });

            fetch(apiBase + '/submissions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ widget_id: widgetId, data: data })
            })
            .then(res => res.json())
            .then(result => {
                container.querySelector('#widget-result').innerText = 'Thank you! Submitted successfully.';
            })
            .catch(err => {
                container.querySelector('#widget-result').innerText = 'Something went wrong.';
            });
        });
    }
})();
"""
    return Response(content=js_code, media_type="application/javascript", headers={"Cache-Control": "public, max-age=3600"})