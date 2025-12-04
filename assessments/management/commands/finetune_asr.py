"""
Django management command to fine-tune ASR model on LibriSpeech dataset.

Usage:
    python manage.py finetune_asr --dataset-path /path/to/librispeech --epochs 3
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import sys

# Add ai_services to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "ai_services"))

from ai_services.finetune import LibriSpeechFineTuner


class Command(BaseCommand):
    help = "Fine-tune Wav2Vec2 ASR model on LibriSpeech dataset"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-model",
            type=str,
            default=settings.ASR_MODEL_NAME,
            help="Base model to fine-tune (default: from settings)",
        )
        parser.add_argument(
            "--dataset-path",
            type=str,
            default=None,
            help="Path to extracted LibriSpeech dev-clean.tar.gz directory",
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
            help="Number of training epochs (default: 3)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=8,
            help="Training batch size (default: 8)",
        )
        parser.add_argument(
            "--learning-rate",
            type=float,
            default=3e-4,
            help="Learning rate (default: 3e-4)",
        )
        parser.add_argument(
            "--max-steps",
            type=int,
            default=None,
            help="Maximum training steps (overrides epochs if set)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting ASR fine-tuning..."))
        self.stdout.write(f"Base model: {options['base_model']}")
        self.stdout.write(f"Output directory: {options['output_dir']}")
        
        if options["dataset_path"]:
            dataset_path = Path(options["dataset_path"])
            if not dataset_path.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"Dataset path does not exist: {dataset_path}"
                    )
                )
                return
            self.stdout.write(f"Using local dataset: {dataset_path}")
        else:
            self.stdout.write("Using HuggingFace Hub dataset (will download if needed)")
        
        try:
            finetuner = LibriSpeechFineTuner(
                base_model=options["base_model"],
                dataset_path=options["dataset_path"],
                output_dir=options["output_dir"],
            )
            
            finetuner.train(
                num_epochs=options["epochs"],
                batch_size=options["batch_size"],
                learning_rate=options["learning_rate"],
                max_steps=options["max_steps"],
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nFine-tuning completed! Model saved to: {options['output_dir']}"
                )
            )
            self.stdout.write(
                f"\nTo use the fine-tuned model, set ASR_MODEL_NAME environment variable:"
            )
            self.stdout.write(
                f"export ASR_MODEL_NAME={Path(options['output_dir']).absolute()}"
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Fine-tuning failed: {e}"))
            raise

