from pathlib import Path
import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from app.database import engine, Base
from app.routes import users, clients, projects, timelog, invoices, auth, admin, billing
from app.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Startup security checks
# ---------------------------------------------------------------------------
_SECRET_KEY = os.getenv("SECRET_KEY", "")
_INSECURE_DEFAULTS = {"", "your-secret-key-change-this", "your-secret-key-here-change-in-production"}

if _SECRET_KEY in _INSECURE_DEFAULTS:
    print(
        "\n[SECURITY ERROR] SECRET_KEY is not set or is using an insecure default.\n"
        "Generate one with:  python -c \"import secrets; print(secrets.token_hex(32))\"\n"
        "Then add it to your .env file as:  SECRET_KEY=<generated_value>\n",
        file=sys.stderr,
    )
    sys.exit(1)

if len(_SECRET_KEY) < 32:
    print(
        "\n[SECURITY WARNING] SECRET_KEY is shorter than 32 characters. "
        "Use at least 32 random bytes for production.\n",
        file=sys.stderr,
    )

# ---------------------------------------------------------------------------
# CORS — env-configurable, safe default for local dev only
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app = FastAPI(
    title="Freelancer Time Tracker API",
    description="Time tracking and invoice generation for freelancers",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(clients.router, prefix="/api/clients", tags=["clients"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(timelog.router, prefix="/api/timelog", tags=["timelog"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["invoices"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Serve the React production build
FRONTEND_BUILD = Path(__file__).parent.parent / "frontend" / "build"

if FRONTEND_BUILD.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD / "static"), name="static")

    @app.get("/")
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str = ""):
        return FileResponse(FRONTEND_BUILD / "index.html")
else:
    @app.get("/")
    def read_root():
        return {"message": "Freelancer Time Tracker API is running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
