# oracle/clear_redis.py
"""
Clear Redis queue and cached tasks
"""

import redis
from app.config import settings

print("Connecting to Redis...")
print(f"Redis URL: {settings.REDIS_URL}")

try:
    # Connect to Redis
    r = redis.from_url(settings.REDIS_URL)
    
    # Ping to test connection
    r.ping()
    print("✅ Connected to Redis")
    
    # Get info about keys
    all_keys = r.keys('*')
    print(f"\nFound {len(all_keys)} keys in Redis")
    
    if all_keys:
        print("\nKeys:")
        for key in all_keys[:10]:  # Show first 10
            print(f"  - {key.decode() if isinstance(key, bytes) else key}")
        
        if len(all_keys) > 10:
            print(f"  ... and {len(all_keys) - 10} more")
    
    # Ask for confirmation
    print("\n⚠️  This will delete ALL data in Redis!")
    response = input("Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        # Flush all data
        r.flushall()
        print("✅ Redis cleared successfully")
        
        # Verify
        remaining = len(r.keys('*'))
        print(f"Remaining keys: {remaining}")
    else:
        print("❌ Operation cancelled")

except redis.ConnectionError:
    print("❌ Could not connect to Redis")
    print("\nIs Redis running?")
    print("If using tasks with SQLite broker, Redis isn't needed.")
    
except Exception as e:
    print(f"❌ Error: {e}")