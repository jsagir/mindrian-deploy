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

# SQL statements to create Chainlit tables - matching Chainlit's expected schema
# Chainlit uses TEXT for IDs and timestamps, not UUID/TIMESTAMP
CREATE_STATEMENTS = [
    # Drop old tables if they have wrong schema
    """DROP TABLE IF EXISTS feedbacks CASCADE""",
    """DROP TABLE IF EXISTS elements CASCADE""",
    """DROP TABLE IF EXISTS steps CASCADE""",
    """DROP TABLE IF EXISTS threads CASCADE""",
    """DROP TABLE IF EXISTS users CASCADE""",
    # Create with correct Chainlit schema
    """CREATE TABLE users (
        "id" TEXT PRIMARY KEY,
        "identifier" TEXT NOT NULL UNIQUE,
        "createdAt" TEXT,
        "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb
    )""",
    """CREATE TABLE threads (
        "id" TEXT PRIMARY KEY,
        "createdAt" TEXT,
        "name" TEXT,
        "userId" TEXT REFERENCES users("id") ON DELETE SET NULL,
        "userIdentifier" TEXT,
        "tags" TEXT[],
        "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb
    )""",
    """CREATE TABLE steps (
        "id" TEXT PRIMARY KEY,
        "name" TEXT NOT NULL,
        "type" TEXT NOT NULL,
        "threadId" TEXT REFERENCES threads("id") ON DELETE CASCADE,
        "parentId" TEXT,
        "streaming" BOOLEAN,
        "waitForAnswer" BOOLEAN,
        "isError" BOOLEAN,
        "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
        "tags" TEXT[],
        "input" TEXT,
        "output" TEXT,
        "createdAt" TEXT,
        "start" TEXT,
        "end" TEXT,
        "generation" JSONB,
        "showInput" TEXT,
        "language" TEXT
    )""",
    """CREATE TABLE elements (
        "id" TEXT PRIMARY KEY,
        "threadId" TEXT REFERENCES threads("id") ON DELETE CASCADE,
        "type" TEXT NOT NULL,
        "chainlitKey" TEXT,
        "url" TEXT,
        "objectKey" TEXT,
        "name" TEXT NOT NULL,
        "display" TEXT,
        "size" TEXT,
        "language" TEXT,
        "page" INTEGER,
        "forId" TEXT,
        "mime" TEXT,
        "props" JSONB,
        "autoPlay" BOOLEAN,
        "playerConfig" JSONB
    )""",
    """CREATE TABLE feedbacks (
        "id" TEXT PRIMARY KEY,
        "forId" TEXT NOT NULL,
        "threadId" TEXT REFERENCES threads("id") ON DELETE CASCADE,
        "value" INTEGER NOT NULL,
        "comment" TEXT
    )""",
    """CREATE INDEX IF NOT EXISTS idx_threads_userid ON threads("userId")""",
    """CREATE INDEX IF NOT EXISTS idx_threads_useridentifier ON threads("userIdentifier")""",
    """CREATE INDEX IF NOT EXISTS idx_steps_threadid ON steps("threadId")""",
    """CREATE INDEX IF NOT EXISTS idx_elements_threadid ON elements("threadId")""",
    """CREATE INDEX IF NOT EXISTS idx_feedbacks_threadid ON feedbacks("threadId")""",
    """CREATE INDEX IF NOT EXISTS idx_feedbacks_forid ON feedbacks("forId")""",
]

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

        # Create all tables using raw SQL - one statement at a time for asyncpg
        async with engine.begin() as conn:
            for stmt in CREATE_STATEMENTS:
                await conn.execute(text(stmt))

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
