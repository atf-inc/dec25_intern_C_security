# ATF CyberX - Accuracy Evaluation Framework

This directory contains the accuracy evaluation system for our hybrid AI phishing detection pipeline.

## Overview

Evaluates the performance of our 3-stage hybrid system:
1. **Heuristics** (free, fast)
2. **Embeddings** (low cost)  
3. **Gemini LLM** (high cost, high accuracy)

## Structure

```
evaluation/
├── datasets/           # Email datasets for testing
├── scripts/           # Evaluation scripts
├── results/           # Generated metrics and reports
└── README.md         # This file
```

## Metrics Measured

### Primary Metrics
- **Precision**: How many flagged emails are truly phishing
- **Recall**: How many phishing emails we actually catch
- **F1 Score**: Balance of precision & recall
- **ROC-AUC**: Overall separability

### Cost Metrics
- **Cost per 1000 emails**
- **LLM call reduction percentage**
- **Average processing latency**

## Usage

1. **Collect Dataset**: `python scripts/collect_data.py`
2. **Run Evaluation**: `python scripts/evaluate_models.py`
3. **Generate Report**: `python scripts/generate_report.py`

## Target Goals (from Technical Document)

| Method | Precision | Recall | F1 | Notes |
|--------|-----------|--------|----|----|
| Heuristics only | 0.55 | 0.50 | 0.52 | weak but cheap |
| Embedding Model | 0.72 | 0.74 | 0.73 | good for classic phishing |
| LLM Prompt Only | 0.80 | 0.86 | 0.83 | best accuracy + explanations |
| **Hybrid (final)** | **0.78** | **0.84** | **0.81** | **best trade-off** |

Expected cost reduction: **~75%** (250 LLM calls vs 1000 per 1000 emails)