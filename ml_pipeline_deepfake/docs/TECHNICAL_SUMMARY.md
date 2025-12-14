# Deepfake Voice Detection MVP - Technical Summary

## 📋 Project Overview

**Objective**: Implement a CPU-friendly, explainable deepfake voice detection system using a multi-expert fusion architecture.

**Status**: MVP Complete ✅

**Architecture**: WavLM-Base-Plus + Whisper-Small + DSP Features → Lightweight Fusion Classifier

---

## 🏗️ Architecture

### Three-Expert Fusion System

```
┌─────────────────────────────────────────────────────────────┐
│                      Audio Input (.wav)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
    ┌────────┐   ┌─────────┐   ┌─────────┐
    │ WavLM  │   │ Whisper │   │   DSP   │
    │ (768d) │   │ (768d)  │   │   (6d)  │
    └────┬───┘   └────┬────┘   └────┬────┘
         │            │             │
         └────────────┼─────────────┘
                      │
                 Concatenate
                   (1542d)
                      │
                      ▼
            ┌──────────────────┐
            │  Fusion MLP      │
            │  (3 layers)      │
            │  ~400K params    │
            └─────────┬────────┘
                      │
                      ▼
              Binary Output
              (Real vs Fake)
```

### Expert Responsibilities

| Expert | Type | Output | What It Captures |
|--------|------|--------|------------------|
| **WavLM-Base-Plus** | Acoustic | 768-dim | Spectral artifacts, phase issues, vocoder fingerprints |
| **Whisper-Small** | Semantic | 768-dim | Prosody mismatches, timing anomalies, linguistic coherence |
| **DSP** | Signal | 6-dim | Pitch variance, energy variance, silence patterns |

---

## 📁 Project Structure

```
ml model/
├── features/
│   ├── __init__.py
│   ├── wavlm_extractor.py      # WavLM acoustic feature extractor
│   ├── whisper_extractor.py    # Whisper semantic feature extractor
│   └── dsp_features.py         # DSP signal feature extractor
│
├── models/
│   ├── __init__.py
│   └── fusion_model.py         # Fusion classifier (MLP)
│
├── training/
│   ├── __init__.py
│   └── train.py                # Training pipeline
│
├── validation/
│   ├── __init__.py
│   └── eval.py                 # Evaluation & explainability
│
├── data/                       # Audio dataset (not included)
│   ├── real/
│   └── fake/
│
├── TECHNICAL_SUMMARY.md        # This file
└── requirements.txt            # Python dependencies
```

---

## 🔧 Technical Details

### 1. Feature Extractors

#### WavLM-Base-Plus (Acoustic Expert)
- **Model**: `microsoft/wavlm-base-plus`
- **Parameters**: 94M (frozen)
- **Output**: 768-dimensional vector
- **Method**: Mean pooling over encoder hidden states
- **Captures**:
  - Spectral inconsistencies (unnatural frequency patterns)
  - Phase coherence issues (vocoder artifacts)
  - Temporal dynamics (prosody, rhythm)
  - Fine-grained acoustic textures (breathing, micro-pauses)

#### Whisper-Small (Semantic Expert)
- **Model**: `openai/whisper-small`
- **Parameters**: 244M (frozen, encoder only)
- **Output**: 768-dimensional vector
- **Method**: Mean pooling over encoder embeddings
- **Captures**:
  - Prosody mismatches (unnatural pitch contours)
  - Timing anomalies (pause durations, speech rate)
  - Linguistic coherence (semantic flow)
  - Cross-modal alignment (audio-to-speech patterns)

#### DSP Features (Signal Expert)
- **Library**: librosa
- **Parameters**: 0 (no ML model)
- **Output**: 6-dimensional vector
- **Features**:
  1. `pitch_mean`: Average pitch level
  2. `pitch_std`: Pitch variance (LOW = AI-like stability)
  3. `pitch_range`: Pitch dynamics (LOW = monotone)
  4. `energy_mean`: Average vocal energy
  5. `energy_std`: Energy variance (LOW = robotic)
  6. `silence_ratio`: Pause patterns (extreme = unnatural)

### 2. Fusion Model

#### Architecture
```python
Input (1542-dim)
    ↓
FC1: 1542 → 256 + BatchNorm + ReLU + Dropout(0.3)
    ↓
FC2: 256 → 128 + BatchNorm + ReLU + Dropout(0.3)
    ↓
FC3: 128 → 1 (logits)
    ↓
Sigmoid → Probability
```

#### Training Configuration
- **Loss**: Binary Cross Entropy with Logits
- **Optimizer**: Adam (lr=1e-3)
- **Batch Size**: 8-16 (CPU-friendly)
- **Epochs**: 5-10 (MVP-scale)
- **Regularization**: Dropout (0.3), BatchNorm
- **Trainable Parameters**: ~400K (only fusion head)

#### Key Design Decisions
- ✅ **Lightweight**: Only fusion head is trained (WavLM/Whisper frozen)
- ✅ **CPU-friendly**: Small batch size, no GPU required
- ✅ **Regularized**: Dropout + BatchNorm for small dataset
- ✅ **Simple**: 3-layer MLP, no complex architectures

---

## 🚀 Usage Guide

### Installation

```bash
# Install dependencies
pip install torch torchaudio transformers librosa scikit-learn numpy

# Or use requirements.txt
pip install -r requirements.txt
```

### 1. Prepare Data

```
data/
├── real/
│   ├── sample_001.wav
│   ├── sample_002.wav
│   └── ...
└── fake/
    ├── sample_001.wav
    ├── sample_002.wav
    └── ...
```

**Recommended Dataset Size**: 40-50 samples (20-25 real, 20-25 fake)

**Audio Format**: WAV, 16kHz, mono, 3-10 seconds per sample

### 2. Train Model

```bash
cd training
python train.py --data_dir ../data/ --epochs 10 --batch_size 8
```

**Options**:
- `--data_dir`: Path to data directory
- `--epochs`: Number of training epochs (default: 10)
- `--batch_size`: Batch size (default: 8)
- `--hidden_dim`: Hidden layer size (default: 256)
- `--dropout`: Dropout rate (default: 0.3)
- `--lr`: Learning rate (default: 1e-3)
- `--save_path`: Model save path (default: fusion_model.pth)
- `--simple`: Use 2-layer model instead of 3-layer
- `--no_cache`: Don't use cached features

**Output**:
- Trained model: `fusion_model.pth`
- Cached features: `data/features_cache.npz`
- Training logs with accuracy, loss, precision, recall, F1, AUC

### 3. Evaluate Model

#### Single File Evaluation
```bash
cd validation
python eval.py --model ../fusion_model.pth --audio_file test_audio.wav
```

**Output**:
```
🎯 PREDICTION: FAKE
   Probability of FAKE: 0.8723
   Confidence: 0.8723
   ✓ HIGH CONFIDENCE

📊 DSP Features (Interpretable):
   pitch_mean          : 185.2341
   pitch_std           : 8.4521
   ...

💡 Interpretation Hints:
   ⚠ Low pitch variance → Unnaturally stable pitch (AI-like)
```

#### Directory Evaluation
```bash
cd validation
python eval.py --model ../fusion_model.pth --test_dir ../test_data/
```

**Output**:
- Per-sample predictions
- Accuracy, precision, recall, F1, AUC
- Confusion matrix
- Uncertain cases (confidence < 0.6)

---

## 📊 Expected Performance

### MVP Baseline (40-50 samples)

| Metric | Expected Range |
|--------|----------------|
| **Accuracy** | 70-85% |
| **Precision** | 65-80% |
| **Recall** | 65-80% |
| **F1-Score** | 65-80% |

**Note**: Performance depends heavily on:
- Dataset quality and diversity
- Balance between real/fake samples
- Audio quality (clean vs noisy)
- Deepfake generation method

### Known Limitations

1. **Small Dataset**: MVP trained on 40-50 samples → limited generalization
2. **CPU-Only**: Slower inference than GPU (~2-3 sec per sample)
3. **No Fine-tuning**: WavLM/Whisper frozen → may miss domain-specific patterns
4. **Simple Fusion**: 3-layer MLP → may not capture complex interactions

---

## 🔍 Explainability Features

### 1. Confidence Scores
- Every prediction includes confidence (0-1)
- Flags uncertain cases (confidence < 0.6)

### 2. Interpretable DSP Features
- Shows all 6 DSP features with values
- Provides interpretation hints for suspicious patterns

### 3. Failure Analysis
- Lists all uncertain/misclassified samples
- Confusion matrix for error patterns
- Per-class precision/recall breakdown

### 4. Feature Transparency
- DSP features are human-interpretable
- Links features to physical impossibilities
- Example: "Low pitch variance → AI-like stability"

---

## 🎯 Design Philosophy

### MVP Constraints (Strictly Followed)

✅ **CPU-Friendly**: No GPU required, small batch sizes  
✅ **Small Dataset**: Designed for 40-50 samples  
✅ **Lightweight**: Only ~400K trainable parameters  
✅ **Explainable**: Interpretable DSP features + confidence scores  
✅ **Simple**: No complex architectures, clear code  
✅ **Frozen Extractors**: No fine-tuning of WavLM/Whisper  

### Why This Architecture?

1. **Multi-Expert Fusion**: Different deepfakes have different weaknesses
   - Some have good spectral quality but poor prosody
   - Others have good prosody but spectral artifacts
   - Fusion captures both

2. **Frozen Extractors**: Prevents overfitting on small data
   - WavLM/Whisper pre-trained on massive datasets
   - Only train lightweight fusion head

3. **DSP Features**: Provide interpretability
   - Explicit, physics-based rules
   - Hard to fool with simple tricks
   - Helps explain predictions

---

## 🔬 Future Improvements (Post-MVP)

### Data
- [ ] Expand dataset to 500+ samples
- [ ] Add diverse audio sources (phone, mic, compressed)
- [ ] Include multiple deepfake generators

### Model
- [ ] Experiment with attention-based fusion
- [ ] Add frame-level temporal analysis
- [ ] Try different aggregation methods (max pooling, attention)

### Features
- [ ] Add more DSP features (spectral flux, zero-crossing rate)
- [ ] Experiment with mel-spectrogram features
- [ ] Try different Whisper layers (not just last)

### Training
- [ ] Implement cross-validation
- [ ] Add data augmentation (noise, speed, pitch shift)
- [ ] Experiment with different loss functions (focal loss)

### Deployment
- [ ] Create REST API for inference
- [ ] Build web demo interface
- [ ] Optimize for real-time processing

---

## 📦 Dependencies

```txt
torch>=2.0.0
torchaudio>=2.0.0
transformers>=4.30.0
librosa>=0.10.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

---

## 🐛 Troubleshooting

### Issue: "Out of memory" during feature extraction
**Solution**: Process files one at a time, clear cache between samples

### Issue: Low accuracy (<60%)
**Possible causes**:
- Dataset too small or imbalanced
- Poor audio quality
- Overfitting (try `--simple` model or higher `--dropout`)

### Issue: All predictions are the same class
**Possible causes**:
- Severe class imbalance in training data
- Learning rate too high/low
- Try reducing `--hidden_dim` or increasing `--dropout`

### Issue: Import errors after restructuring
**Solution**: Run scripts from their respective directories:
```bash
cd training && python train.py
cd validation && python eval.py
```

---

## 📝 Citation & References

### Models Used
- **WavLM**: [microsoft/wavlm-base-plus](https://huggingface.co/microsoft/wavlm-base-plus)
- **Whisper**: [openai/whisper-small](https://huggingface.co/openai/whisper-small)

### Conceptual Inspiration
- [deepfake-whisper-features](https://github.com/piotrkawa/deepfake-whisper-features) (reference only)

---

## ✅ MVP Completion Checklist

- [x] WavLM acoustic feature extractor
- [x] Whisper semantic feature extractor
- [x] DSP signal feature extractor
- [x] Lightweight fusion classifier
- [x] Training pipeline with metrics
- [x] Evaluation script with explainability
- [x] Project restructuring
- [x] Technical documentation

**Status**: Ready for data collection and training 🚀

---

## 📧 Contact & Support

For questions or issues, refer to:
- Code comments (extensive documentation in each file)
- This technical summary
- Individual module docstrings

---

**Last Updated**: 2025-12-14  
**Version**: 1.0.0 (MVP)
