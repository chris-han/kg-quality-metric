"""
Setup Validator: Check all prerequisites for the IE systems pipeline
=====================================================================

Validates that all required files exist and are readable before running the pipeline.
"""

import sys
from pathlib import Path
from typing import List, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(__file__).parent.parent
QUALITY_SCORE_DIR = WORKSPACE_ROOT / "final_output_scores"

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

QUALITY_SCORE_FILES = {
    "clauseie": QUALITY_SCORE_DIR / "final_score_clausie.txt",
    "minie": QUALITY_SCORE_DIR / "final_score_minie.txt",
    "ollie": QUALITY_SCORE_DIR / "final_score_ollie.txt",
    "stanford_4.5.3": QUALITY_SCORE_DIR / "final_score_stanford_4.5.3_openie.txt",
    "stanford_4.5.6": QUALITY_SCORE_DIR / "final_score_stanford_4.5.6_openie.txt",
}

# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def check_python_packages() -> Tuple[bool, List[str]]:
    """Check if required Python packages are installed."""
    required = ["pykeen", "torch", "pandas", "scipy", "numpy"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return len(missing) == 0, missing


def check_file_exists(file_path: Path) -> bool:
    """Check if file exists and is readable."""
    return file_path.exists() and file_path.is_file()


def check_file_readable(file_path: Path) -> bool:
    """Check if file is readable."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            _ = f.read(1)
        return True
    except:
        return False


def check_file_has_content(file_path: Path, min_size_bytes: int = 10) -> bool:
    """Check if file has meaningful content."""
    try:
        return file_path.stat().st_size >= min_size_bytes
    except:
        return False


def count_lines(file_path: Path) -> int:
    """Count lines in file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except:
        return 0


def validate_json_file(file_path: Path) -> bool:
    """Check if file is valid JSON."""
    try:
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# MAIN VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*80)
    print("  IE SYSTEMS PIPELINE — SETUP VALIDATOR")
    print("="*80)
    
    issues = []
    warnings = []
    
    # 1. Check Python packages
    print("\n📦 Checking Python Packages:")
    ok, missing = check_python_packages()
    if ok:
        print("   ✅ All packages installed")
    else:
        msg = f"Missing packages: {', '.join(missing)}"
        print(f"   ❌ {msg}")
        print(f"      Fix: pip install {' '.join(missing)}")
        issues.append(msg)
    
    # 2. Check CUDA availability
    print("\n🎮 Checking GPU Support:")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"   ✅ CUDA available ({torch.cuda.get_device_name(0)})")
        else:
            print("   ⚠️  CUDA not available (will use CPU - slower)")
            warnings.append("CUDA not available - training will be slower")
    except:
        print("   ⚠️  Could not check CUDA")
        warnings.append("PyTorch not fully installed")
    
    # 3. Check workspace root
    print("\n📁 Checking Workspace Root:")
    if WORKSPACE_ROOT.exists():
        print(f"   ✅ Found: {WORKSPACE_ROOT}")
    else:
        msg = f"Workspace root not found: {WORKSPACE_ROOT}"
        print(f"   ❌ {msg}")
        issues.append(msg)
        return False  # Can't continue
    
    # 4. Check quality score directory
    print("\n📊 Checking Quality Score Directory:")
    if QUALITY_SCORE_DIR.exists():
        print(f"   ✅ Found: {QUALITY_SCORE_DIR}")
    else:
        print(f"   ⚠️  Not found: {QUALITY_SCORE_DIR}")
        warnings.append("Quality score directory not found - correlation analysis will be limited")
    
    # 5. Check sentence files
    print("\n📄 Checking Sentence Files:")
    sentence_count = 0
    for dataset_name, dataset_info in DATASETS.items():
        sentence_file = dataset_info["sentences_file"]
        if check_file_exists(sentence_file):
            lines = count_lines(sentence_file)
            sentence_count += lines
            status = "✅" if lines > 0 else "❌ Empty"
            print(f"   {status} {dataset_name}: {lines:,} sentences")
        else:
            msg = f"{dataset_name} sentences file not found: {sentence_file}"
            print(f"   ❌ {msg}")
            issues.append(msg)
    
    # 6. Check triple files
    print("\n🔗 Checking Triple Files:")
    triple_files_ok = 0
    triple_files_total = 0
    
    for dataset_name, dataset_info in DATASETS.items():
        print(f"\n   {dataset_name}:")
        for ie_name, triple_file in dataset_info["ie_systems"].items():
            triple_files_total += 1
            
            if not check_file_exists(triple_file):
                print(f"      ❌ {ie_name}: NOT FOUND")
            elif not check_file_readable(triple_file):
                print(f"      ❌ {ie_name}: NOT READABLE")
            elif not validate_json_file(triple_file):
                print(f"      ⚠️  {ie_name}: INVALID JSON (corrupt?)")
            elif not check_file_has_content(triple_file):
                print(f"      ⚠️  {ie_name}: EMPTY")
            else:
                triple_files_ok += 1
                print(f"      ✅ {ie_name}")
    
    print(f"\n   Summary: {triple_files_ok}/{triple_files_total} triple files OK")
    if triple_files_ok < triple_files_total:
        warnings.append(f"Only {triple_files_ok}/{triple_files_total} triple files are valid")
    
    # 7. Check quality score files
    print("\n📈 Checking Quality Score Files:")
    quality_files_ok = 0
    quality_files_total = len(QUALITY_SCORE_FILES)
    
    for ie_name, score_file in QUALITY_SCORE_FILES.items():
        if check_file_exists(score_file) and check_file_readable(score_file):
            quality_files_ok += 1
            print(f"   ✅ {ie_name}")
        else:
            print(f"   ⚠️  {ie_name}: NOT FOUND")
    
    print(f"\n   Summary: {quality_files_ok}/{quality_files_total} quality score files available")
    if quality_files_ok == 0:
        warnings.append("No quality score files found - run: javac Main.java && java Main")
    
    # 8. Summary
    print("\n" + "="*80)
    print("  SUMMARY")
    print("="*80)
    
    print(f"\n✅ Ready: {triple_files_ok} IE systems × {len(DATASETS)} datasets")
    print(f"   Total data: {sentence_count:,} sentences")
    
    if issues:
        print(f"\n❌ BLOCKING ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"   • {issue}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   • {warning}")
    
    # Readiness
    if not issues:
        print("\n" + "="*80)
        print("  ✅ SYSTEM IS READY — You can run:")
        print("="*80)
        print("\n   python pipeline_ie_systems.py")
        print("   python analyze_correlation.py")
        return True
    else:
        print("\n" + "="*80)
        print("  ❌ SYSTEM NOT READY — Fix blocking issues above")
        print("="*80)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
