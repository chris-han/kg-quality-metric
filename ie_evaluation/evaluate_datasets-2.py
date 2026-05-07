"""
Knowledge Graph Experiment — ALL DATASETS (FINAL)
==================================================
Datasets : FB15k-237 ✅ | WN18RR ✅ | Nations ✅ | Kinships ✅
Models   : TuckER, ComplEx, NodePiece

Note: Nations and Kinships replace FB15k and WN18 due to broken
download URLs in PyKEEN for those datasets. Nations and Kinships
are valid built-in KG benchmarks with no download issues.
"""

import json
import time
import warnings
from pathlib import Path

import pandas as pd
from pykeen.pipeline import pipeline

warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────

MODELS = ["TuckER", "ComplEx", "NodePiece"]

DATASETS = {
    "FB15k-237": {
        "name" : "FB15k237",
        "note" : "Large clean benchmark (14k entities, 237 relations)",
        "model_overrides": {
            "TuckER"   : dict(embedding_dim=200, relation_dim=200),
            "ComplEx"  : dict(embedding_dim=256),
            "NodePiece": dict(num_anchors=500),
        },
    },
    "WN18RR": {
        "name" : "WN18RR",
        "note" : "Large clean benchmark (40k entities, 11 relations)",
        "model_overrides": {
            "TuckER"   : dict(embedding_dim=200, relation_dim=200),
            "ComplEx"  : dict(embedding_dim=256),
            "NodePiece": dict(num_anchors=500),
        },
    },
    "Nations": {
        "name" : "Nations",
        "note" : "Small benchmark (14 entities, 55 relations, ~2k triples)",
        "model_overrides": {
            "TuckER"   : dict(embedding_dim=64, relation_dim=64),   # small dataset → small embeddings
            "ComplEx"  : dict(embedding_dim=64),
            "NodePiece": dict(num_anchors=5),                       # only 14 entities!
        },
    },
    "Kinships": {
        "name" : "Kinships",
        "note" : "Small benchmark (104 entities, 25 relations, ~10k triples)",
        "model_overrides": {
            "TuckER"   : dict(embedding_dim=128, relation_dim=128),
            "ComplEx"  : dict(embedding_dim=128),
            "NodePiece": dict(num_anchors=20),
        },
    },
}

OUTPUT_DIR = Path("results_all")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def build_model_kwargs(model_name: str, overrides: dict) -> dict:
    if model_name == "NodePiece":
        return dict(
            model_kwargs=dict(
                tokenizers="AnchorTokenizer",
                tokenizers_kwargs=dict(
                    selection="Degree",
                    selection_kwargs=dict(
                        num_anchors=overrides.get("num_anchors", 500),
                    ),
                ),
            )
        )
    if model_name == "TuckER":
        return dict(
            model_kwargs=dict(
                embedding_dim=overrides.get("embedding_dim", 200),
                relation_dim =overrides.get("relation_dim",  200),
            )
        )
    if model_name == "ComplEx":
        return dict(
            model_kwargs=dict(embedding_dim=overrides.get("embedding_dim", 256)),
            optimizer_kwargs=dict(lr=0.001),
        )
    return {}


def extract_metrics(result) -> dict:
    m = result.metric_results
    return {
        "MRR"    : round(m.get_metric("mean_reciprocal_rank"), 4),
        "Hits@1" : round(m.get_metric("hits_at_1"),            4),
        "Hits@3" : round(m.get_metric("hits_at_3"),            4),
        "Hits@10": round(m.get_metric("hits_at_10"),           4),
        "MR"     : round(m.get_metric("mean_rank"),            2),
    }


def print_header(text: str, width: int = 65):
    print(f"\n{'='*width}\n  {text}\n{'='*width}")


# ── Main loop ─────────────────────────────────────────────────────────────────

rows       = []
total_runs = len(MODELS) * len(DATASETS)
run_count  = 0

print_header("ALL DATASETS — Knowledge Graph Experiment")
print(f"  Datasets : {', '.join(DATASETS.keys())}")
print(f"  Models   : {', '.join(MODELS)}")
print(f"  Total    : {total_runs} runs\n")

for dataset_label, ds_info in DATASETS.items():
    print_header(f"Dataset: {dataset_label}")
    print(f"  Note: {ds_info['note']}")

    for model_name in MODELS:
        run_count += 1
        print(f"\n  [{run_count}/{total_runs}]  {model_name} on {dataset_label} …")

        overrides    = ds_info["model_overrides"].get(model_name, {})
        model_kwargs = build_model_kwargs(model_name, overrides)

        # NodePiece requires inverse triples
        dataset_kwargs = {}
        if model_name == "NodePiece":
            dataset_kwargs = {"create_inverse_triples": True}

        t_start = time.time()
        try:
            result = pipeline(
                model=model_name,
                dataset=ds_info["name"],
                dataset_kwargs=dataset_kwargs,
                training_loop="sLCWA",
                epochs=100,
                stopper="early",
                stopper_kwargs=dict(patience=5, metric="hits_at_10", larger_is_better=True),
                device="cuda",
                **model_kwargs,
            )

            elapsed = round(time.time() - t_start, 1)
            metrics = extract_metrics(result)

            run_data = {
                "model"  : model_name,
                "dataset": dataset_label,
                "time_s" : elapsed,
                **metrics,
            }

            run_id = f"{model_name}_{dataset_label.replace('-', '')}"
            (OUTPUT_DIR / f"{run_id}.json").write_text(json.dumps(run_data, indent=2))
            rows.append(run_data)
            print(f"     ✅ Done in {elapsed}s  |  MRR={metrics['MRR']}  H@10={metrics['Hits@10']}")

        except Exception as exc:
            elapsed = round(time.time() - t_start, 1)
            print(f"     ❌ ERROR after {elapsed}s: {exc}")
            rows.append({
                "model": model_name, "dataset": dataset_label,
                "time_s": elapsed,
                "MRR": None, "Hits@1": None, "Hits@3": None,
                "Hits@10": None, "MR": None, "error": str(exc),
            })

# ── Summary ───────────────────────────────────────────────────────────────────

df = pd.DataFrame(rows)
print_header("FINAL RESULTS SUMMARY", width=70)

for dataset_label in DATASETS:
    sub  = df[df["dataset"] == dataset_label]
    print(f"\n  {dataset_label}  —  {DATASETS[dataset_label]['note']}")
    cols = [c for c in ["model","MRR","Hits@1","Hits@3","Hits@10","MR","time_s"] if c in sub.columns]
    print(sub[cols].to_string(index=False))

csv_path = OUTPUT_DIR / "all_results.csv"
df.to_csv(csv_path, index=False)
print(f"\n\n→ Full results saved to : {csv_path}")
print(f"→ Individual JSONs in   : {OUTPUT_DIR}/")