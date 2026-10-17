"""
Force create all tables by running migrations properly
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

print("\n" + "="*60)
print("🔴 Creating All Tables in MySQL Database")
print("="*60 + "\n")

# Test connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()[0]
        print(f"✅ Connected to database: {db_name}")
        
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()[0]
        print(f"✅ MySQL Version: {version}\n")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

print("Running migrations...\n")

try:
    # Run migrations
    call_command('migrate', verbosity=2)
    
    print("\n" + "="*60)
    print("✅ Migrations completed!")
    print("="*60)
    
    # Show created tables
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        print(f"\n📊 Total tables created: {len(tables)}\n")
        
        if tables:
            print("Tables list:")
            for i, (table,) in enumerate(tables, 1):
                print(f"   {i}. {table}")
        else:
            print("⚠️ No tables found!")
            
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60 + "\n")
