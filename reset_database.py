# recreate_db.py
import asyncio
import asyncpg
from app.config import settings

async def recreate_database():
    print("Recreating database...")
    
    try:
        # Connect to default postgres database
        conn = await asyncpg.connect(
            user='postgres',
            password='postman',  # Your password
            database='postgres',  # Connect to default database
            host='localhost'
        )
        
        # Terminate all connections to 'relay' database
        print("1. Terminating connections to 'relay' database...")
        await conn.execute("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = 'relay' AND pid <> pg_backend_pid()
        """)
        
        # Drop and recreate the database
        print("2. Dropping 'relay' database...")
        await conn.execute('DROP DATABASE IF EXISTS relay')
        
        print("3. Creating 'relay' database...")
        await conn.execute('CREATE DATABASE relay')
        
        await conn.close()
        print("✅ Database 'relay' recreated successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(recreate_database())