# KG Quality Metric

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Java 8+](https://img.shields.io/badge/java-8+-orange.svg)](https://www.oracle.com/java/technologies/javase-downloads.html)

A metric to evaluate Knowledge Graph triple extraction quality with negation awareness. Compares extracted triples against linguistic ground truth from source sentences.

## Features

- **Structural evaluation**: Node completeness, connectivity, graph components
- **Predicate assessment**: Verb similarity, multiplicity, polarity penalties  
- **Negation handling**: spaCy-based detection, polarity propagation, 4-tuple triples
- **Combined scoring**: `M = 0.5 * M_N + 0.5 * M_V` normalized to [0,1]

## Components

### 1. POS.py
Extracts noun phrases and sentence polarity using NLTK + spaCy dependency parsing.
```bash
python POS.py
# Outputs: output_pos_*.txt, output_polarity_*.txt
```

### 2. negation_detector.py
Detects negation dependencies and predicate polarities.
```python
from negation_detector import NegationDetector
detector = NegationDetector()
polarity = detector.extract_predicate_polarity("He doesn't run", "run")  # "negative"
```

### 3. Triple_Extractor.py
Filters triples, creates 4-tuples with polarity, uses Jaro-Winkler similarity (≥0.5).
```bash
python Triple_Extractor.py
# Outputs: Json/*.json (3-tuple), Json/*_with_polarity.json (4-tuple)
```

### 4. Main.java
Calculates quality metrics with polarity penalties (λ=0.1).
```bash
javac -cp ".;*.jar" Main.java
java -cp ".;*.jar" Main
# Outputs: output_*/ideal_*.txt, combined_metric.txt
```

## Setup

### Dependencies
```bash
pip install nltk spacy jellyfish
python -m spacy download en_core_web_sm
```

### Java JARs (place in root)
- json-simple-1.1.1.jar
- commons-text-1.10.0.jar  
- commons-lang3-3.12.0.jar

## Usage

```bash
# 1. Extract phrases and polarity
python POS.py

# 2. Process triples with polarity  
python Triple_Extractor.py

# 3. Generate polarity JSON
python generate_polarity_json.py

# 4. Calculate metrics
javac -cp ".;*.jar" Main.java && java -cp ".;*.jar" Main
```

## Input Files
- `sentences_*.txt` - Source sentences (one per line)
- `triple_*.txt` - Raw OIE extractions
- Generated: `Json_Ideal/`, `Json_Ideal_Polarity/`

## Output Structure
```
output_ideal_tinybutmighty/ideal_tinybutmighty.txt           # Noun metrics
output_predicate_ideal_tinybutmighty/ideal_tinybutmighty.txt # Verb metrics  
output_combined_ideal_tinybutmighty/combined_metric.txt      # Final scores
```

## Metrics

### Noun Metric (M_N)
```
d_N = (1 - nodes/total_nouns) + Σ(1 - similarity) + (components - 1)
M_N = d_N / (2 * noun_count)
```

### Verb Metric (M_V) with Polarity
```
d_V = similarity_penalties + missing_verbs + λ * polarity_mismatches  
M_V = d_V / (2 * verb_count)
```

### Combined Score
```
M = 0.5 * M_N + 0.5 * M_V
```

Lower scores = better quality (0 = perfect extraction)

## Testing
```bash
python test_negation_pipeline.py  # Test negation handling
python negation_detector.py       # Test specific patterns
```
```bash
# Step 1: Extract linguistic features
python POS.py

# Step 2: Process triples with polarity
python Triple_Extractor.py

# Step 3: Generate polarity-enhanced JSON
python generate_polarity_json.py

# Step 4: Calculate quality metrics
javac -cp ".;json-simple-1.1.1.jar;commons-text-1.10.0.jar;commons-lang3-3.12.0.jar" Main.java
java -cp ".;json-simple-1.1.1.jar;commons-text-1.10.0.jar;commons-lang3-3.12.0.jar" Main
```

## Output Files

### Generated Metrics
```
output_ideal_tinybutmighty/
├── ideal_tinybutmighty.txt          # Noun quality scores
output_predicate_ideal_tinybutmighty/
├── ideal_tinybutmighty.txt          # Predicate quality scores  
output_combined_ideal_tinybutmighty/
├── combined_metric.txt              # Unified quality scores
```

### Enhanced Data Files
```
Json_Ideal_Polarity/
├── tinybutmighty.json               # 4-tuple triples with polarity
├── benchie.json                     # Benchie dataset with polarity
output_polarity_ideal_benchie.txt    # Sentence polarity mapping
```

## Methodology

### Ideal Graph Construction
For each sentence, we construct an ideal reference graph *G_i* where:
- **Nodes**: Distinct noun phrases from dependency parsing
- **Edges**: Predicate-argument relations with multiplicity
- **Polarity**: Negation markers when expressed in the sentence
- **Connectivity**: Single connected component per sentence

### Quality Metrics

#### Noun Metric (M_N)
```
d_N(G_1,G_i) = (1 - V(G_1)/N(G_1)) + Σ(1 - τ_n_j) + (C(G_1) - 1)
M_N = d_N(G_1,G_i) / (2 * N(G_i))
```

#### Verb Metric with Polarity (M_V)
```
d_V(G_1,G_i) = (Vb(G_i) - Vb(G_1)) + Σ(1 - τ_v_j) + λ * polarity_penalty
M_V = d_V(G_1,G_i) / (2 * Vb(G_i))
```

#### Combined Quality Score
```
M = α * M_N + (1-α) * M_V    (α = 0.5 by default)
```

Where:
- **λ = 0.1**: Polarity penalty weight
- **τ**: Jaro-Winkler similarity scores
- **Lower scores = Better quality** (0 = perfect extraction)

## Testing & Validation

### Test Negation Detection
```bash
# Run comprehensive negation tests
python test_negation_pipeline.py

# Test specific negation patterns
python negation_detector.py
```

### Example Polarity Detection
```python
from negation_detector import NegationDetector

detector = NegationDetector()

# Positive sentence
detector.extract_predicate_polarity("The weather is sunny.", "is")
# Output: "positive"

# Negative sentence  
detector.extract_predicate_polarity("The weather is not sunny.", "is")
# Output: "negative"
```

## Use Cases

### 1. OIE System Evaluation
Compare multiple Open Information Extraction tools:
```bash
# Evaluate Stanford OpenIE vs ClausIE vs MiniE
python evaluate_multiple_systems.py
```

### 2. Negation Handling Assessment
Measure how well systems preserve negation:
```python
# Check polarity preservation accuracy
polarity_accuracy = correct_polarities / total_predicates
```

### 3. KG Construction Quality Control
Validate triple quality before KG integration:
```python
if quality_score < threshold:
    flag_for_manual_review()
```

## License

This project is licensed under the Apache License - see the [LICENSE](LICENSE) file for details.
