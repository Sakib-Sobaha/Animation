# pikachu_run.py
# Provides a reusable scene module for hot_runner.py and a standalone entrypoint.

import math
import os
import random
import sys
from typing import Dict, Tuple

import pygame as pg

# ---- config ----
IMAGE_PATH = "pokemon.png"  # <- change if needed
WINDOW_W, WINDOW_H = 960, 540
GROUND_H = 120           # ground thickness
PIKA_HEIGHT_FRACTION = 0.36  # Pikachu height relative to window height
SPEED_PX_PER_SEC = 50000   # horizontal speed
LEFT_MARGIN = 10
RIGHT_MARGIN = 10


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def make_background(w: int, h: int, rng: random.Random) -> pg.Surface:
    """Return a surface with sky gradient, trees, and grass."""
    surf = pg.Surface((w, h)).convert()
    for i in range(h):
        t = i / max(1, h)
        c = (
            30 + int(80 * (1 - t)),
            30 + int(120 * (1 - t)),
            80 + int(120 * (1 - t)),
        )
        pg.draw.line(surf, c, (0, i), (w, i))

    ground_y = h - GROUND_H
    pg.draw.rect(surf, (24, 110, 34), (0, ground_y, w, GROUND_H))

    for x in range(0, w, 3):
        if rng.random() < 0.25:
            blade_h = rng.randint(6, 16)
            xx = x + rng.randint(-1, 1)
            pg.draw.line(
                surf,
                (16, 80, 28),
                (xx, ground_y + GROUND_H - 4),
                (xx, ground_y + GROUND_H - 4 - blade_h),
                1,
            )

    tree_count = max(3, w // 220)
    taken = []
    for _ in range(tree_count * 3):
        tx = rng.randint(40, w - 40)
        if any(abs(tx - t) < 80 for t in taken):
            continue
        taken.append(tx)
        base = ground_y
        trunk_h = rng.randint(40, 70)
        trunk_w = rng.randint(12, 18)
        pg.draw.rect(
            surf,
            (110, 60, 30),
            (tx - trunk_w // 2, base - trunk_h, trunk_w, trunk_h),
        )
        r = rng.randint(26, 40)
        pg.draw.circle(surf, (30, 140, 50), (tx, base - trunk_h), r)
        pg.draw.circle(surf, (30, 150, 55), (tx - r // 2, base - trunk_h + 10), r - 6)
        pg.draw.circle(surf, (26, 130, 48), (tx + r // 2, base - trunk_h + 10), r - 6)

    return surf


def load_pikachu(path: str, window_h: int) -> Tuple[pg.Surface, pg.Surface]:
    """Load + scale Pikachu, return right-facing and left-facing surfaces."""
    img = pg.image.load(path).convert_alpha()
    target_h = int(window_h * PIKA_HEIGHT_FRACTION)
    scale = target_h / img.get_height()
    target_w = int(img.get_width() * scale)
    img = pg.transform.smoothscale(img, (target_w, target_h))
    img_right = img
    img_left = pg.transform.flip(img, True, False)
    return img_right, img_left


def setup(state: Dict, screen: pg.Surface) -> None:
    """Prepare / refresh assets. Keeps motion state so hot reload feels seamless."""
    window_size = screen.get_size()
    state["window_size"] = window_size

    rng = random.Random(42)
    state["background"] = make_background(*window_size, rng)

    pika_r, pika_l = load_pikachu(IMAGE_PATH, window_size[1])
    state["pika_right"] = pika_r
    state["pika_left"] = pika_l

    previous_pos = state.get("pika_pos", LEFT_MARGIN + 10)
    previous_dx = state.get("dx", SPEED_PX_PER_SEC)

    rect = pika_r.get_rect()
    rect.bottom = window_size[1] - GROUND_H - 8
    max_x = window_size[0] - rect.width - RIGHT_MARGIN
    rect.x = int(clamp(previous_pos, LEFT_MARGIN, max_x))
    state["pika_rect"] = rect
    state["pika_pos"] = float(rect.x)

    state["dx"] = previous_dx if previous_dx != 0 else SPEED_PX_PER_SEC
    state["pika_surface"] = pika_r if state["dx"] >= 0 else pika_l
    state.setdefault("bob_time", 0.0)


def update(state: Dict, dt: float, events) -> None:
    rect = state.get("pika_rect")
    if rect is None:
        return

    window_w, _ = state["window_size"]
    pos = state.get("pika_pos", float(rect.x))
    dx = state.get("dx", SPEED_PX_PER_SEC)

    pos += dx * dt
    right_limit = window_w - rect.width - RIGHT_MARGIN
    left_limit = LEFT_MARGIN

    if dx > 0 and pos >= right_limit:
        pos = right_limit
        dx = -SPEED_PX_PER_SEC
        state["pika_surface"] = state.get("pika_left")
    elif dx < 0 and pos <= left_limit:
        pos = left_limit
        dx = SPEED_PX_PER_SEC
        state["pika_surface"] = state.get("pika_right")

    state["dx"] = dx
    state["pika_pos"] = pos
    rect.x = int(round(pos))
    state["bob_time"] = state.get("bob_time", 0.0) + dt * 6.0


def draw(state: Dict, screen: pg.Surface) -> None:
    bg = state.get("background")
    rect = state.get("pika_rect")
    pika = state.get("pika_surface") or state.get("pika_right")
    if not (bg and rect and pika):
        return

    screen.blit(bg, (0, 0))
    bob_offset = int(3 * math.sin(state.get("bob_time", 0.0)))
    screen.blit(pika, (rect.x, rect.y + bob_offset))


def main() -> None:
    pg.init()
    pg.display.set_caption("Pikachu run (window) — ESC to quit")
    screen = pg.display.set_mode((WINDOW_W, WINDOW_H))
    clock = pg.time.Clock()

    state: Dict = {}
    setup(state, screen)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        events = pg.event.get()
        for e in events:
            if e.type == pg.QUIT:
                running = False
            elif e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                running = False

        update(state, dt, events)
        draw(state, screen)
        pg.display.flip()

    pg.quit()
    sys.exit(0)


if __name__ == "__main__":
    if not os.path.exists(IMAGE_PATH):
        print("Update IMAGE_PATH to your Pikachu PNG/JPG.")
    main()
