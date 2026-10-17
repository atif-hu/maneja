# Prompt Evaluation Framework

Comprehensive test dataset and evaluation framework for assessing concept generation prompt quality.

## Overview

This framework helps you systematically evaluate and improve the `generate_daily_concepts` prompt. It includes:

- **5 diverse test brands** (fitness, eco-friendly, beauty, food, fashion) with realistic brand memory
- **Golden-standard concepts** manually created for each brand as reference points
- **Multi-dimensional scoring** across structural, content, and brand alignment metrics
- **Reproducible evaluation** to measure prompt improvements over time

## Files

- `test_dataset.py` — 5 test brands with realistic brand memory and golden concepts
- `evaluation_framework.py` — Evaluation logic and scoring rubric
- `EVALUATION_README.md` — This file

## Running the Evaluation

### Quick Start

```bash
cd apps/orchestrator
python -m evaluation_framework
```

This runs the current `ClaudePromptOrchestrator.generate_daily_concepts` prompt against all 5 test brands and outputs scores.

### Output Format

Results are printed as JSON with structure:

```json
{
  "test_cases": 5,
  "timestamp": "2026-09-29",
  "scores": [
    {
      "brand_id": "test-001-fitness",
      "brand_name": "FitFlow",
      "overall_score": 0.78,
      "set_quality_avg": 0.82,
      "diversity_score": 0.75,
      "approval_alignment": 0.70,
      "summary": "...",
      "concept_scores": [
        {
          "index": 0,
          "overall": 0.85,
          "structural": 1.0,
          "headline": 0.80,
          "prompt": 0.85,
          "brand_faithfulness": 0.78,
          "feedback": "..."
        }
      ]
    }
  ],
  "summary": {
    "avg_overall_score": 0.76,
    "avg_quality": 0.80,
    "avg_diversity": 0.74,
    "avg_approval_alignment": 0.68,
    "successful_tests": 5,
    "failed_tests": 0
  }
}
```

## Scoring Breakdown

### Per-Concept Scores (0.0 - 1.0)

1. **Structural Quality** — Valid JSON, required fields present, minimum length
2. **Headline Quality** — Specificity, engagement, relevance to content, grammar
3. **Prompt Quality** — Detail level (target 100-150 words), specificity markers, feasibility for image generation
4. **Brand Faithfulness** — Respects brand identity, uses referenced pillars/products, avoids banned words/elements
5. **Rationale Quality** — Explains why the concept works for the brand

**Overall Concept Score** = Average of the 5 dimensions

### Set-Level Scores (0.0 - 1.0)

1. **Set Quality Avg** — Average of the 3 concept scores
2. **Diversity Score** — Are the 3 concepts genuinely different, not variations? Checks pillar diversity and headline uniqueness.
3. **Approval History Alignment** — Do concepts lean into approved themes and avoid rejection themes?

**Overall Set Score** = 60% Set Quality + 20% Diversity + 20% Approval Alignment

## Test Dataset Design

### Brands Included

| Brand | Industry | Key Traits |
|-------|----------|-----------|
| FitFlow | Fitness & Wellness | Energetic, authentic, inclusive, focuses on effort not perfection |
| EcoHome | Sustainable Home | Natural, warm, educational, avoids greenwashing |
| GlowNature | Natural Beauty | Luxe but natural, dewy skin, honest, diverse skintones |
| NourishBowl | Healthy Food | Vibrant, colorful, no diet-culture toxicity, diverse cuisines |
| EthicalThreads | Sustainable Fashion | Authentic, diverse bodies, ethical transparency, inclusive |

### Golden Concepts

Each brand has 3 manually-created golden concepts that:

- Respect brand identity and tone
- Reference content pillars and products naturally
- Avoid brand dislike/avoid-list items
- Show clear diversity from each other
- Align with approval history patterns
- Provide image-generation-ready prompts (100-150 words, detailed, feasible)

## Using Results to Improve the Prompt

### Example Workflow

1. **Run baseline evaluation**
   ```bash
   python -m evaluation_framework > baseline_results.json
   ```

2. **Note areas for improvement** (e.g., low diversity score, high rejection of brand preferences)

3. **Modify the prompt** in `claude_orchestrator.py` (the `instruction` variable in `generate_daily_concepts`)

4. **Run evaluation again**
   ```bash
   python -m evaluation_framework > improved_results.json
   ```

5. **Compare scores** to see if changes improved the metrics

### Metrics to Monitor

- **Quality decline?** Check if concepts lost detail or relevance
- **Diversity drops?** Concepts may be too similar or missing pillar variety
- **Brand faithfulness issues?** Prompt may not be emphasizing brand identity enough
- **Approval alignment low?** Add more emphasis on learning from historical decisions

## Customization

### Add More Test Brands

Edit `test_dataset.py` and add entries to `TEST_CASES` with:
- Brand profile (industry, tone, colors, etc.)
- Content pillars and products
- Approval history (what was approved/rejected and why)
- 3 golden concepts per brand

### Adjust Evaluation Weights

Edit `evaluation_framework.py`:
- Per-concept weights in `evaluate_concept_set()` (currently equal)
- Set-level score formula (currently 60% quality + 20% diversity + 20% approval)

### Change Prompt Requirements

If you want to enforce different prompt length, specificity, or structure, update:
- `evaluate_prompt_quality()` for word count and feasibility checks
- `evaluate_structural_quality()` for required fields

## Known Limitations

1. **Headline evaluation** uses Claude (expensive, slow) — early iterations evaluate only locally
2. **Diversity metric** is simple (word overlap + pillar count) — could be more sophisticated
3. **Brand faithfulness** checks keyword presence, not semantic understanding
4. **Golden concepts** were manually created — may have subjective quality variations

## Next Steps

1. Run baseline evaluation to establish current performance
2. Identify 2-3 dimensions with lowest scores
3. Modify prompt to address those dimensions
4. Re-evaluate and compare
5. Iterate until satisfied with quality across all metrics
