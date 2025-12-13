#!/usr/bin/env python3
"""
Quick Start Evaluation Script

Runs the complete evaluation pipeline:
1. Collects dataset
2. Evaluates models  
3. Generates report

Usage:
    python run_evaluation.py --quick
"""

import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd: list, description: str):
    """Run a command and handle errors."""
    print(f"🚀 {description}...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run complete evaluation pipeline")
    parser.add_argument("--quick", action="store_true", 
                       help="Quick evaluation (smaller dataset, skip LLM-only)")
    parser.add_argument("--phishing", type=int, default=50,
                       help="Number of phishing samples")
    parser.add_argument("--benign", type=int, default=50,
                       help="Number of benign samples")
    
    args = parser.parse_args()
    
    scripts_dir = Path(__file__).parent / "scripts"
    
    print("🎯 ATF CyberX - Accuracy Evaluation Pipeline")
    print("=" * 50)
    
    # Step 1: Collect dataset
    collect_cmd = [
        sys.executable, 
        str(scripts_dir / "collect_data.py"),
        "--phishing", str(args.phishing),
        "--benign", str(args.benign)
    ]
    
    if not run_command(collect_cmd, "Dataset Collection"):
        return 1
    
    # Step 2: Evaluate models
    eval_cmd = [
        sys.executable,
        str(scripts_dir / "evaluate_models.py")
    ]
    
    if args.quick:
        eval_cmd.append("--quick")
    
    if not run_command(eval_cmd, "Model Evaluation"):
        return 1
    
    # Step 3: Generate report
    report_cmd = [
        sys.executable,
        str(scripts_dir / "generate_report.py")
    ]
    
    if not run_command(report_cmd, "Report Generation"):
        return 1
    
    print("\\n🎉 Evaluation pipeline completed successfully!")
    print("📊 Check the results/ directory for:")
    print("   - evaluation_results.json (raw metrics)")
    print("   - evaluation_report.md (formatted report)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())