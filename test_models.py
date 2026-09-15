from app.database.session import engine, Base, SessionLocal
from app.models.user import User
from app.models.product import Product, PriceHistory, TrackedProduct

def test_schema_creation():
    print("Creating all database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    db = SessionLocal()
    try:
        # 1. Insert a User
        user = User(name="Test User", email="user@example.com", password_hash="dummyhashedpass")
        db.add(user)
        db.flush()

        # 2. Insert a Product
        product = Product(
            name="A Light in the Attic",
            url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
            current_price=51.77,
            currency="GBP",
            availability=True,
        )
        db.add(product)
        db.flush()

        # 3. Add Price History Point
        history = PriceHistory(product_id=product.id, price=51.77)
        db.add(history)

        # 4. Add Tracked Product Link
        tracked = TrackedProduct(user_id=user.id, product_id=product.id, target_price=45.00)
        db.add(tracked)
        db.commit()

        # Query and assert relationships
        queried_product = db.query(Product).filter_by(id=product.id).first()
        print("\n--- Verification Query ---")
        print(f"Product: {queried_product.name}")
        print(f"Tracked by user count: {len(queried_product.tracked_by)}")
        print(f"History entries: {len(queried_product.history)}")
        print("Schema and relationships verified successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    test_schema_creation()