"""
Dynamic Examples Fetcher
Pulls diverse examples from Neo4j case studies and Gemini File Search (T2/T3 tiers)
"""

import os
import random
from typing import Optional, List, Dict
from dataclasses import dataclass

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Bot to methodology mapping for Neo4j queries
BOT_TO_METHODOLOGY = {
    "tta": ["Trending to the Absurd", "TTA", "Trend Extrapolation"],
    "jtbd": ["Jobs to Be Done", "JTBD", "Job Mapping"],
    "scurve": ["S-Curve", "Technology Lifecycle", "Era of Ferment", "Dominant Design"],
    "redteam": ["Red Team", "Devil's Advocate", "Assumption Attack", "Bias Detection"],
    "ackoff": ["Ackoff", "DIKW", "Pyramid", "Data-Information-Knowledge-Wisdom", "Camera Test"],
    "larry": ["PWS", "Problem Worth Solving", "Innovation"],
}

# Bot to relevant case study topics
BOT_TO_CASE_TOPICS = {
    "tta": ["Refugee Permanence", "Total Urbanization", "Extreme Water", "Naval Aviation", "Remote Work"],
    "jtbd": ["Warby Parker", "Netflix Evolution", "LEGO", "milkshake", "drill"],
    "scurve": ["Electric Vehicle", "Smartphone", "Internet", "Streaming", "Battery"],
    "redteam": ["Target Canada", "Boeing 737", "Theranos", "WeWork"],
    "ackoff": ["Hospital Emergency Room", "Camera Test", "Information Darkness"],
    "larry": ["Warby Parker", "Netflix", "Hospital", "Innovation"],
}

# Fallback static examples (used when dynamic fetch fails)
STATIC_EXAMPLES = {
    "tta": [
        "**Refugee Permanence**: Brookings pushed the refugee trend to its absurd end - what if refugees never go home? This revealed problems in temporary-focused aid systems and led to innovations in permanent settlement support.",
        "**Total Urbanization**: What if no one lives outside of cities? This extreme scenario surfaces problems in food production, resource distribution, and human connection with nature.",
        "**Remote Work Extreme**: What if 95% of knowledge workers never set foot in an office? This forces thinking about problems that don't exist yet: virtual team bonding, 'zoom fatigue' solutions, home office ergonomics at scale.",
        "**Naval Aviation (1910-1941)**: The first plane launched from a ship looked absurd but foreshadowed the aircraft carrier revolution. Those who dismissed it as impractical missed the transformation coming.",
        "**Extreme Water Limitation**: What if you had only one liter of water per day? This extreme surfaces problems in hygiene, cooking, and municipal water systems that we take for granted.",
    ],
    "jtbd": [
        "**Warby Parker**: Reimagined eyewear shopping by understanding the job of 'confident glasses selection'. The functional job was 'see clearly', but the emotional job was 'feel stylish and confident' and the social job was 'look professional'.",
        "**Netflix Evolution**: Transformed from DVD delivery to streaming by understanding the job of 'effortless entertainment'. Customers weren't hiring DVDs - they were hiring a relaxing evening.",
        "**LEGO Platform**: Evolved from toy manufacturer to creativity platform by understanding the job hierarchy: kids want to 'feel creative', parents want 'quality time', and both want 'sense of accomplishment'.",
        "**The Milkshake Example**: McDonald's discovered people 'hire' milkshakes for the morning commute - the job was 'make my boring drive interesting' and 'keep me full until lunch', not 'have a dessert'.",
        "**The Drill Example**: People don't buy a drill for the drill. They don't even want a hole. They want to hang a picture. The functional job is 'hang picture', emotional job is 'feel competent', social job is 'please my partner'.",
    ],
    "scurve": [
        "**Electric Vehicles (2015-2020)**: In 2015, EVs were in the Era of Ferment - Tesla, Leaf, Bolt, and startups all competing. By 2020, a dominant design emerged around lithium-ion batteries and specific form factors. Now we're in incremental improvement mode.",
        "**Smartphone Evolution**: The iPhone launched during the Era of Ferment for smartphones (Palm, BlackBerry, Windows Mobile). Within 3 years, the dominant design crystallized: touchscreen, app store, rectangular form factor.",
        "**Streaming Wars**: Netflix's streaming launched in the Era of Ferment. Now we're past dominant design (subscription on-demand) and into incremental improvements (personalization, original content).",
        "**Battery Technology**: Solid-state batteries are in Era of Ferment today - multiple approaches competing. Watch for dominant design emergence to time your innovation investments.",
        "**Reverse Salient Concept**: In any technology system, one component limits overall progress. Identifying this bottleneck is where breakthrough innovation happens. What's YOUR reverse salient?",
    ],
    "redteam": [
        "**Assumption Attack**: 'You assume customers will pay $50/month. What if they only pay $20? What if there's a free alternative? What if the problem you're solving isn't painful enough to pay for at all?'",
        "**Target Canada Failure ($7B)**: Assumptions that worked in the US (supply chain, brand recognition, pricing) were never validated for Canadian market. Red teaming could have surfaced these blind spots.",
        "**Boeing 737 MAX**: Assumption that pilots would react correctly to MCAS system went unchallenged. Red teaming the human factors could have prevented the tragedies.",
        "**Survivorship Bias Attack**: 'You studied successful startups to find patterns. But did you study the failures with the SAME patterns who still failed? Your success factors might be coincidental.'",
        "**Hidden Constraint Exposure**: 'You assume your solution requires internet connectivity. What if 30% of your target users have unreliable internet? You've excluded them without realizing it.'",
    ],
    "ackoff": [
        "**Camera Test**: 'The line was long' is interpretation. '47 people in line at 12:15' is data. Could a camera record it? If not, it's interpretation, not observation. Always distinguish data from interpretation.",
        "**Hospital Emergency Room**: Patients complained about 'long wait times'. Data showed waits were average. The REAL problem was 'information darkness' - not knowing status. The camera test revealed this.",
        "**Pattern vs Causation**: 'Users leave when prices increase' is a pattern. 'Price increases CAUSE users to leave' is a causal claim we haven't verified. Don't confuse correlation with causation.",
        "**The 5 Whys**: Why do customers complain? → Wait times. Why long wait times? → Understaffed. Why understaffed? → Budget cuts. Why budget cuts? → Revenue down. Why revenue down? → Product-market fit issues. There's your root cause.",
        "**Climb-Down Validation**: Your solution traces cleanly to data—or it doesn't. If there's a gap at the Knowledge level, you're building on assumption, not evidence. That's when projects fail.",
        "**DIKW Ascent Example**: Data: '1,200 support tickets last month.' Information: '40% are password resets.' Knowledge: 'Password reset friction causes high ticket volume.' Wisdom: 'Self-service password reset reduces tickets and improves user experience.'",
    ],
    "larry": [
        "**Problem Before Solution**: The biggest innovation failures come from building solutions to problems that don't exist or don't matter. PWS methodology ensures you validate the problem's worthiness BEFORE investing in solutions.",
        "**Worthiness Criteria**: Market Size (how many affected?), Future Urgency (how urgent will it become?), Solvability (can it be solved?), Expertise Match (do you have the capabilities?), Impact Potential (magnitude of positive change if solved).",
        "**The Innovation Trinity**: Every innovation needs three things in alignment: a Problem worth solving, a Solution that addresses it, and a Business Case that makes it viable. Miss any one, and you fail.",
        "**Premature Solutioning Trap**: Most innovators fall in love with their solution before validating the problem. PWS methodology prevents this by enforcing problem-first thinking.",
        "**Is it Real? Can we Win? Is it Worth It?**: The three validation questions every innovation must answer. Real = problem exists and matters. Win = we can beat alternatives. Worth = returns justify investment.",
    ],
}


@dataclass
class Example:
    """Represents a single example."""
    title: str
    content: str
    source: str  # "neo4j", "filesearch", or "static"
    methodology: str


def get_neo4j_driver():
    """Get Neo4j driver if configured."""
    if not all([NEO4J_URI, NEO4J_PASSWORD]):
        return None
    try:
        from neo4j import GraphDatabase
        return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    except Exception as e:
        print(f"Neo4j connection failed: {e}")
        return None


async def fetch_neo4j_examples(bot_id: str, limit: int = 10) -> List[Example]:
    """Fetch case studies and examples from Neo4j for a specific bot."""
    driver = get_neo4j_driver()
    if not driver:
        return []

    examples = []
    topics = BOT_TO_CASE_TOPICS.get(bot_id, [])
    methodologies = BOT_TO_METHODOLOGY.get(bot_id, [])

    try:
        with driver.session() as session:
            # Query case studies related to this bot's topics
            query = """
            MATCH (cs:CaseStudy)
            WHERE cs.description IS NOT NULL
            AND (
                ANY(topic IN $topics WHERE toLower(cs.name) CONTAINS toLower(topic))
                OR ANY(method IN $methodologies WHERE EXISTS {
                    MATCH (cs)-[:APPLIED_FRAMEWORK|EXEMPLIFIED_BY]->(f:Framework)
                    WHERE toLower(f.name) CONTAINS toLower(method)
                })
            )
            RETURN cs.name as name, cs.description as description
            LIMIT $limit
            """
            result = session.run(query, topics=topics, methodologies=methodologies, limit=limit)

            for record in result:
                if record["description"]:
                    examples.append(Example(
                        title=record["name"],
                        content=f"**{record['name']}**: {record['description']}",
                        source="neo4j",
                        methodology=bot_id
                    ))

            # Also query for absurd scenarios if TTA
            if bot_id == "tta":
                absurd_query = """
                MATCH (n:AbsurdScenario)
                WHERE n.description IS NOT NULL
                RETURN n.name as name, n.description as description
                LIMIT 5
                """
                absurd_result = session.run(absurd_query)
                for record in absurd_result:
                    if record["description"]:
                        examples.append(Example(
                            title=record["name"] or "Absurd Scenario",
                            content=f"**Absurd Scenario**: {record['description']}",
                            source="neo4j",
                            methodology="tta"
                        ))

            # Query for Jobs if JTBD
            if bot_id == "jtbd":
                jobs_query = """
                MATCH (j:Job)
                WHERE j.description IS NOT NULL AND length(j.description) > 20
                RETURN j.name as name, j.description as description
                LIMIT 8
                """
                jobs_result = session.run(jobs_query)
                for record in jobs_result:
                    if record["description"]:
                        examples.append(Example(
                            title=record["name"] or "Job",
                            content=f"**Job to Be Done**: {record['description']}",
                            source="neo4j",
                            methodology="jtbd"
                        ))

    except Exception as e:
        print(f"Neo4j query error: {e}")
    finally:
        driver.close()

    return examples


async def fetch_filesearch_example(bot_id: str, phase: int = 0) -> Optional[Example]:
    """
    Fetch an example from Gemini File Search (T2/T3 tiers).
    Uses a targeted query to get diverse examples.
    """
    try:
        from google import genai
        from google.genai import types

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            return None

        client = genai.Client(api_key=api_key)

        # Build a query prompt based on bot and phase
        methodology_names = BOT_TO_METHODOLOGY.get(bot_id, ["PWS"])
        methodology = methodology_names[0]

        query_prompts = {
            "tta": f"Give me a specific real-world example of Trending to the Absurd methodology applied to identify future problems. Include the trend, the extreme scenario, and the problem revealed. Be specific with names and details. Use a DIFFERENT example than remote work.",
            "jtbd": f"Give me a specific case study example of Jobs to Be Done framework. Include the company, the functional job, emotional job, and social job discovered. Be specific. Use a DIFFERENT example than the drill or milkshake.",
            "scurve": f"Give me a specific example of S-Curve technology lifecycle analysis. Include the technology, what phase it's in (Era of Ferment, Dominant Design, or Incremental), and what that means for innovators. Use a DIFFERENT example than smartphones.",
            "redteam": f"Give me a specific red teaming or devil's advocate example that exposes hidden assumptions in a business case. Include the assumption attacked and what was revealed. Use a DIFFERENT example than Target Canada.",
            "ackoff": f"Give me a specific example of applying Ackoff's DIKW Pyramid to transform data into wisdom. Show each level of the pyramid with the example. Use a DIFFERENT example than the hospital emergency room.",
            "larry": f"Give me a specific example of validating whether a problem is 'worth solving' using PWS methodology. Include the worthiness criteria evaluation.",
        }

        query = query_prompts.get(bot_id, f"Give me a specific example of {methodology} methodology applied in practice.")

        # Add randomization to get different examples
        random_seed = random.choice(["from a tech industry", "from healthcare", "from retail", "from education", "from manufacturing", "from finance", "from government"])
        query += f" Focus on an example {random_seed}."

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=query,
            config=types.GenerateContentConfig(
                temperature=0.9,  # Higher temperature for variety
                max_output_tokens=500,
            )
        )

        if response.text:
            return Example(
                title="File Search Example",
                content=response.text.strip(),
                source="filesearch",
                methodology=bot_id
            )

    except Exception as e:
        print(f"File Search query error: {e}")

    return None


# Cache for examples to avoid repeated queries
_example_cache: Dict[str, List[Example]] = {}


async def get_diverse_example(bot_id: str, phase: int = 0, exclude_recent: List[str] = None) -> str:
    """
    Get a diverse example for the specified bot, avoiding recently shown examples.

    Combines:
    1. Neo4j case studies
    2. Gemini File Search (T2/T3 documentation)
    3. Static fallback examples

    Args:
        bot_id: The bot identifier (tta, jtbd, scurve, redteam, ackoff, larry)
        phase: Current workshop phase (for context)
        exclude_recent: List of example titles to exclude (to avoid repetition)

    Returns:
        Formatted example string
    """
    if exclude_recent is None:
        exclude_recent = []

    all_examples = []

    # 1. Try to get Neo4j examples (cached)
    cache_key = f"neo4j_{bot_id}"
    if cache_key not in _example_cache:
        neo4j_examples = await fetch_neo4j_examples(bot_id)
        _example_cache[cache_key] = neo4j_examples
    all_examples.extend(_example_cache.get(cache_key, []))

    # 2. Add static examples as reliable fallback
    static = STATIC_EXAMPLES.get(bot_id, [])
    for idx, content in enumerate(static):
        # Extract title from content (assumes **Title**: format)
        title = f"static_{bot_id}_{idx}"
        if "**" in content:
            title = content.split("**")[1] if len(content.split("**")) > 1 else title
        all_examples.append(Example(
            title=title,
            content=content,
            source="static",
            methodology=bot_id
        ))

    # 3. Filter out recently shown examples
    available = [e for e in all_examples if e.title not in exclude_recent]

    # 4. If we've shown all examples, reset and add a fresh File Search example
    if not available:
        available = all_examples
        # Get a fresh example from File Search for variety
        fs_example = await fetch_filesearch_example(bot_id, phase)
        if fs_example:
            available.insert(0, fs_example)  # Prioritize fresh example

    # 5. Randomly select from available examples
    if available:
        selected = random.choice(available)
        return selected.content

    # Fallback
    return f"No specific example available for {bot_id}. Try asking about a specific concept!"


def get_example_sync(bot_id: str, phase: int = 0) -> str:
    """Synchronous wrapper for getting examples (uses static only)."""
    static = STATIC_EXAMPLES.get(bot_id, [])
    if static:
        return random.choice(static)
    return "No example available for this methodology."


# Track recently shown examples per session
_session_shown_examples: Dict[str, List[str]] = {}


def track_shown_example(session_id: str, example_title: str):
    """Track which examples have been shown in a session."""
    if session_id not in _session_shown_examples:
        _session_shown_examples[session_id] = []
    _session_shown_examples[session_id].append(example_title)
    # Keep only last 10 to allow cycling
    _session_shown_examples[session_id] = _session_shown_examples[session_id][-10:]


def get_shown_examples(session_id: str) -> List[str]:
    """Get list of recently shown examples for a session."""
    return _session_shown_examples.get(session_id, [])


def clear_session_examples(session_id: str):
    """Clear shown examples for a session."""
    if session_id in _session_shown_examples:
        del _session_shown_examples[session_id]
