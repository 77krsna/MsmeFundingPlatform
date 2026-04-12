# oracle/test_tasks.py
"""Test Celery tasks"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)

print("Testing Celery Tasks...")
print("=" * 60)

# Test 1: Import tasks
print("\n1. Testing imports...")
try:
    from tasks.monitor_gem import scrape_gem_orders, create_order_contract
    print("   ✅ GeM monitoring tasks")
    
    from tasks.verify_gstn import verify_pending_invoices
    print("   ✅ GSTN verification tasks")
    
    from tasks.process_orders import check_delivery_status
    print("   ✅ Order processing tasks")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

# Test 2: Run a task synchronously (without Celery worker)
print("\n2. Testing task execution (synchronous)...")
try:
    result = scrape_gem_orders()
    print(f"   ✅ Task executed: {result}")
except Exception as e:
    print(f"   ❌ Task execution failed: {e}")

print("\n" + "=" * 60)
print("✅ Task tests complete!")
print("\nTo run with Celery worker:")
print("  celery -A tasks.celery_app worker --loglevel=info")