from db.init_db import Base, engine
from db import models  # Ensure all model classes are imported


def create_tables():
    """
    Creates all database tables defined in db/models.py.
    Uses SQLAlchemy's Base metadata to initialize the schema.
    """
    try:
        print("📦 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully.")
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        raise


if __name__ == "__main__":
    create_tables()
