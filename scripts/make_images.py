"""Generate the illustrated listing photos (SVG) used by the fictional demo data.

Run from the repo root:  python scripts/make_images.py
"""

import hashlib
import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from somthing.catalog import SECTIONS  # noqa: E402
from somthing.store import category_emoji  # noqa: E402

OUT_LISTINGS = ROOT / "static" / "img" / "listings"
OUT_CATEGORIES = ROOT / "static" / "img" / "categories"

# Dark backgrounds with pink/magenta accents, picked per listing for variety.
PALETTES = [
    ("#1a0d16", "#ff4fa3"), ("#120d1a", "#ff7ac0"), ("#1c1015", "#ff3d8b"), ("#0f0f14", "#f472b6"),
    ("#1a1212", "#fb7185"), ("#140b18", "#e879f9"), ("#101018", "#ff8fc7"), ("#190f12", "#ff5c9e"),
]
FONT = "Apple Color Emoji, Segoe UI Emoji, Noto Color Emoji, sans-serif"


def svg(emoji: str, label: str, seed: str) -> str:
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    bg, accent = PALETTES[h % len(PALETTES)]
    cx, cy = 200 + h % 400, 120 + (h // 7) % 300
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <defs>
    <radialGradient id="g" cx="{cx}" cy="{cy}" r="520" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{accent}" stop-opacity="0.55"/>
      <stop offset="1" stop-color="{bg}" stop-opacity="1"/>
    </radialGradient>
    <pattern id="d" width="28" height="28" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1.4" fill="#ffffff" fill-opacity="0.07"/>
    </pattern>
  </defs>
  <rect width="800" height="600" fill="{bg}"/>
  <rect width="800" height="600" fill="url(#g)"/>
  <rect width="800" height="600" fill="url(#d)"/>
  <circle cx="400" cy="285" r="170" fill="#000" fill-opacity="0.28"/>
  <circle cx="400" cy="285" r="170" fill="none" stroke="{accent}" stroke-opacity="0.6" stroke-width="3"/>
  <text x="400" y="290" font-size="180" text-anchor="middle" dominant-baseline="central" font-family="{FONT}">{escape(emoji)}</text>
  <rect x="24" y="532" rx="18" width="{min(40 + len(label) * 13, 760)}" height="44" fill="#000" fill-opacity="0.55"/>
  <text x="44" y="561" font-size="22" fill="#ffd1e8" font-family="Helvetica, Arial, sans-serif" font-weight="700">{escape(label)}</text>
</svg>
"""


def main() -> None:
    OUT_LISTINGS.mkdir(parents=True, exist_ok=True)
    OUT_CATEGORIES.mkdir(parents=True, exist_ok=True)
    labels = {cid: label for info in SECTIONS.values() for cid, label in info["categories"].items()}
    listings = json.loads((ROOT / "data" / "listings.json").read_text())
    for l in listings:
        (OUT_LISTINGS / f"{l['id']}.svg").write_text(svg(l["emoji"], labels[l["category"]], l["id"]))
    for cid, emoji in category_emoji().items():
        (OUT_CATEGORIES / f"{cid}.svg").write_text(svg(emoji, labels[cid], cid))
    print(f"Wrote {len(listings)} listing images and {len(labels)} category images.")


if __name__ == "__main__":
    main()
