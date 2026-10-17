# Quick Start: Prompt Evaluation

Get baseline metrics on your current prompt in 5 minutes.

## Setup

```bash
cd apps/orchestrator
```

Ensure dependencies are installed:
- `asyncio` (standard library)
- `anthropic` (already in requirements)
- `sqlalchemy` (already in requirements)

## Run Baseline

```bash
python -m evaluation_framework
```

Wait 2-3 minutes. Results are automatically saved to **test_results.json**

## View Results

```bash
python view_results.py test_results.json
```

Shows:
- Overall scores and summary
- Each brand's generated concepts vs golden reference
- Per-concept evaluation scores
- Detailed feedback

Or just open **test_results.json** in your editor for raw JSON data.

## Interpret the Output

Look for these key metrics:

### Summary Section
```json
"summary": {
  "avg_overall_score": 0.76,      ← Target: 0.80+
  "avg_quality": 0.80,             ← Per-concept quality
  "avg_diversity": 0.74,           ← Are concepts different?
  "avg_approval_alignment": 0.68   ← Do they learn from history?
}
```

### Brand Score Breakdown
```json
{
  "brand_name": "FitFlow",
  "overall_score": 0.78,
  "set_quality_avg": 0.82,         ← Avg of 3 concepts
  "diversity_score": 0.75,         ← 1.0 = all different
  "approval_alignment": 0.70,      ← 1.0 = perfect alignment
  "concept_scores": [
    {
      "index": 0,
      "overall": 0.85,             ← This concept is strong
      "structural": 1.0,           ← Valid JSON, all fields
      "headline": 0.80,
      "prompt": 0.85,              ← Good detail level
      "brand_faithfulness": 0.78,  ← Uses brand values
      "feedback": "..."
    }
  ]
}
```

## Identify Weak Spots

| Score | Issue | Action |
|-------|-------|--------|
| `avg_overall < 0.70` | Quality is too low | Simplify prompt, examples might help |
| `avg_diversity < 0.65` | Concepts feel repetitive | Ask for "genuinely different" emphasis |
| `avg_approval < 0.60` | Ignoring history | Add approval history weight to prompt |
| `headline < 0.70` | Headlines weak | Make headline requirements more explicit |
| `prompt < 0.70` | Image prompts too vague | Require 100-150 words, specific details |
| `brand_faithfulness < 0.65` | Missing brand voice | Add more brand context or constraints |

## Quick Prompt Fixes

### If diversity is low:

**Add to prompt instruction:**
```
These must NOT be 3 stylistic variations of one idea — 
each concept should be genuinely different in subject, 
mood, or angle while remaining authentic to the brand.
Vary the content_pillar and/or product if possible.
```

### If approval alignment is low:

**Add to prompt instruction:**
```
Critically, use the approval history: lean into what 
reviewers have approved before, and steer away from 
anything a rejection note called out.
```

### If prompts are too short:

**Add to prompt instruction:**
```
The "prompt" field must be a detailed, standalone 
image-generation prompt (100-150 words) describing 
the actual scene. Include: composition, lighting, 
mood, details, colors, and what the image conveys.
```

### If brand faithfulness is low:

**Add to prompt instruction:**
```
Ground each concept in the brand's avoid-lists. 
If the profile says "avoid neon", ensure the prompt 
uses different color language. If it says "avoid 
posed looks", say "natural, authentic pose" instead 
of "model-style photo."
```

## After Changes

1. Modify the `instruction` variable in [claude_orchestrator.py:134](../orchestrator/claude_orchestrator.py#L134)

2. Run evaluation again:
   ```bash
   python -m evaluation_framework > new_results.json
   ```

3. Compare metrics:
   ```bash
   # Check if overall_score improved
   cat new_results.json | jq '.summary.avg_overall_score'
   ```

## Golden Concepts Reference

See `test_dataset.py` for examples of what "good" looks like:

- **FitFlow** (fitness) — Concept 0: "Morning movement ritual" shows authentic lifestyle
- **EcoHome** (eco) — Concept 1: "Bulk refill ritual" shows practical sustainability
- **GlowNature** (beauty) — Concept 2: "Real skin radiance" avoids unrealistic transformations
- **NourishBowl** (food) — Concept 1: "Macro transparency" educates while showing product
- **EthicalThreads** (fashion) — Concept 2: "Real diversity" shows inclusive casting

Study these to understand what the scoring system values.

## Troubleshooting

**Error: "Failed to parse concept response"**
- Prompt may be generating invalid JSON
- Add clearer instruction about JSON-only response

**Error: "Claude response contained no text block"**
- API might be throttled; wait and retry

**Low scores across the board**
- Your prompt may not be grounding concepts in brand memory
- Add explicit instruction: "Ground the headline, rationale, and prompt for each concept in the brand identity, audience, visual identity, tone, avoid-lists, and AI-behaviour settings above."

**Diversity always low**
- Current prompt may need to explicitly ask for 3 different concept types
- Try: "concept 1 should focus on [pillar1], concept 2 on [pillar2], concept 3 on [pillar3 or product]"

## Files to Know

- `claude_orchestrator.py:123-187` — The actual prompt you're improving
- `test_dataset.py` — Test cases + golden concepts
- `evaluation_framework.py` — Scoring logic
- `EVALUATION_README.md` — Detailed evaluation docs
