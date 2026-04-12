# oracle/api_examples.py
"""
API Usage Examples for different use cases
"""

import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("  MSME FINANCE PLATFORM - API USAGE EXAMPLES")
print("=" * 70)

# ============================================
# Example 1: Get Platform Overview
# ============================================
print("\n[Example 1] Get Platform Overview\n")
print("Use case: Dashboard showing system health and stats")
print("-" * 70)

health = requests.get(f"{API_BASE}/health").json()
status = requests.get(f"{API_BASE}/status").json()
stats = requests.get(f"{API_BASE}/api/orders/stats/summary").json()

print(f"System Status: {health['status']}")
print(f"Total Orders: {status['platform']['total_orders']}")
print(f"Total Volume: ₹{stats['total_volume']:,.2f}")

# ============================================
# Example 2: Browse Investment Opportunities
# ============================================
print("\n[Example 2] Browse Investment Opportunities\n")
print("Use case: Investor looking for opportunities")
print("-" * 70)

opportunities = requests.get(f"{API_BASE}/api/investors/opportunities").json()

print(f"Found {len(opportunities)} opportunities:\n")
for i, opp in enumerate(opportunities[:3], 1):
    print(f"{i}. {opp['gem_order_id']}")
    print(f"   Amount: ₹{opp['order_amount']:,.2f}")
    print(f"   Return: {opp['estimated_return']}%")
    print(f"   Risk: {opp['risk_score']}/10")
    print()

# ============================================
# Example 3: MSME Registration Flow
# ============================================
print("\n[Example 3] MSME Registration\n")
print("Use case: New MSME company registering")
print("-" * 70)

msme_data = {
    "wallet_address": "0x" + "2" * 40,
    "company_name": "Example MSME Pvt Ltd",
    "gstn": "27AABCU9603R1ZM",
    "pan": "ABCDE1234F",
    "email": "msme@example.com"
}

print("Registration data:")
print(json.dumps(msme_data, indent=2))

# Uncomment to actually register
# response = requests.post(f"{API_BASE}/api/msme/register", json=msme_data)
# print(f"\nResponse: {response.status_code}")

# ============================================
# Example 4: Track Specific Order
# ============================================
print("\n[Example 4] Track Specific Order\n")
print("Use case: MSME tracking their order status")
print("-" * 70)

orders_response = requests.get(f"{API_BASE}/api/orders/?page=1&page_size=1").json()

if orders_response['orders']:
    order = orders_response['orders'][0]
    print(f"Order ID: {order['gem_order_id']}")
    print(f"Amount: ₹{order['order_amount']:,.2f}")
    print(f"Status: {order['status']}")
    print(f"Deadline: {order['delivery_deadline']}")
    print(f"Buyer: {order.get('buyer_organization', 'N/A')}")

# ============================================
# Example 5: Admin Operations
# ============================================
print("\n[Example 5] Admin Operations\n")
print("Use case: Admin triggering manual scrape")
print("-" * 70)

print("Triggering GeM portal scrape...")
response = requests.post(f"{API_BASE}/api/admin/trigger-scrape")

if response.status_code == 200:
    result = response.json()
    print(f"✅ Task queued: {result.get('task_id', 'N/A')}")
    print("Check Celery worker terminal for progress")
else:
    print("❌ Failed to trigger scrape")

print("\n" + "=" * 70)
print("  For more examples, visit: http://localhost:8000/docs")
print("=" * 70)