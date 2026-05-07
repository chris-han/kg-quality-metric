# IE Systems → Link Prediction Pipeline

## Overview

This pipeline correlates **KGCQual extraction quality scores** with **link prediction performance metrics** (MRR, Hits@10) across different IE (Information Extraction) systems.

### Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. LOAD DATASETS                                                     │
│    ├─ WebNLG (sentences_webnlg.txt)                                 │
│    ├─ BenchIE (sentences_benchie.txt)                               │
│    └─ TinyButMighty (sentences_tinybutMighty.txt)                   │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. LOAD EXTRACTED TRIPLES FROM IE SYSTEMS                           │
│    ├─ MinIE, OllIE, ClausIE                                         │
│    ├─ Stanford OpenIE (v4.5.3 & v4.5.6)                            │
│    ├─ GPT-4, Claude, Gemini (LLM-based extraction)                 │
│    └─ [Each system has ~100K+ triples per dataset]                 │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. CREATE TRAIN/TEST/VALID SPLITS (70/15/15)                       │
│    └─ Format: entity\trelation\tobject (tab-separated)             │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. TRAIN EMBEDDING MODELS ON EACH KG                               │
│    ├─ TuckER       (200-dim embedding)                              │
│    ├─ ComplEx      (128-dim embedding)                              │
│    └─ NodePiece    (250 anchors)                                    │
│    └─ Epochs: 50, Early stopping on Hits@10                         │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 5. RECORD LINK PREDICTION METRICS                                   │
│    ├─ MRR (Mean Reciprocal Rank)                                    │
│    ├─ Hits@10                                                        │
│    ├─ Hits@1, Hits@3, Mean Rank                                     │
│    └─ Training time                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 6. CORRELATE WITH KGCQual SCORES                                    │
│    ├─ Load quality scores from final_output_scores/                 │
│    ├─ Compute Pearson & Spearman correlation                        │
│    ├─ Verify: Lower KGCQual → Higher MRR?                          │
│    └─ Generate summary tables and statistics                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Expected Results

### Hypothesis
If **KGCQual is a good quality metric**, we should observe:
- **Negative correlation** between KGCQual (lower = better) and performance metrics
- IE systems with lower quality scores should have lower MRR/Hits@10
- Correlation should be statistically significant (p < 0.05)

### Example Output

```
IE Systems Summary (ranked by quality):

  IE System        | KGCQual | MRR Mean | Hits@10 Mean | Status
  ────────────────────────────────────────────────────────────
  ClausIE          | 0.124   | 0.456    | 0.678        | ✅ High quality
  MinIE            | 0.156   | 0.421    | 0.634        | ✅ Good quality
  Stanford 4.5.6   | 0.189   | 0.398    | 0.601        | ⚠️  Moderate
  OllIE            | 0.245   | 0.312    | 0.512        | ⚠️  Lower quality
  
Correlation Analysis:
  MRR vs KGCQual:     r = -0.682, p = 0.012 ✅ SIGNIFICANT NEGATIVE
  Hits@10 vs KGCQual: r = -0.631, p = 0.028 ✅ SIGNIFICANT NEGATIVE
```

## Quick Start

### 1. Prerequisites

Ensure you have the required packages (from `requirements.txt`):

```bash
pip install pykeen torch pandas scipy numpy
```

For CUDA support (recommended):
```bash
pip install torch torchvision torchaudio -f https://download.pytorch.org/whl/torch_stable.html
```

### 2. Run the Pipeline

```bash
cd ie_evaluation/

# Step 1: Train models and collect metrics
python pipeline_ie_systems.py

# Step 2: Correlate with quality scores
python analyze_correlation.py
```

### 3. Check Results

```bash
# Main results
cat ie_system_results/ie_system_results.csv

# With quality scores merged
cat ie_system_results/ie_system_results_with_quality.csv

# Correlation statistics
cat ie_system_results/correlations.json

# Summary table
cat ie_system_results/ie_system_summary.csv
```

## Input Files

### Sentence Files
- `../sentences_webnlg.txt` - WebNLG dataset sentences
- `../sentences_benchie.txt` - BenchIE dataset sentences
- `../sentences_tinybutMighty.txt` - TinyButMighty dataset sentences

### Triple Files (by IE System)
Located in `../Json/`, `../Json_benchie/`, `../Json_tinybutmighty/`:

```
triple_clauseie.json                    # ClausIE extractions
triple_minie.json                       # MinIE extractions
triple_ollie.json                       # OllIE extractions
stanford_4.5.3_openie.json             # Stanford OpenIE v4.5.3
stanford_4.5.6_openie.json             # Stanford OpenIE v4.5.6
claude3.7sonnet.json                   # Claude 3.7 Sonnet
gemini2.5pro.json                       # Gemini 2.5 Pro
GPT-4o-mini.json                        # GPT-4o Mini
```

### Quality Score Files
Located in `../final_output_scores/`:

```
final_score_clausie.txt                 # ClausIE KGCQual
final_score_minie.txt                   # MinIE KGCQual
final_score_ollie.txt                   # OllIE KGCQual
final_score_stanford_4.5.3_openie.txt   # Stanford 4.5.3 KGCQual
final_score_stanford_4.5.6_openie.txt   # Stanford 4.5.6 KGCQual
```

## Output Files

All results saved in `ie_evaluation/ie_system_results/`:

| File | Description |
|------|-------------|
| `ie_system_results.csv` | Full results: dataset, IE system, model, metrics |
| `ie_system_results_with_quality.csv` | Results merged with KGCQual scores |
| `ie_system_summary.csv` | Summary statistics by IE system |
| `correlations.json` | Correlation coefficients & p-values |
| `temp_*/*.txt` | Temporary train/test/valid splits (can be deleted) |

## Configuration

Edit the script to customize:

```python
# pipeline_ie_systems.py

MODELS = ["TuckER", "ComplEx", "NodePiece"]  # Embedding models to test

# Model hyperparameters
embedding_dim = 200  # Adjust per model
epochs = 50  # Fewer epochs = faster, more = better results
device = "cuda"  # "cuda" or "cpu"
```

## Troubleshooting

### Problem: "Module pykeen not found"
```bash
pip install pykeen
```

### Problem: CUDA out of memory
Reduce `embedding_dim` or `epochs` in the script, or use CPU:
```python
device="cpu"  # in pipeline_ie_systems.py
```

### Problem: "Quality score file not found"
Make sure `final_output_scores/` directory exists with quality score files. 
If not, generate them:
```bash
cd ..
javac -cp ".;*.jar" Main.java
java -cp ".;*.jar" Main
```

### Problem: Correlation p-value shows NaN
Need at least 3 samples with both quality scores and link prediction metrics.
Verify that quality score files are properly formatted and readable.

## Performance Notes

### Typical Runtime
- **Per IE system × Model**: 2-5 minutes (depending on triple count, GPU)
- **All systems (5) × All models (3) × All datasets (3)**: ~2-4 hours
- **Correlation analysis**: < 1 minute

### Storage Requirements
- Temporary triple files: ~500MB
- Results CSV: ~10MB
- Total: ~1GB

## Paper Integration

### Figures to Generate
This pipeline produces data for:

1. **Table: IE System Comparison**
   - KGCQual scores vs link prediction metrics
   - Shows correlation between extraction quality and KG utility

2. **Scatter Plot: KGCQual vs MRR/Hits@10**
   - Each point = (quality score, performance metric)
   - Shows correlation strength visually

3. **Ranking Table: IE Systems by Quality**
   - Ordered by KGCQual score
   - Shows performance ranking alignment

### Statistical Support
Provides:
- Pearson/Spearman correlation coefficients
- P-values for significance testing
- Confidence intervals (optional, can be added)

## Citation

If you use this pipeline in your research:

```bibtex
@misc{kg_quality_pipeline,
  title={IE Systems to Link Prediction Correlation Pipeline},
  year={2024},
  note={Part of KG Quality Metric evaluation framework}
}
```

## Support

For issues or questions, check:
1. Input file paths (all must exist)
2. Quality score file formatting
3. GPU memory availability
4. Python version (requires 3.8+)

