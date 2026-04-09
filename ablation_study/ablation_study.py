"""
Ablation Study: Noun Metric vs. Verb (Predicate) Metric
========================================================

This script reads the per-sentence noun and verb scores produced by Main.java
and evaluates how each component contributes to the final score under various
weighting scenarios:

  Scenario A — Noun metric only   (w_noun=1.0, w_verb=0.0)
  Scenario B — Verb metric only   (w_noun=0.0, w_verb=1.0)
  Scenario C — Equal weights      (w_noun=0.5, w_verb=0.5)
  Scenario D — Noun-dominant      (w_noun=0.7, w_verb=0.3)
  Scenario E — Verb-dominant      (w_noun=0.3, w_verb=0.7)

All outputs (per-sentence CSVs + the summary report) are saved inside this
ablation_study/ folder.
"""

import os
import csv
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Configuration: pairs of (noun_file, verb_file, tool_label)
# Paths are relative to the project root (one level up from this script)
# ─────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent  # kg-quality-metric/

TOOL_CONFIGS = [
    # (noun score file,                                  verb score file,                                            label)
    # ── Traditional OIE tools ──
    (ROOT / "output"           / "clausie_output.txt",            ROOT / "output_predicate"           / "clausie_predicate_output.txt",            "ClausIE"),
    (ROOT / "output"           / "minie_output.txt",              ROOT / "output_predicate"           / "minie_predicate_output.txt",              "MiniE"),
    (ROOT / "output"           / "ollie_output.txt",              ROOT / "output_predicate"           / "ollie_predicate_output.txt",              "Ollie"),
    (ROOT / "output"           / "stanford_4.5.3_openie_output.txt", ROOT / "output_predicate"        / "stanford_4.5.3_openie_predicate_output.txt", "Stanford 4.5.3"),
    (ROOT / "output"           / "stanford_4.5.6_openie_output.txt", ROOT / "output_predicate"        / "stanford_4.5.6_openie_predicate_output.txt", "Stanford 4.5.6"),
    # ── LLM-based tools ──
    (ROOT / "output"           / "claude.txt",                    ROOT / "output_predicate"           / "claude.txt",                    "Claude"),
    (ROOT / "output"           / "gemini.txt",                    ROOT / "output_predicate"           / "gemini.txt",                    "Gemini"),
    (ROOT / "output"           / "gpt4mini.txt",                  ROOT / "output_predicate"           / "gpt4mini.txt",                  "GPT-4o mini"),
    # ── Ideal / TinyButMighty ──
    (ROOT / "output_ideal_tinybutmighty" / "ideal_tinybutmighty.txt",
     ROOT / "output_predicate_ideal_tinybutmighty" / "ideal_tinybutmighty.txt",
     "Ideal (TinyButMighty)"),
]

# Ablation scenarios: (label, w_noun, w_verb)
SCENARIOS = [
    ("Noun Only   (1.0, 0.0)", 1.0, 0.0),
    ("Verb Only   (0.0, 1.0)", 0.0, 1.0),
    ("Equal       (0.5, 0.5)", 0.5, 0.5),
    ("Noun-heavy  (0.7, 0.3)", 0.7, 0.3),
    ("Verb-heavy  (0.3, 0.7)", 0.3, 0.7),
]

OUT_DIR = Path(__file__).parent  # ablation_study/


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def parse_score_file(path: Path) -> dict[int, float]:
    """
    Parse a Java output file with lines like:   <sentence_id> <score>
    Returns a dict {sentence_id: score}.
    Lines that don't match (e.g., the trailing average line) are skipped.
    """
    scores: dict[int, float] = {}
    if not path.exists():
        return scores
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    sid = int(parts[0])
                    val = float(parts[1])
                    scores[sid] = val
                except ValueError:
                    pass  # skip e.g. "Avg. value is: …"
    return scores


def combined_score(noun: float, verb: float, w_n: float, w_v: float) -> float:
    return w_n * noun + w_v * verb


def safe_avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


# ─────────────────────────────────────────────────────────────────────────────
# Main computation
# ─────────────────────────────────────────────────────────────────────────────

def run_ablation():
    summary_rows: list[dict] = []   # one row per (tool, scenario)
    all_results: dict[str, dict] = {}  # tool -> {scenario_label -> per_sentence_list}

    for noun_path, verb_path, tool_label in TOOL_CONFIGS:
        noun_scores = parse_score_file(noun_path)
        verb_scores = parse_score_file(verb_path)

        if not noun_scores and not verb_scores:
            print(f"[SKIP] {tool_label}: no files found at:\n"
                  f"       {noun_path}\n       {verb_path}")
            continue

        # Union of sentence IDs present in either file
        all_ids = sorted(set(noun_scores) | set(verb_scores))

        tool_results: dict[str, list[float]] = {}

        for scenario_label, w_n, w_v in SCENARIOS:
            per_sentence: list[float] = []
            for sid in all_ids:
                n = noun_scores.get(sid, float("nan"))
                v = verb_scores.get(sid, float("nan"))
                # If one metric is missing for this sentence, use 1.0 (worst)
                n = n if not (n != n) else 1.0   # nan → 1.0
                v = v if not (v != v) else 1.0
                per_sentence.append(combined_score(n, v, w_n, w_v))
            tool_results[scenario_label] = per_sentence
            avg = safe_avg(per_sentence)
            summary_rows.append({
                "Tool": tool_label,
                "Scenario": scenario_label.strip(),
                "Avg Score": round(avg, 6),
            })

        all_results[tool_label] = (all_ids, tool_results)

        # ── Save per-sentence CSV for this tool ──
        safe_name = tool_label.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
        csv_path = OUT_DIR / f"per_sentence_{safe_name}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            fieldnames = ["SentenceID", "NounScore", "VerbScore"] + [s for s, *_ in SCENARIOS]
            writer = csv.DictWriter(cf, fieldnames=fieldnames)
            writer.writeheader()
            for i, sid in enumerate(all_ids):
                row_data = {
                    "SentenceID": sid,
                    "NounScore": round(noun_scores.get(sid, float("nan")), 6),
                    "VerbScore": round(verb_scores.get(sid, float("nan")), 6),
                }
                for scenario_label, w_n, w_v in SCENARIOS:
                    row_data[scenario_label] = round(tool_results[scenario_label][i], 6)
                writer.writerow(row_data)
        print(f"[OK]   {tool_label}: per-sentence CSV saved → {csv_path.name}")

    # ── Save summary CSV ──
    summary_csv = OUT_DIR / "ablation_summary.csv"
    if summary_rows:
        with open(summary_csv, "w", newline="", encoding="utf-8") as sf:
            writer = csv.DictWriter(sf, fieldnames=["Tool", "Scenario", "Avg Score"])
            writer.writeheader()
            writer.writerows(summary_rows)

    # ── Build and save markdown report ──
    write_markdown_report(summary_rows, all_results)


# ─────────────────────────────────────────────────────────────────────────────
# Markdown report
# ─────────────────────────────────────────────────────────────────────────────

def write_markdown_report(summary_rows, all_results):
    md_path = OUT_DIR / "ablation_report.md"

    # Group by scenario for the main pivot table
    # We want: rows = tools, columns = scenarios
    tools_ordered = []
    seen = set()
    for r in summary_rows:
        t = r["Tool"]
        if t not in seen:
            tools_ordered.append(t)
            seen.add(t)

    scenarios_ordered = [s.strip() for s, *_ in SCENARIOS]

    # Build lookup {tool: {scenario: score}}
    lookup: dict[str, dict[str, float]] = {}
    for r in summary_rows:
        lookup.setdefault(r["Tool"], {})[r["Scenario"]] = r["Avg Score"]

    lines = [
        "# Ablation Study — Noun Metric vs. Verb Metric",
        "",
        "## Overview",
        "",
        "This report evaluates how the **Noun metric** and **Verb (Predicate) metric**",
        "individually and jointly drive the final Knowledge Graph triple quality score.",
        "",
        "**Scoring formula:**",
        "```",
        "final_score(sentence) = w_noun × noun_score + w_verb × verb_score",
        "```",
        "",
        "Lower scores = better quality (scores are *distance-based* metrics).",
        "",
        "---",
        "",
        "## Ablation Scenarios",
        "",
        "| ID | Scenario         | w\\_noun | w\\_verb |",
        "|----|-----------------|--------|--------|",
    ]
    for i, (lbl, wn, wv) in enumerate(SCENARIOS, start=1):
        lines.append(f"| {chr(64+i)}  | {lbl.strip()} | {wn}    | {wv}    |")

    lines += [
        "",
        "---",
        "",
        "## Average Scores by Tool and Scenario",
        "",
        "*(Lower is better)*",
        "",
    ]

    # Header row
    header = "| Tool | " + " | ".join(scenarios_ordered) + " |"
    sep    = "| --- | " + " | ".join(["---"] * len(scenarios_ordered)) + " |"
    lines += [header, sep]

    for tool in tools_ordered:
        cells = []
        for sc in scenarios_ordered:
            val = lookup.get(tool, {}).get(sc, float("nan"))
            cells.append(f"{val:.4f}" if val == val else "N/A")
        lines.append(f"| {tool} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "---",
        "",
        "## Key Insights",
        "",
        "### Noun Metric Contribution",
        "Compare column **A (Noun Only)** across tools to see how well each tool",
        "captures subject/object noun phrases.",
        "",
        "### Verb Metric Contribution",
        "Compare column **B (Verb Only)** to isolate predicate quality.",
        "",
        "### Relative Importance",
        "If **A < B** for a tool → that tool's noun extraction is better than its predicate extraction.",
        "If **B < A** → predicate extraction is the stronger component.",
        "",
        "---",
        "",
        "## Files Generated",
        "",
        "| File | Description |",
        "| --- | --- |",
        "| `ablation_report.md` | This report |",
        "| `ablation_summary.csv` | All (tool, scenario, avg_score) in CSV |",
    ]

    for noun_path, _, tool_label in TOOL_CONFIGS:
        safe_name = tool_label.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
        lines.append(f"| `per_sentence_{safe_name}.csv` | Per-sentence noun, verb, and combined scores for {tool_label} |")

    lines += ["", "---", "", "*Generated automatically by `ablation_study.py`*", ""]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n[DONE] Markdown report saved → {md_path}")
    print(f"[DONE] Summary CSV saved    → {OUT_DIR / 'ablation_summary.csv'}")

    # Also print the pivot table to console
    print("\n" + "="*80)
    print("ABLATION RESULTS (Average scores, lower = better)")
    print("="*80)
    col_w = 18
    header_parts = [f"{'Tool':<28}"] + [f"{s.split('(')[0].strip()[:col_w]:>{col_w}}" for s in scenarios_ordered]
    print("  ".join(header_parts))
    print("-" * (28 + (col_w + 2) * len(scenarios_ordered)))
    for tool in tools_ordered:
        row_parts = [f"{tool:<28}"]
        for sc in scenarios_ordered:
            val = lookup.get(tool, {}).get(sc, float("nan"))
            row_parts.append(f"{val:>{col_w}.4f}" if val == val else f"{'N/A':>{col_w}}")
        print("  ".join(row_parts))


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_ablation()
