"""Run full ClimaSense evaluation benchmark with the 31B agent model."""

import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/eval_run.log"),
    ],
)
logger = logging.getLogger(__name__)

os.makedirs("logs", exist_ok=True)

# Remove stale checkpoint to start fresh
checkpoint = "logs/checkpoint_eval.json"
if os.path.exists(checkpoint):
    os.remove(checkpoint)
    logger.info("Removed stale checkpoint")

from climasense.agent import ClimaSenseAgent
from climasense.eval.benchmark import run_evaluation, print_results_table

logger.info("Initializing agent with 31B model on GPUs 1+2")
agent = ClimaSenseAgent(
    model_id="google/gemma-4-31B-it",
    audio_model_id=None,  # No audio for eval — text only
    device="auto",
    max_turns=3,
)

logger.info("Starting evaluation (20 scenarios)")
summary = run_evaluation(agent, output_path="logs/eval_results.json", fresh=True)

print_results_table(summary)
logger.info("Evaluation complete!")
