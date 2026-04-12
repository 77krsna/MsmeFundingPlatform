# oracle/quick_status.py
"""Quick status check without live updates"""

import requests

API_BASE = "http://localhost:8000"

print("=" * 70)
print("QUICK STATUS CHECK")
print("=" * 70)

# Health
try:
    r = requests.get(f"{API_BASE}/health")
    health = r.json()
    print(f"\n✅ API Status: {health['status']}")
except:
    print("\n❌ API not responding")
    exit(1)

# Orders
try:
    r = requests.get(f"{API_BASE}/api/orders/stats/summary")
    stats = r.json()
    print(f"\n📊 Orders: {stats['total_orders']}")
    print(f"   Total Volume: ₹{stats['total_volume']:,.2f}")
except Exception as e:
    print(f"\n⚠️  Could not fetch order stats: {e}")

# Status
try:
    r = requests.get(f"{API_BASE}/status")
    status = r.json()
    platform = status.get('platform', {})
    print(f"\n👥 Platform:")
    print(f"   Users: {platform.get('total_users', 0)}")
    print(f"   MSMEs: {platform.get('total_msmes', 0)}")
except Exception as e:
    print(f"\n⚠️  Could not fetch platform status: {e}")

print("\n" + "=" * 70)