import json
import os
import logging
from pathlib import Path
from typing import Callable, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from groq import Groq

from app.database.session import SessionLocal
from app.models.product import Product, PriceHistory, TrackedProduct

from app.services.product_service import ProductService

from dotenv import load_dotenv
load_dotenv()

from groq import Groq

# Explicitly find and load the .env file from the root directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

import numpy as np
logger = logging.getLogger("price_tracker.agent")
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
# Fallback check to see if it's loaded
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is missing from environment variables or .env file.")

client = Groq(api_key=api_key)
class CustomAgentRegistry:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.openai_tools = []

    def register(self, name: str, func: Callable, description: str, parameters: dict):
        self.tools[name] = {"function": func, "description": description}
        self.openai_tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        })

agent_registry = CustomAgentRegistry()

# --- Tool Definitions ---

def search_products_tool(db: Session, query: str = "") -> str:
    db_query = db.query(Product)
    if query:
        db_query = db_query.filter(Product.name.ilike(f"%{query}%"))
    products = db_query.all()
    results = [{"id": p.id, "name": p.name, "price": p.current_price, "currency": p.currency, "url": p.url} for p in products]
    return json.dumps(results, indent=2)

agent_registry.register(
    name="search_products",
    func=search_products_tool,
    description="Search real products in the database by query string.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "The search keyword like laptop, phone, mouse"}},
        "required": ["query"]
    }
)

def get_tracked_products_tool(db: Session, user_id: int) -> str:
    tracked_items = db.query(TrackedProduct).filter(TrackedProduct.user_id == user_id).all()
    if not tracked_items:
        return json.dumps({"message": "You are not tracking any products currently."})
    results = []
    for item in tracked_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        results.append({
            "product_name": product.name if product else "Unknown",
            "current_price": product.current_price if product else None,
            "target_price": item.target_price
        })
    return json.dumps(results, indent=2)

agent_registry.register(
    name="get_tracked_products",
    func=get_tracked_products_tool,
    description="Retrieve all products tracked by the current user.",
    parameters={"type": "object", "properties": {}}
)

def track_product_tool(db: Session, user_id: int, url: str, target_price: float = 500.0) -> str:
    try:
        tracked = ProductService.track_product(db=db, user_id=user_id, url=url, target_price=target_price)
        return json.dumps({"success": True, "message": f"Successfully tracking product ID {tracked.product_id} with target ₹{target_price}"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

agent_registry.register(
    name="track_product",
    func=track_product_tool,
    description="Track an e-commerce URL with a specified target price.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The product URL to track"},
            "target_price": {"type": "number", "description": "The target price threshold"}
        },
        "required": ["url"]
    }
)

def get_price_history_tool(db: Session, product_id: int = 1) -> str:
    history = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).all()
    if not history:
        return json.dumps({"message": "No price history found."})
    prices = [h.price for h in history]
    return json.dumps({
        "product_id": product_id,
        "lowest": min(prices),
        "highest": max(prices),
        "average": round(sum(prices) / len(prices), 2),
        "history": [{"price": h.price, "timestamp": str(h.timestamp)} for h in history]
    }, indent=2)

agent_registry.register(
    name="get_price_history",
    func=get_price_history_tool,
    description="Retrieve price history and statistical trends for a product ID.",
    parameters={
        "type": "object",
        "properties": {"product_id": {"type": "integer", "description": "The product ID"}}
    }
)