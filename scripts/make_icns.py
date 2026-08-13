"""Generates api/icon.icns (macOS) and api/icon.ico (Windows) from site/public/favicon.svg.

The SVG is a wrapper around a single embedded PNG, so the source bitmap is extracted rather than
rendered. The artwork is portrait, so it is scaled to fit and centred on a square transparent
canvas -- application icons must be square.

The .icns step needs macOS (iconutil); the .ico is written everywhere.

Run with no project dependencies:
    uvx --from pillow python scripts/make_icns.py
"""

import base64
import pathlib
import re
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_SVG = ROOT / "site" / "public" / "favicon.svg"
TARGET = ROOT / "api" / "icon.icns"
TARGET_ICO = ROOT / "api" / "icon.ico"

# Sizes Windows picks between for the exe icon, shortcuts and Explorer views.
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]

# macOS iconset: (filename, pixel size)
SIZES = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]

# Leaves a little breathing room so the artwork is not flush to the icon edge.
CANVAS_FILL = 0.92


def extract_png() -> Image.Image:
    match = re.search(r"base64,([A-Za-z0-9+/=]+)", SOURCE_SVG.read_text())

    if match is None:
        raise SystemExit(f"no embedded PNG found in {SOURCE_SVG}")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        handle.write(base64.b64decode(match.group(1)))
        return Image.open(handle.name).convert("RGBA")


def square(image: Image.Image, size: int) -> Image.Image:
    target = int(size * CANVAS_FILL)
    scaled = image.copy()

    scaled.thumbnail((target, target), Image.LANCZOS)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(
        scaled,
        ((size - scaled.width) // 2, (size - scaled.height) // 2),
        scaled,
    )

    return canvas


def main() -> None:
    source = extract_png()
    print(f"source artwork: {source.width}x{source.height}")

    TARGET.parent.mkdir(parents=True, exist_ok=True)

    # Windows .ico: a single file holding every size, which is what gives crisp shortcuts in the
    # Start menu, on the desktop and in Explorer.
    square(source, max(ICO_SIZES)).save(
        TARGET_ICO, format="ICO", sizes=[(size, size) for size in ICO_SIZES]
    )
    print(f"wrote {TARGET_ICO} ({TARGET_ICO.stat().st_size:,} bytes)")

    if sys.platform != "darwin":
        print("skipping .icns: iconutil is macOS only")
        return

    with tempfile.TemporaryDirectory() as workdir:
        iconset = pathlib.Path(workdir) / "icon.iconset"
        iconset.mkdir()

        for name, size in SIZES:
            square(source, size).save(iconset / name)

        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(TARGET)], check=True
        )

    print(f"wrote {TARGET} ({TARGET.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
