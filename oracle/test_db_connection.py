#!/usr/bin/env python3
"""Quick database connection test"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

print("=" * 60)
print("DATABASE CONNECTION DIAGNOSTIC")
print("=" * 60)

# Check environment variable
db_url = os.getenv("DATABASE_URL")
print(f"\n1. DATABASE_URL from .env:")
if db_url:
    # Hide password
    safe_url = db_url.split("@")[0].split(":")
    safe_url[-1] = "****"
    print(f"   {':'.join(safe_url)}@{db_url.split('@')[1]}")
else:
    print("   ❌ NOT SET")
    sys.exit(1)

# Check if PostgreSQL
if "postgresql" in db_url:
    print("\n2. Database Type: PostgreSQL")
    
    # Try to import psycopg2
    try:
        import psycopg2
        print("   ✅ psycopg2 installed")
    except ImportError:
        print("   ❌ psycopg2 not installed")
        print("   Run: pip install psycopg2-binary")
        sys.exit(1)
    
    # Try raw connection
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        result = urlparse(db_url)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port
        
        print(f"\n3. Connection Details:")
        print(f"   Host: {hostname}")
        print(f"   Port: {port}")
        print(f"   Database: {database}")
        print(f"   User: {username}")
        
        print("\n4. Testing raw connection...")
        conn = psycopg2.connect(
            host=hostname,
            port=port,
            database=database,
            user=username,
            password=password
        )
        print("   ✅ Raw connection successful")
        
        # Test query
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"   PostgreSQL version: {version[0][:50]}...")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Raw connection failed: {e}")
        sys.exit(1)

elif "sqlite" in db_url:
    print("\n2. Database Type: SQLite")
    print("   ✅ No server needed")

# Test SQLAlchemy
print("\n5. Testing SQLAlchemy connection...")
try:
    from sqlalchemy import create_engine, text
    
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("   ✅ SQLAlchemy connection successful")
        
except Exception as e:
    print(f"   ❌ SQLAlchemy connection failed: {e}")
    sys.exit(1)

# Test models
print("\n6. Testing models import...")
try:
    from app.models import Base, User, MSME, GeMOrder
    print("   ✅ Models imported successfully")
    
    print(f"\n7. Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("   ✅ Tables created")
    
    # Count tables
    with engine.connect() as conn:
        if "postgresql" in db_url:
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
        else:  # SQLite
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table'
            """))
        
        count = result.fetchone()[0]
        print(f"   Found {count} tables")
    
except Exception as e:
    print(f"   ❌ Models/tables failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Database is ready!")
print("=" * 60)