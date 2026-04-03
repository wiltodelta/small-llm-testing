"""Generate a test bar chart image for the vision benchmark prompt."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent / "assets"
OUTPUT_PATH = ASSETS_DIR / "test_chart.png"

# Chart data: quarterly revenue in millions
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
VALUES = [42, 58, 35, 71]
COLORS = ["#4285F4", "#EA4335", "#FBBC05", "#34A853"]

WIDTH = 600
HEIGHT = 400
MARGIN_LEFT = 80
MARGIN_RIGHT = 40
MARGIN_TOP = 60
MARGIN_BOTTOM = 60


def generate_chart() -> Path:
    """Generate a bar chart and save it to assets/test_chart.png."""
    ASSETS_DIR.mkdir(exist_ok=True)
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        font_label = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except OSError:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()

    # Title
    draw.text(
        (WIDTH // 2, 25),
        "Quarterly Revenue (millions $)",
        fill="black",
        font=font_title,
        anchor="mm",
    )

    chart_w = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    chart_h = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    max_val = max(VALUES)

    bar_count = len(VALUES)
    bar_width = chart_w // (bar_count * 2)
    gap = bar_width

    # Y-axis
    draw.line(
        [(MARGIN_LEFT, MARGIN_TOP), (MARGIN_LEFT, HEIGHT - MARGIN_BOTTOM)],
        fill="gray",
        width=1,
    )

    # Grid lines and Y labels
    for i in range(5):
        val = int(max_val * i / 4)
        y = HEIGHT - MARGIN_BOTTOM - int(chart_h * i / 4)
        draw.line([(MARGIN_LEFT, y), (WIDTH - MARGIN_RIGHT, y)], fill="#E0E0E0", width=1)
        draw.text((MARGIN_LEFT - 10, y), f"${val}", fill="black", font=font_label, anchor="rm")

    # Bars
    for i, (quarter, value, color) in enumerate(zip(QUARTERS, VALUES, COLORS, strict=True)):
        x0 = MARGIN_LEFT + gap + i * (bar_width + gap)
        x1 = x0 + bar_width
        bar_h = int(chart_h * value / max_val)
        y0 = HEIGHT - MARGIN_BOTTOM - bar_h
        y1 = HEIGHT - MARGIN_BOTTOM

        draw.rectangle([x0, y0, x1, y1], fill=color)

        # Value on top
        draw.text(((x0 + x1) // 2, y0 - 8), f"${value}M", fill="black", font=font_label, anchor="mb")

        # Quarter label
        draw.text(((x0 + x1) // 2, y1 + 8), quarter, fill="black", font=font_label, anchor="mt")

    img.save(OUTPUT_PATH)
    log.info("Chart saved to %s", OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_chart()
