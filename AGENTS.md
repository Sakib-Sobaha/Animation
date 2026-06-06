# Repository Guidelines

## Project Structure & Module Organization
- `bounce_curses.py` animates a single glyph in a curses window; keep terminal-safe logic here.
- `hot_runner.py` boots a Pygame window and hot-reloads `pikachu_run.py`; treat it as the desktop playground.
- `pikachu_run.py` handles the windowed Pikachu scene (background, sprite scaling, motion).
- `pickachu_running.py` renders Pikachu in ANSI truecolor via curses; it depends on Pillow for image processing.
- Shell utilities (`bouncer.sh`, `spinner.sh`, `frame.sh`) provide lightweight terminal demos; keep them POSIX-friendly.
- Image assets (`pokemon.png`, `cat_gpt.png`, etc.) live beside the scripts; reference them with relative paths to avoid breakage.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates an isolated environment.
- `pip install pygame pillow` pulls the required runtime libraries.
- `python bounce_curses.py` runs the curses based bounce demo; resize the terminal to confirm it reacts to new dimensions.
- `python hot_runner.py` launches the hot reload loop; edit `pikachu_run.py` and watch for immediate updates.
- `python pickachu_running.py --image pokemon.png` rebuilds the ANSI sprite; use `-h` for tuning width/height.
- `bash bouncer.sh` / `bash spinner.sh` preview the shell effects; ensure scripts stay executable (`chmod +x`).

## Coding Style & Naming Conventions
- Follow PEP 8: four-space indentation, snake_case for functions, and ALL_CAPS for module constants (e.g., `IMAGE_PATH`).
- Favor explicit modules (`import math`) over wildcard imports; keep related helpers grouped.
- Use inline comments sparingly to explain non-obvious math (e.g., bobbing offsets) and keep ANSI escape sequences encapsulated in helpers.

## Testing Guidelines
- There is no automated suite; exercise features manually after each change (terminal resize, ESC key handling, hot reload).
- When adding tests, use `pytest` and isolate graphic helpers so they can be unit-tested without a display.
- Document any new dependencies or environment vars in this guide and in module-level docstrings.

## Commit & Pull Request Guidelines
- Git history is not yet established; adopt imperative subjects under 72 characters (e.g., `Add terminal grass tiling helper`).
- Reference related scripts or assets in the body, list manual verification steps, and link issues where available.
- For visual tweaks, attach a short GIF, screenshot, or terminal capture so reviewers can verify before running locally.

## Assets & Configuration Tips
- Keep binary assets lightweight (<1 MB) to preserve repo size; prefer PNG with transparency for sprites.
- Verify terminal demos on truecolor-capable shells; fall back gracefully by detecting `TERM` capabilities when possible.
- Store user-specific settings (e.g., alternate image paths) in local env files rather than editing tracked scripts.
