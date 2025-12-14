# Deepfake Voice Detection MVP

**Team**: ATF Inc - Security Intern Team (December 2025)  
**Project**: Multi-Modal Fusion Deepfake Voice Detection System  
**Status**: MVP Complete ✅

---

## 🎯 Project Overview

This is a **CPU-friendly, explainable deepfake voice detection system** using a multi-expert fusion architecture:
- **WavLM-Base-Plus**: Acoustic feature extraction (768-dim)
- **Whisper-Small**: Semantic/prosody feature extraction (768-dim)  
- **DSP Features**: Signal processing features (6-dim)
- **Fusion Classifier**: Lightweight MLP (~429K parameters)

**Key Features**: Multi-modal fusion, interpretable results, CPU-friendly inference

---

## 🏗️ Architecture

```
Audio Input (.wav)
    ↓
┌───────────┬────────────┬──────────┐
│   WavLM   │  Whisper   │   DSP    │
│  (768-d)  │  (768-d)   │   (6-d)  │
│  Frozen   │   Frozen   │  Rules   │
└─────┬─────┴──────┬─────┴────┬─────┘
      │            │          │
      └────────────┼──────────┘
                   │
            Concatenate (1542-d)
                   │
                   ▼
         ┌─────────────────┐
         │  Fusion MLP     │
         │  (Trainable)    │
         │  3 Layers       │
         └────────┬────────┘
                  │
                  ▼
         Binary Output
         (Real vs Fake)
```

---

## 📁 Project Structure

```
ml_pipeline_deepfake/
├── checkpoints/           # Trained model checkpoints
│   └── fusion_model.pth      # Pre-trained fusion model
│
├── features/              # Feature extraction modules
│   ├── wavlm_extractor.py    # WavLM acoustic features
│   ├── whisper_extractor.py  # Whisper semantic features
│   ├── dsp_features.py       # DSP signal features
│   └── __init__.py
│
├── models/                # Model architecture
│   ├── fusion_model.py       # Fusion classifier
│   └── __init__.py
│
├── training/              # Training pipeline
│   ├── train.py              # Training script
│   └── __init__.py
│
├── validation/            # Evaluation & testing
│   ├── eval.py               # Comprehensive evaluation
│   └── __init__.py
│
├── scripts/               # Utility scripts
│   ├── data_preparation/     # Data prep scripts
│   └── data_conversion/      # Audio conversion tools
│
├── docs/                  # Documentation
│   ├── TECHNICAL_SUMMARY.md
│   ├── PRIORITY1_RESULTS.md
│   └── ...
│
├── data/                  # Training/test data
│   ├── real/                 # Real voice samples
│   └── fake/                 # Fake voice samples
│
├── inference.py           # 🎯 Simple inference script (START HERE!)
├── run_training.py        # Training entry point
├── test_extractors.py     # Test feature extractors
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to project directory
cd ml_pipeline_deepfake

# Install dependencies
pip install -r requirements.txt
```

**Requirements:**
- Python 3.8+
- PyTorch 2.0+
- Transformers 4.30+
- librosa, scikit-learn, numpy

---

### 2. 🎯 Run Inference (Using Pre-trained Model)

The easiest way to get started is using the pre-trained checkpoint:

```bash
# Single file prediction
python inference.py --audio data/real/DF_E_2000053.wav

# Batch prediction on a directory
python inference.py --audio_dir data/real/ --limit 5

# Use custom checkpoint
python inference.py --audio test.wav --checkpoint checkpoints/my_model.pth
```

**Example Output:**
```
============================================================
RESULTS
============================================================

🎯 PREDICTION: REAL
   Probability of being FAKE: 38.21%
   Confidence: 61.79%
   ⚠ MODERATE CONFIDENCE

📊 Signal Analysis (DSP Features):
   Pitch Mean          : 615.2680
   Pitch Variance      : 1040.1733
   Pitch Range         : 3801.6489
   Energy Mean         : 0.1052
   Energy Variance     : 0.0939
   Silence Ratio       : 0.2661

💡 Interpretation:
   ✓ No obvious signal anomalies detected
```

---

### 3. Train Your Own Model

```bash
# Basic training (5 epochs, small batch)
python run_training.py --epochs 5 --batch_size 4

# Advanced training
python run_training.py \
  --data_dir data/ \
  --epochs 10 \
  --batch_size 8 \
  --hidden_dim 256 \
  --dropout 0.3 \
  --lr 0.001
```

**Training Options:**
- `--data_dir`: Path to data directory (default: `data/`)
- `--epochs`: Number of training epochs (default: 5)
- `--batch_size`: Batch size (default: 4)
- `--hidden_dim`: Hidden layer size (default: 256)
- `--dropout`: Dropout rate (default: 0.3)
- `--save_path`: Where to save model (default: `fusion_model.pth`)

---

### 4. Comprehensive Evaluation

```bash
# Evaluate on test directory with real/ and fake/ subdirectories
python validation/eval.py --model checkpoints/fusion_model.pth --test_dir data/

# Single file evaluation with detailed output
python validation/eval.py --model checkpoints/fusion_model.pth --audio_file test.wav
```

---

## 💻 Python API Usage

### Simple Inference

```python
from inference import DeepfakeInference

# Initialize
detector = DeepfakeInference(checkpoint_path="checkpoints/fusion_model.pth")

# Predict single file
result = detector.predict("audio.wav")
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']:.2%}")

# Batch prediction
results = detector.predict_batch("audio_folder/", limit=10)
```

### Advanced Evaluation

```python
from validation.eval import DeepfakeEvaluator

# Initialize evaluator
evaluator = DeepfakeEvaluator(
    model_path="checkpoints/fusion_model.pth",
    device="cpu"
)

# Detailed single file analysis
result = evaluator.predict_single("test.wav", verbose=True)

# Evaluate entire directory
results = evaluator.evaluate_directory("test_data/")
```

---

## 📊 Model Performance

**Checkpoint**: `checkpoints/fusion_model.pth`

| Metric | Value |
|--------|-------|
| **Model Size** | ~429K parameters |
| **Input Dimension** | 1542 (WavLM: 768, Whisper: 768, DSP: 6) |
| **Architecture** | 3-layer MLP (256 → 128 → 1) |
| **Inference Speed** | ~2-3 seconds/file (CPU) |
| **Device** | CPU-friendly |

---

## 🔬 Technical Details

### Feature Extractors

1. **WavLM-Base-Plus** (Acoustic Expert)
   - Model: `microsoft/wavlm-base-plus`
   - Parameters: 94M (frozen)
   - Output: 768-dim vector
   - Captures: Spectral artifacts, phase issues, vocoder traces

2. **Whisper-Small** (Semantic Expert)
   - Model: `openai/whisper-small`
   - Parameters: 244M (frozen, encoder only)
   - Output: 768-dim vector
   - Captures: Prosody mismatches, timing anomalies

3. **DSP Features** (Signal Expert)
   - Library: librosa
   - Output: 6-dim vector
   - Features: pitch (mean/std/range), energy (mean/std), silence ratio

### Fusion Model

- **Architecture**: 3-layer feedforward network
- **Layers**: 1542 → 256 → 128 → 1
- **Activation**: ReLU
- **Regularization**: Batch normalization + Dropout (0.3)
- **Loss**: Binary Cross Entropy with Logits
- **Optimizer**: Adam (lr=1e-3)

---

## 🎯 Design Philosophy

### Why Multi-Modal Fusion?

1. **Complementary Information**: Each expert catches different artifacts
   - WavLM: Low-level acoustic anomalies
   - Whisper: High-level semantic/prosody issues
   - DSP: Physical impossibilities (pitch/energy patterns)

2. **Explainability**: DSP features provide interpretable signals
3. **Efficiency**: Only fusion head is trainable (~429K params)
4. **Robustness**: Harder to fool multiple modalities

---

## 🛠️ Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Make sure you're in the ml_pipeline_deepfake directory
cd ml_pipeline_deepfake
python inference.py --audio data/real/sample.wav
```

**2. Model Loading Errors**
```bash
# Check checkpoint exists
ls checkpoints/fusion_model.pth

# Use absolute path if needed
python inference.py --audio test.wav --checkpoint /full/path/to/fusion_model.pth
```

**3. Audio File Errors**
- Ensure audio is in supported format (.wav, .mp3, .flac, .m4a)
- Check file exists and is readable
- Try converting to .wav if issues persist

**4. Memory Issues**
```bash
# Reduce batch size
python run_training.py --batch_size 2

# Force CPU usage
python inference.py --audio test.wav --device cpu
```

---

## 📈 Future Improvements

### Short-term
- [ ] Add data augmentation (pitch shift, time stretch, noise)
- [ ] Implement attention-based fusion
- [ ] Add frame-level temporal analysis
- [ ] Create web demo interface

### Long-term
- [ ] Real-time inference API
- [ ] Support for streaming audio
- [ ] Multi-language support
- [ ] Explainability dashboard

---

## 📝 Documentation

- **README.md** (this file): Quick start and usage guide
- **docs/TECHNICAL_SUMMARY.md**: Detailed technical documentation
- **docs/PRIORITY1_RESULTS.md**: Training results and analysis
- **docs/WILD_DATA_STATUS.md**: Data integration status

---

## 🤝 Contributing

This project was developed as part of the ATF Inc Security Intern program (December 2025).

**Team**: ATF Inc Security Intern Team  
**Repository**: https://github.com/atf-inc/dec25_intern_C_security

---

## 📄 License

[Add your license here]

---

## ✅ Project Status

**MVP**: ✅ Complete  
**Inference**: ✅ Working  
**Checkpoint**: ✅ Available (`checkpoints/fusion_model.pth`)  
**Documentation**: ✅ Complete

---

**Last Updated**: December 14, 2025  
**Version**: 1.1.0 (Reorganized)
