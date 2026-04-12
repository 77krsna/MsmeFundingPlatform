#!/usr/bin/env python3
"""Test scraper dependencies"""

print("Testing scraper dependencies...\n")

# Test 1: BeautifulSoup
try:
    from bs4 import BeautifulSoup
    print("✅ BeautifulSoup4 (bs4)")
except ImportError as e:
    print(f"❌ BeautifulSoup4: {e}")

# Test 2: lxml
try:
    import lxml
    print("✅ lxml")
except ImportError as e:
    print(f"❌ lxml: {e}")

# Test 3: Playwright
try:
    from playwright.sync_api import sync_playwright
    print("✅ Playwright")
except ImportError as e:
    print(f"❌ Playwright: {e}")

# Test 4: Selenium
try:
    from selenium import webdriver
    print("✅ Selenium")
except ImportError as e:
    print(f"❌ Selenium: {e}")

# Test 5: datetime
try:
    from datetime import datetime, timedelta
    print("✅ datetime")
except ImportError as e:
    print(f"❌ datetime: {e}")

# Test 6: config (from app)
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from app.config import settings
    print("✅ app.config")
except ImportError as e:
    print(f"❌ app.config: {e}")

print("\n" + "="*50)
print("If all show ✅, scraper should work!")