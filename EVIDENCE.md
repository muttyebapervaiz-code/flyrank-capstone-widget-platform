EVIDENCE.md — Proof of Completion

Each item below was manually tested via the FastAPI /docs interactive interface and/or the live frontend at localhost:5501, with the backend running at localhost:8000.

Widget Management

Authenticated CRUD; unauthenticated requests rejected

POST /widgets without a token → 401 {"detail": "Not authenticated"}
POST /widgets with a valid token → 200, widget created with the logged-in tenant's ID

Multi-tenant isolation proven

Created two accounts (test@example.com, customer2@example.com)
Logged in as customer2 → GET /widgets → [] (empty list, even though customer 1's widget exists in the database)
Confirms one tenant cannot read another tenant's widgets
Public Submission API

Cross-origin submissions work

test-customer-site/index.html (served on localhost:5500) embeds a widget via <script src="http://127.0.0.1:8000/widget.js?id=...">
Form submitted from that page successfully POSTs to localhost:8000/submissions and returns 200 — confirms CORS + preflight handling works across origins

Malformed/oversized payloads rejected cleanly

POST /widgets with title: "", fields: [] → 422 with per-field validation messages ("String should have at least 1 character", "List should have at least 1 item")
POST /auth/signup with email: "not-an-email", password: "12345" → 422 with "value is not a valid email address" and "String should have at least 6 characters"
Abuse Protection

Rate limiting returns 429 under burst, service stays up

Sent 6 rapid POST /submissions requests to the same widget within one minute
Requests 1–5 → 200 OK
Request 6 → 429 {"error": "Rate limit exceeded: 5 per 1 minute"}
Server did not crash; a request after the window resets succeeds normally

Honeypot blocks spam

Submission without website field → is_spam: false
Submission with website: "http://spam-link.com" filled in → is_spam: true, submission still stored (visible in dashboard, flagged)
Enrichment & Safe Side Effects

Geo enrichment fallback chain

Local testing IP (127.0.0.1) returns simulated country: "Pakistan", city: "Islamabad" to demonstrate the enrichment path without requiring a public IP
enrichment.py implements provider A (ip-api.com) → provider B (ipapi.co) fallback; if both fail, submission stores with country: null, city: null instead of failing

Failing side effect does not block the main path

send_confirmation_notification() is made to raise ConnectionError on every call (simulating an email provider outage)
Server log shows: Side effect failed (submission still saved): Simulated email service failure
Response to the client is still 200 OK with the submission stored — confirms non-critical failures never break the main path
Widget Delivery

Config endpoint is public and cached

GET /widgets/{id}/config returns widget title/fields/button_text with no auth required
Response header: cache-control: public,max-age=60

Widget renders on a different origin

widget.js fetches config and renders a styled form via a single <script> tag
Verified working on localhost:5500 (test-customer-site) and inside the dashboard's live-preview panel (localhost:5501)
Dashboard

Owner sees only their own submissions and stats

GET /widgets/{id}/submissions and GET /widgets/{id}/stats both require auth and filter by tenant_id
Stats endpoint correctly aggregates: total submissions, spam vs genuine count, submissions grouped by country
Not yet covered
Automated pytest test suite (manual testing only, documented above)
Production deployment (runs locally per the capstone's realistic-scope guidance)