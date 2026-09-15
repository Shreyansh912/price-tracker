import logging
from app.scrapers.factory import ScraperFactory
from app.scrapers.exceptions import UnsupportedSiteException, NetworkException

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def test_valid_product():
    print("\n--- TEST 1: Valid URL via Factory ---")
    url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    scraper = ScraperFactory.get_scraper(url)
    product = scraper.scrape(url)
    print(f"Success: Scraped '{product.title}' at {product.price} {product.currency}")

def test_unsupported_domain():
    print("\n--- TEST 2: Unsupported Domain ---")
    url = "https://example.com/item/123"
    try:
        ScraperFactory.get_scraper(url)
    except UnsupportedSiteException as e:
        print(f"Caught expected error: {e}")

def test_bad_url_retry():
    print("\n--- TEST 3: Retrying Broken URL ---")
    url = "https://books.toscrape.com/non-existent-page-404"
    scraper = ScraperFactory.get_scraper(url)
    try:
        scraper.scrape(url)
    except NetworkException as e:
        print(f"Caught expected retry exhaustion: {e}")

if __name__ == "__main__":
    test_valid_product()
    test_unsupported_domain()
    test_bad_url_retry()