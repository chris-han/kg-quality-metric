# kg-quality-metric

A metric used to evaluate the quality of Knowledge Graph triples extracted from text.

**Added negation handling with polarity flag and polarity-aware evaluation metric.**

## Overview

This project evaluates the quality of Knowledge Graph (KG) triples extracted from text using various Open Information Extraction (OIE) tools. The system now includes advanced negation handling and polarity-aware evaluation metrics.

## Features

### Core Functionality
- **Triple Quality Evaluation**: Measures how well OIE tools extract meaningful triples from text
- **Multi-tool Comparison**: Supports ClausIE, Stanford OpenIE, MiniE, and other OIE tools
- **Graph-based Analysis**: Constructs knowledge graphs and evaluates connectivity metrics

### Advanced Negation Handling (NEW)
- **Dependency Parsing**: Uses spaCy to detect negation words and patterns
- **Polarity Detection**: Identifies positive/negative polarity in predicates
- **4-tuple Structure**: Extended triples from `(subject, predicate, object)` → `(subject, predicate, object, polarity)`
- **Polarity-aware Metrics**: Includes polarity penalty in evaluation scoring

## Architecture

### Python Components

#### 1. POS.py - Enhanced Noun Phrase & Polarity Extraction
- Extracts noun phrases, adjectives, and cardinal numbers using NLTK
- **NEW**: Detects sentence polarity using spaCy dependency parsing
- Outputs both phrase lists and polarity information
- Generates `output_pos_*.txt` and `output_polarity_*.txt` files

#### 2. negation_detector.py - Negation Detection Engine
- **NEW**: Dedicated module for negation detection
- Uses spaCy dependency parsing to identify `neg` dependencies
- Detects negation words: "not", "never", "no", "neither", "nor", etc.
- Provides predicate-level polarity analysis

#### 3. Triple_Extractor.py - Enhanced Triple Processing
- Filters OIE triples based on extracted noun phrases
- **NEW**: Creates 4-tuple triples with polarity information
- Uses Jaro-Winkler similarity for fuzzy string matching
- **NEW**: Generates both 3-tuple (backward compatible) and 4-tuple JSON files

#### 4. Main.java - Polarity-aware Quality Metrics
- Constructs knowledge graphs from filtered triples
- **NEW**: Enhanced verb metrics with polarity penalty calculation
- **NEW**: Implements polarity mismatch penalty: `dV(G1, Gi) += λ * penalty`
- Maintains normalized scores within [0, 1] range

## Installation & Setup

### Prerequisites
```bash
# Python dependencies
pip install nltk spacy jellyfish

# spaCy English model
python -m spacy download en_core_web_sm

# Java dependencies (place in root directory)
# - json-simple-1.1.1.jar
# - commons-text-1.10.0.jar
# - commons-lang3-3.12.0.jar
```

### Required Input Files
1. **Sentence files**: `sentences_*.txt` (one sentence per line)
2. **OIE triple files**: `triple_clauseie.txt`, `triple_minie.txt`, etc.
3. **JSON tools folder**: `Json/` (for processed outputs)

## Usage

### Step 1: Extract Phrases and Polarity
```bash
python POS.py
```
**Outputs**:
- `output_pos_*.txt`: Extracted noun phrases
- `output_polarity_*.txt`: Sentence polarity information

### Step 2: Extract and Filter Triples with Polarity
```bash
python Triple_Extractor.py
```
**Outputs**:
- `Json/*_with_polarity.json`: 4-tuple triples with polarity
- `Json/*.json`: Traditional 3-tuple triples (backward compatible)

### Step 3: Calculate Quality Metrics
```bash
# Compile Java code
javac -cp ".;json-simple-1.1.1.jar;commons-text-1.10.0.jar;commons-lang3-3.12.0.jar" Main.java

# Run evaluation
java -cp ".;json-simple-1.1.1.jar;commons-text-1.10.0.jar;commons-lang3-3.12.0.jar" Main
```

### Testing Negation Handling
```bash
# Test the negation pipeline
python test_negation_pipeline.py

# Test with sample sentences
python negation_detector.py
```

## Negation Handling Examples

### Polarity Detection
```python
# Positive sentence
"The weather is sunny." → polarity: "positive"

# Negative sentence  
"The weather is not sunny." → polarity: "negative"
```

### 4-tuple Triple Structure
```json
{
  "1": [["weather", "is", "sunny", "positive"]],
  "2": [["weather", "is", "sunny", "negative"]]
}
```

### Polarity Penalty Calculation
```
If extracted_polarity ≠ ideal_polarity:
    penalty = λ (default: 0.1)
    
dV(G1, Gi) = base_similarity_score + polarity_penalty
```

## File Structure
```
kg-quality-metric/
├── POS.py                          # Enhanced phrase & polarity extraction
├── negation_detector.py            # NEW: Negation detection engine
├── Triple_Extractor.py              # Enhanced triple processing
├── Main.java                        # Polarity-aware metrics
├── test_negation_pipeline.py        # NEW: Testing framework
├── test_sentences_negation.txt      # NEW: Test sentences
├── sentences_*.txt                  # Input sentences
├── triple_*.txt                     # Raw OIE triples
├── output_pos_*.txt                 # Extracted phrases
├── output_polarity_*.txt            # NEW: Polarity information
└── Json/
    ├── *_with_polarity.json         # NEW: 4-tuple triples
    └── *.json                       # Traditional 3-tuple triples
```

## Evaluation Metrics

### Base Metrics
1. **Graph Connectivity**: Node count and connected components
2. **Semantic Similarity**: Jaro-Winkler similarity between entities
3. **Coverage**: How well noun phrases are represented in triples