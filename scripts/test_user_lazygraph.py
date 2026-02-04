#!/usr/bin/env python3
"""
Test Per-User LazyGraph + LightRAG Integration
================================================

Quick verification that the user memory system works.

Usage:
  python scripts/test_user_lazygraph.py
"""

import asyncio
import os
import sys

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_user_lazygraph():
    print("=" * 60)
    print("Testing Per-User LazyGraph Memory")
    print("=" * 60)

    # Test imports
    print("\n[1/5] Testing imports...")
    try:
        from tools.user_lazygraph import (
            load_user_memory,
            store_session,
            store_problem,
            extract_entities_lightrag,
            UserSession,
            UserProblem,
            get_cache_stats,
        )
        print("  ✅ user_lazygraph imports OK")
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return

    try:
        from tools.opportunity_bank_lightrag import (
            push_opportunity_to_lightrag,
            extract_domain_relevancy,
        )
        print("  ✅ opportunity_bank_lightrag imports OK")
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return

    try:
        from tools.session_memory import (
            on_session_start,
            on_message_processed,
            get_user_context,
        )
        print("  ✅ session_memory imports OK")
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return

    # Test Neo4j connection
    print("\n[2/5] Testing Neo4j connection...")
    from tools.user_lazygraph import _get_neo4j
    driver = _get_neo4j()
    if driver:
        print("  ✅ Neo4j connection OK")
        try:
            with driver.session() as session:
                result = session.run("RETURN 1 AS test")
                record = result.single()
                print(f"  ✅ Neo4j query test: {record['test']}")
        except Exception as e:
            print(f"  ⚠️ Neo4j query error: {e}")
    else:
        print("  ⚠️ Neo4j not configured (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)")

    # Test LightRAG connection
    print("\n[3/5] Testing LightRAG connection...")
    from tools.user_lazygraph import _get_lightrag_session
    try:
        session = _get_lightrag_session()
        if session:
            print("  ✅ LightRAG login OK")
        else:
            print("  ⚠️ LightRAG not available")
    except Exception as e:
        print(f"  ⚠️ LightRAG error: {e}")

    # Test entity extraction
    print("\n[4/5] Testing entity extraction...")
    if os.getenv("GOOGLE_API_KEY"):
        test_text = """
        I'm exploring urban farming as a problem domain.
        The key assumption is that vertical farming will be cost-effective.
        Using JTBD framework to analyze customer needs.
        """
        try:
            entities = await extract_entities_lightrag(test_text)
            print(f"  ✅ Extracted entities:")
            print(f"     Problems: {entities.get('problems', [])}")
            print(f"     Assumptions: {entities.get('assumptions', [])}")
            print(f"     Frameworks: {entities.get('frameworks', [])}")
            print(f"     Domains: {entities.get('domains', [])}")
        except Exception as e:
            print(f"  ⚠️ Extraction error: {e}")
    else:
        print("  ⚠️ GOOGLE_API_KEY not set (skip extraction test)")

    # Test user memory flow
    print("\n[5/5] Testing user memory flow...")
    test_user_id = "test_user@example.com"
    test_session_id = "test_session_123"

    try:
        # Start session
        context = await on_session_start(
            user_id=test_user_id,
            session_id=test_session_id,
            bot_id="lawrence"
        )
        print(f"  ✅ Session started: {context or 'New user'}")

        # Process a message
        test_conversation = [
            {"role": "user", "content": "I want to explore urban farming opportunities"},
            {"role": "model", "content": "That's an interesting domain. What specific aspect interests you?"},
        ]

        result = await on_message_processed(
            user_id=test_user_id,
            session_id=test_session_id,
            conversation=test_conversation,
            bot_id="lawrence",
            force=True  # Force immediate processing
        )

        if result:
            print(f"  ✅ Message processed:")
            print(f"     Extracted: {result.get('extracted', {})}")
            print(f"     Stored: {result.get('stored', {})}")
        else:
            print("  ⚠️ Message not processed (no entities)")

        # Load user memory
        memory = await load_user_memory(test_user_id)
        print(f"  ✅ User memory loaded:")
        print(f"     Sessions: {len(memory.sessions)}")
        print(f"     Problems: {len(memory.problems)}")
        print(f"     Assumptions: {len(memory.assumptions)}")
        print(f"     Frameworks: {memory.frameworks_used}")

        # Get cache stats
        stats = get_cache_stats()
        print(f"  ✅ Cache stats: {stats}")

    except Exception as e:
        import traceback
        print(f"  ❌ Memory flow error: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_user_lazygraph())
