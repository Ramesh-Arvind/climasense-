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
soil analysis, market prices, and planting advisories. Use them proactively \
to give comprehensive advice.

Respond in the farmer's language when possible. Keep advice practical and \
achievable with limited resources.

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
        try:
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id,
                dtype=torch.bfloat16,
                device_map=self.device,
            )
            logger.info("Primary model loaded successfully")
        except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
            logger.error("OOM loading model: %s", e)
            torch.cuda.empty_cache()
            gc.collect()
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id,
                dtype=torch.bfloat16,
                device_map=self.device,
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
        """Build initial message list with system prompt and user query."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        content = []
        if images:
            for img in images:
                content.append({"type": "image", "image": img})
        content.append({"type": "text", "text": user_query})

        messages.append({"role": "user", "content": content})
        return messages

    def _generate(self, text_prompt: str) -> str:
        """Run a single generation step with OOM protection."""
        inputs = self.processor(text=text_prompt, return_tensors="pt").to(self.model.device)

        try:
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=2048,
                    do_sample=False,
                )
            new_tokens = outputs[0, inputs["input_ids"].shape[1]:]
            return self.processor.decode(new_tokens, skip_special_tokens=False)

        except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
            logger.warning("OOM during generation: %s", e)
            torch.cuda.empty_cache()
            gc.collect()
            return json.dumps({"error": "Model ran out of memory. Try a shorter query or simpler request."})

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
            query = f"[Location: {location[0]:.4f}N, {location[1]:.4f}E] {query}"

        messages = self._build_messages(query, images)
        tool_calls_log = []

        template_kwargs = {"add_generation_prompt": True, "tools": ALL_TOOLS}
        prompt = self.processor.apply_chat_template(
            messages, tokenize=False, **template_kwargs,
        )

        for turn in range(self.max_turns):
            response = self._generate(prompt)
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
                prompt += f"call:response:{log_entry['tool']}{json.dumps(log_entry['result'])}<tool_response|>"
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
