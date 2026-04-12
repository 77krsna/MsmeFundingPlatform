#!/usr/bin/env python3
"""Simple database test without imports"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment
load_dotenv(dotenv_path="../.env")

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Database URL: {DATABASE_URL[:30]}...")

# Create engine
engine = create_engine(DATABASE_URL)

# Test connection
print("\n1. Testing connection...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(f"   ✅ Connection OK: {result.fetchone()}")

# Create a simple table
print("\n2. Creating test table...")
Base = declarative_base()

class TestTable(Base):
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

Base.metadata.create_all(engine)
print("   ✅ Table created")

# Insert data
print("\n3. Inserting test data...")
Session = sessionmaker(bind=engine)
session = Session()

test_record = TestTable(id=1, name="Test")
session.add(test_record)
session.commit()
print("   ✅ Data inserted")

# Query data
print("\n4. Querying data...")
result = session.query(TestTable).first()
print(f"   ✅ Retrieved: {result.name}")

# Cleanup
print("\n5. Cleaning up...")
Base.metadata.drop_all(engine)
session.close()
print("   ✅ Test table dropped")

print("\n✅ ALL TESTS PASSED!")