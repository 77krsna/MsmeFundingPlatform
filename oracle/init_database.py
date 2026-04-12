# oracle/init_database.py
"""
Database initialization script
Run this to create all tables
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("DATABASE INITIALIZATION SCRIPT")
print("=" * 70)

# Step 1: Load environment
print("\n[1/5] Loading environment variables...")
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
print(f"      Loaded from: {env_path}")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    sys.exit(1)

# Hide password
safe_url = DATABASE_URL.split('@')[0].split(':')
safe_url[-1] = '****'
print(f"      Database: {':'.join(safe_url)}@{DATABASE_URL.split('@')[1]}")

# Step 2: Test connection
print("\n[2/5] Testing database connection...")
from sqlalchemy import create_engine, text

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"      ✅ Connected to: {version[:60]}...")
except Exception as e:
    print(f"      ❌ Connection failed: {e}")
    sys.exit(1)

# Step 3: Import models
print("\n[3/5] Importing database models...")
try:
    from app.models import Base, User, MSME, GeMOrder, OracleJob
    print(f"      ✅ Imported {len(Base.metadata.tables)} table definitions:")
    for table_name in Base.metadata.tables.keys():
        print(f"         - {table_name}")
except Exception as e:
    print(f"      ❌ Failed to import models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Create tables
print("\n[4/5] Creating tables in database...")
try:
    Base.metadata.create_all(bind=engine)
    print("      ✅ Tables created successfully")
except Exception as e:
    print(f"      ❌ Failed to create tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Verify tables
print("\n[5/5] Verifying tables exist...")
try:
    with engine.connect() as conn:
        # For PostgreSQL
        if "postgresql" in DATABASE_URL:
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_catalog.pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """))
        # For SQLite
        else:
            result = conn.execute(text("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table'
                ORDER BY name;
            """))
        
        tables = result.fetchall()
        
        if tables:
            print(f"      ✅ Found {len(tables)} tables in database:")
            for table in tables:
                print(f"         - {table[0]}")
        else:
            print("      ⚠️  No tables found in database!")
            sys.exit(1)
            
except Exception as e:
    print(f"      ❌ Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Test insert
print("\n[BONUS] Testing data insertion...")
try:
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if test user exists
    test_user = session.query(User).filter_by(wallet_address="0x1234567890123456789012345678901234567890").first()
    
    if not test_user:
        test_user = User(
            wallet_address="0x1234567890123456789012345678901234567890",
            user_type="ADMIN",
            email="test@example.com"
        )
        session.add(test_user)
        session.commit()
        print(f"      ✅ Test user created: {test_user.wallet_address}")
    else:
        print(f"      ✅ Test user already exists: {test_user.wallet_address}")
    
    # Count users
    user_count = session.query(User).count()
    print(f"      Total users in database: {user_count}")
    
    session.close()
    
except Exception as e:
    print(f"      ⚠️  Insert test failed: {e}")

# Success
print("\n" + "=" * 70)
print("✅ DATABASE INITIALIZATION COMPLETE!")
print("=" * 70)
print("\nYou can now verify in PostgreSQL:")
print("  psql -U postgres -d msme_finance")
print("  \\dt")
print()