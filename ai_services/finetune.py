"""
Fine-tuning script for Wav2Vec2 ASR model using LibriSpeech dataset.

This module provides functionality to fine-tune the Wav2Vec2 model
on LibriSpeech dev-clean dataset for improved transcription accuracy.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import torch
import numpy as np
from datasets import Dataset, load_dataset
from transformers import (
    AutoFeatureExtractor,
    AutoModelForCTC,
    AutoProcessor,
    Trainer,
    TrainingArguments,
    Wav2Vec2CTCTokenizer,
    Wav2Vec2Processor,
)

try:
    import evaluate
    WER_METRIC_AVAILABLE = True
    load_metric = None
except ImportError:
    try:
        from datasets import load_metric
        WER_METRIC_AVAILABLE = True
        evaluate = None
    except ImportError:
        WER_METRIC_AVAILABLE = False
        evaluate = None
        load_metric = None

logger = logging.getLogger(__name__)


class LibriSpeechFineTuner:
    """
    Fine-tune Wav2Vec2 model on LibriSpeech dataset.
    
    Usage:
        finetuner = LibriSpeechFineTuner(
            base_model="facebook/wav2vec2-base-960h",
            dataset_path="path/to/librispeech",
            output_dir="models/finetuned-wav2vec2"
        )
        finetuner.train()
    """

    def __init__(
        self,
        base_model: str = "facebook/wav2vec2-base-960h",
        dataset_path: Optional[str] = None,
        output_dir: str = "models/finetuned-wav2vec2",
        device: Optional[str] = None,
    ):
        self.base_model = base_model
        self.dataset_path = dataset_path
        self.output_dir = Path(output_dir)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized fine-tuner with base model: {base_model}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Device: {self.device}")

    def load_librispeech_dataset(self, split: str = "dev-clean"):
        """
        Load LibriSpeech dataset.
        
        Args:
            split: Dataset split to use (dev-clean, train-clean-100, etc.)
            
        Returns:
            Dataset object
        """
        if self.dataset_path:
            # Load from local path - need to manually build dataset
            logger.info(f"Loading LibriSpeech from local path: {self.dataset_path}")
            dataset = self._load_local_librispeech(split)
        else:
            # Load from HuggingFace Hub
            logger.info(f"Loading LibriSpeech {split} from HuggingFace Hub")
            dataset = load_dataset("librispeech_asr", split=split)
        
        logger.info(f"Loaded {len(dataset)} samples from {split}")
        return dataset
    
    def _load_local_librispeech(self, split: str):
        """
        Load LibriSpeech dataset from local directory.
        
        LibriSpeech structure:
        LibriSpeech/
          dev-clean/
            {speaker_id}/
              {chapter_id}/
                *.flac (audio files)
                {speaker_id}-{chapter_id}.trans.txt (transcriptions)
        """
        import soundfile as sf
        import glob
        
        dataset_path = Path(self.dataset_path)
        split_path = dataset_path / split
        
        if not split_path.exists():
            raise ValueError(f"Split directory not found: {split_path}")
        
        logger.info(f"Scanning {split_path} for audio files...")
        
        # Find all audio files and their corresponding transcriptions
        audio_files = []
        texts = []
        
        # Get all speaker directories
        speaker_dirs = [d for d in split_path.iterdir() if d.is_dir()]
        
        for speaker_dir in speaker_dirs:
            # Get all chapter directories
            chapter_dirs = [d for d in speaker_dir.iterdir() if d.is_dir()]
            
            for chapter_dir in chapter_dirs:
                # Read transcription file
                trans_file = chapter_dir / f"{speaker_dir.name}-{chapter_dir.name}.trans.txt"
                if not trans_file.exists():
                    logger.warning(f"Transcription file not found: {trans_file}")
                    continue
                
                # Parse transcriptions
                transcriptions = {}
                with open(trans_file, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split(" ", 1)
                        if len(parts) == 2:
                            transcriptions[parts[0]] = parts[1]
                
                # Find all audio files in this chapter
                audio_paths = sorted(chapter_dir.glob("*.flac"))
                
                for audio_path in audio_paths:
                    # Get corresponding transcription
                    audio_id = audio_path.stem
                    if audio_id in transcriptions:
                        audio_files.append(str(audio_path))
                        texts.append(transcriptions[audio_id])
        
        logger.info(f"Found {len(audio_files)} audio-text pairs")
        
        # Create dataset from lists
        def load_audio(file_path):
            audio_data, sample_rate = sf.read(file_path)
            return {
                "array": audio_data,
                "sampling_rate": sample_rate,
            }
        
        # Build dataset dictionary
        dataset_dict = {
            "audio": [load_audio(f) for f in audio_files],
            "text": texts,
        }
        
        # Create Dataset from dict
        dataset = Dataset.from_dict(dataset_dict)
        
        return dataset

    def prepare_dataset(self, dataset: Dataset, processor: Wav2Vec2Processor):
        """
        Prepare dataset for training by processing audio and text.
        
        Args:
            dataset: LibriSpeech dataset
            processor: Wav2Vec2 processor for feature extraction
            
        Returns:
            Processed dataset ready for training
        """
        def prepare_example(example):
            # Process audio
            audio = example["audio"]
            inputs = processor(
                audio["array"],
                sampling_rate=audio["sampling_rate"],
                return_tensors="pt",
            )
            
            # Process labels (text transcription)
            # Use tokenizer directly for text encoding
            labels = processor.tokenizer(
                example["text"],
                return_tensors="pt",
                padding=False,  # Don't pad here, will pad in collator
            ).input_ids
            
            # Convert to list for dataset compatibility
            # labels is a tensor with shape [1, seq_len]
            if isinstance(labels, torch.Tensor):
                # Squeeze batch dimension and convert to list
                labels_list = labels.squeeze(0).tolist()
            elif isinstance(labels, list):
                # If already a list, flatten if nested
                labels_list = labels[0] if len(labels) > 0 and isinstance(labels[0], list) else labels
            else:
                # Fallback: convert to list
                labels_list = list(labels) if hasattr(labels, '__iter__') else [int(labels)]
            
            return {
                "input_values": inputs.input_values[0].tolist(),
                "labels": labels_list,
            }

        logger.info("Preparing dataset for training...")
        dataset = dataset.map(
            prepare_example,
            remove_columns=dataset.column_names,
            num_proc=4,
        )
        
        return dataset

    def train(
        self,
        num_epochs: int = 3,
        batch_size: int = 8,
        learning_rate: float = 3e-4,
        warmup_steps: int = 500,
        max_steps: Optional[int] = None,
        save_steps: int = 500,
        eval_steps: int = 500,
        logging_steps: int = 100,
    ):
        """
        Fine-tune the Wav2Vec2 model.
        
        Args:
            num_epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate for training
            warmup_steps: Number of warmup steps
            max_steps: Maximum training steps (overrides num_epochs if set)
            save_steps: Steps between model checkpoints
            eval_steps: Steps between evaluations
            logging_steps: Steps between logging
        """
        logger.info("Starting fine-tuning process...")
        
        # Load processor and model
        logger.info("Loading processor and model...")
        processor = AutoProcessor.from_pretrained(self.base_model)
        model = AutoModelForCTC.from_pretrained(
            self.base_model,
            ctc_loss_reduction="mean",
            pad_token_id=processor.tokenizer.pad_token_id,
        )
        
        # Move model to device
        model.to(self.device)
        
        # Load and prepare dataset
        logger.info("Loading LibriSpeech dataset...")
        dataset = self.load_librispeech_dataset()
        
        # Split dataset (80% train, 20% validation)
        dataset = dataset.train_test_split(test_size=0.2, seed=42)
        train_dataset = dataset["train"]
        eval_dataset = dataset["test"]
        
        logger.info(f"Train samples: {len(train_dataset)}")
        logger.info(f"Validation samples: {len(eval_dataset)}")
        
        # Prepare datasets
        train_dataset = self.prepare_dataset(train_dataset, processor)
        eval_dataset = self.prepare_dataset(eval_dataset, processor)
        
        # Set up data collator
        def data_collator(features):
            # Pad input_values and labels
            input_values = [f["input_values"] for f in features]
            labels = [f["labels"] for f in features]
            
            # Pad sequences
            batch = processor.pad(
                {"input_values": input_values},
                padding=True,
                return_tensors="pt",
            )
            
            # Pad labels
            from torch.nn.utils.rnn import pad_sequence
            labels_tensor = pad_sequence(
                [torch.tensor(l) for l in labels],
                batch_first=True,
                padding_value=processor.tokenizer.pad_token_id,
            )
            batch["labels"] = labels_tensor
            
            return batch
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            gradient_accumulation_steps=2,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            max_steps=max_steps,
            logging_steps=logging_steps,
            eval_steps=eval_steps,
            save_steps=save_steps,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="wer",
            greater_is_better=False,
            push_to_hub=False,
            report_to="tensorboard",
        )
        
        # Set up evaluation metrics
        if WER_METRIC_AVAILABLE:
            if evaluate is not None:
                wer_metric = evaluate.load("wer")
            elif load_metric is not None:
                wer_metric = load_metric("wer")
            else:
                wer_metric = None
        else:
            wer_metric = None
        
        def compute_metrics(pred):
            if wer_metric is None:
                return {}
            
            pred_logits = pred.predictions
            pred_ids = np.argmax(pred_logits, axis=-1)
            
            # Replace -100 with pad_token_id
            label_ids = pred.label_ids.copy()
            label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
            
            pred_str = processor.batch_decode(pred_ids)
            label_str = processor.batch_decode(label_ids, group_tokens=False)
            
            wer = wer_metric.compute(predictions=pred_str, references=label_str)
            return {"wer": wer}
        
        # Initialize trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=processor.feature_extractor,
            compute_metrics=compute_metrics,
        )
        
        # Train
        logger.info("Starting training...")
        trainer.train()
        
        # Save final model
        logger.info(f"Saving fine-tuned model to {self.output_dir}")
        trainer.save_model()
        processor.save_pretrained(self.output_dir)
        
        # Evaluate
        logger.info("Running final evaluation...")
        eval_results = trainer.evaluate()
        logger.info(f"Final WER: {eval_results.get('eval_wer', 'N/A')}")
        
        logger.info("Fine-tuning completed successfully!")
        return str(self.output_dir)


def main():
    """Main entry point for fine-tuning."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tune Wav2Vec2 on LibriSpeech")
    parser.add_argument(
        "--base-model",
        type=str,
        default="facebook/wav2vec2-base-960h",
        help="Base model to fine-tune",
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=None,
        help="Path to LibriSpeech dataset (if downloaded locally)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/finetuned-wav2vec2",
        help="Output directory for fine-tuned model",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Training batch size",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=3e-4,
        help="Learning rate",
    )
    
    args = parser.parse_args()
    
    finetuner = LibriSpeechFineTuner(
        base_model=args.base_model,
        dataset_path=args.dataset_path,
        output_dir=args.output_dir,
    )
    
    finetuner.train(
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )


if __name__ == "__main__":
    main()

