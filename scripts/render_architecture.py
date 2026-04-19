"""Render ClimaSense architecture diagram as PNG using matplotlib."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path("docs")
OUTPUT_DIR.mkdir(exist_ok=True)


def draw_main_architecture():
    """Draw the main system architecture diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Color scheme
    colors = {
        "input": "#FFCDD2",      # Red-ish
        "edge": "#C8E6C9",       # Green
        "cloud": "#BBDEFB",      # Blue
        "tools": "#FFE0B2",      # Orange
        "output": "#E1BEE7",     # Purple
        "cache": "#F0F4C3",      # Yellow-green
        "arrow": "#424242",
        "text": "#212121",
    }

    def box(x, y, w, h, label, sublabel="", color="#E0E0E0", fontsize=10):
        rect = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.15",
            facecolor=color, edgecolor="#666666", linewidth=1.5,
        )
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2 + (0.12 if sublabel else 0),
                label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=colors["text"])
        if sublabel:
            ax.text(x + w/2, y + h/2 - 0.18, sublabel,
                    ha="center", va="center", fontsize=7, color="#555555")

    def arrow(x1, y1, x2, y2, label="", color="#424242"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5))
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx, my + 0.15, label, ha="center", va="center",
                    fontsize=7, color=color, style="italic")

    # Title
    ax.text(8, 9.7, "ClimaSense Architecture", ha="center", va="center",
            fontsize=18, fontweight="bold", color=colors["text"])
    ax.text(8, 9.35, "Agentic Climate Risk Intelligence for Smallholder Farmers",
            ha="center", va="center", fontsize=10, color="#666666")

    # ── Input Layer (top left) ──
    ax.text(2, 8.9, "FARMER INPUT", ha="center", fontsize=9,
            fontweight="bold", color="#C62828")
    box(0.3, 8.0, 1.8, 0.6, "Voice Query", "Swahili/Hindi/French/EN", colors["input"])
    box(2.4, 8.0, 1.8, 0.6, "Text Query", "140+ languages", colors["input"])
    box(4.5, 8.0, 1.8, 0.6, "Crop Photo", "Camera / Gallery", colors["input"])

    # ── Edge Model (middle left) ──
    box(0.3, 5.8, 3.0, 1.5, "Gemma 4 E4B", "Audio + Vision | 1.5GB int4", colors["edge"], 12)
    ax.text(1.8, 6.5, "EDGE DEVICE", ha="center", fontsize=8, fontweight="bold", color="#2E7D32")
    box(0.5, 6.0, 1.2, 0.5, "Transcribe", "16kHz mel", colors["edge"], 8)
    box(1.9, 6.0, 1.2, 0.5, "Diagnose", "LoRA 80%+", colors["edge"], 8)

    # ── Cloud Model (center) ──
    box(5.0, 5.5, 4.0, 2.0, "Gemma 4 31B-IT", "Reasoning + Function Calling", colors["cloud"], 13)
    ax.text(7.0, 6.8, "CLOUD / KAGGLE", ha="center", fontsize=8, fontweight="bold", color="#1565C0")
    box(5.3, 5.7, 1.6, 0.6, "Thinking", "Multi-factor", colors["cloud"], 8)
    box(7.1, 5.7, 1.6, 0.6, "Tool Calls", "Native FC", colors["cloud"], 8)

    # ── Offline Cache ──
    box(0.3, 4.2, 3.0, 0.8, "Offline Cache", "JSON + TTL | Stale fallback", colors["cache"], 10)

    # ── 9 Tools (right side) ──
    ax.text(13.0, 8.9, "9 REAL-API TOOLS", ha="center", fontsize=9,
            fontweight="bold", color="#E65100")

    tool_items = [
        ("Weather Forecast", "Open-Meteo"),
        ("Historical Weather", "Open-Meteo Archive"),
        ("Crop Disease", "DB + Wikipedia"),
        ("Treatment Recs", "DB + Wikipedia"),
        ("Market Prices", "WFP HDX"),
        ("Price Forecast", "WFP Seasonal"),
        ("Soil Analysis", "ISRIC SoilGrids"),
        ("Planting Advisory", "NASA POWER"),
        ("Climate Risk Alert", "NASA POWER"),
    ]
    for i, (name, source) in enumerate(tool_items):
        y = 8.2 - i * 0.55
        box(10.8, y, 2.2, 0.45, name, source, colors["tools"], 8)
        # Arrow from cloud to tool
        arrow(9.0, 6.5, 10.8, y + 0.22, color="#E65100")

    # ── Output Layer (bottom) ──
    ax.text(7.0, 2.8, "FARMER OUTPUT", ha="center", fontsize=9,
            fontweight="bold", color="#6A1B9A")
    box(4.0, 2.0, 2.0, 0.6, "Text Response", "Farmer's language", colors["output"])
    box(6.5, 2.0, 2.0, 0.6, "Voice (gTTS)", "Multilingual MP3", colors["output"])
    box(9.0, 2.0, 2.3, 0.6, "Actionable Advice", "Risk levels + steps", colors["output"])

    # ── Arrows (flow) ──
    # Input → Edge
    arrow(1.2, 8.0, 1.2, 7.3, "audio")
    arrow(5.4, 8.0, 5.4, 7.5, "image")
    # Input → Cloud
    arrow(3.3, 8.0, 6.5, 7.5, "text")
    # Edge → Cloud
    arrow(3.3, 6.5, 5.0, 6.5, "transcribed text")
    # Cloud → Output
    arrow(6.0, 5.5, 5.0, 2.6)
    arrow(7.0, 5.5, 7.5, 2.6)
    arrow(8.0, 5.5, 10.0, 2.6)
    # Tools → Cloud (results back)
    arrow(10.8, 4.5, 9.0, 5.8, "tool results", color="#1565C0")
    # Cache connections (dashed)
    ax.annotate("", xy=(3.3, 5.0), xytext=(5.0, 5.8),
                arrowprops=dict(arrowstyle="-|>", color="#827717", lw=1, linestyle="dashed"))
    ax.text(3.8, 5.3, "cache miss\nfallback", ha="center", fontsize=6, color="#827717")

    # ── Legend ──
    legend_items = [
        mpatches.Patch(facecolor=colors["input"], edgecolor="#666", label="Farmer Input"),
        mpatches.Patch(facecolor=colors["edge"], edgecolor="#666", label="Edge (E4B, 1.5GB)"),
        mpatches.Patch(facecolor=colors["cloud"], edgecolor="#666", label="Cloud (31B, 65GB)"),
        mpatches.Patch(facecolor=colors["tools"], edgecolor="#666", label="Real-API Tools"),
        mpatches.Patch(facecolor=colors["output"], edgecolor="#666", label="Farmer Output"),
        mpatches.Patch(facecolor=colors["cache"], edgecolor="#666", label="Offline Cache"),
    ]
    ax.legend(handles=legend_items, loc="lower left", fontsize=8, ncol=3,
              framealpha=0.9, edgecolor="#CCC")

    # Save
    png_path = OUTPUT_DIR / "architecture.png"
    fig.savefig(png_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {png_path}")

    svg_path = OUTPUT_DIR / "architecture.svg"
    fig2, ax2 = plt.subplots(1, 1, figsize=(16, 10))
    # Re-draw for SVG (matplotlib doesn't support saving same fig twice easily)
    fig.savefig(svg_path, format="svg", bbox_inches="tight", facecolor="white")
    print(f"Saved: {svg_path}")

    return png_path, svg_path


def draw_data_flow():
    """Draw a simplified data flow diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    colors = {
        "step": "#E3F2FD",
        "data": "#FFF3E0",
        "result": "#E8F5E9",
    }

    def step_box(x, y, w, h, title, detail, color):
        rect = FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.12",
            facecolor=color, edgecolor="#666", linewidth=1.5,
        )
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2 + 0.1, title, ha="center", va="center",
                fontsize=11, fontweight="bold")
        ax.text(x + w/2, y + h/2 - 0.15, detail, ha="center", va="center",
                fontsize=8, color="#555")

    ax.text(5, 7.7, "ClimaSense Data Flow", ha="center", fontsize=16, fontweight="bold")

    steps = [
        (1.5, 6.8, 7, 0.6, "1. Farmer speaks Swahili into phone", "\"Hali ya hewa ikoje?\" (How's the weather?)", "#FFCDD2"),
        (1.5, 5.8, 7, 0.6, "2. E4B Audio → Text (1.2s)", "16kHz mel spectrogram → transcription + language detection", colors["step"]),
        (1.5, 4.8, 7, 0.6, "3. 31B Reasoning + Tool Selection (2.2s)", "Thinking mode → selects get_weather_forecast tool", colors["step"]),
        (1.5, 3.8, 7, 0.6, "4. Real API Calls (0.1-4s per tool)", "Open-Meteo, WFP HDX, ISRIC, NASA POWER, Wikipedia", colors["data"]),
        (1.5, 2.8, 7, 0.6, "5. 31B Synthesizes Response", "Farmer-friendly advice in Swahili with risk levels", colors["step"]),
        (1.5, 1.8, 7, 0.6, "6. gTTS Voice Output", "Response spoken back in Swahili (MP3)", colors["result"]),
    ]

    for x, y, w, h, title, detail, color in steps:
        step_box(x, y, w, h, title, detail, color)

    # Arrows between steps
    for i in range(len(steps) - 1):
        ax.annotate("", xy=(5, steps[i+1][1] + steps[i+1][3]),
                    xytext=(5, steps[i][1]),
                    arrowprops=dict(arrowstyle="-|>", color="#424242", lw=2))

    # Timing annotation
    ax.text(9.2, 4.3, "Total: ~10s\nend-to-end", ha="center", fontsize=10,
            fontweight="bold", color="#1565C0",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#E3F2FD", edgecolor="#1565C0"))

    png_path = OUTPUT_DIR / "data_flow.png"
    fig.savefig(png_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {png_path}")
    return png_path


if __name__ == "__main__":
    draw_main_architecture()
    draw_data_flow()
    print("\nAll diagrams rendered!")
