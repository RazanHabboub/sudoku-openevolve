import os
from math import ceil

# Prefer imageio_ffmpeg's bundled binary over the system ffmpeg
try:
    import imageio_ffmpeg as _iio_ffmpeg
    _FFMPEG_EXE = _iio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    _FFMPEG_EXE = None

# ── PIL-based frame renderer ──────────────────────────────────────────────────
from PIL import Image, ImageDraw, ImageFont

# Frame geometry (pixels)
_W, _H = 450, 550          # total canvas
_MARGIN = 25               # left/right margin
_TOP = 60                  # top of grid
_CELL = 50                 # cell size
_GRID_W = _CELL * 9       # 450 – margins = 450 pixels wide grid

# Try to load a truetype font; fall back to the bitmap default
def _load_font(size):
    for name in ('arial.ttf', 'Arial.ttf', 'DejaVuSans.ttf',
                 'FreeSans.ttf', 'LiberationSans-Regular.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            pass
    return ImageFont.load_default()

_FONT_DIGIT   = _load_font(24)
_FONT_TITLE   = _load_font(16)
_FONT_SMALL   = _load_font(13)
_FONT_SOLVED  = _load_font(34)

# Colours
_C_BG_GIVEN   = '#E8E8E8'
_C_DIGIT_GIVEN = '#222222'
_C_DIGIT_PLACE = '#1565C0'
_C_GRID        = '#000000'
_C_SOLVED      = '#2E7D32'
_C_SUBTITLE    = '#333333'


def _draw_frame(initial_grid, current, given, title, bt_count, show_solved):
    """Return a (W x H x 3) uint8 numpy array for one animation frame."""
    import numpy as np

    img  = Image.new('RGB', (_W, _H), 'white')
    draw = ImageDraw.Draw(img)

    # ── title ────────────────────────────────────────────────────────────────
    try:
        tw, th = draw.textlength(title, font=_FONT_TITLE), 16
        draw.text((_W // 2, 22), title, fill='black',
                  font=_FONT_TITLE, anchor='mm')
    except Exception:
        draw.text((_W // 2 - len(title) * 4, 14), title, fill='black')

    # ── given-cell backgrounds ───────────────────────────────────────────────
    for r, c in given:
        x0 = _MARGIN + c * _CELL
        y0 = _TOP    + r * _CELL
        draw.rectangle([x0, y0, x0 + _CELL, y0 + _CELL], fill=_C_BG_GIVEN)

    # ── digit values ─────────────────────────────────────────────────────────
    for r in range(9):
        for c in range(9):
            val = current[r][c]
            if val == 0:
                continue
            color  = _C_DIGIT_GIVEN if (r, c) in given else _C_DIGIT_PLACE
            cx = _MARGIN + c * _CELL + _CELL // 2
            cy = _TOP    + r * _CELL + _CELL // 2
            try:
                draw.text((cx, cy), str(val), fill=color,
                          font=_FONT_DIGIT, anchor='mm')
            except Exception:
                draw.text((cx - 7, cy - 7), str(val), fill=color)

    # ── grid lines ───────────────────────────────────────────────────────────
    for i in range(10):
        lw = 3 if i % 3 == 0 else 1
        x  = _MARGIN + i * _CELL
        y  = _TOP    + i * _CELL
        draw.line([(x, _TOP), (x, _TOP + _GRID_W)],
                  fill=_C_GRID, width=lw)
        draw.line([(_MARGIN, y), (_MARGIN + _GRID_W, y)],
                  fill=_C_GRID, width=lw)

    # ── backtrack counter ────────────────────────────────────────────────────
    bt_label = f'Backtracks: {bt_count}'
    try:
        draw.text((_W // 2, _TOP + _GRID_W + 18), bt_label,
                  fill=_C_SUBTITLE, font=_FONT_SMALL, anchor='mm')
    except Exception:
        draw.text((_W // 2 - 60, _TOP + _GRID_W + 10), bt_label,
                  fill=_C_SUBTITLE)

    # ── "SOLVED ✓" overlay ──────────────────────────────────────────────────
    if show_solved:
        try:
            draw.text((_W // 2, _H // 2), 'SOLVED ✓',
                      fill=_C_SOLVED, font=_FONT_SOLVED, anchor='mm')
        except Exception:
            draw.text((_W // 2 - 70, _H // 2 - 17), 'SOLVED',
                      fill=_C_SOLVED)

    return np.array(img)


# ── public API ────────────────────────────────────────────────────────────────

def render_clip(initial_grid, steps, title, output_path,
                steps_per_frame, total_frames, fps=30):
    """
    Render a Sudoku solve animation to an MP4 file.

    Parameters
    ----------
    initial_grid    : 9x9 list[list[int]]  (0 = empty)
    steps           : list of (r, c, val) tuples from a recording solver
    title           : str shown above the grid
    output_path     : destination .mp4 path
    steps_per_frame : how many solve-steps to advance per frame
    total_frames    : total number of frames (controls video duration)
    fps             : frames per second
    """
    import imageio

    given   = frozenset((r, c)
                        for r in range(9) for c in range(9)
                        if initial_grid[r][c] != 0)
    current = [row[:] for row in initial_grid]

    state = {'step_idx': 0, 'bt': 0}
    solved_at_frame = ceil(len(steps) / steps_per_frame) if steps else 0

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Use imageio's ffmpeg writer (uses imageio_ffmpeg binary if available)
    writer_kwargs = {
        'fps': fps,
        'macro_block_size': 2,   # avoids resize warnings for arbitrary sizes
        'ffmpeg_params': ['-vcodec', 'libx264', '-pix_fmt', 'yuv420p'],
    }
    if _FFMPEG_EXE:
        writer_kwargs['ffmpeg_log_level'] = 'error'

    with imageio.get_writer(output_path, **writer_kwargs) as writer:
        for frame in range(total_frames):
            # Advance solve state
            end_step = min((frame + 1) * steps_per_frame, len(steps))
            while state['step_idx'] < end_step:
                r, c, v = steps[state['step_idx']]
                current[r][c] = v
                if v == 0:
                    state['bt'] += 1
                state['step_idx'] += 1

            show_solved = (frame >= solved_at_frame)
            frame_arr   = _draw_frame(initial_grid, current, given,
                                      title, state['bt'], show_solved)
            writer.append_data(frame_arr)
