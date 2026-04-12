# oracle/test_fastapi.py
"""Test if FastAPI can be imported"""

import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("Current directory:", current_dir)
print("Python path:", sys.path[:3])

# Test imports
print("\n1. Testing app module import...")
try:
    import app
    print("   ✅ app module found")
    print(f"   Location: {app.__file__}")
except ImportError as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print("\n2. Testing app.main import...")
try:
    from app.main import app as fastapi_app
    print("   ✅ app.main imported successfully")
except ImportError as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testing FastAPI app...")
try:
    print(f"   App type: {type(fastapi_app)}")
    print(f"   App title: {fastapi_app.title}")
    print("   ✅ FastAPI app is valid")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print("\n✅ All imports successful!")
print("\nYou can now run:")
print("  python -m uvicorn app.main:app --reload --port 8000")