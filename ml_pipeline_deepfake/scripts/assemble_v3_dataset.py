
import os
import shutil
import random
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
ROOT_DIR = Path(__file__).parent.parent
WAVEFAKE_DIR = ROOT_DIR / "data/wavefake/generated_audio"
ASVSPOOF_DIR = ROOT_DIR / "data/train/fake" # Old training data
REAL_DIR = ROOT_DIR / "data/real/librispeech"

OUTPUT_DIR = ROOT_DIR / "data/train_v3_balanced"

def main():
    logger.info("Initializing Phase 3 Dataset Assembly...")
    
    # 1. Setup Output Structure
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    
    (OUTPUT_DIR / "fake").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "real").mkdir(parents=True, exist_ok=True)
    
    # 2. Collect Modern Fakes (WaveFake)
    # We want ~200 samples total. There are 10 subdirectories.
    # So we take ~20 from each.
    samples_per_variant = 20
    modern_fake_count = 0
    
    if not WAVEFAKE_DIR.exists():
        logger.error(f"WaveFake directory not found at {WAVEFAKE_DIR}")
        return

    logger.info("Scanning WaveFake architectures...")
    architectures = [d for d in WAVEFAKE_DIR.iterdir() if d.is_dir()]
    
    for arch in architectures:
        files = list(arch.glob("*.wav"))
        if not files:
            continue
            
        selected = random.sample(files, min(len(files), samples_per_variant))
        logger.info(f"  - {arch.name}: Selected {len(selected)} samples")
        
        for f in selected:
            # Prefix filename with architecture to avoid collisions and verify later
            dest_name = f"{arch.name}_{f.name}"
            shutil.copy2(f, OUTPUT_DIR / "fake" / dest_name)
            modern_fake_count += 1
            
    logger.info(f"Total Modern Fakes: {modern_fake_count}")
    
    # 3. Collect Classic Fakes (ASVspoof)
    # Adding some classic fakes to ensure we don't regress
    classic_fake_target = 50
    classic_files = list(ASVSPOOF_DIR.glob("*.wav")) if ASVSPOOF_DIR.exists() else []
    
    if classic_files:
        selected_classic = random.sample(classic_files, min(len(classic_files), classic_fake_target))
        for f in selected_classic:
            dest_name = f"asvspoof_{f.name}"
            shutil.copy2(f, OUTPUT_DIR / "fake" / dest_name)
        logger.info(f"Total Classic Fakes: {len(selected_classic)}")
        total_fakes = modern_fake_count + len(selected_classic)
    else:
        logger.warning("No ASVspoof files found! Proceeding with only Modern Fakes.")
        total_fakes = modern_fake_count

    # 4. Collect Real Data (LibriSpeech)
    # Balance the total number of fakes
    real_target = total_fakes
    real_files = list(REAL_DIR.glob("*.wav")) if REAL_DIR.exists() else []
    
    if not real_files:
        logger.error("No Real LibriSpeech files found!")
        return
        
    selected_real = random.sample(real_files, min(len(real_files), real_target))
    logger.info(f"Selected {len(selected_real)} Real samples to balance {total_fakes} Fakes.")
    
    for f in selected_real:
        shutil.copy2(f, OUTPUT_DIR / "real" / f.name)
        
    logger.info("--- Dataset Summary ---")
    logger.info(f"Location: {OUTPUT_DIR}")
    logger.info(f"Total Fakes: {total_fakes}")
    logger.info(f"Total Real: {len(selected_real)}")
    logger.info("Ready for Augmentation & Extraction.")

if __name__ == "__main__":
    main()
