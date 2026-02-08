#!/usr/bin/env python3
"""
Initialize Chainlit database tables.

Run this once to create the required tables for persistence.
"""
import os
import asyncio
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def init_database():
    """Create all required tables for Chainlit persistence."""
    
    # Get database URL
    database_url = os.getenv("CHAINLIT_DATABASE_URL") or os.getenv("DATABASE_URL")
    
    if not database_url:
        print("ERROR: No DATABASE_URL or CHAINLIT_DATABASE_URL set")
        return False
    
    # Convert to asyncpg format
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    print(f"Connecting to database...")
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
        
        # Create engine
        engine = create_async_engine(database_url, echo=True)
        
        # Get metadata from Chainlit's data layer
        from chainlit.data.sql_alchemy import Base
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("\n✅ Database tables created successfully!")
        print("\nTables created:")
        for table in Base.metadata.tables:
            print(f"  - {table}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(init_database())
    sys.exit(0 if success else 1)
