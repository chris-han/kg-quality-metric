"""
Correlation Analysis: KGCQual vs Link Prediction Performance
============================================================

Analyzes correlation between KGCQual quality scores and link prediction metrics
(MRR, Hits@10) across IE systems and datasets.
"""

import json
import warnings
from pathlib import Path
from typing import Dict, Optional, Tuple
import re

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(__file__).parent.parent
RESULTS_DIR = Path(__file__).parent / "ie_system_results"
QUALITY_SCORE_DIR = WORKSPACE_ROOT / "final_output_scores"

# ─────────────────────────────────────────────────────────────────────────────
# QUALITY SCORE EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def read_quality_score_file(file_path: Path) -> Optional[float]:
    """
    Read a single quality score file.
    
    The file format may vary, but typically contains:
    - A single score line: "dataset: score"
    - Multiple lines with the score being the last one
    """
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read().strip()
        
        # Try to extract numeric value(s)
        # Look for patterns like "0.123" or "Score: 0.123"
        matches = re.findall(r'[\d.]+', content)
        
        if matches:
            # Return the last numeric value (usually the final score)
            return float(matches[-1])
    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
    
    return None


def load_all_quality_scores() -> Dict[str, float]:
    """Load all available KGCQual quality scores."""
    scores = {}
    
    # File mapping: (file_path, ie_system_name)
    file_mappings = [
        (QUALITY_SCORE_DIR / "final_score_clausie.txt", "clauseie"),
        (QUALITY_SCORE_DIR / "final_score_minie.txt", "minie"),
        (QUALITY_SCORE_DIR / "final_score_ollie.txt", "ollie"),
        (QUALITY_SCORE_DIR / "final_score_stanford_4.5.3_openie.txt", "stanford_4.5.3"),
        (QUALITY_SCORE_DIR / "final_score_stanford_4.5.6_openie.txt", "stanford_4.5.6"),
    ]
    
    for file_path, ie_name in file_mappings:
        score = read_quality_score_file(file_path)
        if score is not None:
            scores[ie_name] = score
            print(f"  ✅ {ie_name}: {score:.4f}")
        else:
            print(f"  ⚠️  {ie_name}: not found")
    
    return scores


def merge_results_with_quality(
    results_csv: Path,
    quality_scores: Dict[str, float]
) -> pd.DataFrame:
    """
    Merge link prediction results with quality scores.
    
    Returns DataFrame with columns:
    - dataset, ie_system, model, MRR, Hits@10, KGCQual
    """
    if not results_csv.exists():
        raise FileNotFoundError(f"Results CSV not found: {results_csv}")
    
    df = pd.read_csv(results_csv)
    
    # Map quality scores to results
    df["KGCQual"] = df["ie_system"].map(quality_scores)
    
    # Filter to rows where we have quality scores
    df_with_quality = df[df["KGCQual"].notna()].copy()
    
    print(f"\n  Matched {len(df_with_quality)} results with quality scores")
    print(f"  (Skipped {len(df) - len(df_with_quality)} results without quality scores)")
    
    return df_with_quality


# ─────────────────────────────────────────────────────────────────────────────
# CORRELATION ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def compute_correlations(df: pd.DataFrame) -> Dict:
    """
    Compute correlations between KGCQual and performance metrics.
    
    Lower KGCQual = better quality
    Higher MRR, Hits@10 = better performance
    
    Therefore, we expect negative correlation (lower quality → higher errors → lower MRR)
    """
    
    # Remove NaN values
    df_clean = df[["KGCQual", "MRR", "Hits@10"]].dropna()
    
    if len(df_clean) < 3:
        print("  ⚠️  Not enough data for correlation analysis")
        return {}
    
    correlations = {}
    
    for metric in ["MRR", "Hits@10"]:
        # Pearson correlation
        pearson_r, pearson_p = stats.pearsonr(df_clean["KGCQual"], df_clean[metric])
        
        # Spearman correlation
        spearman_r, spearman_p = stats.spearmanr(df_clean["KGCQual"], df_clean[metric])
        
        correlations[metric] = {
            "pearson_r": pearson_r,
            "pearson_p": pearson_p,
            "spearman_r": spearman_r,
            "spearman_p": spearman_p,
            "n_samples": len(df_clean),
        }
    
    return correlations


def print_correlation_results(correlations: Dict):
    """Pretty-print correlation results."""
    print("\n" + "="*70)
    print("  CORRELATION ANALYSIS: KGCQual vs Link Prediction")
    print("="*70)
    print("\nInterpretation:")
    print("  Lower KGCQual = Better extraction quality")
    print("  Higher MRR/Hits@10 = Better link prediction performance")
    print("  Expected: Negative correlation (high quality → high performance)")
    print()
    
    for metric, stats_dict in correlations.items():
        print(f"\n{metric}:")
        print(f"  Pearson:  r={stats_dict['pearson_r']:+.4f}, p={stats_dict['pearson_p']:.4f}")
        print(f"  Spearman: r={stats_dict['spearman_r']:+.4f}, p={stats_dict['spearman_p']:.4f}")
        print(f"  Samples: {stats_dict['n_samples']}")
        
        # Interpret
        p_pearson = stats_dict['pearson_p']
        r_pearson = stats_dict['pearson_r']
        
        if p_pearson < 0.05:
            direction = "✅ SIGNIFICANT" if abs(r_pearson) > 0.3 else "⚠️  WEAK but significant"
            correlation_type = "NEGATIVE" if r_pearson < 0 else "POSITIVE"
            print(f"  → {direction} {correlation_type} correlation (p < 0.05)")
        else:
            print(f"  → ❌ NOT significant (p ≥ 0.05)")


def create_summary_table(df: pd.DataFrame, quality_scores: Dict[str, float]) -> pd.DataFrame:
    """Create summary table of IE systems with quality and performance metrics."""
    
    # Group by IE system and compute means
    summary = df.groupby("ie_system").agg({
        "MRR": ["mean", "std", "count"],
        "Hits@10": ["mean", "std"],
        "KGCQual": "first",
    }).round(4)
    
    # Flatten column names
    summary.columns = ["_".join(col).strip() for col in summary.columns.values]

    # Normalize KGCQual column name if present (e.g., 'KGCQual_first')
    if "KGCQual_first" in summary.columns:
        summary = summary.rename(columns={"KGCQual_first": "KGCQual"})

    # Add quality score from mapping (ensure a consistent column exists)
    summary["quality_score"] = summary.index.map(quality_scores)

    # If aggregated KGCQual is missing, populate it from `quality_score`
    if "KGCQual" not in summary.columns:
        summary["KGCQual"] = summary["quality_score"]

    # Sort by quality score (lower is better)
    summary = summary.sort_values("KGCQual")
    
    return summary


def main():
    print("\n" + "="*70)
    print("  CORRELATION ANALYSIS: KGCQual vs Link Prediction")
    print("="*70)
    
    # Load quality scores
    print("\n📊 Loading KGCQual Quality Scores:")
    quality_scores = load_all_quality_scores()
    
    if not quality_scores:
        print("\n❌ No quality scores found!")
        return
    
    # Merge with results
    print("\n📊 Loading Link Prediction Results:")
    results_csv = RESULTS_DIR / "ie_system_results.csv"
    
    if not results_csv.exists():
        print(f"❌ Results file not found: {results_csv}")
        print("   Please run: python pipeline_ie_systems.py")
        return
    
    df_merged = merge_results_with_quality(results_csv, quality_scores)
    
    if len(df_merged) == 0:
        print("\n❌ No matching results found!")
        return
    
    # Compute correlations
    print("\n📊 Computing Correlations:")
    correlations = compute_correlations(df_merged)
    print_correlation_results(correlations)
    
    # Summary table
    print("\n" + "="*70)
    print("  IE SYSTEMS SUMMARY TABLE")
    print("="*70)
    
    summary = create_summary_table(df_merged, quality_scores)
    print(summary)
    
    # Save summary
    summary_csv = RESULTS_DIR / "ie_system_summary.csv"
    summary.to_csv(summary_csv)
    print(f"\n✅ Summary saved to: {summary_csv}")
    
    # Save merged results
    merged_csv = RESULTS_DIR / "ie_system_results_with_quality.csv"
    df_merged.to_csv(merged_csv, index=False)
    print(f"✅ Merged results saved to: {merged_csv}")
    
    # Save correlations
    correlations_json = RESULTS_DIR / "correlations.json"
    with open(correlations_json, 'w') as f:
        # Convert numpy types to Python types for JSON serialization
        correlations_serializable = {}
        for metric, stats_dict in correlations.items():
            correlations_serializable[metric] = {
                k: float(v) if isinstance(v, (np.floating, np.integer)) else v
                for k, v in stats_dict.items()
            }
        json.dump(correlations_serializable, f, indent=2)
    
    print(f"✅ Correlations saved to: {correlations_json}")
    
    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
