"""
Evaluation framework for concept generation prompts.
Measures structural quality, content quality, brand faithfulness, and diversity.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Optional

from anthropic import AsyncAnthropic

from orchestrator.config import get_settings
from orchestrator.claude_orchestrator import ClaudePromptOrchestrator, _format_brand_memory
from test_dataset import TEST_CASES

logger = logging.getLogger(__name__)


@dataclass
class ConceptEvaluationScore:
    """Score for a single concept against golden standard."""
    brand_id: str
    concept_index: int

    # Structural quality (0-1): does it parse and have required fields?
    structural_quality: float

    # Headline quality (0-1): relevance, specificity, engagement
    headline_quality: float

    # Prompt quality (0-1): detailed enough? feasible for image generation?
    prompt_quality: float

    # Brand faithfulness (0-1): uses pillars/products, respects avoid-lists?
    brand_faithfulness: float

    # Rationale quality (0-1): does it justify the concept?
    rationale_quality: float

    # Overall score
    overall_score: float

    # Detailed feedback
    feedback: str


@dataclass
class ConceptSetEvaluationScore:
    """Score for a complete concept set (3 concepts)."""
    brand_id: str
    brand_name: str

    # Individual concept scores
    concept_scores: list[ConceptEvaluationScore]

    # Diversity score (0-1): are concepts genuinely different?
    diversity_score: float

    # Set quality average
    set_quality_avg: float

    # Approval history alignment (0-1): does it lean into approvals, avoid rejections?
    approval_history_alignment: float

    # Overall set score
    overall_score: float

    # Summary feedback
    summary: str


class ConceptEvaluator:
    """Evaluate generated concepts against golden standards."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.claude_api_key) if settings.claude_api_key else None

    def evaluate_structural_quality(self, concept: dict) -> tuple[float, str]:
        """Check if concept has required fields and valid structure."""
        required_fields = ["headline", "prompt", "rationale", "content_pillar", "product"]
        missing = [f for f in required_fields if f not in concept]

        if missing:
            return 0.0, f"Missing fields: {', '.join(missing)}"

        issues = []
        if not concept.get("headline") or len(concept["headline"].strip()) < 5:
            issues.append("Headline too short or empty")
        if not concept.get("prompt") or len(concept["prompt"].strip()) < 50:
            issues.append("Prompt too short (minimum ~50 chars)")
        if not concept.get("rationale") or len(concept["rationale"].strip()) < 20:
            issues.append("Rationale too short")

        if issues:
            return 0.5, f"Partial issues: {'; '.join(issues)}"
        return 1.0, "All required fields present and sufficient length"

    async def evaluate_headline_quality(self, generated: str, golden: str) -> tuple[float, str]:
        """Compare headline quality using semantic similarity + heuristics."""
        if not generated or len(generated) < 5:
            return 0.0, "Generated headline is empty or too short"

        # Use Claude to evaluate semantic similarity
        if not self.client:
            return 0.5, "No Claude client for evaluation"

        try:
            response = await self.client.messages.create(
                model="claude-opus-5-5",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Compare these two headlines for quality and relevance:

Golden: "{golden}"
Generated: "{generated}"

Rate the generated headline on:
1. Specificity and clarity (1-5)
2. Engagement/intrigue (1-5)
3. Relevance to content (1-5)
4. Grammar and tone (1-5)

Respond with JSON: {{"specificity": N, "engagement": N, "relevance": N, "grammar": N, "feedback": "brief note"}}"""
                }]
            )

            # Find text block (skip ThinkingBlock from extended thinking)
            text = None
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    text = block.text
                    break

            if not text:
                return 0.5, "No text response from Claude"

            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                scores = json.loads(json_match.group())
                avg = (scores.get("specificity", 3) + scores.get("engagement", 3) +
                       scores.get("relevance", 3) + scores.get("grammar", 3)) / 20.0
                return min(1.0, avg), scores.get("feedback", "")
        except Exception as e:
            logger.warning(f"Error evaluating headline: {e}")

        return 0.5, "Evaluation inconclusive"

    async def evaluate_prompt_quality(self, generated: str, golden: str) -> tuple[float, str]:
        """Check prompt quality: detail level, specificity, feasibility for image generation."""
        if not generated or len(generated) < 50:
            return 0.0, "Prompt too short (<50 chars)"

        word_count = len(generated.split())
        if word_count < 60:
            return 0.3, f"Prompt too brief ({word_count} words, target 100-150)"
        if word_count > 300:
            return 0.6, f"Prompt too long ({word_count} words, may confuse image generator)"

        # Check for specificity markers
        specificity_markers = ["style", "color", "light", "composition", "mood", "scene", "person", "detail"]
        found_markers = sum(1 for marker in specificity_markers if marker.lower() in generated.lower())
        specificity_score = found_markers / len(specificity_markers)

        # Check for infeasible requests
        impossible_phrases = ["tell me", "write", "list", "explain", "with text saying", "showing words"]
        has_impossible = any(phrase in generated.lower() for phrase in impossible_phrases)
        if has_impossible:
            return 0.3, "Contains non-image-generation requests (text, lists, explanations)"

        score = 0.6 + (specificity_score * 0.35)
        feedback = f"Specificity: {specificity_score:.0%}, {word_count} words"
        return min(1.0, score), feedback

    def evaluate_brand_faithfulness(self, concept: dict, brand_memory: dict) -> tuple[float, str]:
        """Check if concept respects brand identity, uses pillars/products, avoids avoid-list."""
        score = 0.7  # Start at decent baseline
        issues = []

        profile = brand_memory.get("profile", {})
        pillars = {p["name"].lower(): p for p in brand_memory.get("pillars", [])}
        products = {p["name"].lower(): p for p in brand_memory.get("products", [])}

        concept_text = (concept.get("headline", "") + " " + concept.get("prompt", "") + " " +
                       concept.get("rationale", "")).lower()

        # Check if uses content pillar or product when referenced
        pillar_name = concept.get("content_pillar", "").lower().strip()
        product_name = concept.get("product", "").lower().strip()

        if pillar_name and pillar_name in pillars:
            # Verify pillar is actually used in concept text
            if pillar_name not in concept_text:
                issues.append(f"References pillar '{concept.get('content_pillar')}' but doesn't use it in prompt")
                score -= 0.15

        if product_name and product_name in products:
            if product_name not in concept_text:
                issues.append(f"References product '{concept.get('product')}' but doesn't use it in prompt")
                score -= 0.15

        # Check for avoid-list violations
        avoid_words = (profile.get("words_to_avoid") or "").lower().split(",")
        found_avoid = [w.strip() for w in avoid_words if w.strip() and w.strip() in concept_text]
        if found_avoid:
            issues.append(f"Uses avoided words: {', '.join(found_avoid)}")
            score -= 0.1 * len(found_avoid)

        avoid_elements = (profile.get("visual_elements_to_avoid") or "").lower()
        if avoid_elements and any(elem.strip() in concept_text for elem in avoid_elements.split(",")):
            issues.append("Uses visual elements brand wants to avoid")
            score -= 0.1

        # Check if respects photography/tone style
        photography_style = profile.get("photography_style", "").lower()
        if photography_style and any(style in concept_text for style in ["artificial", "fake", "photoshopped"]):
            issues.append("Describes photography that conflicts with brand style")
            score -= 0.1

        feedback = "; ".join(issues) if issues else "Respects brand identity and guidelines"
        return max(0.0, score), feedback

    def evaluate_diversity(self, concepts: list[dict]) -> tuple[float, str]:
        """Check if 3 concepts are genuinely different, not variations."""
        if len(concepts) != 3:
            return 0.0, f"Expected 3 concepts, got {len(concepts)}"

        # Simple heuristic: check similarity of headlines and pillars
        headlines = [c.get("headline", "").lower() for c in concepts]
        pillars = [c.get("content_pillar", "").lower() for c in concepts]

        # Count unique pillars (if they reference any)
        unique_pillars = set(p for p in pillars if p)
        pillar_diversity = len(unique_pillars) / 3.0 if any(pillars) else 0.5

        # Check headline diversity (very simple: word overlap)
        def words_in_common(h1: str, h2: str) -> int:
            w1 = set(h1.split())
            w2 = set(h2.split())
            return len(w1 & w2)

        overlap_01 = words_in_common(headlines[0], headlines[1])
        overlap_12 = words_in_common(headlines[1], headlines[2])
        overlap_02 = words_in_common(headlines[0], headlines[2])

        total_overlap = overlap_01 + overlap_12 + overlap_02
        overlap_score = 1.0 - (total_overlap / 30.0)  # Max 30 common words = 0 diversity

        score = 0.5 * overlap_score + 0.5 * pillar_diversity

        issues = []
        if overlap_score < 0.5:
            issues.append("Headlines share too many words/concepts")
        if pillar_diversity < 0.4 and any(pillars):
            issues.append("Not enough pillar diversity")

        feedback = "; ".join(issues) if issues else "Good diversity across concepts"
        return max(0.0, min(1.0, score)), feedback

    def evaluate_approval_history_alignment(self, concepts: list[dict], brand_memory: dict) -> tuple[float, str]:
        """Check if concepts align with what was approved/rejected historically."""
        history = brand_memory.get("approval_history", [])
        if not history:
            return 0.7, "No approval history to align with"

        approved = [h for h in history if h.get("decision") == "approved"]
        rejected = [h for h in history if h.get("decision") == "rejected"]

        if not approved and not rejected:
            return 0.7, "No clear approval patterns"

        score = 0.7
        feedback = []

        # Extract themes from approvals
        approval_themes = []
        for a in approved:
            if a.get("note"):
                approval_themes.append(a["note"].lower())

        # Check if concepts mention similar themes
        concept_text = " ".join([c.get("prompt", "") + c.get("rationale", "") for c in concepts]).lower()

        matching_themes = sum(1 for theme in approval_themes if any(word in concept_text for word in theme.split()))
        if matching_themes > 0:
            score += 0.15 * (matching_themes / len(approval_themes))
            feedback.append(f"Aligns with {matching_themes}/{len(approval_themes)} approval themes")

        # Check rejection avoidance
        rejection_themes = [r.get("note", "").lower() for r in rejected if r.get("note")]
        if rejection_themes:
            for theme in rejection_themes:
                if any(word in concept_text for word in theme.split() if len(word) > 3):
                    score -= 0.2
                    feedback.append(f"May repeat rejection theme: {theme}")
                    break

        return max(0.0, min(1.0, score)), "; ".join(feedback) if feedback else "Generally aligned with history"

    async def evaluate_concept_set(self, generated_concepts: list[dict], test_case: dict) -> ConceptSetEvaluationScore:
        """Evaluate a complete set of 3 concepts."""
        brand_id = test_case["brand_id"]
        brand_name = test_case["brand_name"]
        brand_memory = test_case["brand_memory"]
        golden_concepts = test_case["golden_concepts"]

        if len(generated_concepts) != 3 or len(golden_concepts) != 3:
            return ConceptSetEvaluationScore(
                brand_id=brand_id,
                brand_name=brand_name,
                concept_scores=[],
                diversity_score=0.0,
                set_quality_avg=0.0,
                approval_history_alignment=0.0,
                overall_score=0.0,
                summary="Concept count mismatch"
            )

        # Evaluate each concept
        concept_scores = []
        for i, (generated, golden) in enumerate(zip(generated_concepts, golden_concepts)):
            struct_score, struct_feedback = self.evaluate_structural_quality(generated)
            headline_score, headline_feedback = await self.evaluate_headline_quality(
                generated.get("headline", ""), golden["headline"]
            )
            prompt_score, prompt_feedback = await self.evaluate_prompt_quality(
                generated.get("prompt", ""), golden["prompt"]
            )
            brand_score, brand_feedback = self.evaluate_brand_faithfulness(generated, brand_memory)
            rationale_score, rationale_feedback = (
                (1.0, "Good rationale") if generated.get("rationale") and len(generated["rationale"]) > 20
                else (0.5, "Rationale missing or too short")
            )

            overall = (struct_score + headline_score + prompt_score + brand_score + rationale_score) / 5.0

            concept_scores.append(ConceptEvaluationScore(
                brand_id=brand_id,
                concept_index=i,
                structural_quality=struct_score,
                headline_quality=headline_score,
                prompt_quality=prompt_score,
                brand_faithfulness=brand_score,
                rationale_quality=rationale_score,
                overall_score=overall,
                feedback=f"Struct: {struct_feedback} | Headline: {headline_feedback} | Prompt: {prompt_feedback} | Brand: {brand_feedback}"
            ))

        # Evaluate set-level metrics
        diversity_score, diversity_feedback = self.evaluate_diversity(generated_concepts)
        approval_score, approval_feedback = self.evaluate_approval_history_alignment(generated_concepts, brand_memory)

        set_quality_avg = sum(c.overall_score for c in concept_scores) / 3.0
        overall_score = 0.6 * set_quality_avg + 0.2 * diversity_score + 0.2 * approval_score

        summary = (
            f"Quality: {set_quality_avg:.0%} | Diversity: {diversity_score:.0%} | "
            f"Approval align: {approval_score:.0%}\n"
            f"Diversity: {diversity_feedback}\nApproval: {approval_feedback}"
        )

        return ConceptSetEvaluationScore(
            brand_id=brand_id,
            brand_name=brand_name,
            concept_scores=concept_scores,
            diversity_score=diversity_score,
            set_quality_avg=set_quality_avg,
            approval_history_alignment=approval_score,
            overall_score=overall_score,
            summary=summary
        )


async def evaluate_prompt_variant(test_cases=None) -> dict:
    """Run full evaluation against all test cases."""
    if test_cases is None:
        test_cases = TEST_CASES

    orchestrator = ClaudePromptOrchestrator()
    evaluator = ConceptEvaluator()

    results = {
        "test_cases": len(test_cases),
        "timestamp": "2026-09-29",
        "scores": [],
        "summary": {}
    }

    for test_case in test_cases:
        logger.info(f"Testing {test_case['brand_name']}...")

        try:
            # Generate concepts
            generated = await orchestrator.generate_daily_concepts(test_case["brand_memory"])

            # Evaluate
            eval_score = await evaluator.evaluate_concept_set(generated, test_case)
            results["scores"].append({
                "brand_id": eval_score.brand_id,
                "brand_name": eval_score.brand_name,
                "overall_score": eval_score.overall_score,
                "set_quality_avg": eval_score.set_quality_avg,
                "diversity_score": eval_score.diversity_score,
                "approval_alignment": eval_score.approval_history_alignment,
                "summary": eval_score.summary,
                "generated_concepts": generated,
                "golden_concepts": test_case["golden_concepts"],
                "concept_scores": [
                    {
                        "index": c.concept_index,
                        "overall": c.overall_score,
                        "structural": c.structural_quality,
                        "headline": c.headline_quality,
                        "prompt": c.prompt_quality,
                        "brand_faithfulness": c.brand_faithfulness,
                        "rationale": c.rationale_quality,
                        "feedback": c.feedback,
                    }
                    for c in eval_score.concept_scores
                ]
            })
        except Exception as e:
            logger.error(f"Error testing {test_case['brand_name']}: {e}")
            results["scores"].append({
                "brand_id": test_case["brand_id"],
                "brand_name": test_case["brand_name"],
                "error": str(e)
            })

    # Calculate overall summary
    valid_scores = [s for s in results["scores"] if "error" not in s]
    if valid_scores:
        results["summary"] = {
            "avg_overall_score": sum(s["overall_score"] for s in valid_scores) / len(valid_scores),
            "avg_quality": sum(s["set_quality_avg"] for s in valid_scores) / len(valid_scores),
            "avg_diversity": sum(s["diversity_score"] for s in valid_scores) / len(valid_scores),
            "avg_approval_alignment": sum(s["approval_alignment"] for s in valid_scores) / len(valid_scores),
            "successful_tests": len(valid_scores),
            "failed_tests": len(results["scores"]) - len(valid_scores),
        }

    # Save to file
    output_path = "test_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")
    print(f"\nResults saved to {output_path}\n")

    return results


if __name__ == "__main__":
    results = asyncio.run(evaluate_prompt_variant())
    print(json.dumps(results, indent=2))
