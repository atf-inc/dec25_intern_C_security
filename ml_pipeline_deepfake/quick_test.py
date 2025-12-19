import torch
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from models.fusion_model import DeepfakeFusionModel

# Load data
data = np.load('data/features_cache.npz')
wavlm = torch.FloatTensor(data['wavlm'])
whisper = torch.FloatTensor(data['whisper'])
dsp = torch.FloatTensor(data['dsp'])
labels = data['labels']

# Load model
model = DeepfakeFusionModel()
model.load_state_dict(torch.load('checkpoints/fusion_model_improved.pth', map_location='cpu'))
model.eval()

# Test
with torch.no_grad():
    logits = model(wavlm, whisper, dsp)
    probs = torch.sigmoid(logits).detach().numpy().flatten()
    preds = (probs > 0.5).astype(int)

# Metrics
acc = accuracy_score(labels, preds)
p, r, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
cm = confusion_matrix(labels, preds)

print(f'ACCURACY: {acc*100:.2f}%')
print(f'PRECISION: {p*100:.2f}%')
print(f'RECALL: {r*100:.2f}%')
print(f'F1-SCORE: {f1*100:.2f}%')
print(f'\nCONFUSION MATRIX:')
print(f'              Predicted')
print(f'            Real  Fake')
print(f'Real        {cm[0,0]:4d}  {cm[0,1]:4d}')
print(f'Fake        {cm[1,0]:4d}  {cm[1,1]:4d}')
print(f'\nReal Detection: {cm[0,0]}/{cm[0,0]+cm[0,1]} = {cm[0,0]/(cm[0,0]+cm[0,1])*100:.1f}%')
print(f'Fake Detection: {cm[1,1]}/{cm[1,0]+cm[1,1]} = {cm[1,1]/(cm[1,0]+cm[1,1])*100:.1f}%')
