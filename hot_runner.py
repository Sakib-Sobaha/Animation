# hot_runner.py
import importlib
import importlib.util
import sys
import traceback
from pathlib import Path

import pygame as pg

MOD = "pikachu_run"  # the module we will hot-reload

def load_module(mod, state, screen):
    try:
        mod = importlib.reload(mod) if mod else importlib.import_module(MOD)
        if hasattr(mod, "setup"):
            mod.setup(state, screen)  # rebind assets but keep persistent state
        print("[HOT-RELOAD] reloaded", MOD)
        return mod
    except Exception:
        traceback.print_exc()
        return mod


def resolve_module_path() -> Path:
    spec = importlib.util.find_spec(MOD)
    if spec and spec.origin:
        return Path(spec.origin).resolve()
    raise ImportError(f"Unable to locate module {MOD}")

def main():
    pg.init()
    screen = pg.display.set_mode((960, 540))
    pg.display.set_caption("Hot reload runner — ESC to quit")
    clock = pg.time.Clock()

    state = {}       # survives reloads
    mod = None
    mod = load_module(mod, state, screen)

    # track file mtime
    try:
        mod_path = resolve_module_path()
    except ImportError:
        traceback.print_exc()
        return
    last_mtime = mod_path.stat().st_mtime

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        events = pg.event.get()
        for e in events:
            if e.type == pg.QUIT: running = False
            if e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE: running = False

        # Hot reload when the file changes
        try:
            mtime = mod_path.stat().st_mtime
            if mtime != last_mtime:
                last_mtime = mtime
                mod = load_module(sys.modules.get(MOD), state, screen)
                try:
                    mod_path = resolve_module_path()
                    last_mtime = mod_path.stat().st_mtime
                except ImportError:
                    traceback.print_exc()
        except FileNotFoundError:
            pass

        # Game loop calls into the module
        if hasattr(mod, "update"): mod.update(state, dt, events)
        if hasattr(mod, "draw"):   mod.draw(state, screen)
        pg.display.flip()

    pg.quit()

if __name__ == "__main__":
    main()
