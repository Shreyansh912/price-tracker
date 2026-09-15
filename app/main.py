import logging
from pathlib import Path
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request, status, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from google import genai
from sqlalchemy.orm import Session

from app.database.session import engine, Base, get_db
from app.models.product import TrackedProduct, Product
from app.utils.config import settings
from app.scrapers.exceptions import ScraperException, UnsupportedSiteException
from app.api.auth import router as auth_router
from app.api.products import router as product_router
from app.scheduler.task_runner import start_scheduler, stop_scheduler

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from fastapi import FastAPI
from app.api.agent import router as agent_router

app = FastAPI()

# Make sure this line exists in main.py!
app.include_router(agent_router)


# 1. Base Paths & Logging
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("price_tracker")


# 2. Lifecycle Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing application database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database connection verified and tables ready.")

    logger.info("Starting background scheduler...")
    start_scheduler(check_interval_seconds=60)

    yield

    logger.info("Shutting down background scheduler...")
    stop_scheduler()
    logger.info("Application shutdown complete.")


# 3. FastAPI Application Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Automated web scraper, price tracker, and alerting engine.",
    lifespan=lifespan,
)


# 4. Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# 5. Security Middlewares & CORS Setup
origins = [
    os.getenv("FRONTEND_URL", "https://ideally-dart-gorged.ngrok-free.dev"),
    "http://localhost:3000",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# 6. Global Exception Handlers
@app.exception_handler(UnsupportedSiteException)
async def unsupported_site_handler(request: Request, exc: UnsupportedSiteException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Unsupported Domain", "detail": str(exc)},
    )


@app.exception_handler(ScraperException)
async def scraper_exception_handler(request: Request, exc: ScraperException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Scraping Failure", "detail": str(exc)},
    )


# 7. Include Core API Routers
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(agent_router)

# 8. AI Assistant Router & Gemini LLM Integration
ai_router = APIRouter(prefix="/ai", tags=["AI Assistant"])

class AIQuery(BaseModel):
    prompt: str

@ai_router.post("/chat")
async def chat_with_pulse_ai(query: AIQuery, db: Session = Depends(get_db)):
    user_prompt = query.prompt
    
    tracked_items = db.query(Product).join(TrackedProduct, Product.id == TrackedProduct.product_id).all()
    
    inventory_context = "The user is currently tracking the following products on PricePulse:\n"
    if tracked_items:
        for p in tracked_items:
            inventory_context += f"- {p.name}: Current Price {p.current_price} {p.currency}, Availability: {p.availability}\n"
    else:
        inventory_context += "No products are currently being tracked.\n"

    system_instruction = (
        "You are Pulse AI, an elite, futuristic e-commerce shopping assistant and price analyst for the PricePulse platform. "
        "Keep your answers concise, smart, professional, and helpful. Use the live inventory context provided below to answer the user's questions accurately.\n\n"
        f"{inventory_context}"
    )

    try:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config={
                'system_instruction': system_instruction,
                'temperature': 0.7,
            }
        )
        ai_answer = response.text
    except Exception as e:
        ai_answer = f"Pulse AI encountered an error processing your request via LLM: {str(e)}"

    return {"response": ai_answer}

app.include_router(ai_router)

# 9. Static Dashboard Mounting & General Endpoints
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", tags=["General"])
def serve_dashboard():
    """Serves the single-page frontend dashboard."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint for container and uptime monitoring."""
    return {"status": "healthy", "database": "connected"}