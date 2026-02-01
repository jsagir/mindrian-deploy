"""
JSON Schemas for Protocol Validation

Provides formal contracts for machine consumers of the A2A protocol.
"""

from pathlib import Path

SCHEMA_DIR = Path(__file__).parent

A2A_HANDOFF_SCHEMA = SCHEMA_DIR / "a2a_handoff_v1.json"
