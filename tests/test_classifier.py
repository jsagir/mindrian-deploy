"""
Classifier Test Suite - 50+ Test Cases

Validates the two-stage classifier (Cynefin + PWS) meets 80% accuracy target.

Test categories:
1. Clear cases (obvious classification)
2. Boundary cases (edge between stages)
3. Multi-domain cases (mixed signals)
4. Override triggers (user intent vs detection)
5. Real-world examples from PWS curriculum
"""

import pytest
import asyncio
from typing import List, Dict, Any

# Import classifier (will work when run from project root)
import sys
sys.path.insert(0, '.')
from protocols.classifier import (
    classify,
    Classification,
    get_routing_recommendation,
    _mock_classify
)


# === TEST CASES: 50+ scenarios ===

TEST_CASES: List[Dict[str, Any]] = [
    # =====================================================
    # SECTION 1: CLEAR CYNEFIN DOMAIN (10 cases)
    # =====================================================
    {
        "id": "clear_01",
        "text": "How do I format a JSON file in Python?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined",
        "category": "clear_technical"
    },
    {
        "id": "clear_02",
        "text": "What's the syntax for a SQL JOIN statement?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined",
        "category": "clear_technical"
    },
    {
        "id": "clear_03",
        "text": "How do I create a new Git branch?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined",
        "category": "clear_technical"
    },
    {
        "id": "clear_04",
        "text": "What's the formula for calculating compound interest?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined",
        "category": "clear_factual"
    },
    {
        "id": "clear_05",
        "text": "How many ounces are in a pound?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined",
        "category": "clear_factual"
    },
    {
        "id": "clear_06",
        "text": "What are the steps to register an LLC in Delaware?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined",
        "category": "clear_process"
    },
    {
        "id": "clear_07",
        "text": "How do I file a patent application?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined",
        "category": "clear_process"
    },
    {
        "id": "clear_08",
        "text": "What documents do I need for a visa application?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined",
        "category": "clear_process"
    },
    {
        "id": "clear_09",
        "text": "How do I set up a basic Express.js server?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined",
        "category": "clear_technical"
    },
    {
        "id": "clear_10",
        "text": "What's the standard format for a business email?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined",
        "category": "clear_best_practice"
    },

    # =====================================================
    # SECTION 2: COMPLICATED CYNEFIN DOMAIN (10 cases)
    # =====================================================
    {
        "id": "complicated_01",
        "text": "How should we architect our microservices for the payment system?",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "complicated_architecture"
    },
    {
        "id": "complicated_02",
        "text": "What's the best database choice for our e-commerce platform?",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "complicated_architecture"
    },
    {
        "id": "complicated_03",
        "text": "How should we structure our engineering team for a 50-person company?",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "complicated_organizational"
    },
    {
        "id": "complicated_04",
        "text": "What marketing channels should we prioritize for B2B SaaS?",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "complicated_strategy"
    },
    {
        "id": "complicated_05",
        "text": "How do we optimize our supply chain for faster delivery?",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "complicated_operations"
    },
    {
        "id": "complicated_06",
        "text": "What's the best approach to migrate our legacy system to the cloud?",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "complicated_technical"
    },
    {
        "id": "complicated_07",
        "text": "How should we price our enterprise software product?",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "complicated_business"
    },
    {
        "id": "complicated_08",
        "text": "What security measures should we implement for HIPAA compliance?",
        "expected_cynefin": "complicated",
        "expected_pws": "well-defined",
        "category": "complicated_compliance"
    },
    {
        "id": "complicated_09",
        "text": "How do we reduce our customer acquisition cost by 30%?",
        "expected_cynefin": "complicated",
        "expected_pws": "well-defined",
        "category": "complicated_metrics"
    },
    {
        "id": "complicated_10",
        "text": "What's the optimal inventory level for our retail stores?",
        "expected_cynefin": "complicated",
        "expected_pws": "well-defined",
        "category": "complicated_optimization"
    },

    # =====================================================
    # SECTION 3: COMPLEX CYNEFIN DOMAIN (10 cases)
    # =====================================================
    {
        "id": "complex_01",
        "text": "What opportunities exist in the future of sustainable energy?",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "complex_exploration"
    },
    {
        "id": "complex_02",
        "text": "How will AI change the healthcare industry over the next decade?",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "complex_futures"
    },
    {
        "id": "complex_03",
        "text": "What's the future of urban transportation?",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "complex_futures"
    },
    {
        "id": "complex_04",
        "text": "I want to start a company but don't know what to build",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "complex_entrepreneurship"
    },
    {
        "id": "complex_05",
        "text": "People seem frustrated with how healthcare data is shared between providers",
        "expected_cynefin": "complex",
        "expected_pws": "ill-defined",
        "category": "complex_problem_sensing"
    },
    {
        "id": "complex_06",
        "text": "There's something broken about how people find and hire contractors",
        "expected_cynefin": "complex",
        "expected_pws": "ill-defined",
        "category": "complex_problem_sensing"
    },
    {
        "id": "complex_07",
        "text": "How do we create a culture of innovation in our 100-year-old company?",
        "expected_cynefin": "complex",
        "expected_pws": "ill-defined",
        "category": "complex_organizational"
    },
    {
        "id": "complex_08",
        "text": "What will education look like in 2040?",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "complex_futures"
    },
    {
        "id": "complex_09",
        "text": "How might climate change affect the insurance industry?",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "complex_impact"
    },
    {
        "id": "complex_10",
        "text": "What new jobs will exist that don't exist today?",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "complex_futures"
    },

    # =====================================================
    # SECTION 4: CHAOTIC CYNEFIN DOMAIN (5 cases)
    # =====================================================
    {
        "id": "chaotic_01",
        "text": "We have 2 weeks of runway left and our main customer just churned",
        "expected_cynefin": "chaotic",
        "expected_pws": "ill-defined",
        "category": "chaotic_crisis"
    },
    {
        "id": "chaotic_02",
        "text": "Our entire production database was just deleted and we have no backups",
        "expected_cynefin": "chaotic",
        "expected_pws": "well-defined",
        "category": "chaotic_technical"
    },
    {
        "id": "chaotic_03",
        "text": "A competitor just launched the exact product we've been building for 2 years",
        "expected_cynefin": "chaotic",
        "expected_pws": "ill-defined",
        "category": "chaotic_competitive"
    },
    {
        "id": "chaotic_04",
        "text": "Our CTO and 3 senior engineers all quit this morning",
        "expected_cynefin": "chaotic",
        "expected_pws": "ill-defined",
        "category": "chaotic_organizational"
    },
    {
        "id": "chaotic_05",
        "text": "We just got hit with a ransomware attack and all systems are down",
        "expected_cynefin": "chaotic",
        "expected_pws": "well-defined",
        "category": "chaotic_security"
    },

    # =====================================================
    # SECTION 5: BOUNDARY CASES (10 cases)
    # =====================================================
    {
        "id": "boundary_01",
        "text": "We've done customer research but haven't validated our assumptions yet",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "boundary_framing_defining"
    },
    {
        "id": "boundary_02",
        "text": "We have a hypothesis about what customers want but no data",
        "expected_cynefin": "complex",
        "expected_pws": "ill-defined",
        "category": "boundary_exploring_framing"
    },
    {
        "id": "boundary_03",
        "text": "We've identified the problem clearly but aren't sure about the solution approach",
        "expected_cynefin": "complicated",
        "expected_pws": "well-defined",
        "category": "boundary_defining_solving"
    },
    {
        "id": "boundary_04",
        "text": "The market research says one thing but our gut says another",
        "expected_cynefin": "complex",
        "expected_pws": "ill-defined",
        "category": "boundary_data_intuition"
    },
    {
        "id": "boundary_05",
        "text": "We have a working MVP but don't know if we're solving the right problem",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "boundary_validation"
    },
    {
        "id": "boundary_06",
        "text": "Customers say they want this feature but their behavior suggests otherwise",
        "expected_cynefin": "complex",
        "expected_pws": "ill-defined",
        "category": "boundary_stated_revealed"
    },
    {
        "id": "boundary_07",
        "text": "The technical solution is clear but we're not sure about product-market fit",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "boundary_tech_market"
    },
    {
        "id": "boundary_08",
        "text": "We know the industry is changing but don't know how to position ourselves",
        "expected_cynefin": "complex",
        "expected_pws": "ill-defined",
        "category": "boundary_macro_micro"
    },
    {
        "id": "boundary_09",
        "text": "The problem is well-understood in academia but no one has commercialized it",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "boundary_theory_practice"
    },
    {
        "id": "boundary_10",
        "text": "We've validated the problem exists but not whether anyone will pay to solve it",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "boundary_problem_business"
    },

    # =====================================================
    # SECTION 6: MULTI-DOMAIN / MIXED SIGNALS (5 cases)
    # =====================================================
    {
        "id": "multi_01",
        "text": "The technology is straightforward but the market dynamics are chaotic",
        "expected_cynefin": "complex",
        "expected_pws": "ill-defined",
        "category": "multi_tech_market"
    },
    {
        "id": "multi_02",
        "text": "We understand the technical solution but the regulatory environment is uncertain",
        "expected_cynefin": "complex",
        "expected_pws": "ill-defined",
        "category": "multi_tech_regulatory"
    },
    {
        "id": "multi_03",
        "text": "The product is simple but the go-to-market strategy is complex",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "multi_product_gtm"
    },
    {
        "id": "multi_04",
        "text": "Engineering is well-defined but sales process is a mess",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "multi_eng_sales"
    },
    {
        "id": "multi_05",
        "text": "The core technology works but integration with legacy systems is unpredictable",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "multi_core_integration"
    },

    # =====================================================
    # SECTION 7: USER INTENT OVERRIDE (5 cases)
    # =====================================================
    {
        "id": "override_01",
        "text": "I know what I want to build, I just need to explore the space first",
        "expected_cynefin": "complicated",
        "expected_pws": "un-defined",
        "category": "override_explore_intent"
    },
    {
        "id": "override_02",
        "text": "We've already decided on the solution, now help us validate the problem",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "override_validate_intent"
    },
    {
        "id": "override_03",
        "text": "Don't tell me what problem to solve, help me think through trends",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "override_trend_intent"
    },
    {
        "id": "override_04",
        "text": "I want to brainstorm, not analyze. What if we could teleport?",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "override_creative_intent"
    },
    {
        "id": "override_05",
        "text": "Skip the exploration, I need to execute on this specific plan",
        "expected_cynefin": "complicated",
        "expected_pws": "well-defined",
        "category": "override_execute_intent"
    },

    # =====================================================
    # SECTION 8: PWS CURRICULUM EXAMPLES (5 cases)
    # =====================================================
    {
        "id": "pws_01",
        "text": "What if everyone stopped driving personal cars in the next 10 years?",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "pws_tta"
    },
    {
        "id": "pws_02",
        "text": "When I try to schedule a doctor's appointment, I can never get one within a week",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "pws_jtbd"
    },
    {
        "id": "pws_03",
        "text": "Battery technology seems to be reaching its physical limits",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined",
        "category": "pws_scurve"
    },
    {
        "id": "pws_04",
        "text": "The assumption that people want to own things is being challenged",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined",
        "category": "pws_redteam"
    },
    {
        "id": "pws_05",
        "text": "How can we help nurses reduce medication errors by 50%?",
        "expected_cynefin": "complicated",
        "expected_pws": "well-defined",
        "category": "pws_well_defined"
    },
]


# === TEST FUNCTIONS ===

def test_case_count():
    """Verify we have 50+ test cases."""
    assert len(TEST_CASES) >= 50, f"Need 50+ test cases, have {len(TEST_CASES)}"


def test_case_categories():
    """Verify test cases cover all categories."""
    categories = set(tc["category"] for tc in TEST_CASES)

    required_prefixes = ["clear", "complicated", "complex", "chaotic", "boundary", "multi", "override", "pws"]
    for prefix in required_prefixes:
        matching = [c for c in categories if c.startswith(prefix)]
        assert len(matching) > 0, f"Missing category prefix: {prefix}"


def test_cynefin_distribution():
    """Verify reasonable distribution across Cynefin domains."""
    cynefin_counts = {}
    for tc in TEST_CASES:
        domain = tc["expected_cynefin"]
        cynefin_counts[domain] = cynefin_counts.get(domain, 0) + 1

    # Should have at least 5 cases per domain
    for domain in ["clear", "complicated", "complex", "chaotic"]:
        assert cynefin_counts.get(domain, 0) >= 5, f"Need more {domain} cases"


def test_pws_distribution():
    """Verify reasonable distribution across PWS types."""
    pws_counts = {}
    for tc in TEST_CASES:
        pws_type = tc["expected_pws"]
        pws_counts[pws_type] = pws_counts.get(pws_type, 0) + 1

    # Should have at least 10 cases per type
    for pws_type in ["un-defined", "ill-defined", "well-defined"]:
        assert pws_counts.get(pws_type, 0) >= 10, f"Need more {pws_type} cases"


@pytest.mark.asyncio
async def test_mock_classifier():
    """Test mock classifier returns valid results."""
    for tc in TEST_CASES[:5]:  # Test first 5
        result = _mock_classify(tc["text"])
        assert result.cynefin in ["clear", "complicated", "complex", "chaotic"]
        assert result.pws in ["un-defined", "ill-defined", "well-defined"]
        assert 0 <= result.cynefin_confidence <= 1
        assert 0 <= result.pws_confidence <= 1


@pytest.mark.asyncio
async def test_routing_recommendation():
    """Test routing recommendations are valid."""
    from protocols.classifier import Classification

    classification = Classification(
        cynefin="complex",
        pws="un-defined",
        cynefin_confidence=0.8,
        pws_confidence=0.8,
        reasoning="Test"
    )

    routing = get_routing_recommendation(classification)

    assert "primary_agent" in routing
    assert "style" in routing
    assert "tools" in routing
    assert "red_team_frequency" in routing


# === ACCURACY VALIDATION ===

async def run_full_validation(use_llm: bool = False) -> Dict[str, Any]:
    """
    Run full validation suite.

    Args:
        use_llm: If True, use actual LLM. If False, use mock.

    Returns:
        Detailed accuracy report
    """
    results = []

    for tc in TEST_CASES:
        if use_llm:
            classification = await classify(tc["text"])
        else:
            classification = _mock_classify(tc["text"])

        cynefin_correct = classification.cynefin == tc["expected_cynefin"]
        pws_correct = classification.pws == tc["expected_pws"]

        results.append({
            "id": tc["id"],
            "category": tc["category"],
            "text": tc["text"][:60] + "..." if len(tc["text"]) > 60 else tc["text"],
            "expected_cynefin": tc["expected_cynefin"],
            "actual_cynefin": classification.cynefin,
            "cynefin_correct": cynefin_correct,
            "expected_pws": tc["expected_pws"],
            "actual_pws": classification.pws,
            "pws_correct": pws_correct,
            "both_correct": cynefin_correct and pws_correct,
            "confidence": min(classification.cynefin_confidence, classification.pws_confidence)
        })

    # Calculate metrics
    total = len(results)
    cynefin_correct = sum(r["cynefin_correct"] for r in results)
    pws_correct = sum(r["pws_correct"] for r in results)
    both_correct = sum(r["both_correct"] for r in results)

    # Per-category breakdown
    categories = {}
    for r in results:
        cat = r["category"].split("_")[0]  # Get prefix
        if cat not in categories:
            categories[cat] = {"total": 0, "correct": 0}
        categories[cat]["total"] += 1
        if r["both_correct"]:
            categories[cat]["correct"] += 1

    category_accuracy = {
        cat: data["correct"] / data["total"]
        for cat, data in categories.items()
    }

    # Failed cases for analysis
    failed = [r for r in results if not r["both_correct"]]

    return {
        "total_cases": total,
        "cynefin_accuracy": cynefin_correct / total,
        "pws_accuracy": pws_correct / total,
        "combined_accuracy": both_correct / total,
        "target_accuracy": 0.80,
        "meets_target": (both_correct / total) >= 0.80,
        "category_accuracy": category_accuracy,
        "failed_cases": failed,
        "detailed_results": results
    }


def print_validation_report(report: Dict[str, Any]):
    """Print formatted validation report."""
    print("\n" + "="*60)
    print("CLASSIFIER VALIDATION REPORT")
    print("="*60)

    print(f"\nTotal Cases: {report['total_cases']}")
    print(f"Target Accuracy: {report['target_accuracy']*100:.0f}%")
    print(f"\nCynefin Accuracy: {report['cynefin_accuracy']*100:.1f}%")
    print(f"PWS Accuracy: {report['pws_accuracy']*100:.1f}%")
    print(f"Combined Accuracy: {report['combined_accuracy']*100:.1f}%")
    print(f"\nMeets Target: {'YES' if report['meets_target'] else 'NO'}")

    print("\n--- Category Breakdown ---")
    for cat, acc in sorted(report["category_accuracy"].items()):
        status = "✓" if acc >= 0.8 else "✗"
        print(f"  {status} {cat}: {acc*100:.0f}%")

    if report["failed_cases"]:
        print(f"\n--- Failed Cases ({len(report['failed_cases'])}) ---")
        for case in report["failed_cases"][:10]:  # Show first 10
            print(f"\n  [{case['id']}] {case['text']}")
            print(f"    Cynefin: expected={case['expected_cynefin']}, got={case['actual_cynefin']}")
            print(f"    PWS: expected={case['expected_pws']}, got={case['actual_pws']}")


# === MAIN ===

if __name__ == "__main__":
    print(f"Test cases loaded: {len(TEST_CASES)}")

    # Run quick validation with mock
    report = asyncio.run(run_full_validation(use_llm=False))
    print_validation_report(report)

    # To run with actual LLM:
    # report = asyncio.run(run_full_validation(use_llm=True))
    # print_validation_report(report)
