"""
Stage 5: Expert Panel Discussion
================================
Multi-agent panel discussion using Gemini for persona simulation.

4 Rounds:
1. Domain Presentations (each expert presents findings)
2. Cross-Domain Connections (identify synergies)
3. Breakthrough Ideation (collaborative design)
4. Implementation Planning (concrete next steps)
"""

import asyncio
from typing import Dict, List, Any, Optional
import google.generativeai as genai


async def simulate_expert_response(
    persona: Dict,
    prompt: str,
    context: str = "",
    model_name: str = "gemini-2.0-flash"
) -> str:
    """
    Simulate an expert persona's response using Gemini.

    Args:
        persona: Persona dict with expertise and hat info
        prompt: The prompt/question for the expert
        context: Additional context (research findings, etc.)
        model_name: Gemini model to use

    Returns:
        Expert's response as string
    """
    hat_info = persona.get("thinking_hat", {})
    hat_instruction = ""
    if hat_info:
        hat_instruction = f"""
You are wearing the {hat_info.get('name', 'White Hat')} - your thinking mode is {hat_info.get('mode', 'objective')}.
Focus on: {hat_info.get('focus', 'facts and information')}.
Key questions you ask: {', '.join(persona.get('hat_questions', [])[:3])}
"""

    system_prompt = f"""You are {persona['name']}, an expert in {persona['primaryExpertise']}.
Expertise depth: {persona['expertiseDepth']}
{hat_instruction}
Your competencies: {', '.join(persona['competencies']['core'][:5])}
Research approach: {persona['researchApproach']['primary']}

Your role in this panel: {persona['collaborationStyle']['role']}
{persona['collaborationStyle']['approach']}

Respond concisely (2-3 paragraphs max) from your expert perspective.
Focus on actionable insights, not generic observations.
Never use real human names - you are an expertise-based persona.
"""

    try:
        model = genai.GenerativeModel(model_name)
        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        response = await asyncio.to_thread(
            model.generate_content,
            [
                {"role": "user", "parts": [{"text": system_prompt}]},
                {"role": "model", "parts": [{"text": "I understand my role and will respond from this expert perspective."}]},
                {"role": "user", "parts": [{"text": full_prompt}]},
            ]
        )

        return response.text if response.text else "[No response generated]"

    except Exception as e:
        return f"[Expert response error: {str(e)[:100]}]"


async def run_round_1_presentations(
    personas: List[Dict],
    research_findings: Dict[str, List],
    model_name: str = "gemini-2.0-flash"
) -> Dict[str, str]:
    """
    Round 1: Each expert presents domain findings.

    Args:
        personas: List of persona dicts
        research_findings: Dict mapping persona names to their findings
        model_name: Gemini model

    Returns:
        Dict mapping persona names to their presentations
    """
    presentations = {}

    async def get_presentation(persona):
        findings = research_findings.get(persona["name"], [])
        findings_text = "\n".join([
            f"- {f.get('title', 'Finding')}: {f.get('content', f.get('snippet', ''))[:200]}"
            for f in findings[:5]
        ]) if findings else "No specific findings yet."

        prompt = f"""Based on these research findings from your domain perspective:

{findings_text}

Present your 3 most important insights for the panel. What does your domain expertise reveal about this challenge? What patterns do you see?"""

        return persona["name"], await simulate_expert_response(
            persona, prompt, model_name=model_name
        )

    # Run in parallel
    tasks = [get_presentation(p) for p in personas]
    results = await asyncio.gather(*tasks)

    for name, presentation in results:
        presentations[name] = presentation

    return presentations


async def run_round_2_connections(
    personas: List[Dict],
    presentations: Dict[str, str],
    model_name: str = "gemini-2.0-flash"
) -> List[Dict]:
    """
    Round 2: Identify cross-domain connections.

    Integration architect leads, others contribute.
    """
    connections = []

    # Find integration architect
    integrator = next(
        (p for p in personas if "Integration" in p["name"]),
        personas[0]  # Fallback to first persona
    )

    # Compile all presentations
    all_presentations = "\n\n".join([
        f"**{name}**:\n{pres}"
        for name, pres in presentations.items()
    ])

    prompt = f"""Review all expert presentations and identify cross-domain connections:

{all_presentations}

Identify:
1. Where do different domains converge?
2. What synergies exist between domains?
3. What conflicts or tensions need resolution?
4. What unexpected connections emerge?

List 3-5 specific cross-domain connections with evidence."""

    response = await simulate_expert_response(
        integrator, prompt, model_name=model_name
    )

    connections.append({
        "identified_by": integrator["name"],
        "connections": response,
    })

    return connections


async def run_round_3_ideation(
    personas: List[Dict],
    presentations: Dict[str, str],
    connections: List[Dict],
    model_name: str = "gemini-2.0-flash"
) -> List[Dict]:
    """
    Round 3: Breakthrough ideation.

    All experts contribute breakthrough ideas.
    """
    breakthroughs = []

    # Compile context
    connections_text = "\n".join([c["connections"] for c in connections])

    # Get breakthrough ideas from key personas
    key_personas = [
        p for p in personas
        if p["expertiseDepth"] == "AUTHORITY" or "Integration" in p["name"]
    ][:3]

    async def get_breakthrough(persona):
        prompt = f"""Based on the cross-domain connections identified:

{connections_text}

From your {persona['primaryExpertise']} perspective (wearing {persona.get('thinking_hat', {}).get('name', 'no hat')}):

Propose 1-2 breakthrough opportunities that emerge from these domain intersections.
For each breakthrough:
- Name it clearly
- Explain why it's transformative
- Rate: breakthrough potential (1-10), feasibility (1-10), cross-domain impact (1-10)
- List 2-3 implementation steps"""

        response = await simulate_expert_response(
            persona, prompt, model_name=model_name
        )
        return {
            "proposed_by": persona["name"],
            "hat": persona.get("thinking_hat", {}).get("name", "None"),
            "ideas": response,
        }

    tasks = [get_breakthrough(p) for p in key_personas]
    breakthroughs = await asyncio.gather(*tasks)

    return list(breakthroughs)


async def run_round_4_implementation(
    personas: List[Dict],
    breakthroughs: List[Dict],
    model_name: str = "gemini-2.0-flash"
) -> Dict[str, Any]:
    """
    Round 4: Implementation planning.

    Focus on concrete next steps for top breakthroughs.
    """
    # Find methodology expert for validation
    validator = next(
        (p for p in personas if "Methodology" in p["name"]),
        personas[-1]
    )

    # Compile breakthroughs
    breakthroughs_text = "\n\n".join([
        f"From {b['proposed_by']} ({b['hat']}):\n{b['ideas']}"
        for b in breakthroughs
    ])

    prompt = f"""Review all proposed breakthroughs:

{breakthroughs_text}

As the methodology validator, provide:
1. Which breakthroughs pass validation? Why?
2. What are the risks for each?
3. Concrete implementation roadmap (phases, timeline)
4. Success criteria and metrics
5. What additional research is needed?"""

    implementation = await simulate_expert_response(
        validator, prompt, model_name=model_name
    )

    return {
        "validator": validator["name"],
        "implementation_plan": implementation,
        "breakthroughs_reviewed": len(breakthroughs),
    }


async def run_expert_panel(
    personas: List[Dict],
    research_findings: Dict[str, List],
    model_name: str = "gemini-2.0-flash",
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Run full 4-round expert panel discussion.

    Args:
        personas: List of persona dicts
        research_findings: Dict mapping persona names to findings
        model_name: Gemini model to use
        progress_callback: Optional async callback for progress updates

    Returns:
        Complete panel findings
    """
    if progress_callback:
        await progress_callback("Starting Round 1: Domain Presentations...")

    # Round 1
    presentations = await run_round_1_presentations(
        personas, research_findings, model_name
    )

    if progress_callback:
        await progress_callback("Round 1 complete. Starting Round 2: Cross-Domain Connections...")

    # Round 2
    connections = await run_round_2_connections(
        personas, presentations, model_name
    )

    if progress_callback:
        await progress_callback("Round 2 complete. Starting Round 3: Breakthrough Ideation...")

    # Round 3
    breakthroughs = await run_round_3_ideation(
        personas, presentations, connections, model_name
    )

    if progress_callback:
        await progress_callback("Round 3 complete. Starting Round 4: Implementation Planning...")

    # Round 4
    implementation = await run_round_4_implementation(
        personas, breakthroughs, model_name
    )

    if progress_callback:
        await progress_callback("Expert panel complete!")

    return {
        "rounds": {
            "round_1_presentations": presentations,
            "round_2_connections": connections,
            "round_3_breakthroughs": breakthroughs,
            "round_4_implementation": implementation,
        },
        "panel_size": len(personas),
        "breakthroughs": breakthroughs,
        "expert_insights": [
            {"persona": name, "insight": pres[:500]}
            for name, pres in presentations.items()
        ],
        "cross_domain_connections": connections,
    }
