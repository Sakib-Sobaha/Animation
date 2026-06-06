# bounce_curses.py
import curses, time, random

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    # Colors
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)

    # Initial state
    max_y, max_x = stdscr.getmaxyx()
    y, x = max_y // 2, max_x // 2
    dy, dx = 1, 1
    ch = "●"

    while True:
        # Resize-aware
        ny, nx = stdscr.getmaxyx()
        if (ny, nx) != (max_y, max_x):
            max_y, max_x = ny, nx
            stdscr.clear()

        stdscr.erase()
        # Border
        stdscr.border()

        # Move
        y += dy; x += dx
        if y <= 1 or y >= max_y - 2: dy *= -1
        if x <= 1 or x >= max_x - 2: dx *= -1

        try:
            stdscr.addstr(y, x, ch, curses.color_pair(1))
        except curses.error:
            pass  # In case of tiny terminal

        stdscr.refresh()
        time.sleep(0.01)

        # Quit on 'q'
        try:
            if stdscr.getch() in (ord('q'), ord('Q')):
                break
        except:
            pass

if __name__ == "__main__":
    curses.wrapper(main)
