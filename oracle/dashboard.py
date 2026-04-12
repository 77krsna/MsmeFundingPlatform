# oracle/dashboard.py
"""
Real-time dashboard - monitors system status
"""

import requests
import time
import os
from datetime import datetime

API_BASE = "http://localhost:8000"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_status():
    try:
        health = requests.get(f"{API_BASE}/health", timeout=2).json()
        status = requests.get(f"{API_BASE}/status", timeout=2).json()
        stats = requests.get(f"{API_BASE}/api/orders/stats/summary", timeout=2).json()
        return health, status, stats, None
    except requests.exceptions.RequestException as e:
        return None, None, None, str(e)
    except Exception as e:
        return None, None, None, str(e)

def display_dashboard():
    while True:
        clear_screen()
        
        print("=" * 80)
        print(" " * 20 + "MSME FINANCE PLATFORM - LIVE DASHBOARD")
        print("=" * 80)
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        health, status, stats, error = get_status()
        
        if error:
            print(f"❌ Error: {error}")
            print("\nMake sure FastAPI is running:")
            print("  python -m uvicorn app.main:app --reload --port 8000")
            print("\nPress Ctrl+C to exit | Retrying in 5 seconds...")
            time.sleep(5)
            continue
        
        if not health:
            print("❌ API is not responding!")
            print("\nPress Ctrl+C to exit | Retrying in 5 seconds...")
            time.sleep(5)
            continue
        
        # Health Status
        print("🏥 SYSTEM HEALTH")
        print("-" * 80)
        try:
            print(f"Overall Status:  {health.get('status', 'unknown').upper()}")
            services = health.get('services', {})
            print(f"Database:        {services.get('database', 'unknown')}")
            print(f"Blockchain:      {services.get('blockchain', 'unknown')}")
        except Exception as e:
            print(f"Error displaying health: {e}")
        print()
        
        # Platform Stats
        print("📊 PLATFORM STATISTICS")
        print("-" * 80)
        try:
            platform = status.get('platform', {})
            print(f"Total Orders:    {platform.get('total_orders', 0):>6}")
            print(f"Active Orders:   {platform.get('active_orders', 0):>6}")
            print(f"Completed:       {platform.get('completed_orders', 0):>6}")
            print(f"Total MSMEs:     {platform.get('total_msmes', 0):>6}")
            print(f"Total Users:     {platform.get('total_users', 0):>6}")
        except Exception as e:
            print(f"Error displaying platform stats: {e}")
        print()
        
        # Financial Stats
        print("💰 FINANCIAL OVERVIEW")
        print("-" * 80)
        try:
            total_volume = stats.get('total_volume', 0)
            print(f"Total Volume:    ₹{total_volume:>15,.2f}")
            print()
            print("Status Breakdown:")
            by_status = stats.get('by_status', {})
            for status_name, count in by_status.items():
                if count > 0:
                    print(f"  {status_name:<20} {count:>6}")
        except Exception as e:
            print(f"Error displaying financial stats: {e}")
        print()
        
        # Instructions
        print("=" * 80)
        print("🔗 Access Points:")
        print(f"   API Docs:    http://localhost:8000/docs")
        print(f"   Orders API:  http://localhost:8000/api/orders/")
        print()
        print("Press Ctrl+C to exit | Auto-refresh every 5 seconds")
        print("=" * 80)
        
        time.sleep(5)

if __name__ == "__main__":
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")