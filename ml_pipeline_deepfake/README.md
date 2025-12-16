# 🎙️ Fusion Deepfake Voice Detection Pipeline

Multi-modal deepfake voice detection using WavLM + Whisper + DSP fusion architecture.

## 🎯 Architecture Overview

**Three Expert Branches:**
1. **WavLM (Acoustic Expert)** - 768-dim embeddings
   - Detects micro-glitches, compression artifacts, vocoder traces
2. **Whisper (Semantic Expert)** - 768-dim embeddings
   - Detects prosody mismatches, unnatural pauses, emotion inconsistencies
3. **DSP (Signal Expert)** - 8-dim features
   - Detects impossible physics, spectral anomalies, phase errors

**Total Fusion Vector:** 1544 dimensions (768 + 768 + 8)

**Expected Accuracy:** 92-95%

---

## 📁 Project Structure

```
ml_pipeline_deepfake/
├── src/
│   ├── features/           # Feature extractors
│   │   ├── wavlm_extractor.py
│   │   ├── whisper_extractor.py
│   │   └── dsp_extractor.py
│   └── models/             # Fusion model
│       └── fusion_model.py
├── scripts/
│   ├── download_dataset.py    # Dataset download
│   ├── extract_features.py    # Feature extraction
│   └── train_fusion.py        # Model training
├── data/                   # Raw audio files
│   ├── train/
│   ├── dev/
│   └── test/
├── features/               # Extracted features (.npy)
│   ├── train/
│   ├── dev/
│   └── test/
├── models/                 # Trained models
│   └── fusion_detector.pth
├── test_extractors.py      # Test all extractors
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test Extractors

```bash
python test_extractors.py
```

Expected output:
```
✅ WavLM extraction successful! (768-dim)
✅ Whisper extraction successful! (768-dim)
✅ DSP extraction successful! (8-dim)
✅ Fusion successful! (1544-dim)
```

### 3. Download Dataset

**Option A: Quick (WaveFake - 5GB, ~1 hour)**
```bash
python scripts/download_dataset.py --dataset wavefake --output data/
```

**Option B: Production (ASVspoof 2021 - 25GB, overnight)**
```bash
python scripts/download_dataset.py --dataset asvspoof --output data/
```

### 4. Extract Features

```bash
python scripts/extract_features.py --data_dir data/ --output features/
```

This will:
- Process all audio files in `data/train/`, `data/dev/`, `data/test/`
- Extract WavLM, Whisper, and DSP features
- Save as `.npy` files in `features/`
- Takes ~9 seconds per audio file on CPU

### 5. Train Fusion Model

```bash
python scripts/train_fusion.py --features_dir features/ --epochs 20 --batch_size 32
```

Training parameters:
- **Epochs:** 20 (adjust based on dataset size)
- **Batch size:** 32 (reduce if out of memory)
- **Learning rate:** 0.001 (with ReduceLROnPlateau scheduler)
- **Optimizer:** Adam
- **Loss:** Binary Cross Entropy

### 6. Evaluate Model

The training script automatically evaluates on the dev set and saves the best model.

Final metrics:
- Accuracy
- Precision / Recall / F1
- AUC-ROC
- Confusion Matrix

---

## 📊 Expected Performance

| Metric | Target |
|--------|--------|
| Accuracy | 92-95% |
| Precision | >90% |
| Recall | >90% |
| F1 Score | >90% |
| AUC-ROC | >0.95 |

---

## 🔧 Advanced Usage

### Custom Dataset

If you have your own dataset:

1. Organize files:
```
data/
├── train/
│   ├── real/  (real voice samples)
│   └── fake/  (deepfake samples)
├── dev/
│   ├── real/
│   └── fake/
└── test/
    ├── real/
    └── fake/
```

2. Extract features:
```bash
python scripts/extract_features.py --data_dir data/ --output features/
```

3. Train:
```bash
python scripts/train_fusion.py --features_dir features/ --epochs 20
```

### Hyperparameter Tuning

```bash
# Larger model
python scripts/train_fusion.py --features_dir features/ --epochs 30 --batch_size 64 --lr 0.0005

# More regularization (small dataset)
python scripts/train_fusion.py --features_dir features/ --epochs 15 --batch_size 16 --lr 0.001
```

### CPU vs GPU

```bash
# Force CPU training
python scripts/train_fusion.py --features_dir features/ --cpu

# GPU training (automatic if available)
python scripts/train_fusion.py --features_dir features/
```

---

## 🧪 Testing

### Test Individual Extractors

```python
from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor
import numpy as np

# Generate test audio
audio = np.sin(2 * np.pi * 440 * np.linspace(0, 3, 48000))

# Extract features
wavlm_ext = WavLMExtractor()
whisper_ext = WhisperExtractor()
dsp_ext = DSPExtractor()

wavlm_emb = wavlm_ext.extract(audio, 16000)
whisper_emb = whisper_ext.extract(audio, 16000)
dsp_feat = dsp_ext.extract(audio, 16000)

print(f"WavLM: {wavlm_emb.shape}")      # (768,)
print(f"Whisper: {whisper_emb.shape}")  # (768,)
print(f"DSP: {dsp_feat.shape}")         # (8,)
```

### Test Fusion Model

```python
import torch
from src.models import FusionDeepfakeDetector

model = FusionDeepfakeDetector()
model.load_state_dict(torch.load('models/fusion_detector.pth'))
model.eval()

# Dummy features
wavlm = torch.randn(1, 768)
whisper = torch.randn(1, 768)
dsp = torch.randn(1, 8)

# Predict
confidence = model(wavlm, whisper, dsp)
print(f"Deepfake confidence: {confidence.item():.4f}")

# With explainability
result = model.predict_with_explanation(wavlm, whisper, dsp)
print(f"Expert scores: {result['expert_scores']}")
```

---

## 🔗 Integration with Backend

Once trained, integrate the model into the backend:

```python
# backend/app/ml/deepfake_model.py

from ml_pipeline_deepfake.src.features import WavLMExtractor, WhisperExtractor, DSPExtractor
from ml_pipeline_deepfake.src.models import FusionDeepfakeDetector
import torch

class FusionDeepfakeDetector:
    def __init__(self, model_path='ml_pipeline_deepfake/models/fusion_detector.pth'):
        self.wavlm_ext = WavLMExtractor()
        self.whisper_ext = WhisperExtractor()
        self.dsp_ext = DSPExtractor()
        
        self.model = FusionDeepfakeDetector()
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()
    
    def predict(self, audio_path):
        # Load audio
        import librosa
        waveform, sr = librosa.load(audio_path, sr=16000)
        
        # Extract features
        wavlm_emb = self.wavlm_ext.extract(waveform, sr)
        whisper_emb = self.whisper_ext.extract(waveform, sr)
        dsp_feat = self.dsp_ext.extract(waveform, sr)
        
        # Convert to tensors
        wavlm_t = torch.FloatTensor(wavlm_emb).unsqueeze(0)
        whisper_t = torch.FloatTensor(whisper_emb).unsqueeze(0)
        dsp_t = torch.FloatTensor(dsp_feat).unsqueeze(0)
        
        # Predict with explainability
        result = self.model.predict_with_explanation(wavlm_t, whisper_t, dsp_t)
        
        return {
            'is_deepfake': result['confidence'] > 0.5,
            'confidence': result['confidence'],
            'expert_scores': result['expert_scores']
        }
```

---

## 📚 References

- **WavLM Paper:** https://arxiv.org/abs/2110.13900
- **Whisper Paper:** https://arxiv.org/abs/2212.04356
- **ASVspoof 2021:** https://www.asvspoof.org/index2021.html
- **WaveFake Dataset:** https://zenodo.org/record/5642506

---

## 🎯 Next Steps

1. ✅ Feature extractors implemented
2. ✅ Fusion model created
3. ✅ Training pipeline ready
4. ⏳ Download dataset
5. ⏳ Extract features
6. ⏳ Train model
7. ⏳ Integrate with backend

---

**Ready to train? Start with Step 3 (Download Dataset)!**
