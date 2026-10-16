# ⚡ PricePulse

> Stop watching prices. Let AI watch them for you.

**PricePulse** is an advanced, production-ready Python-based FastAPI e-commerce price tracker and intelligent shopping assistant. It features automated multi-site web scraping, background scheduling, instant target price alerting, secure user authentication, and a custom tool-calling AI agent powered by Groq and Llama-3.3-70b.

---

## 🚀 Key Features

* **🛍️ Automated Price Tracking:** Monitor products across e-commerce platforms (e.g., Amazon, BooksToScrape) with automatic background checks.
* **🤖 Pulse AI Assistant:** An integrated LLM agent powered by Groq and Llama-3.3-70b that dynamically executes live database tools to query tracked items, search the catalog, and analyze price history.
* **📈 Interactive Price Dynamics:** Visualize historical price fluctuations over time using Chart.js with dynamic gradient fills.
* **🔔 Smart Price Alerts:** Instantly catch price drops and target thresholds with real-time savings calculations and quick-buy links.
* **🔒 Secure Authentication:** Complete JWT-based authentication system featuring user registration, secure login, and a 6-digit OTP password reset workflow.
* **⚡ Rate-Limited & Optimized:** Built with `slowapi` rate limiting and robust security HTTP headers middleware (`X-Content-Type-Options`, `HSTS`, etc.).

---

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI, SQLAlchemy, SQLite/PostgreSQL, APScheduler, SlowAPI
* **AI / LLM:** Groq API (`llama-3.3-70b-versatile`), Custom Tool-Calling Registry
* **Frontend:** HTML5, Modern CSS3 (Glassmorphism UI), JavaScript (ES6+), Chart.js
* **Security:** Passlib (Bcrypt hashing), python-jose (JWT tokens), CORS middleware

---

## 📁 Project Structure

```text
price-tracker/
├── app/
│   ├── api/             # API routers (auth, products, AI agent)
│   ├── agent/           # Custom AI agent logic and tool registry
│   ├── database/        # Database session and configuration engine
│   ├── models/          # SQLAlchemy database models (User, Product, etc.)
│   ├── scrapers/        # Multi-site web scraping engine & custom exceptions
│   ├── scheduler/       # APScheduler background task runner
│   ├── utils/           # Configuration settings and helper utilities
│   └── main.py          # FastAPI application entrypoint and middleware
├── frontend/            # Single-page dashboard interface (index.html)
├── requirements.txt     # Python backend dependencies
└── README.md            # Project documentation
```

---

## ⚙️ Getting Started & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Shreyansh912/price-tracker.git
cd price-tracker
```

### 2. Create a Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory and add your configuration credentials:
```env
PROJECT_NAME=PricePulse
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_super_secret_jwt_signature_key
FRONTEND_URL=https://your-ngrok-url.ngrok-free.dev
```

### 4. Run the Application
Start the FastAPI server using Uvicorn with hot-reloading enabled:
```bash
uvicorn app.main:app --reload
```

Open your browser and navigate to `http://127.0.0.1:8000` to access the live dashboard or check the interactive API documentation at `http://127.0.0.1:8000/docs`.

---

## 🔌 API Endpoints Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/` | `GET` | Serves the single-page frontend dashboard |
| `/health` | `GET` | Health check for uptime monitors and container status |
| `/auth/register` | `POST` | Registers a new user account |
| `/auth/login` | `POST` | Authenticates user and returns a Bearer JWT token |
| `/auth/me` | `GET` | Retrieves profile details for the currently logged-in user |
| `/auth/forgot-password` | `POST` | Triggers a 6-digit OTP code for password recovery |
| `/auth/reset-password` | `POST` | Updates user password using email and OTP |
| `/products/` | `GET` | Lists all active tracked items for the user |
| `/products/` | `POST` | Scrapes a target URL and starts tracking the product |
| `/products/{id}/history`| `GET` | Fetches historical price logs for trend charts |
| `/products/{id}/track` | `DELETE` | Untracks and removes a product from the radar |
| `/products/alerts` | `GET` | Retrieves active price drop alerts |
| `/api/agent/chat` | `POST` | Communicates with the Pulse AI assistant (Groq LLM) |

---

## 💡 Usage Guide

1. **Sign Up / Sign In:** Launch the application and create an account to secure your personal price dashboard.
2. **Add Products:** Paste any supported e-commerce product URL (such as Amazon or BooksToScrape links), set your custom target price threshold in Rupees/Currency, and click **Track Product**.
3. **Chat with Pulse AI:** Use the built-in AI assistant interface to ask conversational queries like:
   * *"What items am I currently tracking?"*
   * *"Search for laptops or books"*
   * *"Show price history for my recent items"*

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.