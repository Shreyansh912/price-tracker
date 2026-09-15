import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.tracker_service import TrackerService
from app.models.product import Product, TrackedProduct
from app.models.user import User
from app.utils.notifier import send_price_drop_alert
from app.database.session import SessionLocal

logger = logging.getLogger("price_tracker.scheduler")
scheduler = BackgroundScheduler()


def start_scheduler(check_interval_seconds: int = 60):
    """Initializes and starts the periodic price scanner."""
    if not scheduler.running:
        scheduler.add_job(
            func=TrackerService.check_all_tracked_products,
            trigger=IntervalTrigger(seconds=check_interval_seconds),
            id="periodic_price_checker",
            name="Periodic Product Price Checker",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            f"Scheduler started. Running price checks every {check_interval_seconds} seconds."
        )


def stop_scheduler():
    """Safely terminates the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler cleanly shut down.")

def check_prices_job():
    db = SessionLocal() # Or your existing database session getter
    try:
        tracked_items = db.query(TrackedProduct).all()
        
        for item in tracked_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            user = db.query(User).filter(User.id == item.user_id).first()
            
            if not product or not user:
                continue
                
            # Check if current price has met or gone below the user's target price
            if product.current_price <= item.target_price:
                # Calculate savings
                savings = round(product.original_price - product.current_price, 2) if product.original_price else 0.0
                
                # Send the email alert
                send_price_drop_alert(
                    to_email=user.email,
                    product_name=product.name,
                    current_price=product.current_price,
                    currency=product.currency,
                    product_url=product.url
                )
                logger.info(f"Target price met for {product.name}! Alert email dispatched to {user.email}")
                
    except Exception as e:
        logger.error(f"Error in price checking task: {e}")
    finally:
        db.close()