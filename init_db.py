import sys
import os
import time

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import User, LoginHistory

def init_db():
    """Initialize database tables"""
    print("Waiting for database to start...")
    time.sleep(2)  # Wait for database to fully start
    
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")
        
    except Exception as e:
        print(f"Error creating database tables: {e}")
        # Retry once
        time.sleep(2)
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()