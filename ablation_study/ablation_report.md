# Ablation Study — Noun Metric vs. Verb Metric

## Overview

This report evaluates how the **Noun metric** and **Verb (Predicate) metric**
individually and jointly drive the final Knowledge Graph triple quality score.

**Scoring formula:**
```
final_score(sentence) = w_noun × noun_score + w_verb × verb_score
```

Lower scores = better quality (scores are *distance-based* metrics).

---

## Ablation Scenarios

| ID | Scenario         | w\_noun | w\_verb |
|----|-----------------|--------|--------|
| A  | Noun Only   (1.0, 0.0) | 1.0    | 0.0    |
| B  | Verb Only   (0.0, 1.0) | 0.0    | 1.0    |
| C  | Equal       (0.5, 0.5) | 0.5    | 0.5    |
| D  | Noun-heavy  (0.7, 0.3) | 0.7    | 0.3    |
| E  | Verb-heavy  (0.3, 0.7) | 0.3    | 0.7    |

---

## Average Scores by Tool and Scenario

*(Lower is better)*

| Tool | Noun Only   (1.0, 0.0) | Verb Only   (0.0, 1.0) | Equal       (0.5, 0.5) | Noun-heavy  (0.7, 0.3) | Verb-heavy  (0.3, 0.7) |
| --- | --- | --- | --- | --- | --- |
| ClausIE | 0.1538 | 0.2301 | 0.1919 | 0.1767 | 0.2072 |
| MiniE | 0.3078 | 0.5712 | 0.4395 | 0.3868 | 0.4922 |
| Ollie | 0.2208 | 0.4657 | 0.3432 | 0.2943 | 0.3922 |
| Stanford 4.5.3 | 0.2431 | 0.4740 | 0.3586 | 0.3124 | 0.4048 |
| Stanford 4.5.6 | 0.2475 | 0.6441 | 0.4458 | 0.3665 | 0.5251 |
| Claude | 0.3546 | 0.5443 | 0.4495 | 0.4115 | 0.4874 |
| Gemini | 0.3674 | 0.5495 | 0.4585 | 0.4221 | 0.4949 |
| GPT-4o mini | 0.4043 | 0.6891 | 0.5467 | 0.4897 | 0.6037 |
| Ideal (TinyButMighty) | 0.3483 | 0.2760 | 0.3122 | 0.3266 | 0.2977 |

---

## Key Insights

### Noun Metric Contribution
Compare column **A (Noun Only)** across tools to see how well each tool
captures subject/object noun phrases.

### Verb Metric Contribution
Compare column **B (Verb Only)** to isolate predicate quality.

### Relative Importance
If **A < B** for a tool → that tool's noun extraction is better than its predicate extraction.
If **B < A** → predicate extraction is the stronger component.

---

## Files Generated

| File | Description |
| --- | --- |
| `ablation_report.md` | This report |
| `ablation_summary.csv` | All (tool, scenario, avg_score) in CSV |
| `per_sentence_ClausIE.csv` | Per-sentence noun, verb, and combined scores for ClausIE |
| `per_sentence_MiniE.csv` | Per-sentence noun, verb, and combined scores for MiniE |
| `per_sentence_Ollie.csv` | Per-sentence noun, verb, and combined scores for Ollie |
| `per_sentence_Stanford_4.5.3.csv` | Per-sentence noun, verb, and combined scores for Stanford 4.5.3 |
| `per_sentence_Stanford_4.5.6.csv` | Per-sentence noun, verb, and combined scores for Stanford 4.5.6 |
| `per_sentence_Claude.csv` | Per-sentence noun, verb, and combined scores for Claude |
| `per_sentence_Gemini.csv` | Per-sentence noun, verb, and combined scores for Gemini |
| `per_sentence_GPT-4o_mini.csv` | Per-sentence noun, verb, and combined scores for GPT-4o mini |
| `per_sentence_Ideal_TinyButMighty.csv` | Per-sentence noun, verb, and combined scores for Ideal (TinyButMighty) |

---

*Generated automatically by `ablation_study.py`*
