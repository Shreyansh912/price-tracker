import logging
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.product import Product, TrackedProduct
from app.models.price_history import PriceHistory
from app.scrapers.factory import ScraperFactory
from app.services.alert_service import AlertService

logger = logging.getLogger("price_tracker.scheduler")


def run_price_check_job():
    """Background cron job that iterates through all tracked products,
    scrapes current prices, updates records, and triggers alerts."""
    db: Session = SessionLocal()
    try:
        tracked_records = db.query(TrackedProduct).all()
        if not tracked_records:
            logger.info("Periodic price check: No active items being tracked.")
            return

        # Deduplicate products so we don't scrape the same URL twice in one cycle
        unique_product_ids = {t.product_id for t in tracked_records}
        logger.info(f"Running automated price refresh for {len(unique_product_ids)} unique product(s)...")

        for product_id in unique_product_ids:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                continue

            try:
                scraper = ScraperFactory.get_scraper(product.url)
                scraped_data = scraper.scrape(product.url)

                # Update product baseline
                product.current_price = scraped_data.price
                product.availability = scraped_data.availability
                if scraped_data.image_url:
                    product.image_url = scraped_data.image_url

                # Log to time-series history
                history_entry = PriceHistory(
                    product_id=product.id,
                    price=scraped_data.price,
                )
                db.add(history_entry)
                db.commit()

                logger.info(f"Updated '{product.name[:30]}' -> {scraped_data.price} {product.currency}")

            except Exception as scrape_err:
                logger.warning(f"Failed to refresh product ID {product.id}: {scrape_err}")
                db.rollback()
                continue

        # Evaluate target thresholds and send emails where applicable
        for track in tracked_records:
            try:
                AlertService.evaluate_and_notify(
                    db=db,
                    user_id=track.user_id,
                    product_id=track.product_id,
                )
            except Exception as alert_err:
                logger.error(f"Error checking alerts for user {track.user_id}: {alert_err}")

    except Exception as general_err:
        logger.error(f"Critical error in price check worker: {general_err}")
    finally:
        db.close()