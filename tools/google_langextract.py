"""
Google LangExtract Integration for PWS Opportunity Extraction
=============================================================

Uses Google's official LangExtract library for structured extraction
of PWS-compliant opportunities from conversation summaries.

Features:
- Precise source grounding (character offsets)
- Few-shot learning with PWS examples
- Interactive HTML visualization
- Gemini integration

Installation:
    pip install langextract

Usage:
    from tools.google_langextract import extract_pws_opportunities

    opportunities = await extract_pws_opportunities(
        text="User discussed problems with tracking innovation...",
        created_by="Jonathan Sagir"
    )
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# Check if langextract is available
try:
    import langextract as lx
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False
    print("Google LangExtract not installed. Run: pip install langextract")

# Gemini API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGEXTRACT_MODEL = os.getenv("LANGEXTRACT_MODEL", "gemini-2.0-flash")


# =============================================================================
# PWS EXTRACTION SCHEMA - Few-Shot Examples
# =============================================================================

def get_pws_examples() -> List:
    """
    Define PWS-compliant extraction examples for few-shot learning.

    These examples teach LangExtract how to identify and structure
    opportunities according to PWS methodology.
    """
    if not LANGEXTRACT_AVAILABLE:
        return []

    return [
        lx.data.ExampleData(
            text="""The user mentioned that traditional education relies on passive
            information transfer, which leads to poor retention rates. They noted
            that peer tutoring research shows 2x retention when students teach others.
            This suggests an opportunity for AI-powered mirror learning where children
            teach AI characters to learn themselves.""",
            extractions=[
                lx.data.Extraction(
                    extraction_class="opportunity",
                    extraction_text="AI-powered mirror learning where children teach AI characters",
                    attributes={
                        "name": "AI-Powered Mirror Learning for Education",
                        "problem": "Traditional education relies on passive information transfer leading to poor retention",
                        "value_potential": "transformative",
                        "solution_direction": "Deploy AI characters that children teach, inverting the learning relationship",
                        "job_to_be_done": "Help children develop genuine understanding through teaching",
                        "domain": "educational_technology",
                        "opportunity_type": "problem_worth_solving",
                        "evidence": "Peer tutoring research shows 2x retention when teaching"
                    }
                )
            ]
        ),
        lx.data.ExampleData(
            text="""Small business owners struggle to track customer feedback across
            multiple channels - email, social media, reviews, and in-person comments.
            They spend hours manually consolidating this data and often miss important
            patterns. A unified feedback aggregation system could save them significant
            time and surface actionable insights.""",
            extractions=[
                lx.data.Extraction(
                    extraction_class="opportunity",
                    extraction_text="unified feedback aggregation system",
                    attributes={
                        "name": "Multi-Channel Customer Feedback Aggregator",
                        "problem": "Small business owners struggle to track and consolidate customer feedback across multiple channels",
                        "value_potential": "high",
                        "solution_direction": "Build unified system that aggregates feedback from email, social, reviews, and notes",
                        "job_to_be_done": "Help business owners understand customer sentiment without manual consolidation",
                        "domain": "small_business_tools",
                        "opportunity_type": "unmet_need",
                        "evidence": "Business owners spend hours manually consolidating and often miss patterns"
                    }
                )
            ]
        ),
        lx.data.ExampleData(
            text="""The healthcare system lacks efficient ways to match organ donors
            with recipients across different hospitals. Current processes involve
            phone calls and faxes, leading to delays that can cost lives. AI-powered
            matching could optimize for compatibility, urgency, and logistics simultaneously.""",
            extractions=[
                lx.data.Extraction(
                    extraction_class="opportunity",
                    extraction_text="AI-powered matching could optimize for compatibility, urgency, and logistics",
                    attributes={
                        "name": "AI-Optimized Organ Donor Matching System",
                        "problem": "Healthcare lacks efficient organ donor-recipient matching across hospitals",
                        "value_potential": "transformative",
                        "solution_direction": "AI system optimizing for compatibility, urgency, and logistics simultaneously",
                        "job_to_be_done": "Save lives by reducing organ transplant matching delays",
                        "domain": "healthcare",
                        "opportunity_type": "reverse_salient",
                        "evidence": "Current phone/fax processes cause life-threatening delays"
                    }
                )
            ]
        )
    ]


PWS_EXTRACTION_PROMPT = """Extract innovation opportunities from this text using the PWS (Problems Worth Solving) methodology.

For each opportunity found, identify:
- name: Clear, actionable title
- problem: The constraint or reverse salient being addressed
- value_potential: low, medium, high, or transformative
- solution_direction: How it could be solved
- job_to_be_done: What user need is served (JTBD framing)
- domain: Industry or field
- opportunity_type: problem_worth_solving, unmet_need, market_gap, technology_opportunity, process_improvement, emerging_trend, reverse_salient, or validated_insight
- evidence: Supporting evidence from the text

Only extract opportunities with clear substance - not vague ideas.
List opportunities in order of appearance in the text."""


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

async def extract_pws_opportunities(
    text: str,
    created_by: str = "system",
    created_by_type: str = "ai_agent",
    source_type: str = "conversation",
    source_id: str = None,
    model_id: str = None
) -> List[Dict[str, Any]]:
    """
    Extract PWS-compliant opportunities from text using Google LangExtract.

    Args:
        text: The text to extract opportunities from (conversation summary, document, etc.)
        created_by: Who is extracting (person name, bot name, etc.)
        created_by_type: user, ai_agent, framework, system
        source_type: conversation, document, framework, analysis, external
        source_id: Unique identifier for the source
        model_id: LLM model to use (default: gemini-2.0-flash)

    Returns:
        List of opportunity dictionaries ready for registration
    """
    if not LANGEXTRACT_AVAILABLE:
        print("LangExtract not available. Install with: pip install langextract")
        return []

    if not text or len(text.strip()) < 50:
        return []

    model = model_id or LANGEXTRACT_MODEL
    examples = get_pws_examples()

    try:
        # Set API key for LangExtract
        os.environ["LANGEXTRACT_API_KEY"] = GOOGLE_API_KEY

        # Run extraction
        result = lx.extract(
            text_or_documents=text,
            prompt_description=PWS_EXTRACTION_PROMPT,
            examples=examples,
            model_id=model
        )

        # Convert to opportunity format
        opportunities = []
        for extraction in result.extractions:
            if extraction.extraction_class == "opportunity":
                attrs = extraction.attributes or {}

                opp = {
                    "name": attrs.get("name", extraction.extraction_text[:100]),
                    "description": extraction.extraction_text,
                    "problem": attrs.get("problem", ""),
                    "value_potential": attrs.get("value_potential", "medium"),
                    "solution_direction": attrs.get("solution_direction", ""),
                    "job_to_be_done": attrs.get("job_to_be_done", ""),
                    "domain": attrs.get("domain", ""),
                    "opportunity_type": attrs.get("opportunity_type", "problem_worth_solving"),
                    "evidence": [attrs.get("evidence")] if attrs.get("evidence") else [],

                    # Source grounding from LangExtract
                    "source_snippet": extraction.extraction_text,
                    "source_start": extraction.start_offset if hasattr(extraction, 'start_offset') else None,
                    "source_end": extraction.end_offset if hasattr(extraction, 'end_offset') else None,

                    # Provenance
                    "created_by": created_by,
                    "created_by_type": created_by_type,
                    "source_type": source_type,
                    "source_id": source_id,

                    # Metadata
                    "extraction_method": "langextract",
                    "extraction_confidence": 0.8,  # LangExtract doesn't provide confidence
                    "extracted_at": datetime.utcnow().isoformat()
                }
                opportunities.append(opp)

        return opportunities

    except Exception as e:
        print(f"LangExtract extraction error: {e}")
        return []


async def extract_and_visualize(
    text: str,
    output_dir: str = "langextract_results",
    output_name: str = None
) -> tuple:
    """
    Extract opportunities and generate interactive HTML visualization.

    Args:
        text: Text to extract from
        output_dir: Directory for output files
        output_name: Base name for output files (default: timestamp)

    Returns:
        (opportunities_list, html_path)
    """
    if not LANGEXTRACT_AVAILABLE:
        return [], None

    import os
    os.makedirs(output_dir, exist_ok=True)

    if not output_name:
        output_name = f"pws_extraction_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    try:
        os.environ["LANGEXTRACT_API_KEY"] = GOOGLE_API_KEY

        result = lx.extract(
            text_or_documents=text,
            prompt_description=PWS_EXTRACTION_PROMPT,
            examples=get_pws_examples(),
            model_id=LANGEXTRACT_MODEL
        )

        # Save to JSONL
        jsonl_path = os.path.join(output_dir, f"{output_name}.jsonl")
        lx.io.save_annotated_documents([result], output_name=jsonl_path, output_dir=".")

        # Generate HTML visualization
        html_content = lx.visualize(jsonl_path)
        html_path = os.path.join(output_dir, f"{output_name}.html")
        with open(html_path, 'w') as f:
            f.write(html_content)

        # Convert to opportunity format
        opportunities = []
        for extraction in result.extractions:
            if extraction.extraction_class == "opportunity":
                attrs = extraction.attributes or {}
                opportunities.append({
                    "name": attrs.get("name", extraction.extraction_text[:100]),
                    "description": extraction.extraction_text,
                    **attrs
                })

        return opportunities, html_path

    except Exception as e:
        print(f"Extract and visualize error: {e}")
        return [], None


def check_langextract_available() -> Dict[str, Any]:
    """Check if LangExtract is properly configured."""
    status = {
        "installed": LANGEXTRACT_AVAILABLE,
        "api_key_set": bool(GOOGLE_API_KEY),
        "model": LANGEXTRACT_MODEL,
        "ready": LANGEXTRACT_AVAILABLE and bool(GOOGLE_API_KEY)
    }

    if not status["installed"]:
        status["message"] = "Install with: pip install langextract"
    elif not status["api_key_set"]:
        status["message"] = "Set GOOGLE_API_KEY environment variable"
    else:
        status["message"] = "Ready to extract"

    return status


# =============================================================================
# INTEGRATION WITH OPPORTUNITY BANK
# =============================================================================

async def extract_and_register_opportunities(
    text: str,
    created_by: str = "system",
    created_by_type: str = "ai_agent",
    source_type: str = "conversation",
    source_id: str = None,
    conversation_id: str = None,
    user_id: str = None
) -> tuple:
    """
    Extract opportunities using LangExtract and register them in the Bank.

    This is the main integration point - extracts from text and stores
    in both Supabase and Neo4j.

    Returns:
        (list of stored opportunities, summary dict)
    """
    # Extract using LangExtract
    raw_opportunities = await extract_pws_opportunities(
        text=text,
        created_by=created_by,
        created_by_type=created_by_type,
        source_type=source_type,
        source_id=source_id
    )

    if not raw_opportunities:
        return [], {"extracted": 0, "stored": 0}

    # Import opportunity bank functions
    try:
        from tools.opportunity_bank import (
            Opportunity,
            store_opportunity,
            generate_opportunity_id
        )
    except ImportError:
        print("Could not import opportunity_bank")
        return raw_opportunities, {"extracted": len(raw_opportunities), "stored": 0}

    # Convert and store each opportunity
    stored = []
    for raw in raw_opportunities:
        opp_id = generate_opportunity_id(raw.get("name", ""), conversation_id or "")

        opp = Opportunity(
            id=opp_id,
            name=raw.get("name", "Untitled"),
            description=raw.get("description", ""),
            problem=raw.get("problem", ""),
            value_potential=raw.get("value_potential", "medium"),
            solution_direction=raw.get("solution_direction", ""),
            job_to_be_done=raw.get("job_to_be_done", ""),
            opportunity_type=raw.get("opportunity_type", "problem_worth_solving"),
            domain=raw.get("domain", ""),
            evidence=raw.get("evidence", []),
            source_snippet=raw.get("source_snippet", ""),
            created_by=created_by,
            created_by_type=created_by_type,
            source_type=source_type,
            source_id=source_id or conversation_id,
            conversation_id=conversation_id,
            user_id=user_id,
            extraction_method="langextract",
            extraction_confidence=raw.get("extraction_confidence", 0.8)
        )

        # Store in all backends
        result = await store_opportunity(opp)
        stored.append(opp.to_dict())

    summary = {
        "extracted": len(raw_opportunities),
        "stored": len(stored),
        "method": "google_langextract",
        "model": LANGEXTRACT_MODEL
    }

    return stored, summary
