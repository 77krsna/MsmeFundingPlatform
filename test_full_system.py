# test_full_system.py
"""Test the complete system: Backend + Frontend"""

import requests
import time
from datetime import datetime

print("=" * 70)
print("  FULL SYSTEM TEST")
print("=" * 70)
print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Test 1: Backend API
print("[1/4] Testing Backend API (port 5000)...")
try:
    r = requests.get("http://localhost:5000/health", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"  ✅ Backend is running")
        print(f"     Status: {data.get('status', 'OK')}")
    else:
        print(f"  ❌ Backend returned {r.status_code}")
except requests.exceptions.ConnectionError:
    print("  ❌ Backend NOT running on port 5000")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 2: Oracle API
print("\n[2/4] Testing Oracle API (port 8001)...")
try:
    r = requests.get("http://localhost:8001/health", timeout=5)
    if r.status_code == 200:
        print(f"  ✅ Oracle is running")
    else:
        print(f"  ❌ Oracle returned {r.status_code}")
except requests.exceptions.ConnectionError:
    print("  ❌ Oracle NOT running on port 8001")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 3: Blockchain
print("\n[3/4] Testing Blockchain (port 8545)...")
try:
    r = requests.post("http://localhost:8545", 
                     json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1},
                     timeout=5)
    if r.status_code == 200:
        print(f"  ✅ Blockchain is running")
    else:
        print(f"  ❌ Blockchain returned {r.status_code}")
except Exception as e:
    print(f"  ❌ Blockchain NOT running: {e}")

# Test 4: Frontend
print("\n[4/4] Testing Frontend (port 3000)...")
try:
    r = requests.get("http://localhost:3000", timeout=5)
    if r.status_code == 200:
        print(f"  ✅ Frontend is running")
        print(f"     Page size: {len(r.text)} bytes")
    else:
        print(f"  ❌ Frontend returned {r.status_code}")
except requests.exceptions.ConnectionError:
    print("  ❌ Frontend NOT running")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Summary
print("\n" + "=" * 70)
print("  SYSTEM URLS:")
print("=" * 70)
print(f"  Frontend:    http://localhost:3000")
print(f"  Backend API: http://localhost:5000")
print(f"  Backend Docs: http://localhost:5000/docs")
print(f"  Oracle API:  http://localhost:8001")
print(f"  Oracle Docs: http://localhost:8001/docs")
print(f"  Blockchain:  http://localhost:8545")
print("=" * 70)

print("\n  PAGES TO TEST:")
print("  📊 Dashboard:  http://localhost:3000/")
print("  📋 Orders:     http://localhost:3000/orders")
print("  🏭 MSME:       http://localhost:3000/msme")
print("  💰 Investors:  http://localhost:3000/investors")
print("  ⚙️  Admin:      http://localhost:3000/admin")
print("=" * 70)