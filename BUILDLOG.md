BUILDLOG.md — AI Usage Log

This capstone was built with Claude (Anthropic) as a step-by-step coding assistant/tutor. Per the capstone's AI-usage rule: this log records where AI helped, where it was wrong or needed correction, and what I changed or verified myself.

Where AI helped
Explaining unfamiliar concepts: virtual environments, PATH issues on Windows, JWT tokens, CORS, rate limiting, honeypot spam detection, fallback chains — I asked for plain-language explanations before writing any code, and re-explained concepts back in my own words during the build.
Generating boilerplate: FastAPI route structure, SQLAlchemy models, Pydantic schemas — written by AI, then I ran and tested every endpoint myself via /docs before moving to the next piece.
Debugging real errors: e.g. a bcrypt/passlib version incompatibility (AttributeError: module 'bcrypt' has no attribute '__about__'), a Windows python vs py PATH alias issue, duplicate function definitions causing route errors, and a Git merge conflict in .gitignore after creating the GitHub repo with README/gitignore/license pre-added. In each case I pasted the actual terminal error and the AI diagnosed the specific cause rather than guessing.
Frontend design: AI proposed a design token system (color palette, typography, a "mock browser window" signature element) for the dashboard rather than a generic template look.
Where it was wrong / needed correction
Files were occasionally generated in the wrong folder (e.g. .gitignore and .env.example initially landed inside app/ instead of the project root) because of which folder had terminal focus at the time — caught by checking file location in the VS Code explorer before committing to Git, then fixed by recreating them at the correct path and removing the wrong copies from Git tracking.
An early version of create_submission had duplicated db.commit() / return lines after a manual edit, causing a Pylance error — caught immediately by VS Code's Problems panel and fixed by cleanly rewriting the function.
What I changed / verified myself
I manually tested every single endpoint through /docs before trusting it worked — signup, login, widget CRUD, submissions, rate limiting (sent 6 rapid requests myself to confirm the 429), the honeypot (submitted with and without the hidden field to confirm is_spam flips), and CORS (built and ran a separate dummy HTML page on a different port to confirm cross-origin requests actually succeed rather than trusting the code alone).
I pushed back when the auto-generated widget preview was unstyled and asked for it to match the dashboard's visual design — the resulting CSS in widget.js was revised based on that feedback.
I asked for the frontend copy to be converted from Roman Urdu (used during development conversation) to proper English before final submission.
Git conflict resolution (merge conflict in .gitignore after pushing to a repo that GitHub had pre-populated) was walked through and resolved by manually editing the conflicted file rather than blindly accepting a suggested resolution.