"""Curate 1-2 clean demo images per PlantVillage class into data/demo_crops/.

Selection heuristic: pick images with the median file size within each class.
Extreme sizes are often over/under-exposed; the median tends to be the
'standard-looking' sample. Copies two per class for redundancy.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from finetune_vision import DISEASE_CLASSES

DATA_DIR = Path("/data/home/rnaa/gemma4_hackathon/data/plantvillage/PlantVillage")
OUT_DIR = Path("/data/home/rnaa/gemma4_hackathon/data/demo_crops")
PICKS_PER_CLASS = 2


def slug(label: str) -> str:
    return label.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(".", "")


def pick_class_images(folder: Path, n: int) -> list[Path]:
    """Pick n images with sizes closest to the median of the class."""
    imgs = sorted(folder.glob("*.JPG")) + sorted(folder.glob("*.jpg"))
    if not imgs:
        return []
    sized = [(p, p.stat().st_size) for p in imgs]
    sized.sort(key=lambda x: x[1])
    mid = len(sized) // 2
    lo = max(0, mid - n // 2)
    hi = min(len(sized), lo + n)
    return [p for p, _ in sized[lo:hi]]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for folder_name, label in DISEASE_CLASSES.items():
        src_folder = DATA_DIR / folder_name
        if not src_folder.exists():
            print(f"MISSING  {folder_name}")
            continue
        picks = pick_class_images(src_folder, PICKS_PER_CLASS)
        for i, src in enumerate(picks, start=1):
            dst_name = f"{slug(label)}_{i:02d}{src.suffix.lower()}"
            dst = OUT_DIR / dst_name
            shutil.copy2(src, dst)
            manifest.append({
                "class_folder": folder_name,
                "label": label,
                "source_file": src.name,
                "demo_file": dst_name,
                "size_bytes": src.stat().st_size,
            })
            print(f"  {label:<45}  ->  {dst_name}")

    import json
    with open(OUT_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nCurated {len(manifest)} images across {len(DISEASE_CLASSES)} classes -> {OUT_DIR}")


if __name__ == "__main__":
    main()
