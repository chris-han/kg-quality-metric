"""
Pipeline: IE Systems → KG Quality Correlation with Link Prediction
===================================================================

Correlates KGCQual scores with link prediction performance (MRR/Hits@10)
across IE systems (MinIE, OllIE, ClausIE, Stanford OpenIE, GPT-4, Claude, Gemini)
and datasets (WebNLG, TinyButMighty, BenchIE).

Flow:
1. Load sentences from each dataset
2. Load extracted triples from each IE system
3. Create train/test/valid splits from triples
4. Train embedding models (TuckER, ComplEx, NodePiece)
5. Record MRR and Hits@10
6. Correlate with KGCQual scores
"""

import json
import sys
import time
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

import numpy as np
import pandas as pd
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(__file__).parent.parent
RESULTS_DIR = Path(__file__).parent / "ie_system_results"
RESULTS_DIR.mkdir(exist_ok=True)

# Datasets with their sentence files and IE system triples
DATASETS = {
    "WebNLG": {
        "sentences_file": WORKSPACE_ROOT / "sentences_webnlg.txt",
        "ie_systems": {
            "claude": WORKSPACE_ROOT / "Json" / "claude3.7sonnet.json",
            "gemini": WORKSPACE_ROOT / "Json" / "gemini2.5pro.json",
            "gpt4": WORKSPACE_ROOT / "Json" / "GPT-4o-mini.json",
            "stanford_4.5.3": WORKSPACE_ROOT / "Json" / "stanford_4.5.3_openie.json",
            "stanford_4.5.6": WORKSPACE_ROOT / "Json" / "stanford_4.5.6_openie.json",
            "clauseie": WORKSPACE_ROOT / "Json" / "triple_clauseie.json",
            "minie": WORKSPACE_ROOT / "Json" / "triple_minie.json",
            "ollie": WORKSPACE_ROOT / "Json" / "triple_ollie.json",
        }
    },
    "BenchIE": {
        "sentences_file": WORKSPACE_ROOT / "sentences_benchie.txt",
        "ie_systems": {
            "stanford_4.5.3": WORKSPACE_ROOT / "Json_benchie" / "stanford_4.5.3_openie.json",
            "stanford_4.5.6": WORKSPACE_ROOT / "Json_benchie" / "stanford_4.5.6_openie.json",
            "clauseie": WORKSPACE_ROOT / "Json_benchie" / "triple_clausie.json",
            "minie": WORKSPACE_ROOT / "Json_benchie" / "triple_minie.json",
            "ollie": WORKSPACE_ROOT / "Json_benchie" / "triple_ollie.json",
        }
    },
    "TinyButMighty": {
        "sentences_file": WORKSPACE_ROOT / "sentences_tinybutMighty.txt",
        "ie_systems": {
            "stanford_4.5.3": WORKSPACE_ROOT / "Json_tinybutmighty" / "stanford_4.5.3_openie.json",
            "stanford_4.5.6": WORKSPACE_ROOT / "Json_tinybutmighty" / "stanford_4.5.6_openie.json",
            "clauseie": WORKSPACE_ROOT / "Json_tinybutmighty" / "triple_clausie.json",
            "minie": WORKSPACE_ROOT / "Json_tinybutmighty" / "triple_minie.json",
            "ollie": WORKSPACE_ROOT / "Json_tinybutmighty" / "triple_ollie.json",
        }
    },
}

MODELS = ["TuckER", "ComplEx", "NodePiece"]
QUALITY_SCORE_DIR = WORKSPACE_ROOT / "final_output_scores"

# ─────────────────────────────────────────────────────────────────────────────
# TRIPLE LOADING & PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def load_triples_from_json(json_file: Path) -> List[Tuple[str, str, str]]:
    """Load triples from JSON file (format: {id: [[s,r,o], ...], ...})."""
    if not json_file.exists():
        print(f"  ⚠️  {json_file.name} not found")
        return []
    
    with open(json_file, encoding='utf-8') as f:
        data = json.load(f)
    
    triples = []
    for sent_id, triple_list in data.items():
        if isinstance(triple_list, list):
            for triple in triple_list:
                if isinstance(triple, list) and len(triple) >= 3:
                    # Handle both 3-tuples and 4-tuples (with polarity)
                    s, r, o = triple[0], triple[1], triple[2]
                    # Clean and normalize
                    s, r, o = str(s).strip(), str(r).strip(), str(o).strip()
                    # Filter out invalid triples
                    if s and r and o and len(s) > 1 and len(r) > 1 and len(o) > 1:
                        triples.append((s, r, o))
    
    return triples


def create_train_test_valid_splits(
    triples: List[Tuple[str, str, str]],
    train_ratio: float = 0.7,
    test_ratio: float = 0.15,
    seed: int = 42
) -> Tuple[List[Tuple[str, str, str]], List[Tuple[str, str, str]], List[Tuple[str, str, str]]]:
    """Split triples into train/test/valid."""
    np.random.seed(seed)
    indices = np.random.permutation(len(triples))
    
    train_end = int(len(triples) * train_ratio)
    test_end = train_end + int(len(triples) * test_ratio)
    
    train = [triples[i] for i in indices[:train_end]]
    test = [triples[i] for i in indices[train_end:test_end]]
    valid = [triples[i] for i in indices[test_end:]]
    
    return train, test, valid


def save_triple_files(
    triples: List[Tuple[str, str, str]],
    output_dir: Path,
    prefix: str
) -> Tuple[Path, Path, Path]:
    """Save train/test/valid triples as tab-separated files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    train, test, valid = create_train_test_valid_splits(triples)
    
    train_file = output_dir / f"{prefix}_train.txt"
    test_file = output_dir / f"{prefix}_test.txt"
    valid_file = output_dir / f"{prefix}_valid.txt"
    
    for path, data in [(train_file, train), (test_file, test), (valid_file, valid)]:
        with open(path, 'w', encoding='utf-8') as f:
            for s, r, o in data:
                f.write(f"{s}\t{r}\t{o}\n")
    
    return train_file, test_file, valid_file


def build_model_kwargs(model_name: str, embedding_dim: int = 200, num_anchors: int = 500) -> dict:
    """Build model-specific kwargs for PyKEEN pipeline."""
    if model_name == "NodePiece":
        return dict(
            model_kwargs=dict(
                embedding_dim=embedding_dim,
            )
        )
    if model_name == "TuckER":
        return dict(
            model_kwargs=dict(
                embedding_dim=embedding_dim,
                relation_dim=embedding_dim,
            )
        )
    if model_name == "ComplEx":
        return dict(
            model_kwargs=dict(embedding_dim=embedding_dim),
            optimizer_kwargs=dict(lr=0.001),
        )
    return {}


def extract_metrics(result) -> dict:
    """Extract MRR, Hits@1, Hits@3, Hits@10, MR from PyKEEN result."""
    m = result.metric_results
    return {
        "MRR": round(m.get_metric("mean_reciprocal_rank"), 4),
        "Hits@1": round(m.get_metric("hits_at_1"), 4),
        "Hits@3": round(m.get_metric("hits_at_3"), 4),
        "Hits@10": round(m.get_metric("hits_at_10"), 4),
        "MR": round(m.get_metric("mean_rank"), 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# QUALITY SCORE LOADING
# ─────────────────────────────────────────────────────────────────────────────

def extract_quality_scores(dataset_name: str) -> Optional[Dict[str, float]]:
    """
    Extract KGCQual scores for each IE system from final_output_scores.
    
    Looks for files like: final_score_clausie.txt, final_score_minie.txt, etc.
    Each file should contain the quality score for that system on the dataset.
    """
    scores = {}
    
    # Map IE system names to file patterns
    ie_file_patterns = {
        "clauseie": "final_score_clausie.txt",
        "minie": "final_score_minie.txt",
        "ollie": "final_score_ollie.txt",
        "stanford_4.5.3": "final_score_stanford_4.5.3_openie.txt",
        "stanford_4.5.6": "final_score_stanford_4.5.6_openie.txt",
    }
    
    for ie_name, file_pattern in ie_file_patterns.items():
        score_file = QUALITY_SCORE_DIR / file_pattern
        
        if score_file.exists():
            try:
                with open(score_file) as f:
                    content = f.read().strip()
                    # Try to extract a numeric score (first number found)
                    match = re.search(r'[\d.]+', content)
                    if match:
                        scores[ie_name] = float(match.group())
            except Exception as e:
                print(f"  ⚠️  Could not read quality score from {score_file}: {e}")
    
    # For LLMs (Claude, GPT, Gemini), quality scores may not exist in final_output_scores
    # They can be added manually or we'll mark them as NaN
    for llm in ["claude", "gemini", "gpt4"]:
        if llm not in scores:
            scores[llm] = np.nan
    
    return scores if scores else None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def process_dataset(dataset_name: str, dataset_info: dict) -> pd.DataFrame:
    """Process one dataset: load sentences, extract triples, train models."""
    print(f"\n{'='*70}")
    print(f"  DATASET: {dataset_name}")
    print(f"{'='*70}")
    
    results = []
    
    for ie_system, triple_file in dataset_info["ie_systems"].items():
        print(f"\n  [{ie_system}] Loading triples from {triple_file.name} …")
        
        if not triple_file.exists():
            print(f"    ⚠️  File not found: {triple_file}")
            continue
        
        triples = load_triples_from_json(triple_file)
        
        if len(triples) < 10:
            print(f"    ⚠️  Too few triples ({len(triples)}), skipping")
            continue
        
        print(f"    ✅ Loaded {len(triples)} triples")
        
        # Create temporary directory for this IE system's splits
        temp_dir = RESULTS_DIR / f"temp_{dataset_name}_{ie_system}"
        train_file, test_file, valid_file = save_triple_files(
            triples, temp_dir, f"{dataset_name}_{ie_system}"
        )
        
        # Load as TriplesFactory
        try:
            train_tf = TriplesFactory.from_path(train_file, create_inverse_triples=True)
            test_tf = TriplesFactory.from_path(
                test_file,
                entity_to_id=train_tf.entity_to_id,
                relation_to_id=train_tf.relation_to_id,
            )
            valid_tf = TriplesFactory.from_path(
                valid_file,
                entity_to_id=train_tf.entity_to_id,
                relation_to_id=train_tf.relation_to_id,
            )
        except Exception as e:
            print(f"    ❌ Error loading triples: {e}")
            continue
        
        print(f"    Entities: {len(train_tf.entity_to_id)}, Relations: {len(train_tf.relation_to_id)}")
        
        # Train models
        for model_name in MODELS:
            print(f"      Training {model_name} …", end=" ", flush=True)
            
            t_start = time.time()
            try:
                overrides = {}
                if model_name == "TuckER":
                    overrides = {"embedding_dim": 100}
                elif model_name == "ComplEx":
                    overrides = {"embedding_dim": 128}
                elif model_name == "NodePiece":
                    overrides = {"num_anchors": 250}
                
                model_kwargs = build_model_kwargs(model_name, **overrides)
                
                result = pipeline(
                    model=model_name,
                    training=train_tf,
                    testing=test_tf,
                    validation=valid_tf,
                    training_loop="sLCWA",
                    epochs=50,
                    stopper="early",
                    stopper_kwargs=dict(patience=3, metric="hits_at_10", larger_is_better=True),
                    device="cuda" if is_cuda_available() else "cpu",
                    **model_kwargs,
                )
                
                elapsed = round(time.time() - t_start, 1)
                metrics = extract_metrics(result)
                
                result_entry = {
                    "dataset": dataset_name,
                    "ie_system": ie_system,
                    "model": model_name,
                    "num_triples": len(triples),
                    "num_entities": len(train_tf.entity_to_id),
                    "num_relations": len(train_tf.relation_to_id),
                    "time_s": elapsed,
                    **metrics,
                }
                
                results.append(result_entry)
                
                print(f"✅ ({elapsed}s, MRR={metrics['MRR']}, H@10={metrics['Hits@10']})")
                
            except Exception as e:
                elapsed = round(time.time() - t_start, 1)
                print(f"❌ Error: {str(e)[:50]}")
                
                results.append({
                    "dataset": dataset_name,
                    "ie_system": ie_system,
                    "model": model_name,
                    "num_triples": len(triples),
                    "time_s": elapsed,
                    "error": str(e),
                })
    
    return pd.DataFrame(results)


def is_cuda_available():
    """Check if CUDA is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except:
        return False


def main():
    print("\n" + "="*70)
    print("  IE SYSTEMS → KG QUALITY CORRELATION PIPELINE")
    print("="*70)
    
    all_results = []
    
    # Process each dataset
    for dataset_name, dataset_info in DATASETS.items():
        if not dataset_info["sentences_file"].exists():
            print(f"\n⚠️  {dataset_name} sentences file not found: {dataset_info['sentences_file']}")
            continue
        
        df_dataset = process_dataset(dataset_name, dataset_info)
        all_results.append(df_dataset)
    
    # Combine results
    if all_results:
        df_final = pd.concat(all_results, ignore_index=True)
        
        # Save main results
        results_csv = RESULTS_DIR / "ie_system_results.csv"
        df_final.to_csv(results_csv, index=False)
        print(f"\n✅ Results saved to: {results_csv}")
        
        # Try to load quality scores and correlate
        print("\n" + "="*70)
        print("  QUALITY SCORE CORRELATION")
        print("="*70)
        
        # For each dataset, try to get quality scores
        for dataset_name in DATASETS.keys():
            quality_scores = extract_quality_scores(dataset_name)
            if quality_scores:
                print(f"\n{dataset_name} - Quality Scores:")
                for ie_sys, score in quality_scores.items():
                    print(f"  {ie_sys}: {score}")
        
        # Summary statistics
        print("\n" + "="*70)
        print("  SUMMARY STATISTICS")
        print("="*70)
        print(df_final.groupby(["dataset", "model"])[["MRR", "Hits@10"]].mean())
        
    else:
        print("\n❌ No results generated.")
    
    print("\n✅ Pipeline complete!")


if __name__ == "__main__":
    main()
