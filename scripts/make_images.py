"""Generate SOMthing's navy-and-white illustrations (SVG).

Run from the repo root:  python scripts/make_images.py

Writes:
  static/img/listings/<id>.svg     photo for each fictional listing
  static/img/categories/<cat>.svg  photo used for new posts without an uploaded photo
  static/img/icons/<cat>.svg       small category icons (transparent background)
"""

import hashlib
import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from illustrations import CATEGORY_DRAWING, DRAWINGS, LISTING_DRAWING, N, P  # noqa: E402
from somthing.catalog import SECTIONS  # noqa: E402

OUT = ROOT / "static" / "img"
BACKGROUNDS = ["#eef3fa", "#e9f0f9", "#f2f5fb", "#e6edf7"]


def photo(drawing: str, label: str, seed: str) -> str:
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    bg = BACKGROUNDS[h % len(BACKGROUNDS)]
    cx, cy = 150 + h % 500, 90 + (h // 7) % 200
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <rect width="800" height="600" fill="{bg}"/>
  <circle cx="{cx}" cy="{cy}" r="230" fill="#ffffff" opacity="0.75"/>
  <circle cx="{800 - cx}" cy="{560 - cy // 3}" r="120" fill="{P}" opacity="0.9"/>
  <rect x="0" y="472" width="800" height="128" fill="#dfe7f3"/>
  {DRAWINGS[drawing]()}
  <rect x="24" y="532" rx="18" width="{min(40 + len(label) * 13, 760)}" height="44" fill="{N}"/>
  <text x="44" y="561" font-size="22" fill="#ffffff" font-family="Helvetica, Arial, sans-serif" font-weight="700">{escape(label)}</text>
</svg>
"""


def icon(drawing: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="110 60 580 440" width="58" height="44">{DRAWINGS[drawing]()}</svg>\n'


def illustration(drawing: str) -> str:
    """Drawing only, on a transparent background (used on the home and login pages)."""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="110 60 580 440" width="580" height="440">{DRAWINGS[drawing]()}</svg>\n'


def main() -> None:
    labels = {cid: label for info in SECTIONS.values() for cid, label in info["categories"].items()}
    for sub in ("listings", "categories", "icons", "art"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    listings = json.loads((ROOT / "data" / "listings.json").read_text())
    for l in listings:
        (OUT / "listings" / f"{l['id']}.svg").write_text(photo(LISTING_DRAWING[l["id"]], labels[l["category"]], l["id"]))
    for cid, drawing in CATEGORY_DRAWING.items():
        (OUT / "categories" / f"{cid}.svg").write_text(photo(drawing, labels[cid], cid))
        (OUT / "icons" / f"{cid}.svg").write_text(icon(drawing))
    for name in ("sofa", "desk_lamp", "bike", "laptop_code", "camera", "piano", "grad_cap", "spreadsheet"):
        (OUT / "art" / f"{name}.svg").write_text(illustration(name))
    print(f"Wrote {len(listings)} listing photos, {len(CATEGORY_DRAWING)} category photos and icons, and page art.")


if __name__ == "__main__":
    main()
