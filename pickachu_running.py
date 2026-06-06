# pika_image_run.py
# Animate a Pikachu image left<->right over a grassy field using curses + ANSI truecolor.
# Requires: pip install pillow

import argparse, curses, time, random, math
from PIL import Image, ImageOps

# ---------- Scene bits (same as before) ----------
TREE = [
    "   &&&   ",
    "  &&&&&  ",
    " &&&&&&& ",
    "   |||   ",
    "   |||   ",
]

def build_grass(width, density=0.12):
    chars = ["'", ",", "`", '"', ".", "^"]
    line = [" "]*width
    for i in range(width):
        if random.random() < density:
            line[i] = random.choice(chars)
    return "".join(line)

def scatter_trees(max_y, max_x):
    spots = []
    if max_x < 40 or max_y < 12:
        return spots
    tree_w = len(TREE[0])
    ground_y = max_y - 4
    count = max(3, min(6, max_x // 20))
    taken = []
    for _ in range(count * 2):  # try extra times to spread out
        x = random.randint(1, max_x - tree_w - 2)
        if any(abs(x - tx) < tree_w + 2 for tx in taken):
            continue
        taken.append(x)
        spots.append((ground_y - len(TREE), x))
        if len(spots) >= count:
            break
    return spots

# ---------- Image -> ANSI half-block sprite ----------
def color_dist(a, b):
    return math.sqrt(sum((a[i] - b[i])**2 for i in range(3)))

def chroma_key_rgba(img_rgba, thresh=48):
    """Treat pixels near the average corner color as transparent (if no alpha)."""
    w, h = img_rgba.size
    px = img_rgba.load()
    # sample a few corner points
    samples = []
    for dx in range(min(8, w)):
        for dy in range(min(8, h)):
            samples += [px[dx, dy], px[w-1-dx, dy], px[dx, h-1-dy], px[w-1-dx, h-1-dy]]
    if not samples:
        return img_rgba
    avg = tuple(int(sum(p[i] for p in samples)/len(samples)) for i in range(4))
    bg = avg[:3]
    # build new with alpha punched out
    out = Image.new("RGBA", (w, h))
    out_px = out.load()
    for y in range(h):
        for x in range(w):
            r,g,b,a = px[x,y]
            if a < 10:
                out_px[x,y] = (r,g,b,0)
            elif color_dist((r,g,b), bg) < thresh:
                out_px[x,y] = (r,g,b,0)
            else:
                out_px[x,y] = (r,g,b,a)
    return out

def to_ansi_sprite(img_path, target_cols, max_rows_cells=None, do_chroma=True):
    """
    Convert image to a list of strings (rows) using upper half-block '▀'
    with 24-bit fg/bg colors. Each row represents 2 image pixels vertically.
    """
    im = Image.open(img_path).convert("RGBA")
    # Optional chroma-key if no transparency
    if do_chroma and im.getchannel("A").getextrema() == (255, 255):
        im = chroma_key_rgba(im)

    # Compute target size keeping aspect; each terminal row = 2 image pixels
    w0, h0 = im.size
    # First scale by width
    tw = max(8, target_cols)
    th_pixels = int(h0 * (tw / w0))
    if max_rows_cells:
        max_h_pixels = max_rows_cells * 2
        if th_pixels > max_h_pixels:
            tw = int(tw * (max_h_pixels / th_pixels))
            th_pixels = max_h_pixels
    im = im.resize((tw, max(2, th_pixels)), Image.LANCZOS)

    # Ensure even pixel height for pairing
    if im.size[1] % 2 == 1:
        im = im.crop((0, 0, im.size[0], im.size[1]-1))

    w, h = im.size
    px = im.load()
    lines = []
    ESC = "\x1b["
    RESET = ESC + "0m"
    for y in range(0, h, 2):
        row_chunks = []
        for x in range(w):
            r1,g1,b1,a1 = px[x, y]
            r2,g2,b2,a2 = px[x, y+1]
            # transparency handling
            top_vis = a1 > 15
            bot_vis = a2 > 15
            if top_vis and bot_vis:
                # '▀' uses FG as top color, BG as bottom color
                row_chunks.append(
                    f"{ESC}38;2;{r1};{g1};{b1}m{ESC}48;2;{r2};{g2};{b2}m▀"
                )
            elif top_vis and not bot_vis:
                row_chunks.append(f"{ESC}38;2;{r1};{g1};{b1}m▀{RESET}")
            elif bot_vis and not top_vis:
                # lower half-block: FG color draws the bottom half
                row_chunks.append(f"{ESC}38;2;{r2};{g2};{b2}m▄{RESET}")
            else:
                row_chunks.append(" ")
        lines.append("".join(row_chunks) + RESET)
    return lines, w, len(lines)

def mirror_sprite_from_image(img_path, target_cols, max_rows_cells=None, do_chroma=True):
    """Produce left/right sprites by mirroring the processed RGBA image."""
    im = Image.open(img_path).convert("RGBA")
    if do_chroma and im.getchannel("A").getextrema() == (255, 255):
        im = chroma_key_rgba(im)
    # We'll create two temp files in-memory via ImageOps.mirror
    def sprite_from_image_object(img_obj):
        w0, h0 = img_obj.size
        tw = max(8, target_cols)
        th_pixels = int(h0 * (tw / w0))
        if max_rows_cells:
            max_h_pixels = max_rows_cells * 2
            if th_pixels > max_h_pixels:
                tw = int(tw * (max_h_pixels / th_pixels))
                th_pixels = max_h_pixels
        img_r = img_obj.resize((tw, max(2, th_pixels)), Image.LANCZOS)
        if img_r.size[1] % 2 == 1:
            img_r = img_r.crop((0, 0, img_r.size[0], img_r.size[1]-1))
        # Render to ANSI lines
        # To avoid duplicating logic, temporarily save to bytes and reload pathless
        # But we'll implement inline painter:
        w, h = img_r.size
        px = img_r.load()
        lines = []
        ESC = "\x1b["
        RESET = ESC + "0m"
        for y in range(0, h, 2):
            row_chunks = []
            for x in range(w):
                r1,g1,b1,a1 = px[x, y]
                r2,g2,b2,a2 = px[x, y+1]
                top_vis = a1 > 15
                bot_vis = a2 > 15
                if top_vis and bot_vis:
                    row_chunks.append(f"{ESC}38;2;{r1};{g1};{b1}m{ESC}48;2;{r2};{g2};{b2}m▀")
                elif top_vis and not bot_vis:
                    row_chunks.append(f"{ESC}38;2;{r1};{g1};{b1}m▀{RESET}")
                elif bot_vis and not top_vis:
                    row_chunks.append(f"{ESC}38;2;{r2};{g2};{b2}m▄{RESET}")
                else:
                    row_chunks.append(" ")
            lines.append("".join(row_chunks) + RESET)
        return lines, w, len(lines)

    # Right-facing = original; Left-facing = mirror
    right_lines, sw, sh = sprite_from_image_object(im)
    left_lines, _, _ = sprite_from_image_object(ImageOps.mirror(im))
    return (right_lines, left_lines, sw, sh)

# ---------- Animation ----------
def draw_sprite_lines(stdscr, y, x, lines):
    max_y, max_x = stdscr.getmaxyx()
    for i, row in enumerate(lines):
        ry = y + i
        if 0 <= ry < max_y:
            try:
                stdscr.addstr(ry, max(0, x), row[: max_x - x])
            except curses.error:
                pass

def main(stdscr, img_path):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    have_colors = curses.has_colors()
    if have_colors:
        curses.start_color()
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)   # trunk
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK) # leaves/grass
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)  # sky text

    max_y, max_x = stdscr.getmaxyx()
    grass1 = build_grass(max_x)
    grass2 = build_grass(max_x, density=0.08)
    trees = scatter_trees(max_y, max_x)

    # Decide sprite size based on terminal width
    target_cols = max(16, min(36, max_x // 4))
    max_rows_cells = max(6, min(12, max_y // 3))
    right_sprite, left_sprite, sprite_w, sprite_h = mirror_sprite_from_image(
        img_path, target_cols=target_cols, max_rows_cells=max_rows_cells, do_chroma=True
    )

    sprites = right_sprite
    y = max(1, max_y - sprite_h - 4)  # float above grass
    x = 2
    dx = 1

    clouds = []
    if max_y >= 12:
        for _ in range(max(4, min(10, max_x // 12))):
            cy = random.randint(1, max(2, max_y // 3))
            cx = random.randint(0, max_x - 1)
            clouds.append([cy, float(cx)])

    while True:
        ny, nx = stdscr.getmaxyx()
        if (ny, nx) != (max_y, max_x):
            max_y, max_x = ny, nx
            stdscr.clear()
            grass1 = build_grass(max_x)
            grass2 = build_grass(max_x, density=0.08)
            trees = scatter_trees(max_y, max_x)
            target_cols = max(16, min(36, max_x // 4))
            max_rows_cells = max(6, min(12, max_y // 3))
            right_sprite, left_sprite, sprite_w, sprite_h = mirror_sprite_from_image(
                img_path, target_cols=target_cols, max_rows_cells=max_rows_cells, do_chroma=True
            )
            sprites = right_sprite if dx > 0 else left_sprite
            y = max(1, max_y - sprite_h - 4)
            x = min(x, max_x - sprite_w - 2)

        stdscr.erase()

        # Title
        title = " Pikachu image sprite — press 'q' to quit "
        try:
            stdscr.addstr(0, max(0, (max_x - len(title)) // 2), title, curses.color_pair(5) if have_colors else 0)
        except curses.error:
            pass

        # Clouds
        for c in clouds:
            c[1] -= 0.2
            if c[1] < 0:
                c[1] = max_x - 1
                c[0] = random.randint(1, max(2, max_y // 3))
            try:
                stdscr.addstr(int(c[0]), int(c[1]), ".", curses.color_pair(5) if have_colors else 0)
            except curses.error:
                pass

        # Trees
        for ty, tx in scatter_trees(max_y, max_x) if not trees else trees:
            for i, row in enumerate(TREE):
                color = 3 if i < 3 else 2
                try:
                    stdscr.addstr(ty + i, tx, row, curses.color_pair(color) if have_colors else 0)
                except curses.error:
                    pass

        # Grass
        try:
            stdscr.addstr(max_y - 2, 0, grass2[:max_x], curses.color_pair(3) if have_colors else 0)
            stdscr.addstr(max_y - 1, 0, grass1[:max_x], curses.color_pair(3) if have_colors else 0)
        except curses.error:
            pass

        # Sprite
        draw_sprite_lines(stdscr, y, x, sprites)

        stdscr.refresh()

        # Motion
        x += dx
        if dx > 0 and x + sprite_w >= max_x - 1:
            dx = -1
            sprites = left_sprite
        elif dx < 0 and x <= 1:
            dx = 1
            sprites = right_sprite

        time.sleep(0.03)

        # Quit?
        try:
            ch = stdscr.getch()
            if ch in (ord('q'), ord('Q')):
                break
        except:
            pass

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", "-i", default="pikachu.png", help="Path to Pikachu image (PNG/JPG).")
    args = ap.parse_args()
    curses.wrapper(main, args.image)
