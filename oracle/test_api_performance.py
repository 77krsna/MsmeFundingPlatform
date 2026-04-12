# oracle/test_api_performance.py
"""
API Performance Testing
"""

import requests
import time
from statistics import mean, median

API_BASE = "http://localhost:8000"

def measure_endpoint(endpoint, iterations=10):
    """Measure endpoint response time"""
    times = []
    
    for i in range(iterations):
        start = time.time()
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            if response.status_code == 200:
                times.append((time.time() - start) * 1000)  # Convert to ms
        except:
            pass
    
    if times:
        return {
            'mean': mean(times),
            'median': median(times),
            'min': min(times),
            'max': max(times)
        }
    return None

print("=" * 70)
print("  API PERFORMANCE TEST")
print("=" * 70)

endpoints = [
    ("Health Check", "/health"),
    ("System Status", "/status"),
    ("List Orders", "/api/orders/"),
    ("Order Stats", "/api/orders/stats/summary"),
    ("Opportunities", "/api/investors/opportunities"),
]

results = []

for name, endpoint in endpoints:
    print(f"\nTesting: {name}")
    print(f"Endpoint: {endpoint}")
    
    stats = measure_endpoint(endpoint, iterations=10)
    
    if stats:
        print(f"  Mean:   {stats['mean']:.2f} ms")
        print(f"  Median: {stats['median']:.2f} ms")
        print(f"  Min:    {stats['min']:.2f} ms")
        print(f"  Max:    {stats['max']:.2f} ms")
        results.append((name, stats['mean']))
    else:
        print("  ❌ Failed")

print("\n" + "=" * 70)
print("  PERFORMANCE SUMMARY")
print("=" * 70)

for name, avg_time in sorted(results, key=lambda x: x[1]):
    status = "🚀" if avg_time < 100 else "✅" if avg_time < 500 else "⚠️"
    print(f"{status} {name:<25} {avg_time:>8.2f} ms")

print("=" * 70)