#!/usr/bin/env python3
"""Test if all critical imports work"""

print("Testing imports...")

try:
    import fastapi
    print("✅ FastAPI")
    
    import sqlalchemy
    print("✅ SQLAlchemy")
    
    import web3
    print("✅ Web3.py")
    
    import redis
    print("✅ Redis")
    
    import celery
    print("✅ Celery")
    
    from playwright.sync_api import sync_playwright
    print("✅ Playwright")
    
    import httpx
    print("✅ HTTPX")
    
    from cryptography.fernet import Fernet
    print("✅ Cryptography")
    
    print("\n🎉 All imports successful!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)