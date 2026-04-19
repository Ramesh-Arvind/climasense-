"""Benchmark LoRA v2 adapter on PlantVillage val split.

Loads E4B + models/plantvillage_lora_v2 adapter, runs inference on the
same validation slice the training script used (seed=42, 30 per class),
and reports overall + per-class accuracy. Target: >80%.
"""
from __future__ import annotations

import json
import logging
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import torch
from peft import PeftModel
from PIL import Image
from tqdm import tqdm
from transformers import AutoModelForImageTextToText, AutoProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))
from finetune_vision import DISEASE_CLASSES, DIAGNOSIS_PROMPT  # noqa: E402

BASE_MODEL = "google/gemma-4-E4B-it"
ADAPTER_DIR = "/data/home/rnaa/gemma4_hackathon/models/plantvillage_lora_v2"
DATA_DIR = "/data/home/rnaa/gemma4_hackathon/data/plantvillage/PlantVillage"
OUT_JSON = "/data/home/rnaa/gemma4_hackathon/logs/lora_v2_bench.json"
MAX_PER_CLASS = 30
VAL_RATIO = 0.1


def load_val_split():
    """Mirror PlantVillageDataset's val split exactly."""
    samples = []
    for folder_name, label in DISEASE_CLASSES.items():
        folder_path = Path(DATA_DIR) / folder_name
        if not folder_path.exists():
            logger.warning("Missing class folder: %s", folder_path)
            continue
        images = sorted(os.listdir(folder_path))
        random.seed(42)
        random.shuffle(images)
        split_idx = int(len(images) * (1 - VAL_RATIO))
        val_images = images[split_idx:][:MAX_PER_CLASS]
        for img_name in val_images:
            samples.append({
                "image_path": str(folder_path / img_name),
                "label": label,
                "folder": folder_name,
            })
    random.seed(42)
    random.shuffle(samples)
    return samples


def label_in_response(response: str, label: str) -> bool:
    """Lenient match: the response contains the distinguishing term(s) of the label."""
    r = response.lower()
    l = label.lower()

    if l in r:
        return True
    core = l.split(" (")[0]
    if core in r:
        return True
    return False


def main():
    logger.info("Loading base model: %s", BASE_MODEL)
    processor = AutoProcessor.from_pretrained(BASE_MODEL)
    model = AutoModelForImageTextToText.from_pretrained(
        BASE_MODEL,
        dtype=torch.bfloat16,
        device_map="cuda:2",
    )

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
    logger.info("Replaced %d ClippableLinear modules", len(replacements))

    logger.info("Loading adapter: %s", ADAPTER_DIR)
    model = PeftModel.from_pretrained(model, ADAPTER_DIR)
    model.eval()

    samples = load_val_split()
    logger.info("Val samples: %d across %d classes", len(samples), len(DISEASE_CLASSES))

    results = []
    per_class = defaultdict(lambda: {"correct": 0, "total": 0})

    t0 = time.time()
    for sample in tqdm(samples, desc="Benchmarking"):
        img = Image.open(sample["image_path"]).convert("RGB")
        messages = [
            {"role": "user", "content": [
                {"type": "image", "image": img},
                {"type": "text", "text": DIAGNOSIS_PROMPT},
            ]},
        ]
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=text, images=[img], return_tensors="pt").to(model.device)

        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=80, do_sample=False)
        new_tokens = out[0, inputs["input_ids"].shape[1]:]
        response = processor.decode(new_tokens, skip_special_tokens=True).strip()

        correct = label_in_response(response, sample["label"])
        per_class[sample["folder"]]["total"] += 1
        if correct:
            per_class[sample["folder"]]["correct"] += 1
        results.append({
            "folder": sample["folder"],
            "label": sample["label"],
            "response": response[:200],
            "correct": correct,
        })

    elapsed = time.time() - t0
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    accuracy = correct / total if total else 0.0

    per_class_acc = {
        folder: {
            "label": DISEASE_CLASSES[folder],
            "accuracy": round(stats["correct"] / stats["total"], 3) if stats["total"] else 0.0,
            "correct": stats["correct"],
            "total": stats["total"],
        }
        for folder, stats in sorted(per_class.items())
    }

    summary = {
        "base_model": BASE_MODEL,
        "adapter": ADAPTER_DIR,
        "total_samples": total,
        "correct": correct,
        "accuracy": round(accuracy, 3),
        "elapsed_s": round(elapsed, 1),
        "s_per_sample": round(elapsed / total, 2) if total else None,
        "per_class": per_class_acc,
    }

    Path(OUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump({"summary": summary, "samples": results}, f, indent=2)
    logger.info("Saved benchmark: %s", OUT_JSON)

    print("\n" + "=" * 60)
    print(f"LoRA v2 Accuracy: {accuracy:.1%}  ({correct}/{total})")
    print(f"Time: {elapsed:.0f}s  ({elapsed/total:.2f}s/sample)")
    print("=" * 60)
    print("\nPer-class accuracy:")
    for folder, info in sorted(per_class_acc.items(), key=lambda kv: kv[1]["accuracy"], reverse=True):
        print(f"  {info['accuracy']:.1%}  {info['correct']:2d}/{info['total']:2d}  {info['label']}")


if __name__ == "__main__":
    main()
