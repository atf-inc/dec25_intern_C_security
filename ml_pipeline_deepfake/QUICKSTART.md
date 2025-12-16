# 🚀 Quick Start Guide - Fusion Deepfake Detection

Get the fusion model trained and running in 5 steps.

---

## ✅ Step 1: Verify Extractors (DONE)

```bash
cd dec25_intern_C_security/ml_pipeline_deepfake
python test_extractors.py
```

**Expected output:**
```
✅ WavLM extraction successful! (768-dim)
✅ Whisper extraction successful! (768-dim)
✅ DSP extraction successful! (8-dim)
✅ Fusion successful! (1544-dim)
🎉 All extractors working! Ready for training.
```

**Status:** ✅ COMPLETE (All tests passing)

---

## 📥 Step 2: Get Dataset

You have two options:

### Option A: Quick Test (Recommended for MVP)

Use a small custom dataset for quick testing:

```bash
# Create sample dataset structure
mkdir -p data/train/real data/train/fake
mkdir -p data/dev/real data/dev/fake
mkdir -p data/test/real data/test/fake

# Add your audio files:
# - Real voice samples → data/train/real/
# - Deepfake samples → data/train/fake/
# - Same for dev/ and test/
```

**Minimum samples for testing:**
- Train: 20 real + 20 fake = 40 samples
- Dev: 10 real + 10 fake = 20 samples
- Test: 10 real + 10 fake = 20 samples

**Where to get samples:**
- Real: Record yourself, use podcast clips, TED talks
- Fake: Use ElevenLabs, Play.ht, or other TTS services

### Option B: Production Dataset

**WaveFake (5GB, ~1 hour download):**
```bash
python scripts/download_dataset.py --dataset wavefake --output data/
```

**ASVspoof 2021 (25GB, overnight):**
```bash
python scripts/download_dataset.py --dataset asvspoof --output data/
```

---

## 🔧 Step 3: Extract Features

Once you have audio files in `data/`:

```bash
python scripts/extract_features.py --data_dir data/ --output features/
```

**What this does:**
- Loads all `.wav` files from `data/train/`, `data/dev/`, `data/test/`
- Extracts WavLM (768-dim), Whisper (768-dim), DSP (8-dim) features
- Saves as `.npy` files in `features/`

**Time estimate:**
- ~9 seconds per audio file on CPU
- ~2 seconds per audio file on GPU

**Example:**
- 100 audio files = ~15 minutes on CPU

---

## 🎓 Step 4: Train Model

```bash
python scripts/train_fusion.py --features_dir features/ --epochs 20 --batch_size 32
```

**Training parameters:**
- `--epochs 20`: Number of training epochs (adjust based on dataset size)
- `--batch_size 32`: Batch size (reduce if out of memory)
- `--lr 0.001`: Learning rate (default is good)
- `--cpu`: Force CPU training (if no GPU)

**Time estimate:**
- Small dataset (100 samples): ~5 minutes
- Medium dataset (1000 samples): ~30 minutes
- Large dataset (10k+ samples): ~2-3 hours

**What to expect:**
```
Epoch 1/20
Train - Loss: 0.6234 | Acc: 0.6500
Val   - Loss: 0.5891 | Acc: 0.7000
...
Epoch 20/20
Train - Loss: 0.1234 | Acc: 0.9500
Val   - Loss: 0.1456 | Acc: 0.9300
✓ Best model saved to models/fusion_detector.pth
```

**Target metrics:**
- Accuracy: >90%
- Precision: >90%
- Recall: >90%
- F1 Score: >90%

---

## 🧪 Step 5: Test Model

Create a test script:

```python
# test_model.py
import torch
import librosa
from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor
from src.models import FusionDeepfakeDetector

# Load model
model = FusionDeepfakeDetector()
model.load_state_dict(torch.load('models/fusion_detector.pth'))
model.eval()

# Initialize extractors
wavlm_ext = WavLMExtractor()
whisper_ext = WhisperExtractor()
dsp_ext = DSPExtractor()

# Test on audio file
audio_path = 'test_audio.wav'
waveform, sr = librosa.load(audio_path, sr=16000)

# Extract features
wavlm_emb = wavlm_ext.extract(waveform, sr)
whisper_emb = whisper_ext.extract(waveform, sr)
dsp_feat = dsp_ext.extract(waveform, sr)

# Convert to tensors
wavlm_t = torch.FloatTensor(wavlm_emb).unsqueeze(0)
whisper_t = torch.FloatTensor(whisper_emb).unsqueeze(0)
dsp_t = torch.FloatTensor(dsp_feat).unsqueeze(0)

# Predict
result = model.predict_with_explanation(wavlm_t, whisper_t, dsp_t)

print(f"Is Deepfake: {result['confidence'] > 0.5}")
print(f"Confidence: {result['confidence']:.4f}")
print(f"Expert Scores:")
print(f"  Acoustic: {result['expert_scores']['acoustic']:.4f}")
print(f"  Semantic: {result['expert_scores']['semantic']:.4f}")
print(f"  Signal: {result['expert_scores']['signal']:.4f}")
```

Run:
```bash
python test_model.py
```

---

## 🔗 Step 6: Integrate with Backend

Update `backend/app/ml/deepfake_model.py`:

```python
import sys
sys.path.append('ml_pipeline_deepfake')

from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor
from src.models import FusionDeepfakeDetector
import torch
import librosa

class DeepfakeDetector:
    def __init__(self):
        self.wavlm_ext = WavLMExtractor()
        self.whisper_ext = WhisperExtractor()
        self.dsp_ext = DSPExtractor()
        
        self.model = FusionDeepfakeDetector()
        self.model.load_state_dict(torch.load('ml_pipeline_deepfake/models/fusion_detector.pth'))
        self.model.eval()
    
    def predict(self, audio_path):
        # Load audio
        waveform, sr = librosa.load(audio_path, sr=16000)
        
        # Extract features
        wavlm_emb = self.wavlm_ext.extract(waveform, sr)
        whisper_emb = self.whisper_ext.extract(waveform, sr)
        dsp_feat = self.dsp_ext.extract(waveform, sr)
        
        # Convert to tensors
        wavlm_t = torch.FloatTensor(wavlm_emb).unsqueeze(0)
        whisper_t = torch.FloatTensor(whisper_emb).unsqueeze(0)
        dsp_t = torch.FloatTensor(dsp_feat).unsqueeze(0)
        
        # Predict
        result = self.model.predict_with_explanation(wavlm_t, whisper_t, dsp_t)
        
        return {
            'is_deepfake': result['confidence'] > 0.5,
            'confidence': float(result['confidence']),
            'expert_scores': result['expert_scores'],
            'explanation': self._generate_explanation(result)
        }
    
    def _generate_explanation(self, result):
        scores = result['expert_scores']
        dominant = max(scores, key=scores.get)
        
        explanations = {
            'acoustic': "Detected acoustic artifacts (vocoder traces, phase errors)",
            'semantic': "Detected prosody mismatch - emotion doesn't match words",
            'signal': "Detected impossible signal physics (too perfect patterns)"
        }
        
        return explanations[dominant]
```

---

## 📊 Troubleshooting

### Issue: Out of Memory

**Solution:** Reduce batch size
```bash
python scripts/train_fusion.py --features_dir features/ --batch_size 8
```

### Issue: Models not downloading

**Solution:** Download manually
```bash
# WavLM
python -c "from transformers import WavLMModel; WavLMModel.from_pretrained('microsoft/wavlm-base-plus')"

# Whisper
python -c "from transformers import WhisperModel; WhisperModel.from_pretrained('openai/whisper-small')"
```

### Issue: Slow extraction

**Solution:** Use GPU or reduce dataset size
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"
```

### Issue: Low accuracy

**Solutions:**
1. More training data (aim for 1000+ samples)
2. More epochs (try 30-50)
3. Data augmentation (add noise, pitch shift)
4. Check data quality (ensure labels are correct)

---

## 🎯 Summary

**Current Status:**
- ✅ Feature extractors: WORKING (all tests passing)
- ✅ Fusion model: IMPLEMENTED
- ✅ Training pipeline: READY
- ⏳ Dataset: PENDING (need to download or create)
- ⏳ Training: PENDING (waiting for dataset)
- ⏳ Integration: PENDING (waiting for trained model)

**Next Action:**
Choose your dataset approach (Option A or B in Step 2) and proceed!

**Time to Production:**
- Quick path (small dataset): 1-2 hours
- Production path (full dataset): 6-8 hours (mostly automated)

---

**Ready? Start with Step 2 (Get Dataset)!**
