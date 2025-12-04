# Quick Start: Fine-tuning Wav2Vec2 on LibriSpeech

## After Downloading dev-clean.tar.gz

### Step 1: Extract the Dataset
```bash
tar -xzf dev-clean.tar.gz
# This creates: LibriSpeech/dev-clean/
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Fine-tuning
```bash
python manage.py finetune_asr \
    --dataset-path /path/to/LibriSpeech \
    --output-dir models/finetuned-wav2vec2 \
    --epochs 3
```

### Step 4: Use Fine-tuned Model
```bash
export ASR_MODEL_NAME=/absolute/path/to/models/finetuned-wav2vec2
python manage.py runserver
```

## Full Documentation
See `docs/FINETUNING.md` for detailed instructions, troubleshooting, and advanced options.

