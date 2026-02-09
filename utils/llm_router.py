"""
LLM Router - Hybrid Claude/Gemini Model Strategy
=================================================

Routes tasks to the optimal model based on complexity:
- Claude Opus 4.5: Orchestration, classification, reasoning, conclusions
- Gemini Flash: Bulk generation, summarization, extraction

Includes comprehensive cost tracking for all API calls.
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Literal, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from functools import wraps

logger = logging.getLogger("llm_router")

# ============================================================================
# COST TRACKING
# ============================================================================

@dataclass
class APICallRecord:
    """Single API call record."""
    timestamp: str
    model: str
    provider: str  # anthropic, google, tavily
    task_type: str  # orchestration, bulk, search
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """
    Tracks API costs across all providers.
    Persists daily summaries to Supabase.
    """

    # Pricing per 1K tokens (as of Feb 2026)
    PRICING = {
        # Claude models
        "claude-opus-4-5-20250514": {"input": 0.015, "output": 0.075},
        "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
        "claude-haiku-3-5-20250514": {"input": 0.0008, "output": 0.004},

        # Gemini models
        "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},
        "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},

        # Tavily (per search)
        "tavily-basic": {"per_call": 0.001},
        "tavily-advanced": {"per_call": 0.002},
    }

    def __init__(self):
        self.calls: List[APICallRecord] = []
        self.daily_totals: Dict[str, Dict] = {}
        self._session_start = datetime.now()

    def record_call(
        self,
        model: str,
        provider: str,
        task_type: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0,
        success: bool = True,
        error: str = None,
        metadata: Dict = None,
    ) -> float:
        """Record an API call and return cost."""

        # Calculate cost
        if provider == "tavily":
            pricing = self.PRICING.get(model, self.PRICING["tavily-basic"])
            cost = pricing.get("per_call", 0.001)
        else:
            pricing = self.PRICING.get(model, {"input": 0.001, "output": 0.004})
            cost = (
                (input_tokens / 1000) * pricing["input"] +
                (output_tokens / 1000) * pricing["output"]
            )

        record = APICallRecord(
            timestamp=datetime.now().isoformat(),
            model=model,
            provider=provider,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            success=success,
            error=error,
            metadata=metadata or {},
        )

        self.calls.append(record)
        self._update_daily_totals(record)

        logger.info(
            f"[COST] {provider}/{model} | {task_type} | "
            f"tokens: {input_tokens}+{output_tokens} | "
            f"cost: ${cost:.6f} | latency: {latency_ms}ms"
        )

        return cost

    def _update_daily_totals(self, record: APICallRecord):
        """Update daily totals."""
        today = date.today().isoformat()

        if today not in self.daily_totals:
            self.daily_totals[today] = {
                "total_cost": 0.0,
                "by_provider": {},
                "by_task": {},
                "call_count": 0,
                "errors": 0,
            }

        day = self.daily_totals[today]
        day["total_cost"] += record.cost_usd
        day["call_count"] += 1

        if not record.success:
            day["errors"] += 1

        # By provider
        if record.provider not in day["by_provider"]:
            day["by_provider"][record.provider] = {"cost": 0.0, "calls": 0}
        day["by_provider"][record.provider]["cost"] += record.cost_usd
        day["by_provider"][record.provider]["calls"] += 1

        # By task
        if record.task_type not in day["by_task"]:
            day["by_task"][record.task_type] = {"cost": 0.0, "calls": 0}
        day["by_task"][record.task_type]["cost"] += record.cost_usd
        day["by_task"][record.task_type]["calls"] += 1

    def get_session_summary(self) -> Dict:
        """Get summary for current session."""
        total_cost = sum(r.cost_usd for r in self.calls)
        total_calls = len(self.calls)

        by_provider = {}
        by_task = {}

        for r in self.calls:
            if r.provider not in by_provider:
                by_provider[r.provider] = {"cost": 0.0, "calls": 0, "tokens": 0}
            by_provider[r.provider]["cost"] += r.cost_usd
            by_provider[r.provider]["calls"] += 1
            by_provider[r.provider]["tokens"] += r.input_tokens + r.output_tokens

            if r.task_type not in by_task:
                by_task[r.task_type] = {"cost": 0.0, "calls": 0}
            by_task[r.task_type]["cost"] += r.cost_usd
            by_task[r.task_type]["calls"] += 1

        return {
            "session_start": self._session_start.isoformat(),
            "total_cost_usd": total_cost,
            "total_calls": total_calls,
            "by_provider": by_provider,
            "by_task": by_task,
            "errors": sum(1 for r in self.calls if not r.success),
        }

    def format_summary(self) -> str:
        """Format summary as markdown."""
        s = self.get_session_summary()

        lines = [
            "## API Cost Summary",
            f"**Session:** {s['session_start'][:19]}",
            f"**Total Cost:** ${s['total_cost_usd']:.4f}",
            f"**Total Calls:** {s['total_calls']} ({s['errors']} errors)",
            "",
            "### By Provider",
        ]

        for provider, data in s["by_provider"].items():
            lines.append(f"- **{provider}**: ${data['cost']:.4f} ({data['calls']} calls, {data['tokens']} tokens)")

        lines.append("")
        lines.append("### By Task")

        for task, data in s["by_task"].items():
            lines.append(f"- **{task}**: ${data['cost']:.4f} ({data['calls']} calls)")

        return "\n".join(lines)

    async def persist_to_supabase(self, user_id: str = None):
        """Persist session costs to Supabase."""
        try:
            from supabase import create_client

            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")

            if not url or not key:
                logger.warning("Supabase not configured, skipping cost persistence")
                return

            supabase = create_client(url, key)
            summary = self.get_session_summary()

            supabase.table("api_cost_tracking").insert({
                "user_id": user_id,
                "session_start": summary["session_start"],
                "total_cost_usd": summary["total_cost_usd"],
                "total_calls": summary["total_calls"],
                "by_provider": summary["by_provider"],
                "by_task": summary["by_task"],
                "errors": summary["errors"],
                "created_at": datetime.now().isoformat(),
            }).execute()

            logger.info(f"[COST] Persisted session costs: ${summary['total_cost_usd']:.4f}")

        except Exception as e:
            logger.error(f"[COST] Failed to persist costs: {e}")


# Global cost tracker
cost_tracker = CostTracker()


# ============================================================================
# LLM CLIENTS
# ============================================================================

def get_claude_client():
    """Lazy-load Anthropic client."""
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=api_key)


def get_gemini_client():
    """Lazy-load Gemini client."""
    from google import genai
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    return genai.Client(api_key=api_key)


# ============================================================================
# LLM ROUTER
# ============================================================================

class LLMRouter:
    """
    Routes tasks to optimal LLM based on complexity.

    Strategy:
    - Claude Opus: Orchestration, classification, reasoning, conclusions
    - Claude Sonnet: Moderate complexity routing decisions
    - Gemini Flash: Bulk generation, summarization, extraction
    """

    # Model selection
    ORCHESTRATION_MODEL = "claude-opus-4-5-20250514"
    ROUTING_MODEL = "claude-sonnet-4-20250514"
    BULK_MODEL = "gemini-2.5-flash"

    @staticmethod
    async def orchestrate(
        prompt: str,
        system: str = None,
        task_type: str = "orchestration",
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> str:
        """
        Use Claude Opus for orchestration decisions.
        High-stakes tasks requiring complex reasoning.
        """
        import time
        start = time.time()

        try:
            client = get_claude_client()

            response = client.messages.create(
                model=LLMRouter.ORCHESTRATION_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system or "You are a PWS methodology orchestrator. Be precise and structured.",
                messages=[{"role": "user", "content": prompt}]
            )

            latency = int((time.time() - start) * 1000)

            # Track cost
            cost_tracker.record_call(
                model=LLMRouter.ORCHESTRATION_MODEL,
                provider="anthropic",
                task_type=task_type,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=latency,
                success=True,
            )

            return response.content[0].text

        except Exception as e:
            latency = int((time.time() - start) * 1000)
            cost_tracker.record_call(
                model=LLMRouter.ORCHESTRATION_MODEL,
                provider="anthropic",
                task_type=task_type,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency,
                success=False,
                error=str(e),
            )
            raise

    @staticmethod
    async def route_decision(
        prompt: str,
        system: str = None,
        task_type: str = "routing",
        max_tokens: int = 500,
    ) -> str:
        """
        Use Claude Sonnet for routing decisions.
        Moderate complexity, faster than Opus.
        """
        import time
        start = time.time()

        try:
            client = get_claude_client()

            response = client.messages.create(
                model=LLMRouter.ROUTING_MODEL,
                max_tokens=max_tokens,
                temperature=0.2,
                system=system or "You are a routing decision maker. Be concise.",
                messages=[{"role": "user", "content": prompt}]
            )

            latency = int((time.time() - start) * 1000)

            cost_tracker.record_call(
                model=LLMRouter.ROUTING_MODEL,
                provider="anthropic",
                task_type=task_type,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=latency,
                success=True,
            )

            return response.content[0].text

        except Exception as e:
            latency = int((time.time() - start) * 1000)
            cost_tracker.record_call(
                model=LLMRouter.ROUTING_MODEL,
                provider="anthropic",
                task_type=task_type,
                latency_ms=latency,
                success=False,
                error=str(e),
            )
            raise

    @staticmethod
    async def bulk_generate(
        prompt: str,
        task_type: str = "bulk",
        max_tokens: int = 1000,
        temperature: float = 0.4,
    ) -> str:
        """
        Use Gemini Flash for single bulk generation.
        Fast and cheap.
        """
        import time
        from google.genai import types

        start = time.time()

        try:
            client = get_gemini_client()

            response = client.models.generate_content(
                model=LLMRouter.BULK_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            latency = int((time.time() - start) * 1000)

            # Estimate tokens (Gemini doesn't always return usage)
            input_tokens = len(prompt) // 4
            output_tokens = len(response.text) // 4 if response.text else 0

            cost_tracker.record_call(
                model=LLMRouter.BULK_MODEL,
                provider="google",
                task_type=task_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency,
                success=True,
            )

            return response.text

        except Exception as e:
            latency = int((time.time() - start) * 1000)
            cost_tracker.record_call(
                model=LLMRouter.BULK_MODEL,
                provider="google",
                task_type=task_type,
                latency_ms=latency,
                success=False,
                error=str(e),
            )
            raise

    @staticmethod
    async def bulk_generate_parallel(
        prompts: List[str],
        task_type: str = "bulk_parallel",
        max_tokens: int = 500,
    ) -> List[str]:
        """
        Use Gemini Flash for parallel bulk generation.
        Executes all prompts concurrently.
        """
        async def single(prompt: str) -> str:
            return await LLMRouter.bulk_generate(
                prompt,
                task_type=task_type,
                max_tokens=max_tokens
            )

        return await asyncio.gather(*[single(p) for p in prompts], return_exceptions=True)

    @staticmethod
    async def classify_problem(
        problem: str,
        context: Dict = None,
    ) -> Dict:
        """
        Claude Opus classifies problem type with reasoning.
        Returns structured classification.
        """
        context = context or {}

        prompt = f"""Classify this problem for PWS (Problems Worth Solving) methodology.

PROBLEM STATEMENT:
{problem}

ADDITIONAL CONTEXT:
{json.dumps(context, indent=2) if context else "None provided"}

Analyze and return JSON:
{{
    "problem_type": "undefined|ill_defined|well_defined|wicked",
    "problem_type_reasoning": "Why this classification (2-3 sentences)",
    "cynefin_domain": "clear|complicated|complex|chaotic",
    "cynefin_reasoning": "Why this domain placement (2-3 sentences)",
    "wickedness_score": 0.0-1.0,
    "wickedness_indicators": ["indicator1", "indicator2"],
    "confidence": 0.0-1.0,
    "evidence": ["evidence1", "evidence2", "evidence3"],
    "recommended_first_step": "What to do first"
}}

Classification Guide:
- UNDEFINED: Broad opportunity space, scattered observations, not yet articulated
- ILL_DEFINED: General direction but lacks specificity, emerging opportunities
- WELL_DEFINED: Specific, measurable, falsifiable, Camera Test ready
- WICKED: No stopping rule, stakeholder-contested, interconnected

Cynefin Guide:
- CLEAR: Known solution, best practice applies
- COMPLICATED: Analyzable, expert knowledge needed
- COMPLEX: Emergent, requires probing and sensing
- CHAOTIC: Novel, requires immediate action to stabilize"""

        response = await LLMRouter.orchestrate(
            prompt,
            system="You are a PWS methodology expert. Classify problems rigorously.",
            task_type="classification",
        )

        # Parse JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response

            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            logger.error(f"Failed to parse classification response: {response[:200]}")
            return {
                "problem_type": "ill_defined",
                "cynefin_domain": "complicated",
                "wickedness_score": 0.5,
                "confidence": 0.3,
                "evidence": ["Classification parsing failed"],
                "error": "JSON parse failed",
            }

    @staticmethod
    async def generate_beautiful_questions(
        problem: str,
        problem_type: str,
        context: Dict = None,
    ) -> Dict:
        """
        Claude Opus generates Beautiful Questions tailored to problem type.
        """
        context = context or {}

        prompt = f"""Generate Beautiful Questions for this {problem_type} problem.

PROBLEM: {problem}

CONTEXT: {json.dumps(context, indent=2) if context else "None"}

Beautiful Questions Framework (Warren Berger):
- WHY questions: Dig into root causes, challenge assumptions
- WHAT IF questions: Explore possibilities, alternatives, combinations
- HOW questions: Move toward action, implementation, testing

Tailor to problem type:
- UNDEFINED: Focus on exploration, pattern recognition, future scenarios
- ILL_DEFINED: Focus on clarification, root causes, stakeholder needs
- WELL_DEFINED: Focus on validation, falsifiability, metrics
- WICKED: Focus on stakeholders, trade-offs, partial solutions

Return JSON:
{{
    "why_questions": [
        {{"question": "Why...", "purpose": "What this explores"}},
        {{"question": "Why...", "purpose": "What this explores"}},
        {{"question": "Why...", "purpose": "What this explores"}}
    ],
    "what_if_questions": [
        {{"question": "What if...", "purpose": "What this explores"}},
        {{"question": "What if...", "purpose": "What this explores"}},
        {{"question": "What if...", "purpose": "What this explores"}}
    ],
    "how_questions": [
        {{"question": "How might we...", "purpose": "What this enables"}},
        {{"question": "How could we...", "purpose": "What this enables"}},
        {{"question": "How would we...", "purpose": "What this enables"}}
    ],
    "priority_question": "The single most important question to answer first",
    "priority_reasoning": "Why this question matters most"
}}"""

        response = await LLMRouter.orchestrate(
            prompt,
            system="You are a Socratic educator. Generate thought-provoking questions.",
            task_type="beautiful_questions",
        )

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response

            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            logger.error(f"Failed to parse questions response: {response[:200]}")
            return {
                "why_questions": [{"question": "Why does this problem exist?", "purpose": "Root cause"}],
                "what_if_questions": [{"question": "What if we approached this differently?", "purpose": "Alternatives"}],
                "how_questions": [{"question": "How might we validate this?", "purpose": "Testing"}],
                "error": "JSON parse failed",
            }

    @staticmethod
    async def research_conclusion(
        question: str,
        evidence: List[Dict],
        context: Dict = None,
    ) -> Dict:
        """
        Claude Opus synthesizes research and draws conclusions.
        The most important orchestration task.
        """
        context = context or {}

        # Format evidence
        evidence_text = ""
        for i, e in enumerate(evidence[:10], 1):
            evidence_text += f"""
SOURCE {i}: {e.get('title', 'Untitled')}
URL: {e.get('url', 'N/A')}
SUMMARY: {e.get('summary', e.get('content', '')[:500])}
KEY FACTS: {e.get('facts', 'N/A')}
---"""

        prompt = f"""Analyze this research and provide a rigorous conclusion.

RESEARCH QUESTION: {question}

CONTEXT: {json.dumps(context, indent=2) if context else "General research"}

GATHERED EVIDENCE:
{evidence_text}

ANALYSIS REQUIRED:

1. **Evidence Evaluation**
   - Rate overall evidence quality (strong/moderate/weak)
   - Identify most credible sources
   - Note any methodological concerns

2. **Pattern Detection**
   - What patterns emerge across sources?
   - Any surprising findings?
   - What do sources agree on? Disagree on?

3. **Gap Analysis**
   - What couldn't we find?
   - What questions remain unanswered?
   - What would strengthen our confidence?

4. **Contradiction Analysis**
   - Any conflicting information?
   - How do we resolve contradictions?
   - What explains the disagreements?

CONCLUSION REQUIRED:

5. **Key Finding** (1-2 sentences)
   The single most important insight from this research.

6. **Supporting Evidence** (3-5 bullets)
   Specific facts with source citations.

7. **Confidence Assessment**
   - Level: high/medium/low
   - Reasoning: Why this confidence level?

8. **PWS Implications**
   How does this relate to Problems Worth Solving?
   What does this mean for the user's journey?

9. **Recommended Next Steps** (3-5 actions)
   What should the user do with this information?

10. **New Questions Raised**
    What new questions did this research surface?

Return as structured markdown. Be rigorous. Acknowledge uncertainty."""

        response = await LLMRouter.orchestrate(
            prompt,
            system="""You are a senior research analyst with expertise in PWS methodology.
Synthesize evidence rigorously. Never overstate confidence.
Always cite sources. Acknowledge gaps and contradictions.
Your conclusions should be actionable and pedagogically valuable.""",
            task_type="research_conclusion",
            max_tokens=3000,
        )

        return {
            "conclusion": response,
            "sources_analyzed": len(evidence),
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# TAVILY INTEGRATION WITH COST TRACKING
# ============================================================================

class TrackedTavilySearch:
    """Tavily search with cost tracking."""

    @staticmethod
    async def search(
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_domains: List[str] = None,
        exclude_domains: List[str] = None,
    ) -> Dict:
        """Execute Tavily search with cost tracking."""
        import time
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not set")

        start = time.time()
        model = f"tavily-{search_depth}"

        try:
            client = TavilyClient(api_key=api_key)

            response = client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_domains=include_domains or [],
                exclude_domains=exclude_domains or [],
            )

            latency = int((time.time() - start) * 1000)

            cost_tracker.record_call(
                model=model,
                provider="tavily",
                task_type="web_search",
                latency_ms=latency,
                success=True,
                metadata={
                    "query": query[:100],
                    "results_count": len(response.get("results", [])),
                    "search_depth": search_depth,
                },
            )

            return {
                "query": query,
                "results": response.get("results", []),
                "answer": response.get("answer", ""),
            }

        except Exception as e:
            latency = int((time.time() - start) * 1000)
            cost_tracker.record_call(
                model=model,
                provider="tavily",
                task_type="web_search",
                latency_ms=latency,
                success=False,
                error=str(e),
                metadata={"query": query[:100]},
            )
            raise

    @staticmethod
    async def search_parallel(
        queries: List[str],
        search_depth: str = "basic",
        max_results: int = 5,
    ) -> List[Dict]:
        """Execute multiple Tavily searches in parallel."""
        async def single(query: str) -> Dict:
            return await TrackedTavilySearch.search(
                query,
                search_depth=search_depth,
                max_results=max_results,
            )

        return await asyncio.gather(*[single(q) for q in queries], return_exceptions=True)

    @staticmethod
    async def get_search_context(
        query: str,
        search_depth: str = "advanced",
        max_results: int = 5,
        max_tokens: int = 4000,
    ) -> str:
        """Get RAG-optimized context from Tavily."""
        import time
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Error: Tavily API key not configured"

        start = time.time()

        try:
            client = TavilyClient(api_key=api_key)

            context = client.get_search_context(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                max_tokens=max_tokens,
            )

            latency = int((time.time() - start) * 1000)

            cost_tracker.record_call(
                model=f"tavily-{search_depth}",
                provider="tavily",
                task_type="search_context",
                latency_ms=latency,
                success=True,
                metadata={"query": query[:100]},
            )

            return context

        except Exception as e:
            latency = int((time.time() - start) * 1000)
            cost_tracker.record_call(
                model=f"tavily-{search_depth}",
                provider="tavily",
                task_type="search_context",
                latency_ms=latency,
                success=False,
                error=str(e),
            )
            return f"Error: {str(e)}"


# ============================================================================
# RESEARCH PIPELINE (HYBRID)
# ============================================================================

class HybridResearchPipeline:
    """
    Full research pipeline using hybrid Claude/Gemini strategy.

    1. PLAN (Claude Opus): Query decomposition, strategy
    2. GATHER (Gemini Flash + Tavily): Parallel search and summarization
    3. ANALYZE & CONCLUDE (Claude Opus): Synthesis, conclusions
    """

    @staticmethod
    async def run(
        question: str,
        context: str = "",
        depth: str = "standard",  # quick, standard, deep
        problem_type: str = None,
    ) -> Dict:
        """Execute full hybrid research pipeline."""

        logger.info(f"[RESEARCH] Starting hybrid pipeline: {question[:50]}... (depth={depth})")

        # ═══════════════════════════════════════════════════════
        # PHASE 1: PLANNING (Claude Opus)
        # ═══════════════════════════════════════════════════════

        max_queries = {"quick": 3, "standard": 6, "deep": 10}.get(depth, 6)

        planning_prompt = f"""Plan a research strategy for this question.

QUESTION: {question}

CONTEXT: {context[:500] if context else "None provided"}

PROBLEM TYPE: {problem_type or "Unknown"}

DEPTH: {depth} (max {max_queries} queries)

Return JSON:
{{
    "queries": [
        {{"query": "specific search query", "purpose": "what this finds", "priority": 1-3}},
        ...
    ],
    "search_strategy": "basic|advanced",
    "key_entities": ["entity1", "entity2"],
    "validation_queries": ["query to challenge assumptions"],
    "expected_sources": ["type of sources expected"]
}}

Make queries specific and searchable (keywords, not questions).
Include recent time markers (2024, 2025) for current data."""

        plan_response = await LLMRouter.orchestrate(
            planning_prompt,
            system="You are a research strategist. Plan thorough, unbiased research.",
            task_type="research_planning",
        )

        try:
            if "```json" in plan_response:
                plan = json.loads(plan_response.split("```json")[1].split("```")[0])
            else:
                plan = json.loads(plan_response)
        except json.JSONDecodeError:
            logger.warning("[RESEARCH] Plan parsing failed, using fallback")
            plan = {
                "queries": [
                    {"query": question, "purpose": "main query", "priority": 1},
                    {"query": f"{question} 2024 2025", "purpose": "recent data", "priority": 2},
                ],
                "search_strategy": "basic",
            }

        # ═══════════════════════════════════════════════════════
        # PHASE 2: GATHERING (Tavily + Gemini Flash)
        # ═══════════════════════════════════════════════════════

        # Execute searches in parallel
        queries = [q["query"] for q in plan.get("queries", [])[:max_queries]]
        search_depth = plan.get("search_strategy", "basic")

        search_results = await TrackedTavilySearch.search_parallel(
            queries,
            search_depth=search_depth,
            max_results=5,
        )

        # Flatten results
        all_sources = []
        for result in search_results:
            if isinstance(result, dict) and "results" in result:
                all_sources.extend(result.get("results", []))

        if not all_sources:
            logger.warning("[RESEARCH] No sources found")
            return {
                "plan": plan,
                "sources": [],
                "conclusion": "No sources found for this query.",
                "cost_summary": cost_tracker.get_session_summary(),
            }

        # Gemini summarizes each source in parallel
        summarization_prompts = [
            f"Summarize this in 2-3 sentences, focusing on key facts:\n\nTitle: {s.get('title', 'Untitled')}\n\n{s.get('content', '')[:1500]}"
            for s in all_sources[:8]
        ]

        summaries = await LLMRouter.bulk_generate_parallel(
            summarization_prompts,
            task_type="source_summarization",
            max_tokens=200,
        )

        # Attach summaries to sources
        for i, source in enumerate(all_sources[:8]):
            if i < len(summaries) and not isinstance(summaries[i], Exception):
                source["summary"] = summaries[i]
            else:
                source["summary"] = source.get("content", "")[:200]

        # ═══════════════════════════════════════════════════════
        # PHASE 3: ANALYSIS & CONCLUSION (Claude Opus)
        # ═══════════════════════════════════════════════════════

        conclusion_result = await LLMRouter.research_conclusion(
            question=question,
            evidence=all_sources[:8],
            context={"problem_type": problem_type, "user_context": context[:300]},
        )

        return {
            "question": question,
            "plan": plan,
            "sources": all_sources,
            "summaries": summaries,
            "conclusion": conclusion_result["conclusion"],
            "sources_analyzed": conclusion_result["sources_analyzed"],
            "cost_summary": cost_tracker.get_session_summary(),
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_cost_summary() -> str:
    """Get formatted cost summary."""
    return cost_tracker.format_summary()


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker."""
    return cost_tracker


async def persist_costs(user_id: str = None):
    """Persist costs to database."""
    await cost_tracker.persist_to_supabase(user_id)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test():
        # Test classification
        result = await LLMRouter.classify_problem(
            "How can we deterministically create same-sized quantum dots for uniform emission wavelength?",
            context={"domain": "quantum computing", "industry": "semiconductor"}
        )
        print("Classification:", json.dumps(result, indent=2))

        # Test cost summary
        print("\n" + get_cost_summary())

    asyncio.run(test())
