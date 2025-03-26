# database/__init__.py
from .models import Cohort, Marker, MarkerData, CellTypeData
from .db_connect import get_session, init_db
from .seed_data import seed_database

# Initialize the database if needed
def initialize_database():
    """Initialize the database and seed it if it doesn't exist"""
    from pathlib import Path
    import os
    
    db_path = Path('immune_atlas.db')
    
    if not db_path.exists():
        print("Database not found, initializing and seeding...")
        init_db()
        seed_database()
    else:
        print("Database found, skipping initialization.")