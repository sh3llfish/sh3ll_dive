#!/usr/bin/env python3
"""Generate a pre-composited tarot background image.

The script arranges the tarot card PNGs from `public/tarot/` into a tiled
composition and saves the result as an RGBA image. Tweak the CLI flags to
change the canvas size, card height, and spacing.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tarot-dir",
        type=Path,
        default=Path("public/tarot"),
        help="Directory containing individual tarot PNGs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("public/tarot_background.png"),
        help="Where to write the generated background image",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=2400,
        help="Output canvas width in pixels",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=3600,
        help="Output canvas height in pixels",
    )
    parser.add_argument(
        "--card-height",
        type=int,
        default=540,
        help="Target height for each card in pixels (maintains aspect ratio)",
    )
    parser.add_argument(
        "--column-gap",
        type=int,
        default=24,
        help="Horizontal gap between card columns in pixels",
    )
    parser.add_argument(
        "--row-gap",
        type=int,
        default=12,
        help="Base vertical gap between cards in pixels",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible layouts",
    )
    return parser.parse_args()


def load_cards(tarot_dir: Path, target_height: int) -> list[Image.Image]:
    card_paths = sorted(tarot_dir.glob("*.png"))
    if not card_paths:
        raise FileNotFoundError(f"No PNG cards found in {tarot_dir!s}")

    cards: list[Image.Image] = []
    for path in card_paths:
        with Image.open(path) as img:
            img = img.convert("RGBA")
            scale = target_height / img.height
            new_size = (int(img.width * scale), target_height)
            resized = img.resize(new_size, Image.LANCZOS)
            cards.append(resized)
    return cards


def composite_background(
    cards: list[Image.Image],
    width: int,
    height: int,
    column_gap: int,
    row_gap: int,
) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Determine column geometry from the first card (all resized equally).
    sample_card = cards[0]
    card_w, card_h = sample_card.size
    column_step = card_w + column_gap
    column_count = max(1, math.ceil((width + column_gap) / column_step))

    columns: list[int] = []
    for col in range(column_count):
        if col == 0:
            x = 0
        else:
            x = col * column_step
        columns.append(min(max(int(x), 0), max(width - card_w, 0)))

    for col, x in enumerate(columns):
        y = -random.randint(0, card_h)
        while y < height:
            card = random.choice(cards)
            dest_y = int(y)
            if dest_y >= 0:
                offset_x = x
                canvas.alpha_composite(card, (offset_x, dest_y))

            jitter = random.randint(-row_gap, row_gap)
            y += card_h + row_gap + jitter

    return canvas


def main() -> None:
    args = parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    tarot_dir = args.tarot_dir
    if not tarot_dir.is_absolute():
        tarot_dir = (ROOT / tarot_dir).resolve()

    output_path = args.output
    if not output_path.is_absolute():
        output_path = (ROOT / output_path).resolve()

    cards = load_cards(tarot_dir, args.card_height)
    background = composite_background(
        cards,
        width=args.width,
        height=args.height,
        column_gap=args.column_gap,
        row_gap=args.row_gap,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    background.save(output_path)
    print(f"Generated tarot background → {output_path}")


if __name__ == "__main__":
    main()
