"""ClimaSense Agentic Core — Multi-step reasoning with Gemma 4 native function calling.

Dual-model architecture:
- Gemma 4 E4B: Audio transcription (farmer voice queries)
- Gemma 4 31B: Reasoning, vision, function calling (9 tools)

Single-model mode also supported (E4B handles everything).
"""

import gc
import json
import logging
import re
from pathlib import Path

import numpy as np
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText

from climasense.tools import TOOL_REGISTRY, ALL_TOOLS

logger = logging.getLogger(__name__)

# Bounding boxes for the WFP-supported countries (the only ones the market tool
# can price). Used to resolve a (lat, lon) into a country name so the model
# passes the right `country` arg to get_commodity_prices.
# Boxes are deliberately loose; overlap is rare for these regions.
_COUNTRY_BBOXES = [
    # (name, lat_min, lat_max, lon_min, lon_max)
    ("kenya",         -4.7,   5.5,   33.9,  41.9),
    ("uganda",        -1.5,   4.3,   29.5,  35.0),
    ("tanzania",     -11.7,  -1.0,   29.3,  40.5),
    ("rwanda",        -2.9,  -1.0,   28.8,  30.9),
    ("ethiopia",       3.4,  14.9,   33.0,  48.0),
    ("somalia",       -1.7,  12.0,   40.9,  51.4),
    ("south sudan",    3.5,  12.2,   24.1,  35.9),
    ("malawi",       -17.1,  -9.4,   32.7,  35.9),
    ("mozambique",   -26.9, -10.5,   30.2,  40.9),
    ("zambia",       -18.1,  -8.2,   21.9,  33.7),
    ("zimbabwe",     -22.4, -15.6,   25.2,  33.1),
    ("madagascar",   -25.6, -11.9,   43.2,  50.5),
    ("nigeria",        4.2,  13.9,    2.7,  14.7),
    ("ghana",          4.7,  11.2,   -3.3,   1.2),
    ("cameroon",       1.7,  13.1,    8.5,  16.2),
    ("senegal",       12.3,  16.7,  -17.5, -11.4),
    ("mali",          10.2,  25.0,  -12.3,   4.3),
    ("niger",         11.7,  23.5,    0.2,  16.0),
    ("burkina faso",   9.4,  15.1,   -5.5,   2.4),
    ("democratic republic of congo", -13.5, 5.4, 12.0, 31.3),
    ("india",          6.5,  35.7,   68.1,  97.4),
    ("bangladesh",    20.6,  26.6,   88.0,  92.7),
    ("nepal",         26.3,  30.4,   80.0,  88.2),
    ("pakistan",      23.6,  37.1,   60.9,  77.0),
]


def _country_from_latlon(lat: float, lon: float) -> str | None:
    """Return the WFP country containing (lat, lon), or None if outside coverage."""
    for name, lat_min, lat_max, lon_min, lon_max in _COUNTRY_BBOXES:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return name
    return None

SYSTEM_PROMPT = """\
You are ClimaSense, an expert agricultural advisor for smallholder farmers. \
You help farmers make informed decisions about planting, crop protection, and \
market timing by analyzing weather, soil, crop health, and market data.

Your role:
- Analyze the farmer's situation using available tools
- Provide clear, actionable advice in simple language
- Prioritize urgent risks (frost, disease outbreaks, flooding)
- Consider the farmer's local context (climate zone, available resources)
- Always explain WHY you recommend an action, not just what to do
- When unsure, recommend the farmer consult their local agricultural extension officer

You have access to tools for weather forecasting, crop disease diagnosis, \
soil analysis, market prices, planting advisories, satellite NDVI, and \
post-harvest risk. Use them proactively.

DECISIVENESS RULES (very important):
- If the farmer mentions weather, rain, planting timing, soil, market \
prices, harvest, drying, storage, or a crop disease, immediately call the \
relevant tool. DO NOT ask for clarification first.
- If the farmer's question is vague, still make at least one tool call \
using their location, then ask one targeted follow-up only if truly needed.
- When tools return uncertain results, give the most likely answer and \
explain your confidence — never refuse to answer.

VISION RULES (very important):
- If an image is attached, you can see it clearly. Describe what you \
visually observe (colour, lesion shape, distribution, leaf stage) and use \
that observation as the symptoms argument when calling diagnose_crop_disease.
- NEVER write phrases like "I cannot see the image", "please send a \
clearer photo", "since I cannot see", "I cannot give a definitive answer", \
or "please describe the symptoms". You have full vision capability — use it.
- Pick the single most likely diagnosis from the tool result and commit to \
it. Do not list "if it's X… if it's Y… if it's Z…" — that is not helpful \
to a farmer who needs one answer.

CRITICAL LANGUAGE RULE: Always respond in the SAME language as the user's most \
recent message. If the user wrote in English, respond in English. If French, French. \
If Swahili, Swahili. Do not switch languages unless the user explicitly asks. \
Names like "Amina" or "Maria" are NOT a language signal — only the words of the question are.

Keep advice practical and achievable with limited resources.

When a tool result contains a data_source, source, or _cache_meta field, \
communicate the provenance and freshness to the farmer in plain language. \
Specifically: name the upstream source (e.g. "Sentinel-2 satellite image from \
3 days ago", "Open-Meteo forecast", "ISRIC soil grid, nearest valid pixel 800 m \
away", "cached 2 days ago — offline"). Never hide a fallback or a stale-cache \
flag. Trust is more valuable than appearing precise."""


class ClimaSenseAgent:
    """Agentic reasoning engine using Gemma 4 native function calling.

    Supports two modes:
    1. Single-model: One model handles everything (text, vision, audio, tools)
    2. Dual-model: E4B for audio → 31B for reasoning/vision/tools
    """

    def __init__(
        self,
        model_id: str = "google/gemma-4-31B-it",
        audio_model_id: str | None = "google/gemma-4-E4B-it",
        device: str = "auto",
        audio_device: str | None = None,
        max_turns: int = 5,
        enable_thinking: bool = True,
    ):
        """Initialize the agent.

        Args:
            model_id: Primary model for reasoning/vision/tools.
            audio_model_id: Audio model for voice transcription. None = use primary model.
            device: Device for primary model ('auto', 'cuda:0', etc.).
            audio_device: Device for audio model. None = auto-select.
            max_turns: Max reasoning turns before forcing a response.
            enable_thinking: Enable Gemma 4 thinking mode.
        """
        self.model_id = model_id
        self.audio_model_id = audio_model_id
        self.max_turns = max_turns
        self.enable_thinking = enable_thinking
        self.device = device
        self.audio_device = audio_device

        # Primary model (reasoning)
        self.model = None
        self.processor = None

        # Audio model (optional, separate)
        self.audio_model = None
        self.audio_processor = None

    def load_model(self):
        """Load the primary Gemma 4 model with OOM protection."""
        if self.model is not None:
            return

        logger.info("Loading primary model: %s", self.model_id)

        # On small GPUs (Kaggle T4 = 16 GB, sometimes only 14.5 GB free), the
        # bfloat16 model + multi-tool KV cache OOMs. Drop to 4-bit nf4 there.
        kwargs = {"device_map": self.device}
        if torch.cuda.is_available():
            total_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            if total_gb < 20:
                # bitsandbytes runtime must be importable, not just BitsAndBytesConfig
                try:
                    import bitsandbytes  # noqa: F401
                    from transformers import BitsAndBytesConfig
                    kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.bfloat16,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True,
                    )
                    print(f"[ClimaSense] Small GPU ({total_gb:.1f} GB) detected — loading in 4-bit nf4")
                    logger.info("Small GPU (%.1f GB) — loading in 4-bit nf4", total_gb)
                except ImportError as e:
                    kwargs["dtype"] = torch.bfloat16
                    print(f"[ClimaSense] WARNING: bitsandbytes unavailable ({e}); falling back to bfloat16 — expect OOM on T4")
                    logger.warning("bitsandbytes unavailable; falling back to bfloat16")
            else:
                kwargs["dtype"] = torch.bfloat16
                print(f"[ClimaSense] GPU {total_gb:.1f} GB — loading in bfloat16")
        else:
            kwargs["dtype"] = torch.bfloat16

        try:
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            self.model = AutoModelForImageTextToText.from_pretrained(self.model_id, **kwargs)
            logger.info("Primary model loaded successfully")
        except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
            logger.error("OOM loading model: %s", e)
            torch.cuda.empty_cache()
            gc.collect()
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id,
                **kwargs,
                attn_implementation="sdpa",
                low_cpu_mem_usage=True,
            )
            self.processor = AutoProcessor.from_pretrained(self.model_id)

    def load_audio_model(self):
        """Load the audio model (E4B) for voice transcription."""
        if self.audio_model is not None:
            return

        audio_id = self.audio_model_id or self.model_id

        # If same model as primary, reuse it
        if audio_id == self.model_id and self.model is not None:
            self.audio_model = self.model
            self.audio_processor = self.processor
            logger.info("Reusing primary model for audio")
            return

        logger.info("Loading audio model: %s", audio_id)
        device = self.audio_device or "auto"
        self.audio_processor = AutoProcessor.from_pretrained(audio_id)
        self.audio_model = AutoModelForImageTextToText.from_pretrained(
            audio_id,
            dtype=torch.bfloat16,
            device_map=device,
        )
        logger.info("Audio model loaded successfully")

    def transcribe_audio(
        self,
        audio_input,
        sample_rate: int = 16000,
    ) -> str:
        """Transcribe farmer's voice query using E4B.

        Args:
            audio_input: Audio as numpy array, file path, or torch.Tensor.
            sample_rate: Audio sample rate (default 16000).

        Returns:
            Transcribed text.
        """
        self.load_audio_model()

        # Load from file if needed
        if isinstance(audio_input, (str, Path)):
            from climasense.multimodal.audio import load_audio
            audio_array, sample_rate = load_audio(audio_input)
        elif isinstance(audio_input, torch.Tensor):
            audio_array = audio_input.cpu().numpy()
        else:
            audio_array = np.asarray(audio_input, dtype=np.float32)

        prompt = (
            "Listen to this farmer's voice query. "
            "Transcribe exactly what they said, then identify the language."
        )
        messages = [
            {"role": "user", "content": [
                {"type": "audio", "audio": audio_array},
                {"type": "text", "text": prompt},
            ]}
        ]

        text = self.audio_processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        inputs = self.audio_processor(
            text=text,
            audio=[audio_array],
            sampling_rate=sample_rate,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.audio_model.device) if hasattr(v, "to") else v for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.audio_model.generate(**inputs, max_new_tokens=512, do_sample=False)

        new_tokens = outputs[0, inputs["input_ids"].shape[1]:]
        return self.audio_processor.decode(new_tokens, skip_special_tokens=True)

    def _build_messages(self, user_query: str, images: list | None = None) -> list[dict]:
        """Build initial message list with system prompt and user query.

        When images are present, every message must use list-of-content-blocks
        format (not plain strings) — apply_chat_template iterates content
        looking for image/video blocks and crashes on a bare string.
        """
        if images:
            sys_content = [{"type": "text", "text": SYSTEM_PROMPT}]
        else:
            sys_content = SYSTEM_PROMPT
        messages = [{"role": "system", "content": sys_content}]

        content = []
        if images:
            for img in images:
                content.append({"type": "image", "image": img})
        content.append({"type": "text", "text": user_query})

        messages.append({"role": "user", "content": content})
        return messages

    def _vram_aware_max_new_tokens(self) -> int:
        """Pick a generation budget that fits the current GPU.

        T4 class (≤16 GB) is tight: after E4B weights and a multi-tool
        KV cache, 2048 new tokens reliably OOMs. With E4B in 4-bit nf4
        (~3 GB) plus _compact_tool_result trimming the KV cache, 768 is
        the largest budget that survives a 4-tool chain on Kaggle T4
        without truncating final advisories mid-sentence.
        """
        if not torch.cuda.is_available():
            return 1024
        total_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        if total_gb < 20:
            return 768
        if total_gb < 40:
            return 1024
        return 2048

    def _generate(
        self,
        text_prompt: str,
        images: list | None = None,
        messages_for_vision: list | None = None,
    ) -> str:
        """Run a single generation step with OOM protection.

        For the first turn with images we route through apply_chat_template
        with tokenize=True so the processor properly aligns the image
        placeholder tokens with the pixel features. For text-only turns we
        use the cached string prompt directly (faster, supports tool-result
        appending).
        """
        if images and messages_for_vision is not None:
            inputs = self.processor.apply_chat_template(
                messages_for_vision,
                add_generation_prompt=True,
                tools=ALL_TOOLS,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ).to(self.model.device)
        elif images:
            inputs = self.processor(
                text=text_prompt, images=images, return_tensors="pt"
            ).to(self.model.device)
        else:
            inputs = self.processor(text=text_prompt, return_tensors="pt").to(self.model.device)

        try:
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self._vram_aware_max_new_tokens(),
                    do_sample=False,
                )
            new_tokens = outputs[0, inputs["input_ids"].shape[1]:]
            decoded = self.processor.decode(new_tokens, skip_special_tokens=False)
            del inputs, outputs, new_tokens
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return decoded

        except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
            logger.warning("OOM during generation: %s", e)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            return json.dumps({"error": "Model ran out of memory. Try a shorter query or simpler request."})

    @staticmethod
    def _compact_tool_result(result: dict) -> str:
        """Trim verbose fields from tool results to keep KV cache small on T4-class GPUs.

        Drops debug/meta keys and known-large arrays (e.g. planting_advisory's 12-month
        breakdown, weather hourly arrays) before re-serialising. The full result is still
        returned to the caller via tool_calls_log; only the prompt-injected copy is compacted.
        """
        if not isinstance(result, dict):
            return json.dumps(result)
        slim = {k: v for k, v in result.items() if not k.startswith("_")}
        # Known verbose fields — drop them entirely
        for verbose_key in ("monthly_analysis", "hourly", "markets_reporting", "additional_possibilities"):
            slim.pop(verbose_key, None)
        # Truncate any remaining list to 7 entries max (covers 7-day forecasts)
        for k, v in list(slim.items()):
            if isinstance(v, list) and len(v) > 7:
                slim[k] = v[:7] + [f"... ({len(v) - 7} more truncated)"]
        out = json.dumps(slim, default=str)
        # Hard cap as final defense — 3000 chars ≈ ~1000 tokens per tool result
        if len(out) > 3000:
            out = out[:3000] + '..."}'
        return out

    def _parse_tool_calls(self, response: str) -> list[dict]:
        """Parse Gemma 4 tool call format from response.

        Gemma 4 uses: <|tool_call>call:func{key:<|"|>str_val<|"|>,key2:num}<tool_call|>
        """
        tool_calls = []
        pattern = r'<\|tool_call>call:(\w+)\{(.*?)\}<tool_call\|>'
        for match in re.finditer(pattern, response, re.DOTALL):
            func_name = match.group(1)
            args_str = match.group(2)

            args = {}
            for pair in re.finditer(r'(\w+):(?:<\|"\|>(.*?)<\|"\|>|([^,}]+))', args_str):
                key = pair.group(1)
                val = pair.group(2) if pair.group(2) is not None else pair.group(3)
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
                args[key] = val
            tool_calls.append({"name": func_name, "arguments": args})

        return tool_calls

    def _execute_tool(self, tool_call: dict) -> dict:
        """Execute a tool call and return the result."""
        func_name = tool_call["name"]
        args = tool_call["arguments"]

        if func_name not in TOOL_REGISTRY:
            return {"error": f"Unknown tool: {func_name}"}

        try:
            result = TOOL_REGISTRY[func_name](**args)
            return result
        except Exception as e:
            logger.error("Tool %s failed: %s", func_name, e)
            return {"error": f"Tool {func_name} failed: {str(e)}"}

    def _extract_text_response(self, response: str) -> str:
        """Extract the final text response, removing thinking and tool call tokens."""
        text = re.sub(r'<\|thinking\|>.*?<\|/thinking\|>', '', response, flags=re.DOTALL)
        text = re.sub(r'<\|tool_call>.*?<tool_call\|>', '', text, flags=re.DOTALL)
        text = re.sub(r'<\|[^>]+\|>', '', text)
        return text.strip()

    def run(
        self,
        query: str | None = None,
        audio: str | Path | np.ndarray | None = None,
        images: list | None = None,
        location: tuple[float, float] | None = None,
        tts: bool = False,
        tts_output_path: str | Path | None = None,
        tts_lang: str | None = None,
    ) -> dict:
        """Run the full agentic loop.

        Accepts text, audio, and/or images. If audio is provided,
        it is transcribed first using E4B, then the text query goes
        to the primary model for reasoning.

        Args:
            query: Farmer's text question (optional if audio provided).
            audio: Audio input — file path, numpy array, or tensor.
            images: Optional list of PIL images (crop photos, etc.).
            location: Optional (latitude, longitude) tuple.
            tts: If True, generate audio output from the response.
            tts_output_path: Custom path for TTS audio file. Auto-generated if None.
            tts_lang: Language code for TTS. Auto-detected if None.

        Returns:
            Dictionary with response, tool calls made, transcription (if audio),
            turns, and audio_output_path (if tts=True).
        """
        result_meta = {}

        # Step 1: Handle audio input — transcribe with E4B
        if audio is not None:
            logger.info("Audio input detected — transcribing with audio model")
            transcription = self.transcribe_audio(audio)
            result_meta["audio_transcription"] = transcription
            logger.info("Transcription: %s", transcription[:200])

            # Use transcription as query (append to any existing text query)
            if query:
                query = f"{query}\n\n[Voice transcription]: {transcription}"
            else:
                query = transcription

        if not query:
            return {"error": "No query provided (text or audio required)"}

        def _maybe_add_tts(result: dict) -> dict:
            """Attach TTS audio to result if tts=True."""
            if tts and "response" in result:
                try:
                    from climasense.multimodal.tts import text_to_speech
                    audio_path = text_to_speech(
                        result["response"],
                        output_path=tts_output_path,
                        lang=tts_lang,
                    )
                    result["audio_output_path"] = str(audio_path)
                except Exception as e:
                    logger.warning("TTS generation failed: %s", e)
                    result["tts_error"] = str(e)
            return result

        # Step 2: Run the reasoning loop with primary model
        self.load_model()

        if location:
            country = _country_from_latlon(location[0], location[1])
            country_hint = f", country={country}" if country else ""
            query = f"[Location: {location[0]:.4f}N, {location[1]:.4f}E{country_hint}] {query}"

        messages = self._build_messages(query, images)
        tool_calls_log = []

        template_kwargs = {"add_generation_prompt": True, "tools": ALL_TOOLS}
        prompt = self.processor.apply_chat_template(
            messages, tokenize=False, **template_kwargs,
        )

        for turn in range(self.max_turns):
            # Pass images on every turn. Each model.generate() call is
            # stateless — without re-passing the image, by turn 1 the model
            # has zero memory of it and starts saying "I cannot see".
            # On turn 0 we use the messages-based path for proper image-token
            # alignment; on subsequent turns the prompt string still contains
            # the <image> placeholders so processor(text, images) can re-bind.
            turn_messages = messages if turn == 0 else None
            response = self._generate(
                prompt, images=images, messages_for_vision=turn_messages,
            )
            parsed_calls = self._parse_tool_calls(response)

            if not parsed_calls:
                final_text = self._extract_text_response(response)
                return _maybe_add_tts({
                    **result_meta,
                    "response": final_text,
                    "tool_calls": tool_calls_log,
                    "turns": turn + 1,
                })

            for tc in parsed_calls:
                result = self._execute_tool(tc)
                tool_calls_log.append({"tool": tc["name"], "args": tc["arguments"], "result": result})
                logger.info("Tool %s called with %s", tc["name"], tc["arguments"])

            prompt += response.rstrip()
            for log_entry in tool_calls_log[-len(parsed_calls):]:
                prompt += f"call:response:{log_entry['tool']}{self._compact_tool_result(log_entry['result'])}<tool_response|>"
            prompt += "\n<|turn>model\n"

        final_response = self._generate(prompt)
        return _maybe_add_tts({
            **result_meta,
            "response": self._extract_text_response(final_response),
            "tool_calls": tool_calls_log,
            "turns": self.max_turns,
            "warning": "Maximum reasoning turns reached",
        })


def run_demo():
    """Quick demo of the agent."""
    agent = ClimaSenseAgent()

    scenarios = [
        {
            "query": "My tomato leaves have dark brown spots with rings. What should I do?",
            "location": (-1.2921, 36.8219),
        },
        {
            "query": "When should I plant maize this season? And what's the price looking like?",
            "location": (9.0820, 8.6753),
        },
        {
            "query": "There's been no rain for 3 weeks and my cassava is wilting. Help!",
            "location": (-6.7924, 39.2083),
        },
    ]

    for i, scenario in enumerate(scenarios):
        print(f"\n{'='*60}")
        print(f"Scenario {i+1}: {scenario['query']}")
        print(f"Location: {scenario['location']}")
        print(f"{'='*60}")

        result = agent.run(
            query=scenario["query"],
            location=scenario["location"],
        )

        print(f"\nResponse:\n{result['response']}")
        print(f"\nTools used: {[tc['tool'] for tc in result['tool_calls']]}")
        print(f"Turns: {result['turns']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_demo()
