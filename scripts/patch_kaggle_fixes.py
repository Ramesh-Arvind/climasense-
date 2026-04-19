"""Patch the notebook for Kaggle T4: add gtts install and KV-cache clears
between scenarios. Run once after authoring changes upstream."""
from __future__ import annotations

from pathlib import Path
import nbformat as nbf

NB = Path("notebooks/climasense_demo.ipynb")
nb = nbf.read(NB, as_version=4)

INSTALL_MARKER = "import climasense  # noqa: F401"
GTTS_INSTALL_SNIPPET = """
# gtts is not always resolved transitively on Kaggle — install explicitly
try:
    import gtts  # noqa: F401
except ImportError:
    _pip_install("gtts")
    import gtts  # noqa: F401
"""

SCENARIO_HEADER_PATTERNS = {
    "SCENARIO 2": "# Scenario 2: Comprehensive planning",
    "SCENARIO 3": "# Scenario 3: Farmer says",
}
CACHE_CLEAR = "import gc\nif torch.cuda.is_available():\n    torch.cuda.empty_cache()\ngc.collect()\n"

for cell in nb.cells:
    if cell.cell_type != "code":
        continue
    src = cell.source

    if INSTALL_MARKER in src and "import gtts" not in src:
        insertion = src.rstrip() + "\n" + GTTS_INSTALL_SNIPPET
        if "print(f\"PyTorch:" in src:
            insertion = src.replace(
                "print(f\"PyTorch:",
                GTTS_INSTALL_SNIPPET.strip() + "\n\nprint(f\"PyTorch:",
            )
        cell.source = insertion

    for _label, marker in SCENARIO_HEADER_PATTERNS.items():
        if marker in src and "torch.cuda.empty_cache()" not in src.split(marker, 1)[0]:
            cell.source = CACHE_CLEAR + "\n" + src

nbf.write(nb, NB)
print(f"Patched {NB}")
for i, c in enumerate(nb.cells):
    first = (c.source or "").strip().split("\n")[0][:70]
    print(f"  [{i:2d}] {c.cell_type:<8} {first}")
