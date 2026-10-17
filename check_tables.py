"""
Script to verify MySQL tables are created
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def check_tables():
    """Check all tables in database"""
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        print("\n" + "="*60)
        print("🔴 REDFUSION BLOOD DONOR - MySQL Database Tables")
        print("="*60)
        print(f"\n✅ Total Tables Created: {len(tables)}\n")
        
        # Group tables by app
        accounts_tables = []
        donors_tables = []
        hospitals_tables = []
        ngos_tables = []
        blood_tables = []
        camps_tables = []
        core_tables = []
        django_tables = []
        
        for i, (table,) in enumerate(tables, 1):
            if 'accounts' in table:
                accounts_tables.append(table)
            elif 'donor' in table:
                donors_tables.append(table)
            elif 'hospital' in table:
                hospitals_tables.append(table)
            elif 'ngo' in table:
                ngos_tables.append(table)
            elif 'blood' in table or 'donation' in table:
                blood_tables.append(table)
            elif 'camp' in table:
                camps_tables.append(table)
            elif 'core' in table or 'notification' in table:
                core_tables.append(table)
            else:
                django_tables.append(table)
        
        # Print grouped tables
        if accounts_tables:
            print("📁 ACCOUNTS APP:")
            for table in accounts_tables:
                print(f"   ✓ {table}")
        
        if donors_tables:
            print("\n📁 DONORS APP:")
            for table in donors_tables:
                print(f"   ✓ {table}")
        
        if hospitals_tables:
            print("\n📁 HOSPITALS APP:")
            for table in hospitals_tables:
                print(f"   ✓ {table}")
        
        if ngos_tables:
            print("\n📁 NGOs APP:")
            for table in ngos_tables:
                print(f"   ✓ {table}")
        
        if blood_tables:
            print("\n📁 BLOOD REQUESTS APP:")
            for table in blood_tables:
                print(f"   ✓ {table}")
        
        if camps_tables:
            print("\n📁 CAMPS APP:")
            for table in camps_tables:
                print(f"   ✓ {table}")
        
        if core_tables:
            print("\n📁 CORE APP:")
            for table in core_tables:
                print(f"   ✓ {table}")
        
        if django_tables:
            print("\n📁 DJANGO SYSTEM TABLES:")
            for table in django_tables:
                print(f"   ✓ {table}")
        
        print("\n" + "="*60)
        
        # Get database info
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()[0]
        print(f"📊 Database: {db_name}")
        
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()[0]
        print(f"🔧 MySQL Version: {version}")
        
        print("="*60)
        print("✅ All tables are ready!")
        print("="*60 + "\n")

if __name__ == '__main__':
    try:
        check_tables()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. MySQL server is running")
        print("2. Database 'blood_donor_db' exists")
        print("3. Credentials in .env are correct")
