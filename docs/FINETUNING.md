# Fine-tuning Wav2Vec2 on LibriSpeech

This guide explains how to fine-tune the Wav2Vec2 ASR model using the LibriSpeech dev-clean dataset.

## Prerequisites

1. **Download LibriSpeech dev-clean dataset**
   - Download from: http://www.openslr.org/12/
   - File: `dev-clean.tar.gz` (337MB)
   - Extract the archive:
     ```bash
     tar -xzf dev-clean.tar.gz
     ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Hardware requirements**
   - GPU recommended (CUDA-compatible) for faster training
   - Minimum 16GB RAM
   - ~10GB free disk space for dataset and model

## Step-by-Step Fine-tuning Process

### Step 1: Extract the Dataset

After downloading `dev-clean.tar.gz`, extract it:

```bash
cd /path/to/downloads
tar -xzf dev-clean.tar.gz
```

This will create a directory structure like:
```
LibriSpeech/
  dev-clean/
    84/
      121123/
        *.flac (audio files)
        *.txt (transcriptions)
```

### Step 2: Run Fine-tuning

#### Option A: Using Django Management Command (Recommended)

```bash
python manage.py finetune_asr \
    --dataset-path /path/to/LibriSpeech \
    --output-dir models/finetuned-wav2vec2 \
    --epochs 3 \
    --batch-size 8 \
    --learning-rate 3e-4
```

#### Option B: Using Python Script Directly

```bash
python -m ai_services.finetune \
    --base-model facebook/wav2vec2-base-960h \
    --dataset-path /path/to/LibriSpeech \
    --output-dir models/finetuned-wav2vec2 \
    --epochs 3 \
    --batch-size 8
```

#### Option C: Using HuggingFace Hub (No Local Download)

If you don't want to download the dataset locally, the script will automatically download it from HuggingFace:

```bash
python manage.py finetune_asr \
    --output-dir models/finetuned-wav2vec2 \
    --epochs 3
```

### Step 3: Monitor Training

Training progress will be logged to:
- Console output
- TensorBoard logs in `models/finetuned-wav2vec2/runs/`

To view TensorBoard:
```bash
tensorboard --logdir models/finetuned-wav2vec2/runs
```

### Step 4: Use Fine-tuned Model

After training completes, update your settings to use the fine-tuned model:

#### Option A: Environment Variable

```bash
export ASR_MODEL_NAME=/absolute/path/to/models/finetuned-wav2vec2
python manage.py runserver
```

#### Option B: Update settings.py

```python
# In asr_platform/settings.py
ASR_MODEL_NAME = "models/finetuned-wav2vec2"  # Relative path
# OR
ASR_MODEL_NAME = "/absolute/path/to/models/finetuned-wav2vec2"  # Absolute path
```

## Training Parameters

### Recommended Settings

- **Epochs**: 3-5 (more epochs = better accuracy but longer training)
- **Batch Size**: 
  - GPU: 8-16
  - CPU: 2-4
- **Learning Rate**: 3e-4 (default, usually works well)

### Advanced Options

```bash
python manage.py finetune_asr \
    --dataset-path /path/to/LibriSpeech \
    --output-dir models/finetuned-wav2vec2 \
    --epochs 5 \
    --batch-size 16 \
    --learning-rate 1e-4 \
    --max-steps 10000  # Override epochs with step limit
```

## Expected Training Time

- **CPU**: ~24-48 hours for 3 epochs
- **GPU (NVIDIA)**: ~2-4 hours for 3 epochs
- **GPU (Apple Silicon M1/M2)**: ~4-8 hours for 3 epochs

## Model Output

After training, you'll have:

```
models/finetuned-wav2vec2/
  ├── config.json
  ├── preprocessor_config.json
  ├── pytorch_model.bin
  ├── tokenizer_config.json
  ├── vocab.json
  └── runs/  (TensorBoard logs)
```

## Verification

To verify the fine-tuned model works:

```python
from ai_services.asr import ASREngine
from pathlib import Path

# Load fine-tuned model
asr = ASREngine(model_name="models/finetuned-wav2vec2")
result = asr.transcribe(Path("path/to/test/audio.webm"))
print(result)
```

## Troubleshooting

### Out of Memory Errors

- Reduce `--batch-size` (try 4 or 2)
- Use `--max-steps` to limit training
- Enable gradient accumulation (already set to 2)

### Slow Training

- Use GPU if available (automatically detected)
- Reduce dataset size for testing (use `--max-steps 1000`)
- Use smaller batch size if memory constrained

### Dataset Not Found

- Verify the path to LibriSpeech directory
- Ensure the directory contains `dev-clean/` subdirectory
- Check file permissions

## Next Steps

1. **Evaluate the model**: Test on your own audio samples
2. **Compare performance**: Compare WER before/after fine-tuning
3. **Further fine-tuning**: Fine-tune on domain-specific data if needed
4. **Deploy**: Update production settings to use fine-tuned model

## Additional Resources

- [Wav2Vec2 Documentation](https://huggingface.co/docs/transformers/model_doc/wav2vec2)
- [LibriSpeech Dataset](http://www.openslr.org/12/)
- [HuggingFace Fine-tuning Guide](https://huggingface.co/docs/transformers/training)

