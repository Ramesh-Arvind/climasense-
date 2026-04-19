"""Fine-tune Gemma 4 E4B on PlantVillage crop disease images using LoRA.

Target: Go from 20% zero-shot → 90%+ accuracy on disease classification.
Uses PEFT LoRA on the language model layers for efficient fine-tuning.
"""

import gc
import json
import logging
import os
import random
from pathlib import Path

import torch
from PIL import Image
from peft import LoraConfig, get_peft_model, TaskType
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
from transformers import AutoProcessor, AutoModelForImageTextToText

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Disease class mapping
DISEASE_CLASSES = {
    "Tomato_Early_blight": "Early Blight (Alternaria solani)",
    "Tomato_Late_blight": "Late Blight (Phytophthora infestans)",
    "Tomato_Bacterial_spot": "Bacterial Spot",
    "Tomato_Leaf_Mold": "Leaf Mold",
    "Tomato_Septoria_leaf_spot": "Septoria Leaf Spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "Spider Mites",
    "Tomato__Target_Spot": "Target Spot",
    "Tomato__Tomato_mosaic_virus": "Tomato Mosaic Virus",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "Yellow Leaf Curl Virus",
    "Tomato_healthy": "Healthy",
    "Potato___Early_blight": "Potato Early Blight (Alternaria solani)",
    "Potato___Late_blight": "Potato Late Blight (Phytophthora infestans)",
    "Potato___healthy": "Healthy Potato",
    "Pepper__bell___Bacterial_spot": "Pepper Bacterial Spot",
    "Pepper__bell___healthy": "Healthy Pepper",
}

DIAGNOSIS_PROMPT = "You are an expert crop disease diagnostician. Examine this leaf image. What disease do you see? Give the disease name and a one-sentence explanation."


class PlantVillageDataset(Dataset):
    """PlantVillage dataset for vision fine-tuning."""

    def __init__(self, data_dir: str, processor, max_per_class: int = 200, split: str = "train", val_ratio: float = 0.1):
        self.processor = processor
        self.samples = []

        for folder_name, label in DISEASE_CLASSES.items():
            folder_path = Path(data_dir) / folder_name
            if not folder_path.exists():
                logger.warning("Missing class folder: %s", folder_path)
                continue

            images = sorted(os.listdir(folder_path))
            random.seed(42)
            random.shuffle(images)

            # Split into train/val
            split_idx = int(len(images) * (1 - val_ratio))
            if split == "train":
                images = images[:split_idx]
            else:
                images = images[split_idx:]

            # Cap per class
            images = images[:max_per_class]

            for img_name in images:
                self.samples.append({
                    "image_path": str(folder_path / img_name),
                    "label": label,
                    "folder": folder_name,
                })

        random.seed(42)
        random.shuffle(self.samples)
        logger.info("Loaded %d %s samples from %d classes", len(self.samples), split, len(DISEASE_CLASSES))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        img = Image.open(sample["image_path"]).convert("RGB")

        # Build the training conversation
        messages = [
            {"role": "user", "content": [
                {"type": "image", "image": img},
                {"type": "text", "text": DIAGNOSIS_PROMPT},
            ]},
            {"role": "assistant", "content": [
                {"type": "text", "text": f"{sample['label']}. This leaf shows characteristic symptoms of this condition."},
            ]},
        ]

        # Tokenize — don't truncate (image tokens need full space)
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False,
        )
        inputs = self.processor(
            text=text,
            images=[img],
            return_tensors="pt",
        )

        # Squeeze batch dimension
        inputs = {k: v.squeeze(0) if hasattr(v, "squeeze") else v for k, v in inputs.items()}

        # Create labels (mask the input portion, only train on the answer)
        labels = inputs["input_ids"].clone()
        # Find where the assistant response starts (after the last user turn)
        # Simple approach: mask everything before the label text
        label_tokens = self.processor.tokenizer.encode(sample["label"], add_special_tokens=False)
        # Find first occurrence of label tokens in the sequence
        ids = inputs["input_ids"].tolist()
        label_start = -1
        for i in range(len(ids) - len(label_tokens)):
            if ids[i:i+len(label_tokens)] == label_tokens:
                label_start = i
                break
        if label_start > 0:
            labels[:label_start] = -100  # mask input tokens

        inputs["labels"] = labels
        return inputs


def collate_fn(batch):
    """Collate batch items."""
    keys = batch[0].keys()
    result = {}
    for key in keys:
        values = [item[key] for item in batch]
        if isinstance(values[0], torch.Tensor):
            result[key] = torch.stack(values)
        else:
            result[key] = values
    return result


def main():
    data_dir = "/data/home/rnaa/gemma4_hackathon/data/plantvillage/PlantVillage"
    output_dir = "/data/home/rnaa/gemma4_hackathon/models/plantvillage_lora_v2"
    model_id = "google/gemma-4-E4B-it"

    # Training config — v2: upgraded for >80% accuracy target
    max_per_class = 300  # images per class (was 100)
    num_epochs = 8       # was 3
    batch_size = 2
    learning_rate = 1e-4  # lower LR for more stable training with more data
    gradient_accumulation_steps = 8  # effective batch size = 16
    warmup_steps = 50

    os.makedirs(output_dir, exist_ok=True)

    logger.info("Loading model: %s", model_id)
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        dtype=torch.bfloat16,
        device_map="cuda:0",
    )

    # Swap Gemma4ClippableLinear → nn.Linear in vision/audio towers
    # (PEFT doesn't support ClippableLinear)
    from transformers.models.gemma4.modeling_gemma4 import Gemma4ClippableLinear
    replacements = []
    for name, module in model.named_modules():
        if isinstance(module, Gemma4ClippableLinear) and ("vision_tower" in name or "audio_tower" in name):
            replacements.append(name)
    for name in replacements:
        parts = name.split(".")
        parent = model
        for p in parts[:-1]:
            parent = getattr(parent, p)
        setattr(parent, parts[-1], getattr(parent, parts[-1]).linear)
    logger.info("Replaced %d ClippableLinear modules for PEFT compatibility", len(replacements))

    # Freeze vision and audio towers
    for name, param in model.named_parameters():
        if "vision_tower" in name or "audio_tower" in name:
            param.requires_grad = False

    # Configure LoRA on attention + MLP layers — v2: r=32 for more capacity
    lora_config = LoraConfig(
        r=32,
        lora_alpha=64,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load datasets
    train_dataset = PlantVillageDataset(data_dir, processor, max_per_class=max_per_class, split="train")
    val_dataset = PlantVillageDataset(data_dir, processor, max_per_class=30, split="val")

    # Optimizer + scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    total_steps = (len(train_dataset) * num_epochs) // gradient_accumulation_steps
    from torch.optim.lr_scheduler import CosineAnnealingLR
    scheduler = CosineAnnealingLR(optimizer, T_max=total_steps, eta_min=1e-6)

    # Training loop — batch_size=1 (variable-length image token sequences)
    logger.info("Starting training: %d epochs, %d samples, grad_accum=%d, total_steps=%d",
                num_epochs, len(train_dataset), gradient_accumulation_steps, total_steps)

    model.train()
    global_step = 0
    best_loss = float("inf")

    for epoch in range(num_epochs):
        total_loss = 0
        num_samples = 0
        indices = list(range(len(train_dataset)))
        random.shuffle(indices)
        pbar = tqdm(indices, desc=f"Epoch {epoch+1}/{num_epochs}")

        for step, idx in enumerate(pbar):
            try:
                batch = train_dataset[idx]
                batch = {k: v.unsqueeze(0).to(model.device) if hasattr(v, "unsqueeze") else v for k, v in batch.items()}

                outputs = model(**batch)
                loss = outputs.loss / gradient_accumulation_steps
                loss.backward()

                if (step + 1) % gradient_accumulation_steps == 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad()
                    global_step += 1

                total_loss += outputs.loss.item()
                num_samples += 1
                pbar.set_postfix(loss=f"{outputs.loss.item():.4f}", avg=f"{total_loss/num_samples:.4f}")

            except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
                logger.warning("OOM at step %d: %s — skipping", step, e)
                torch.cuda.empty_cache()
                gc.collect()
                optimizer.zero_grad()
                continue

        avg_loss = total_loss / max(num_samples, 1)
        logger.info("Epoch %d: avg_loss=%.4f", epoch + 1, avg_loss)

        # Save checkpoint
        if avg_loss < best_loss:
            best_loss = avg_loss
            model.save_pretrained(output_dir)
            processor.save_pretrained(output_dir)
            logger.info("Saved best model (loss=%.4f) to %s", best_loss, output_dir)

    # Save final
    model.save_pretrained(output_dir)
    logger.info("Training complete. Final model saved to %s", output_dir)

    # Save training metadata
    meta = {
        "model_id": model_id,
        "lora_r": 32,
        "lora_alpha": 64,
        "epochs": num_epochs,
        "max_per_class": max_per_class,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "best_loss": best_loss,
        "num_classes": len(DISEASE_CLASSES),
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
    }
    with open(os.path.join(output_dir, "training_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    main()
