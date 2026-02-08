#!/usr/bin/env python3
"""
Initialize Chainlit database tables.

Run this once to create the required tables for persistence.
Chainlit doesn't export SQLAlchemy models, so we create tables with raw SQL.
"""
import os
import asyncio
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# SQL statements to create Chainlit tables (based on Chainlit's sql_alchemy.py queries)
CREATE_TABLES_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    "id" UUID PRIMARY KEY,
    "identifier" TEXT NOT NULL UNIQUE,
    "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "metadata" JSONB DEFAULT '{}'::jsonb
);

-- Threads table
CREATE TABLE IF NOT EXISTS threads (
    "id" UUID PRIMARY KEY,
    "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "name" TEXT,
    "userId" UUID REFERENCES users("id") ON DELETE SET NULL,
    "userIdentifier" TEXT,
    "tags" TEXT[],
    "metadata" JSONB DEFAULT '{}'::jsonb
);

-- Steps table
CREATE TABLE IF NOT EXISTS steps (
    "id" UUID PRIMARY KEY,
    "name" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "threadId" UUID REFERENCES threads("id") ON DELETE CASCADE,
    "parentId" UUID,
    "streaming" BOOLEAN DEFAULT FALSE,
    "waitForAnswer" BOOLEAN DEFAULT FALSE,
    "isError" BOOLEAN DEFAULT FALSE,
    "metadata" JSONB DEFAULT '{}'::jsonb,
    "input" TEXT,
    "output" TEXT,
    "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "start" TIMESTAMP WITH TIME ZONE,
    "end" TIMESTAMP WITH TIME ZONE,
    "generation" JSONB,
    "showInput" TEXT,
    "indent" INTEGER DEFAULT 0,
    "language" TEXT
);

-- Elements table
CREATE TABLE IF NOT EXISTS elements (
    "id" UUID PRIMARY KEY,
    "threadId" UUID REFERENCES threads("id") ON DELETE CASCADE,
    "type" TEXT NOT NULL,
    "url" TEXT,
    "chainlitKey" TEXT,
    "name" TEXT NOT NULL,
    "display" TEXT,
    "objectKey" TEXT,
    "size" TEXT,
    "page" INTEGER,
    "language" TEXT,
    "forId" UUID,
    "mime" TEXT
);

-- Feedbacks table
CREATE TABLE IF NOT EXISTS feedbacks (
    "id" UUID PRIMARY KEY,
    "forId" UUID NOT NULL,
    "threadId" UUID REFERENCES threads("id") ON DELETE CASCADE,
    "value" INTEGER NOT NULL,
    "comment" TEXT
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_threads_userid ON threads("userId");
CREATE INDEX IF NOT EXISTS idx_threads_useridentifier ON threads("userIdentifier");
CREATE INDEX IF NOT EXISTS idx_steps_threadid ON steps("threadId");
CREATE INDEX IF NOT EXISTS idx_elements_threadid ON elements("threadId");
CREATE INDEX IF NOT EXISTS idx_feedbacks_threadid ON feedbacks("threadId");
CREATE INDEX IF NOT EXISTS idx_feedbacks_forid ON feedbacks("forId");
"""

async def init_database():
    """Create all required tables for Chainlit persistence using raw SQL."""

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

    print("Connecting to database...")

    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        # Create engine
        engine = create_async_engine(database_url, echo=False)

        # Create all tables using raw SQL
        async with engine.begin() as conn:
            await conn.execute(text(CREATE_TABLES_SQL))

        # Verify tables were created
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]

        print("\n✅ Database tables created successfully!")
        print("\nTables in database:")
        for table in tables:
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
