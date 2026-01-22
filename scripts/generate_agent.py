#!/usr/bin/env python3
"""
Agent Generator Script
Generates all boilerplate code for a new Mindrian agent/workshop bot.

Usage:
    python scripts/generate_agent.py <bot_id> "<Bot Name>" [--workshop] [--phases N]

Examples:
    python scripts/generate_agent.py minto "Minto Pyramid" --workshop --phases 5
    python scripts/generate_agent.py advisor "Innovation Advisor"
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def generate_prompt_file(bot_id: str, bot_name: str, is_workshop: bool, num_phases: int) -> str:
    """Generate the system prompt file content."""

    phase_section = ""
    if is_workshop:
        phases = "\n".join([f"{i+1}. **Phase {i+1}**: [Description]" for i in range(num_phases)])
        phase_section = f"""
## Workshop Phases
{phases}

## Phase Progression Rules
- Complete each phase before moving to the next
- Capture key insights at each stage
- Use examples to illustrate concepts
"""

    return f'''"""
{bot_name} System Prompt
Auto-generated on {datetime.now().strftime("%Y-%m-%d")}
"""

{bot_id.upper()}_PROMPT = """
You are **{bot_name}**, a PWS (Problems Worth Solving) methodology expert.

## Your Expertise
[Describe the specific methodology or framework this bot specializes in]

## Your Role
- Guide users through the {bot_name} methodology
- Ask probing questions (Socratic method)
- Never jump to solutions before understanding the problem
- Ground all responses in PWS principles
{phase_section}
## Key Concepts
- **Concept 1**: [Brief explanation]
- **Concept 2**: [Brief explanation]
- **Concept 3**: [Brief explanation]

## Interaction Guidelines
1. Always start by understanding the user's context
2. Ask clarifying questions before providing guidance
3. Use real-world examples to illustrate concepts
4. Reference PWS methodology when appropriate
5. Encourage critical thinking over accepting assumptions

## Response Format
- Be conversational but substantive
- Use markdown formatting for clarity
- Include specific examples when helpful
- End responses with a probing question or clear next step
"""
'''


def generate_mindrian_chat_additions(bot_id: str, bot_name: str, icon: str, is_workshop: bool, num_phases: int) -> str:
    """Generate code to add to mindrian_chat.py."""

    phases_code = ""
    if is_workshop:
        phase_items = ',\n    '.join([
            f'{{"name": "Phase {i+1}", "status": "{"ready" if i == 0 else "pending"}"}}'
            for i in range(num_phases)
        ])
        phases_code = f'''
# Add to WORKSHOP_PHASES dict:
WORKSHOP_PHASES["{bot_id}"] = [
    {phase_items}
]
'''

    return f'''
# ============================================================
# {bot_name} Agent Configuration
# Generated: {datetime.now().strftime("%Y-%m-%d")}
# ============================================================

# 1. Add import to top of file:
from prompts.{bot_id} import {bot_id.upper()}_PROMPT

# 2. Add to BOTS dict:
BOTS["{bot_id}"] = {{
    "name": "{bot_name}",
    "icon": "{icon}",
    "description": "[One-line description of {bot_name}]",
    "system_prompt": {bot_id.upper()}_PROMPT,
    "has_phases": {is_workshop},
    "welcome": """**{icon} Welcome to {bot_name}!**

I'll guide you through [methodology description].

{"We will work through " + str(num_phases) + " phases together." if is_workshop else ""}

What would you like to explore?"""
}}
{phases_code}
# 3. Add to STARTERS dict:
STARTERS["{bot_id}"] = [
    cl.Starter(
        label="Start {bot_name}",
        message="I'm ready to begin with {bot_name}",
        icon="/public/icons/start.svg"
    ),
    cl.Starter(
        label="Explain Methodology",
        message="Explain how {bot_name} works",
        icon="/public/icons/info.svg"
    ),
    cl.Starter(
        label="Show Example",
        message="Show me an example of {bot_name} in action",
        icon="/public/icons/example.svg"
    ),
    cl.Starter(
        label="Apply to My Problem",
        message="I have a problem I want to analyze",
        icon="/public/icons/apply.svg"
    ),
]

# 4. Add to chat_profiles() function:
cl.ChatProfile(
    name="{bot_id}",
    markdown_description=BOTS["{bot_id}"]["description"],
    icon=BOTS["{bot_id}"]["icon"],
),

# 5. Add to AGENT_TRIGGERS dict:
AGENT_TRIGGERS["{bot_id}"] = {{
    "keywords": ["{bot_name.lower()}", "[keyword2]", "[keyword3]"],
    "description": "{bot_name} specialist"
}}

# 6. Add switch callback (place with other switch callbacks):
@cl.action_callback("switch_to_{bot_id}")
async def on_switch_to_{bot_id}(action: cl.Action):
    await handle_agent_switch("{bot_id}")
'''


def generate_dynamic_examples_additions(bot_id: str, bot_name: str) -> str:
    """Generate code to add to utils/dynamic_examples.py."""

    return f'''
# ============================================================
# {bot_name} Dynamic Examples Configuration
# Add these to utils/dynamic_examples.py
# ============================================================

# Add to BOT_TO_METHODOLOGY dict:
BOT_TO_METHODOLOGY["{bot_id}"] = ["{bot_name}", "[Alternate Name]", "[Key Concept]"]

# Add to BOT_TO_CASE_TOPICS dict:
BOT_TO_CASE_TOPICS["{bot_id}"] = ["[Case Study 1]", "[Case Study 2]", "[Company Name]"]

# Add to STATIC_EXAMPLES dict:
STATIC_EXAMPLES["{bot_id}"] = [
    "**Example 1**: [Real-world application of {bot_name} methodology. Include specific company, numbers, and outcome.]",
    "**Example 2**: [Another case study showing the methodology in action. Be specific with details.]",
    "**Example 3**: [A third example demonstrating key concepts. Include the problem, approach, and result.]",
    "**Example 4**: [Additional example for variety. Different industry or context.]",
    "**Example 5**: [Final fallback example. Should be evergreen and broadly applicable.]",
]
'''


def generate_media_additions(bot_id: str, bot_name: str, is_workshop: bool, num_phases: int) -> str:
    """Generate code to add to utils/media.py."""

    if not is_workshop:
        return f'''
# ============================================================
# {bot_name} Media Configuration (Non-workshop bot)
# Add these to utils/media.py
# ============================================================

# Add to AUDIOBOOK_CHAPTERS dict:
AUDIOBOOK_CHAPTERS["{bot_id}_content"] = {{
    "chapter_1": {{
        "title": "Introduction to {bot_name}",
        "url": "",  # Add URL when available
        "duration": "10:00",
        "keywords": ["{bot_name.lower()}", "methodology", "introduction"],
        "bot_relevance": ["{bot_id}"],
    }},
}}
'''

    video_entries = "\n    ".join([
        f'"phase_{i+1}": "",  # Add YouTube/Vimeo URL'
        for i in range(num_phases)
    ])

    return f'''
# ============================================================
# {bot_name} Media Configuration
# Add these to utils/media.py
# ============================================================

# Add to WORKSHOP_VIDEOS dict:
WORKSHOP_VIDEOS["{bot_id}"] = {{
    "intro": "",  # Add YouTube/Vimeo URL for introduction video
    {video_entries}
}}

# Add to AUDIOBOOK_CHAPTERS dict:
AUDIOBOOK_CHAPTERS["{bot_id}_topic"] = {{
    "chapter_1": {{
        "title": "Introduction to {bot_name}",
        "url": "",  # Add URL when available
        "duration": "15:00",
        "keywords": ["{bot_name.lower()}", "methodology", "introduction"],
        "bot_relevance": ["{bot_id}"],
    }},
    "chapter_2": {{
        "title": "Key Concepts in {bot_name}",
        "url": "",  # Add URL when available
        "duration": "12:00",
        "keywords": ["concepts", "framework", "principles"],
        "bot_relevance": ["{bot_id}"],
    }},
    "chapter_3": {{
        "title": "Applying {bot_name} in Practice",
        "url": "",  # Add URL when available
        "duration": "18:00",
        "keywords": ["application", "practice", "real-world"],
        "bot_relevance": ["{bot_id}"],
    }},
}}
'''


def generate_neo4j_cypher(bot_id: str, bot_name: str) -> str:
    """Generate Cypher queries for Neo4j setup."""

    return f'''
// ============================================================
// {bot_name} Neo4j Configuration
// Run these Cypher queries in Neo4j Browser
// ============================================================

// Create Framework node
CREATE (f:Framework {{
    name: "{bot_name}",
    description: "[Description of {bot_name} methodology]",
    category: "PWS"
}})
RETURN f;

// Create example Case Study nodes
CREATE (cs1:CaseStudy {{
    name: "[Case Study 1 Name]",
    description: "[Brief description of how {bot_name} was applied]"
}})
CREATE (cs2:CaseStudy {{
    name: "[Case Study 2 Name]",
    description: "[Brief description of another application]"
}});

// Link case studies to framework
MATCH (f:Framework {{name: "{bot_name}"}})
MATCH (cs:CaseStudy)
WHERE cs.name IN ["[Case Study 1 Name]", "[Case Study 2 Name]"]
CREATE (cs)-[:APPLIED_FRAMEWORK]->(f);

// Create methodology-specific nodes (customize based on methodology)
// Example for concepts:
CREATE (c1:Concept {{
    name: "[Key Concept 1]",
    description: "[Description]",
    methodology: "{bot_id}"
}})
CREATE (c2:Concept {{
    name: "[Key Concept 2]",
    description: "[Description]",
    methodology: "{bot_id}"
}});
'''


def generate_rag_setup(bot_id: str, bot_name: str) -> str:
    """Generate RAG cache setup function."""

    return f'''
# ============================================================
# {bot_name} RAG Cache Setup
# Add this function to utils/gemini_rag.py
# ============================================================

def setup_{bot_id}_cache():
    """
    Set up the {bot_name} workshop cache with all materials.
    Run this once to upload materials and create the cache.
    """
    from prompts.{bot_id} import {bot_id.upper()}_PROMPT

    # Path to {bot_name} materials - UPDATE THESE PATHS
    base_path = Path("/path/to/{bot_id}_materials")

    file_paths = [
        base_path / "lecture.txt",
        base_path / "worksheet.txt",
        # Add more files as needed
    ]

    # Verify files exist
    for fp in file_paths:
        if not fp.exists():
            raise FileNotFoundError(f"File not found: {{fp}}")

    cache_name = create_workshop_cache(
        workshop_id="{bot_id}",
        file_paths=[str(fp) for fp in file_paths],
        system_instruction={bot_id.upper()}_PROMPT,
        model="models/gemini-2.0-flash-001",
        ttl_seconds=604800  # 7 days
    )

    print(f"\\n{{'='*50}}")
    print(f"{bot_name} cache setup complete!")
    print(f"Cache name: {{cache_name}}")
    print(f"{{'='*50}}")

    return cache_name
'''


def main():
    parser = argparse.ArgumentParser(
        description="Generate boilerplate for a new Mindrian agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/generate_agent.py minto "Minto Pyramid" --workshop --phases 5
    python scripts/generate_agent.py advisor "Innovation Advisor"
    python scripts/generate_agent.py scqa "SCQA Framework" --workshop --phases 4
        """
    )

    parser.add_argument("bot_id", help="Bot identifier (lowercase, no spaces)")
    parser.add_argument("bot_name", help="Human-readable bot name")
    parser.add_argument("--workshop", action="store_true", help="Create as workshop bot with phases")
    parser.add_argument("--phases", type=int, default=4, help="Number of workshop phases (default: 4)")
    parser.add_argument("--icon", default="🆕", help="Emoji icon for the bot (default: 🆕)")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: creates in project)")

    args = parser.parse_args()

    # Validate bot_id
    if not args.bot_id.isidentifier():
        print(f"Error: bot_id '{args.bot_id}' must be a valid Python identifier")
        sys.exit(1)

    bot_id = args.bot_id.lower()
    bot_name = args.bot_name
    is_workshop = args.workshop
    num_phases = args.phases if is_workshop else 0
    icon = args.icon

    print(f"\n{'='*60}")
    print(f"Generating agent: {bot_name} ({bot_id})")
    print(f"Type: {'Workshop' if is_workshop else 'General'} bot")
    if is_workshop:
        print(f"Phases: {num_phases}")
    print(f"{'='*60}\n")

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = PROJECT_ROOT / "generated" / bot_id

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate all files
    files_to_create = {}

    # 1. System prompt
    prompt_content = generate_prompt_file(bot_id, bot_name, is_workshop, num_phases)
    files_to_create[f"prompts/{bot_id}.py"] = prompt_content

    # 2. mindrian_chat.py additions
    chat_additions = generate_mindrian_chat_additions(bot_id, bot_name, icon, is_workshop, num_phases)
    files_to_create["MINDRIAN_CHAT_ADDITIONS.py"] = chat_additions

    # 3. Dynamic examples
    examples_additions = generate_dynamic_examples_additions(bot_id, bot_name)
    files_to_create["DYNAMIC_EXAMPLES_ADDITIONS.py"] = examples_additions

    # 4. Media configuration
    media_additions = generate_media_additions(bot_id, bot_name, is_workshop, num_phases)
    files_to_create["MEDIA_ADDITIONS.py"] = media_additions

    # 5. Neo4j Cypher
    neo4j_cypher = generate_neo4j_cypher(bot_id, bot_name)
    files_to_create["NEO4J_SETUP.cypher"] = neo4j_cypher

    # 6. RAG setup
    rag_setup = generate_rag_setup(bot_id, bot_name)
    files_to_create["RAG_SETUP.py"] = rag_setup

    # Write all files
    for filename, content in files_to_create.items():
        filepath = output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            f.write(content)

        print(f"✅ Created: {filepath}")

    # Also create the actual prompt file in the project
    actual_prompt_path = PROJECT_ROOT / "prompts" / f"{bot_id}.py"
    if not actual_prompt_path.exists():
        with open(actual_prompt_path, "w") as f:
            f.write(prompt_content)
        print(f"✅ Created: {actual_prompt_path}")
    else:
        print(f"⚠️  Skipped (exists): {actual_prompt_path}")

    # Print next steps
    print(f"\n{'='*60}")
    print("NEXT STEPS:")
    print(f"{'='*60}")
    print(f"""
1. Review and customize the prompt:
   {actual_prompt_path}

2. Add the code from generated files to:
   - mindrian_chat.py (MINDRIAN_CHAT_ADDITIONS.py)
   - utils/dynamic_examples.py (DYNAMIC_EXAMPLES_ADDITIONS.py)
   - utils/media.py (MEDIA_ADDITIONS.py)

3. Export the prompt in prompts/__init__.py:
   from .{bot_id} import {bot_id.upper()}_PROMPT

4. (Optional) Run Neo4j setup:
   NEO4J_SETUP.cypher

5. (Optional) Set up RAG cache:
   Add function from RAG_SETUP.py to utils/gemini_rag.py

6. Test the agent:
   chainlit run mindrian_chat.py --watch

7. Verify checklist in CLAUDE.md:
   - [ ] Bot appears in dropdown
   - [ ] Starters work
   - [ ] Phases progress (if workshop)
   - [ ] Switch callback works
   - [ ] Examples are diverse
""")

    print(f"\nGenerated files are in: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
