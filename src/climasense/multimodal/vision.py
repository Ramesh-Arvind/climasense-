"""Crop image analysis using Gemma 4 vision capabilities.

Processes photos taken by farmers to:
1. Diagnose crop diseases from leaf/fruit images
2. Assess growth stage
3. Estimate crop health
4. Analyze satellite imagery for drought/flood detection
"""

import gc
import logging
from pathlib import Path

import torch
from PIL import Image

logger = logging.getLogger(__name__)

CROP_DIAGNOSIS_PROMPT = """\
You are an expert agricultural pathologist. Analyze this image of a crop plant.

Provide:
1. **Crop identification**: What crop is this?
2. **Health assessment**: Is the plant healthy, stressed, or diseased?
3. **Disease/pest identification**: If unhealthy, what specific disease or pest do you see?
   - Describe the visual symptoms you observe
   - Rate confidence: high/medium/low
4. **Severity**: mild/moderate/severe/critical
5. **Recommended action**: What should the farmer do immediately?

Be specific and practical. The farmer may have limited access to agrochemicals.\
"""

GROWTH_STAGE_PROMPT = """\
Analyze this crop image and determine:
1. **Crop type**: What crop is this?
2. **Growth stage**: germination / vegetative / flowering / fruiting / maturation
3. **Days since planting estimate**: Approximate age of the crop
4. **Health indicators**: Color, vigor, uniformity
5. **Management recommendation**: What the farmer should focus on at this stage\
"""

SATELLITE_ANALYSIS_PROMPT = """\
Analyze this satellite or aerial image of agricultural land.

Assess:
1. **Vegetation health**: NDVI-like assessment (green = healthy, brown = stressed)
2. **Water status**: Signs of flooding, waterlogging, or drought
3. **Land use**: Active cultivation, fallow, mixed cropping patterns
4. **Risk indicators**: Erosion, deforestation, urban encroachment
5. **Recommendation**: Actions based on observed conditions\
"""


def analyze_crop_image(
    image_path: str | Path,
    processor,
    model,
    analysis_type: str = "diagnosis",
) -> dict:
    """Analyze a crop image using Gemma 4 vision.

    Args:
        image_path: Path to the crop image.
        processor: Loaded Gemma 4 processor.
        model: Loaded Gemma 4 model.
        analysis_type: One of 'diagnosis', 'growth_stage', 'satellite'.

    Returns:
        Dictionary with analysis results.
    """
    prompts = {
        "diagnosis": CROP_DIAGNOSIS_PROMPT,
        "growth_stage": GROWTH_STAGE_PROMPT,
        "satellite": SATELLITE_ANALYSIS_PROMPT,
    }
    prompt = prompts.get(analysis_type, CROP_DIAGNOSIS_PROMPT)

    image = Image.open(image_path).convert("RGB")
    # Resize if too large to prevent OOM
    max_dim = 1024
    if max(image.size) > max_dim:
        ratio = max_dim / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        image = image.resize(new_size, Image.LANCZOS)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    try:
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            return_tensors="pt",
            return_dict=True,
            add_generation_prompt=True,
        )
        inputs = inputs.to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.0,
                do_sample=False,
            )

        new_tokens = outputs[0, inputs["input_ids"].shape[1]:]
        response = processor.decode(new_tokens, skip_special_tokens=True)

        return {
            "analysis_type": analysis_type,
            "image": str(image_path),
            "result": response,
        }

    except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
        logger.warning("OOM during image analysis: %s", e)
        torch.cuda.empty_cache()
        gc.collect()
        return {
            "analysis_type": analysis_type,
            "image": str(image_path),
            "error": "Image analysis failed due to memory constraints. Try a smaller image.",
        }
