"""
Knowledge Graph Experiment — ALL DATASETS (FIXED v4)
=====================================================
Datasets : FB15k-237 ✅ | WN18RR ✅ | FB15k ⚠️ | WN18 ⚠️
Models   : TuckER, ComplEx, NodePiece

Fixes vs previous version:
  1. NodePiece: num_anchors → selection_kwargs=dict(num_anchors=N) ✅
  2. FB15k/WN18: dead URL → load from local files (see SETUP below) ✅
  3. ComplEx: added lr=0.001 so it actually converges ✅

==============================================================
SETUP — do this once before running:
--------------------------------------------------------------
FB15k and WN18 have a broken download URL in PyKEEN.
Download them manually:

  FB15k:
    https://huggingface.co/datasets/pykeen/fb15k/resolve/main/train.txt
    https://huggingface.co/datasets/pykeen/fb15k/resolve/main/test.txt
    https://huggingface.co/datasets/pykeen/fb15k/resolve/main/valid.txt
    → save to:  ./data/fb15k/

  WN18:
    https://huggingface.co/datasets/pykeen/wn18/resolve/main/train.txt
    https://huggingface.co/datasets/pykeen/wn18/resolve/main/test.txt
    https://huggingface.co/datasets/pykeen/wn18/resolve/main/valid.txt
    → save to:  ./data/wn18/

Or run this in terminal to auto-download:
    python kg_experiment_all.py --download
==============================================================
"""

import argparse
import json
import sys
import time
import urllib.request
import warnings
from pathlib import Path

import pandas as pd
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory

warnings.filterwarnings("ignore")

# ── Download helper ───────────────────────────────────────────────────────────

MANUAL_DATASET_URLS = {
    "fb15k": {
        "dir": Path("data/fb15k"),
        "files": {
            "train.txt": "https://huggingface.co/datasets/pykeen/fb15k/resolve/main/train.txt",
            "test.txt" : "https://huggingface.co/datasets/pykeen/fb15k/resolve/main/test.txt",
            "valid.txt": "https://huggingface.co/datasets/pykeen/fb15k/resolve/main/valid.txt",
        }
    },
    "wn18": {
        "dir": Path("data/wn18"),
        "files": {
            "train.txt": "https://huggingface.co/datasets/pykeen/wn18/resolve/main/train.txt",
            "test.txt" : "https://huggingface.co/datasets/pykeen/wn18/resolve/main/test.txt",
            "valid.txt": "https://huggingface.co/datasets/pykeen/wn18/resolve/main/valid.txt",
        }
    },
}


def download_manual_datasets():
    """Download FB15k and WN18 from HuggingFace."""
    for ds_key, info in MANUAL_DATASET_URLS.items():
        info["dir"].mkdir(parents=True, exist_ok=True)
        for fname, url in info["files"].items():
            dest = info["dir"] / fname
            if dest.exists():
                print(f"  already exists: {dest}")
                continue
            print(f"  downloading {dest} …")
            try:
                urllib.request.urlretrieve(url, dest)
                print(f"  ✅ saved {dest}")
            except Exception as e:
                print(f"  ❌ failed: {e}")


def load_local_dataset(ds_key: str, create_inverse: bool = False):
    """Load a manually downloaded dataset as TriplesFactory objects."""
    d = MANUAL_DATASET_URLS[ds_key]["dir"]
    train = TriplesFactory.from_path(d / "train.txt", create_inverse_triples=create_inverse)
    test  = TriplesFactory.from_path(
        d / "test.txt",
        entity_to_id=train.entity_to_id,
        relation_to_id=train.relation_to_id,
    )
    valid = TriplesFactory.from_path(
        d / "valid.txt",
        entity_to_id=train.entity_to_id,
        relation_to_id=train.relation_to_id,
    )
    return train, test, valid


def local_files_exist(ds_key: str) -> bool:
    d = MANUAL_DATASET_URLS[ds_key]["dir"]
    return all((d / f).exists() for f in ["train.txt", "test.txt", "valid.txt"])


# ── Config ────────────────────────────────────────────────────────────────────

MODELS = ["TuckER", "ComplEx", "NodePiece"]

DATASETS = {
    "FB15k-237": {
        "pykeen_name": "FB15k237",
        "local_key"  : None,           # uses PyKEEN built-in
        "leaky"      : False,
        "note"       : "Clean benchmark — trust these scores",
        "model_overrides": {
            "TuckER"   : dict(embedding_dim=200, relation_dim=200),
            "ComplEx"  : dict(embedding_dim=256),
            "NodePiece": dict(num_anchors=500),
        },
    },
    "WN18RR": {
        "pykeen_name": "WN18RR",
        "local_key"  : None,
        "leaky"      : False,
        "note"       : "Clean benchmark — trust these scores",
        "model_overrides": {
            "TuckER"   : dict(embedding_dim=200, relation_dim=200),
            "ComplEx"  : dict(embedding_dim=256),
            "NodePiece": dict(num_anchors=500),
        },
    },
    # "FB15k": {
    #     "pykeen_name": None,
    #     "local_key"  : "fb15k",        # loaded from ./data/fb15k/
    #     "leaky"      : True,
    #     "note"       : "Leaky — inflated scores. Compare with old papers only.",
    #     "model_overrides": {
    #         "TuckER"   : dict(embedding_dim=200, relation_dim=30),
    #         "ComplEx"  : dict(embedding_dim=256),
    #         "NodePiece": dict(num_anchors=250),
    #     },
    # },
    # "WN18": {
    #     "pykeen_name": None,
    #     "local_key"  : "wn18",
    #     "leaky"      : True,
    #     "note"       : "Leaky — inflated scores. Compare with old papers only.",
    #     "model_overrides": {
    #         "TuckER"   : dict(embedding_dim=200, relation_dim=200),
    #         "ComplEx"  : dict(embedding_dim=256),
    #         "NodePiece": dict(num_anchors=500),
    #     },
    # },
}

OUTPUT_DIR = Path("results_all")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def build_model_kwargs(model_name: str, overrides: dict) -> dict:
    """FIX 1: NodePiece now uses selection_kwargs=dict(num_anchors=N)"""
    if model_name == "NodePiece":
        return dict(
            model_kwargs=dict(
                tokenizers="AnchorTokenizer",
                tokenizers_kwargs=dict(
                    selection="Degree",
                    selection_kwargs=dict(           # ← FIXED
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
            optimizer_kwargs=dict(lr=0.001),         # FIX 3: ComplEx needs explicit lr
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


# ── Entry point ───────────────────────────────────────────────────────────────
# Note: Using PyKEEN's built-in dataset loaders (FB15k-237 and WN18RR)
# If you want to use FB15k and WN18, uncomment them above and run:
#   python kg_experiment_all.py --download

# ── Main loop ─────────────────────────────────────────────────────────────────

rows       = []
total_runs = len(MODELS) * len(DATASETS)
run_count  = 0

print_header("ALL DATASETS — Knowledge Graph Experiment")
print(f"  Datasets : {', '.join(DATASETS.keys())}")
print(f"  Models   : {', '.join(MODELS)}")
print(f"  Total    : {total_runs} runs\n")

for dataset_label, ds_info in DATASETS.items():
    leaky_tag = "⚠️  LEAKY" if ds_info["leaky"] else "✅ clean"
    print_header(f"Dataset: {dataset_label}  [{leaky_tag}]")
    print(f"  Note: {ds_info['note']}")

    for model_name in MODELS:
        run_count += 1
        print(f"\n  [{run_count}/{total_runs}]  {model_name} on {dataset_label} …")

        overrides    = ds_info["model_overrides"].get(model_name, {})
        model_kwargs = build_model_kwargs(model_name, overrides)
        needs_inverse = (model_name == "NodePiece")

        t_start = time.time()
        try:
            # FIX 2: local datasets loaded via TriplesFactory
            if ds_info["local_key"]:
                train, test, valid = load_local_dataset(
                    ds_info["local_key"], create_inverse=needs_inverse
                )
                result = pipeline(
                    model=model_name,
                    training=train,
                    testing=test,
                    validation=valid,
                    training_loop="sLCWA",
                    epochs=100,
                    stopper="early",
                    stopper_kwargs=dict(patience=5, metric="hits_at_10", larger_is_better=True),
                    device="cuda",
                    **model_kwargs,
                )
            else:
                dataset_kwargs = {"create_inverse_triples": True} if needs_inverse else {}
                result = pipeline(
                    model=model_name,
                    dataset=ds_info["pykeen_name"],
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
                "leaky"  : ds_info["leaky"],
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
                "leaky": ds_info["leaky"], "time_s": elapsed,
                "MRR": None, "Hits@1": None, "Hits@3": None,
                "Hits@10": None, "MR": None, "error": str(exc),
            })

# ── Summary ───────────────────────────────────────────────────────────────────

df = pd.DataFrame(rows)
print_header("FINAL RESULTS SUMMARY", width=70)
print("✅ = clean (trust these)   ⚠️  = leaky (inflated)\n")

for dataset_label in DATASETS:
    sub   = df[df["dataset"] == dataset_label]
    tag   = "⚠️  LEAKY" if DATASETS[dataset_label]["leaky"] else "✅ clean"
    print(f"\n  {dataset_label}  [{tag}]")
    cols  = [c for c in ["model","MRR","Hits@1","Hits@3","Hits@10","MR","time_s"] if c in sub.columns]
    print(sub[cols].to_string(index=False))

csv_path = OUTPUT_DIR / "all_results.csv"
df.to_csv(csv_path, index=False)
print(f"\n\n→ Full results saved to : {csv_path}")
print(f"→ Individual JSONs in   : {OUTPUT_DIR}/")