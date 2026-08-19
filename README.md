WidgetHive — Embeddable Widget & Lead-Capture Platform

FlyRank Backend Track Capstone — a platform that lets customers create embeddable widgets (signup forms, contact forms, popups) and install them on any website with a single <script> tag.

What it does
Customers sign up, log in, and create widgets through a dashboard
Each widget gets a public embed snippet (<script src="...">)
Visitors on any website can submit the widget's form — no login required
Submissions are validated, rate-limited, spam-checked, and geo-enriched before being stored
Owners view their submissions and stats on a live dashboard
Architecture
Widget Owner (authenticated)
  └─► Widget Management API ─► widgets table (tenant-isolated)

Customer Website (any origin)
  └─ <script src="widget.js?id=abc123">
       └─► GET /widget.js (cached, versioned)
       └─► GET /widgets/:id/config (public, cached, CORS)
       └─► renders form in the page

Website Visitor
  └─► POST /submissions (public, CORS)
        ├─ validate payload        → bad? 4xx, never 500
        ├─ rate limit + honeypot   → flood/bot? 429 / dropped
        ├─ geo enrich: provider A → fails → provider B → fails → store anyway
        ├─ store in submissions table
        └─ side effect: email  → fails? submission still succeeds

Widget Owner (authenticated)
  └─► Dashboard API ◄── submissions + stats
Tech stack
Backend: Python, FastAPI, SQLAlchemy, SQLite
Auth: JWT (python-jose), bcrypt password hashing (passlib)
Rate limiting: slowapi
Geo enrichment: ip-api.com (primary), ipapi.co (fallback)
Frontend: Vanilla HTML/CSS/JS (no framework)
Setup — run locally
1. Backend
bash
cd app_folder  # the folder containing this README
python -m venv venv
venv\Scripts\activate        # Windows
pip install fastapi uvicorn sqlalchemy python-dotenv passlib bcrypt "python-jose[cryptography]" python-multipart "pydantic[email]" httpx slowapi
uvicorn app.main:app --reload

Backend runs at http://127.0.0.1:8000. Interactive API docs at http://127.0.0.1:8000/docs.

2. Frontend dashboard

In a separate folder (e.g. widget-dashboard/ — contains index.html, dashboard.html, style.css, app.js):

bash
python -m http.server 5501

Open http://localhost:5501 in a browser.

3. Test customer site (simulates a second origin)

In test-customer-site/:

bash
python -m http.server 5500

Open http://localhost:5500 — this page embeds a widget via <script> tag, proving cross-origin delivery works.

API Endpoints
Method	Endpoint	Auth	Purpose
POST	/auth/signup	—	Create account
POST	/auth/login	—	Get JWT token
POST	/widgets	Yes	Create widget
GET	/widgets	Yes	List own widgets
GET	/widgets/{id}	Yes	Get one widget
PUT	/widgets/{id}	Yes	Update widget
DELETE	/widgets/{id}	Yes	Delete widget
GET	/widgets/{id}/config	—	Public config for widget.js
GET	/widgets/{id}/embed	Yes	Get embed snippet
GET	/widget.js	—	Public widget script
POST	/submissions	—	Visitor submits form (rate-limited)
GET	/widgets/{id}/submissions	Yes	Dashboard: view submissions
GET	/widgets/{id}/stats	Yes	Dashboard: analytics
Security & resilience features
Passwords hashed with bcrypt, never stored in plaintext
JWT-based authentication on all owner-facing endpoints
Multi-tenant isolation — every widget/submission query filters by tenant_id
Input validation via Pydantic (Field constraints, EmailStr) — malformed input returns clean 422 errors, never a crash
Rate limiting (5 requests/minute per IP) on the public submission endpoint — returns 429 on abuse
Honeypot spam field — bot-filled submissions are flagged is_spam: true
Geo enrichment fallback chain — if the primary IP-geolocation provider fails, a second provider is tried; if both fail, the submission still succeeds without location data
Fail-safe side effect — a simulated confirmation-email failure does not block the submission from being saved
CORS configured so the public endpoints (/widget.js, /widgets/{id}/config, /submissions) can be called from any origin
Limitations (honest notes)
Runs locally only (SQLite, no production deployment by default)
5 fixed widget types rather than a fully custom form builder — kept scope realistic per the capstone brief
Email side-effect is simulated (logs a failure to console) to demonstrate fail-safe design; a real email/webhook provider is not wired in
No automated CI pipeline; tests are run manually