"""
Augmentation & Feature Extraction Pipeline

Enhances the dataset by generating augmented versions of training samples.
For each TRAINING file, it generates 5 augmented versions:
1. Original
2. Noise Injection
3. Pitch Shift
4. Time Stretch
5. Combined Random Augmentation

Then extracts features (WavLM, Whisper, DSP) for all.
"""

import sys
import os
import argparse
import numpy as np
import librosa
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import torch

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor
from src.utils.augmentation import AudioAugmentor

# Global variables for workers
worker_extractors = None
worker_augmentor = None

def init_worker():
    """Initialize models in each worker process."""
    global worker_extractors, worker_augmentor
    worker_extractors = {
        'wavlm': WavLMExtractor(),
        'whisper': WhisperExtractor(),
        'dsp': DSPExtractor()
    }
    worker_augmentor = AudioAugmentor()

def load_audio(audio_path, target_sr=16000):
    try:
        waveform, sr = librosa.load(audio_path, sr=target_sr)
        return waveform, sr
    except Exception as e:
        return None, None

def process_single_item(item):
    """
    Process a single (path, label, num_augs) tuple.
    Returns list of (wavlm, whisper, dsp, label) tuples.
    """
    path, label, num_augs = item
    augmentor = worker_augmentor
    extractors = worker_extractors
    
    waveform, sr = load_audio(path)
    if waveform is None: return []
    
    versions = [waveform] # Always keep original
    
    # Generate augmentations
    if num_augs > 0:
        for _ in range(num_augs):
            versions.append(augmentor.apply_random_augmentation(waveform))
            
    results = []
    for wav in versions:
        try:
            # Extract
            w_emb = extractors['wavlm'].extract(wav, sr)
            s_emb = extractors['whisper'].extract(wav, sr)
            d_feat = extractors['dsp'].extract(wav, sr)
            
            results.append((w_emb, s_emb, d_feat, label))
        except Exception:
            pass
            
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--output', type=str, default='features_augmented')
    parser.add_argument('--workers', type=int, default=2) # Conservative default
    args = parser.parse_args()
    
    # Define splits
    splits = ['train', 'dev', 'test']
    
    for split in splits:
        print(f"\nProcessing {split.upper()}...")
        is_train = (split == 'train')
        
        # 1. Collect Files
        # For TRAIN: Look in global 'real' and 'fake' first
        if is_train:
            data_root = args.data_dir
            real_dir = os.path.join(data_root, 'real')
            fake_dir = os.path.join(data_root, 'fake')
            # Fallback
            if not os.path.exists(real_dir): real_dir = os.path.join(data_root, split, 'real')
            if not os.path.exists(fake_dir): fake_dir = os.path.join(data_root, split, 'fake')
        else:
            real_dir = os.path.join(args.data_dir, split, 'real')
            fake_dir = os.path.join(args.data_dir, split, 'fake')
            
        real_files = [str(f) for f in Path(real_dir).glob('**/*.wav')] if os.path.exists(real_dir) else []
        fake_files = [str(f) for f in Path(fake_dir).glob('**/*.wav')] if os.path.exists(fake_dir) else []
        
        print(f"Found {len(real_files)} Real, {len(fake_files)} Fake.")
        
        # 2. Build Worklist
        worklist = []
        if is_train:
            # Process ALL files found (Selection done by assemble script)
            
            # Fakes: Apply augmentation to make them robust
            # We have ~250 fakes. Let's do 2 augmentations per file (Total ~750)
            augs_per_fake = 2 
            
            if fake_files:
                print(f"Augmenting {len(fake_files)} Fakes with {augs_per_fake} augmentations each.")
                for f in fake_files:
                    worklist.append((f, 1, augs_per_fake))
            
            # Reals: Apply augmentation to make them robust to noise
            # We have ~250 reals. Let's do 2 augmentations (Total ~750)
            augs_per_real = 2
            
            if real_files:
                print(f"Augmenting {len(real_files)} Reals with {augs_per_real} augmentations each.")
                for f in real_files:
                    worklist.append((f, 0, augs_per_real))
        else:
            # No aug for dev/test
            for f in real_files: worklist.append((f, 0, 0))
            for f in fake_files: worklist.append((f, 1, 0))
            
        if not worklist:
            print("Nothing to process.")
            continue
            
        # 3. Parallel Execution
        all_wavlm = []
        all_whisper = []
        all_dsp = []
        all_labels = []
        
        # Adjust workers: if very few items, use 1
        num_workers = args.workers if len(worklist) > 10 else 1
        
        print(f"Starting pool with {num_workers} workers for {len(worklist)} items...")
        
        with ProcessPoolExecutor(max_workers=num_workers, initializer=init_worker) as executor:
            # Chunksize helps with tqdm
            results = list(tqdm(executor.map(process_single_item, worklist), total=len(worklist)))
            
        # 4. Aggregate
        print("Aggregating results...")
        for batch in results:
            for item in batch:
                w, s, d, l = item
                all_wavlm.append(w)
                all_whisper.append(s)
                all_dsp.append(d)
                all_labels.append(l)
                
        # 5. Save
        out_path = os.path.join(args.output, split)
        os.makedirs(out_path, exist_ok=True)
        
        if all_labels:
            np.save(os.path.join(out_path, 'wavlm_features.npy'), np.array(all_wavlm, dtype=np.float32))
            np.save(os.path.join(out_path, 'whisper_features.npy'), np.array(all_whisper, dtype=np.float32))
            np.save(os.path.join(out_path, 'dsp_features.npy'), np.array(all_dsp, dtype=np.float32))
            np.save(os.path.join(out_path, 'labels.npy'), np.array(all_labels, dtype=np.int64))
            print(f"Saved {len(all_labels)} samples to {out_path}")
        else:
            print("No samples generated.")

if __name__ == '__main__':
    # Fix for windows multiprocessing
    torch.multiprocessing.set_start_method('spawn', force=True)
    main()
