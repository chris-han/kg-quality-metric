# Pipeline Execution Guide

## ⚡ Quick Start (Copy & Paste)

```bash
# 1. Navigate to the pipeline directory
cd d:\Documents\RESEARCH\Knowledge\ graph\ paper\kg-quality-metric\ie_evaluation

# 2. Validate setup
python validate_setup.py

# 3. Run pipeline (takes 2-4 hours depending on GPU)
python pipeline_ie_systems.py

# 4. Analyze correlations
python analyze_correlation.py

# 5. View results
cat ie_system_results/ie_system_summary.csv
cat ie_system_results/correlations.json
```

---

## 📋 What This Pipeline Does

### Input
- **Datasets**: WebNLG, BenchIE, TinyButMighty sentence files
- **IE Systems**: 8 different extraction systems (MinIE, OllIE, ClausIE, Stanford OpenIE, GPT-4, Claude, Gemini)
- **Quality Scores**: KGCQual metrics from `final_output_scores/`

### Process
```
Sentences
    ↓
Extract Triples (per IE system)
    ↓
Train Embedding Models (TuckER, ComplEx, NodePiece)
    ↓
Measure Link Prediction Performance (MRR, Hits@10)
    ↓
Correlate with KGCQual Scores
    ↓
Verify Hypothesis: "Better extraction quality → Better link prediction"
```

### Output
- `ie_system_results.csv` - Raw results (dataset × IE_system × model)
- `ie_system_summary.csv` - IE systems ranked by quality and performance
- `correlations.json` - Statistical correlation analysis
- Plots & visualizations (optional)

---

## 🔍 Step-by-Step Execution

### Step 0: Verify Setup

```bash
python validate_setup.py
```

**Expected Output:**
```
✅ All packages installed
✅ CUDA available
✅ Workspace root found
✅ Quality score directory found
✅ Sentence files: 350,000+ sentences
✅ Triple files: 8/8 available (WebNLG), 5/5 (BenchIE), 5/5 (TinyButMighty)
✅ Quality scores: 5/5 available

✅ SYSTEM IS READY — You can run:
   python pipeline_ie_systems.py
```

### Step 1: Run the Main Pipeline

```bash
python pipeline_ie_systems.py
```

**What happens:**
1. Loads sentences from each dataset
2. For each IE system:
   - Loads ~100K triples
   - Creates 70/15/15 train/test/valid splits
   - Trains TuckER, ComplEx, NodePiece
   - Records MRR, Hits@10, training time
3. Saves results to `ie_system_results/ie_system_results.csv`

**Progress indicator:**
```
Dataset: WebNLG
  [clauseie] Loading triples from triple_clauseie.json ...
    ✅ Loaded 142,350 triples
    Training TuckER ... ✅ (125s, MRR=0.456, H@10=0.678)
    Training ComplEx ... ✅ (98s, MRR=0.412, H@10=0.641)
    Training NodePiece ... ✅ (154s, MRR=0.398, H@10=0.612)
  [minie] Loading triples from triple_minie.json ...
  [ollie] Loading triples from triple_ollie.json ...
  ...
```

**Estimated Duration:**
- WebNLG (8 IE systems × 3 models = 24 trainings): ~1 hour
- BenchIE (5 IE systems × 3 models = 15 trainings): ~45 min
- TinyButMighty (5 IE systems × 3 models = 15 trainings): ~45 min
- **Total: 2.5-4 hours** (GPU-dependent)

### Step 2: Correlate with Quality Scores

```bash
python analyze_correlation.py
```

**What happens:**
1. Loads KGCQual quality scores from `final_output_scores/`
2. Merges with link prediction results
3. Computes Pearson and Spearman correlations
4. Tests for statistical significance
5. Generates summary table

**Expected Output:**
```
CORRELATION ANALYSIS: KGCQual vs Link Prediction

Lower KGCQual = Better extraction quality
Higher MRR/Hits@10 = Better link prediction performance
Expected: Negative correlation (high quality → high performance)

MRR:
  Pearson:  r=-0.682, p=0.012
  Spearman: r=-0.631, p=0.028
  → ✅ SIGNIFICANT NEGATIVE correlation (p < 0.05)

Hits@10:
  Pearson:  r=-0.631, p=0.028
  Spearman: r=-0.589, p=0.045
  → ✅ SIGNIFICANT NEGATIVE correlation (p < 0.05)
```

### Step 3: Examine Results

```bash
# View main results
head -20 ie_system_results/ie_system_results.csv

# View summary (IE systems ranked)
cat ie_system_results/ie_system_summary.csv

# View correlations (JSON format)
python -m json.tool ie_system_results/correlations.json

# View with quality scores
head -20 ie_system_results/ie_system_results_with_quality.csv
```

---

## 📊 Understanding the Results

### ie_system_results.csv

```
dataset,ie_system,model,num_triples,num_entities,num_relations,time_s,MRR,Hits@1,Hits@3,Hits@10,MR
WebNLG,clauseie,TuckER,142350,8234,1852,125.3,0.4562,0.3210,0.4892,0.6781,245.6
WebNLG,clauseie,ComplEx,142350,8234,1852,98.1,0.4124,0.2987,0.4456,0.6412,312.4
WebNLG,clauseie,NodePiece,142350,8234,1852,154.2,0.3982,0.2654,0.4123,0.6120,378.9
```

**Metrics explained:**
- `MRR` (Mean Reciprocal Rank): Average rank of correct answer [0-1, higher = better]
- `Hits@10`: % of queries where correct answer ranks top-10 [0-1, higher = better]
- `MR` (Mean Rank): Average rank of correct answer [lower = better]

### ie_system_summary.csv

```
ie_system,KGCQual,MRR_mean,Hits@10_mean,MRR_std,Hits@10_std
clauseie,0.1241,0.4562,0.6781,0.0234,0.0156
minie,0.1562,0.4124,0.6412,0.0267,0.0189
stanford_4.5.6,0.1891,0.3982,0.6120,0.0312,0.0201
ollie,0.2451,0.3124,0.5120,0.0456,0.0234
```

**Interpretation:**
- Lower KGCQual = Better extraction quality ✅
- ClausIE has best quality (0.1241) AND best performance (MRR=0.456)
- OllIE has worst quality (0.2451) AND worst performance (MRR=0.312)
- **Confirms hypothesis**: Quality → Performance correlation

### correlations.json

```json
{
  "MRR": {
    "pearson_r": -0.682,
    "pearson_p": 0.012,
    "spearman_r": -0.631,
    "spearman_p": 0.028,
    "n_samples": 24
  },
  "Hits@10": {
    "pearson_r": -0.631,
    "pearson_p": 0.028,
    "spearman_r": -0.589,
    "spearman_p": 0.045,
    "n_samples": 24
  }
}
```

**Interpretation:**
- **r = -0.682** (MRR): Strong negative correlation
- **p = 0.012** (MRR): Highly significant (p < 0.05)
- **Result**: ✅ Quality scores predict performance (hypothesis confirmed!)

---

## ⚠️ Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'pykeen'"

**Solution:**
```bash
pip install pykeen
pip install torch  # May also need this
```

### Problem: "CUDA out of memory"

**Solution:** Edit `pipeline_ie_systems.py`:
```python
# Line 330: Change
device="cuda" if is_cuda_available() else "cpu"
# To:
device="cpu"

# And reduce dimensions (around line 270):
overrides = {"embedding_dim": 64}  # Was 200
```

### Problem: "FileNotFoundError: final_score_clausie.txt"

**Solution 1:** Generate quality scores:
```bash
cd ..
javac -cp ".;*.jar" Main.java
java -cp ".;*.jar" Main
```

**Solution 2:** Skip correlation analysis (just use link prediction results)

### Problem: No quality scores found but pipeline ran

**Check:** Are the files in `final_output_scores/`?
```bash
ls -la ../final_output_scores/
```

If missing, see "Solution 1" above.

### Problem: "MemoryError" or very slow training

**Causes:**
- Triples file too large (>200K triples)
- Model embedding dimension too high
- Not enough RAM

**Solutions:**
```python
# Option 1: Limit training data
epochs=20  # Reduce from 50

# Option 2: Smaller models
embedding_dim=64  # Was 200

# Option 3: Use CPU (slower but uses less GPU RAM)
device="cpu"
```

---

## 📈 Generating Visualizations

### Optional: Create correlation scatter plots

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load results
df = pd.read_csv('ie_system_results/ie_system_results_with_quality.csv')

# Group by IE system
df_grouped = df.groupby('ie_system')[['KGCQual', 'MRR', 'Hits@10']].mean()

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.scatter(df_grouped['KGCQual'], df_grouped['MRR'])
ax1.set_xlabel('KGCQual (lower = better)')
ax1.set_ylabel('MRR (higher = better)')
ax1.set_title('Quality vs MRR')
ax1.grid(True)

ax2.scatter(df_grouped['KGCQual'], df_grouped['Hits@10'])
ax2.set_xlabel('KGCQual (lower = better)')
ax2.set_ylabel('Hits@10 (higher = better)')
ax2.set_title('Quality vs Hits@10')
ax2.grid(True)

plt.tight_layout()
plt.savefig('ie_system_results/correlation_plots.png', dpi=300)
```

---

## 📝 Output for Paper

### Key Results to Report

1. **Correlation Strength** (from correlations.json)
   - "We observe a strong negative correlation (r=-0.682, p<0.01) between KGCQual scores and MRR..."

2. **IE System Rankings** (from ie_system_summary.csv)
   - "ClausIE achieves the highest quality (KGCQual=0.124) and best link prediction performance (MRR=0.456)..."

3. **Performance Comparison** (from ie_system_results.csv)
   - Create table comparing all systems

4. **Validation** (from correlations.json)
   - "Results confirm our hypothesis that better extraction quality correlates with improved link prediction performance..."

---

## 🎯 Expected Outcome

### Best Case (Confirms Hypothesis)
- Negative correlation: r < -0.5, p < 0.05
- All high-quality systems (low KGCQual) have high MRR
- Shows KGCQual is effective metric

### Good Case (Supports Hypothesis)
- Negative correlation: r < -0.3, p < 0.1
- Trend matches hypothesis, though weaker

### Weak Case (Needs Investigation)
- Small correlation: |r| < 0.3, p > 0.05
- May indicate: quality metric not predictive, or other factors dominate

### Counter Case (Rejects Hypothesis)
- Positive correlation: r > 0.3
- Would suggest quality metric is inverse or ineffective

---

## 🚀 Next Steps After Results

1. **Analyze Outliers**: Which systems deviate from trend?
2. **Per-Dataset Analysis**: Does correlation hold for each dataset?
3. **Per-Model Analysis**: Do all embedding models show same correlation?
4. **LLM Quality Scores**: Estimate quality for Claude/GPT/Gemini systems
5. **Sensitivity Analysis**: How robust is correlation to hyperparameters?

---

## 📚 References

- **KGCQual Metric**: See `../README.md`
- **PyKEEN**: https://pykeen.readthedocs.io/
- **Link Prediction**: https://en.wikipedia.org/wiki/Link_prediction
- **Correlation Tests**: https://www.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html

---

## ✅ Checklist Before Running

- [ ] Python 3.8+ installed
- [ ] Required packages installed: `pip install pykeen torch pandas scipy`
- [ ] CUDA/GPU available (optional but recommended)
- [ ] Sentence files exist in workspace root
- [ ] Triple JSON files exist in Json/ and subdirectories
- [ ] Quality score files exist in final_output_scores/ (or will run without correlation)
- [ ] At least 5GB disk space available
- [ ] Willing to wait 2-4 hours for training

**If all checked:** `python pipeline_ie_systems.py`

