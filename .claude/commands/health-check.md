Run the Mindrian health check protocol to verify all systems are operational.

Execute: `python3 scripts/health_check.py` from the mindrian-deploy directory.

This checks:
1. All environment variables (required, recommended, optional)
2. Google Gemini API (LLM + FileSearch RAG)
3. Neo4j LazyGraph (connection, node counts, Domain Selection graph, case studies)
4. Tavily Search API
5. Supabase (storage + persistence)
6. ElevenLabs TTS
7. Optional research APIs (SerpAPI, FRED, BLS, NewsMesh, Kaggle, ArXiv)
8. LangExtract (instant extraction + coaching hints)
9. Code integrity (syntax check all critical files + prompt imports)

Report any failures and suggest fixes.
