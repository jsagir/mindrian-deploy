# Health Check

Run the Mindrian health check to verify all integrations are working.

```bash
python3 scripts/health_check.py
```

This verifies:
- AI API (Gemini)
- FileSearch RAG
- Neo4j LazyGraph
- Tavily search
- Supabase storage
- ElevenLabs TTS
- LangExtract
- Code integrity

Fix any failures before proceeding with development.

$ARGUMENTS
