import os
import urllib.request
from math import ceil

# Prefer imageio_ffmpeg's bundled binary over the system ffmpeg
try:
    import imageio_ffmpeg as _iio_ffmpeg
    _FFMPEG_EXE = _iio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    _FFMPEG_EXE = None

# ── PIL-based frame renderer ──────────────────────────────────────────────────
from PIL import Image, ImageDraw, ImageFont

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
_EPILOGUE_URL = (
    'https://raw.githubusercontent.com/google/fonts/main/ofl/epilogue/'
    'Epilogue%5Bwght%5D.ttf'
)
_EPILOGUE_PATH = os.path.join(_FONT_DIR, 'Epilogue-var.ttf')


def _ensure_epilogue():
    """Download Epilogue variable font to animation/fonts/ if not present."""
    if os.path.exists(_EPILOGUE_PATH):
        return
    os.makedirs(_FONT_DIR, exist_ok=True)
    try:
        urllib.request.urlretrieve(_EPILOGUE_URL, _EPILOGUE_PATH)
    except Exception:
        pass


_ensure_epilogue()

# Frame geometry (pixels)
_W, _H   = 500, 540
_MARGIN  = 25
_TOP     = 58        # top of grid
_CELL    = 50
_GRID_W  = _CELL * 9  # 450px — grid right edge at x=475, fits in 500px canvas

# Colours
_C_CANVAS      = '#F8F8F6'
_C_BG_GIVEN    = '#F08792'   # RGB(240,135,146) — medium pink for given cells
_C_DIGIT_GIVEN = '#1A1A2E'
_C_DIGIT_PLACE = '#8B1A26'   # deep rose — darker for contrast against #CC0000 backtrack red
_C_GRID_THIN   = '#BBBBBB'
_C_GRID_THICK  = '#2A2A2A'
_C_SOLVED_BG   = '#84CC16'   # lime green
_C_SOLVED_TEXT = '#1A3300'   # dark text for lime pill
_C_TITLE       = '#1A1A2E'
_C_BT          = '#CC0000'


def _load_font(size, bold=False):
    # Prefer Epilogue variable font (downloaded to animation/fonts/)
    if os.path.exists(_EPILOGUE_PATH):
        try:
            font = ImageFont.truetype(_EPILOGUE_PATH, size)
            font.set_variation_by_axes([700 if bold else 400])
            return font
        except (IOError, OSError, AttributeError):
            pass
    # Fallback to system fonts
    candidates = []
    if bold:
        candidates = [
            'calibrib.ttf', 'CalibriB.ttf',
            'seguisb.ttf',
            'segoeuib.ttf',
            'arialbd.ttf',
            'DejaVuSans-Bold.ttf',
            'LiberationSans-Bold.ttf',
        ]
    candidates += [
        'calibri.ttf', 'Calibri.ttf',
        'segoeui.ttf', 'SegoeUI.ttf',
        'arial.ttf', 'Arial.ttf',
        'DejaVuSans.ttf',
        'FreeSans.ttf',
        'LiberationSans-Regular.ttf',
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            pass
    return ImageFont.load_default()


_FONT_DIGIT  = _load_font(26, bold=True)
_FONT_TITLE  = _load_font(20, bold=True)
_FONT_BT     = _load_font(15)
_FONT_SOLVED = _load_font(24, bold=True)


def _draw_checkmark(draw, cx, cy, size=9, color='white', width=3):
    """Geometric tick mark — reliable across all fonts/platforms."""
    pts = [
        (int(cx - size),      int(cy)),
        (int(cx - size // 3), int(cy + size * 0.8)),
        (int(cx + size),      int(cy - size * 0.7)),
    ]
    draw.line(pts, fill=color, width=width)


def _draw_frame(initial_grid, current, given, title, bt_count, show_solved):
    """Return a (W x H x 3) uint8 numpy array for one animation frame."""
    import numpy as np

    img  = Image.new('RGB', (_W, _H), _C_CANVAS)
    draw = ImageDraw.Draw(img)

    # ── title ────────────────────────────────────────────────────────────────
    try:
        draw.text((_W // 2, 30), title, fill=_C_TITLE,
                  font=_FONT_TITLE, anchor='mm')
    except Exception:
        draw.text((_W // 2 - len(title) * 5, 20), title, fill=_C_TITLE)

    # ── given-cell backgrounds ────────────────────────────────────────────────
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
            color = _C_DIGIT_GIVEN if (r, c) in given else _C_DIGIT_PLACE
            cx = _MARGIN + c * _CELL + _CELL // 2
            cy = _TOP    + r * _CELL + _CELL // 2
            try:
                draw.text((cx, cy), str(val), fill=color,
                          font=_FONT_DIGIT, anchor='mm')
            except Exception:
                draw.text((cx - 7, cy - 7), str(val), fill=color)

    # ── grid lines ────────────────────────────────────────────────────────────
    for i in range(10):
        thick = (i % 3 == 0)
        lw    = 3 if thick else 1
        clr   = _C_GRID_THICK if thick else _C_GRID_THIN
        x = _MARGIN + i * _CELL
        y = _TOP    + i * _CELL
        draw.line([(x, _TOP), (x, _TOP + _GRID_W)], fill=clr, width=lw)
        draw.line([(_MARGIN, y), (_MARGIN + _GRID_W, y)], fill=clr, width=lw)

    # ── SOLVED pill — floating on grid, sized to text, "SOLVED" then checkmark
    if show_solved:
        label = 'SOLVED'
        try:
            bbox = draw.textbbox((0, 0), label, font=_FONT_SOLVED)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            tw, th = 88, 24

        pad_x    = 18
        ck_space = 30   # gap + checkmark width
        pill_w   = pad_x + tw + ck_space + pad_x
        pill_h   = max(th + 22, 46)

        gcx = _MARGIN + _GRID_W // 2   # horizontal centre of grid
        gcy = _TOP    + _GRID_W // 2   # vertical centre of grid
        bx, by   = gcx - pill_w // 2, gcy - pill_h // 2
        bx2, by2 = bx + pill_w,       by + pill_h

        try:
            draw.rounded_rectangle([bx, by, bx2, by2],
                                   radius=pill_h // 2, fill=_C_SOLVED_BG)
        except AttributeError:
            draw.rectangle([bx, by, bx2, by2], fill=_C_SOLVED_BG)

        # "SOLVED" text left-aligned within pill
        try:
            draw.text((bx + pad_x, gcy), label, fill=_C_SOLVED_TEXT,
                      font=_FONT_SOLVED, anchor='lm')
        except Exception:
            draw.text((bx + pad_x, gcy - 12), label, fill=_C_SOLVED_TEXT, font=_FONT_SOLVED)

        # Geometric checkmark to the right of the text
        _draw_checkmark(draw,
                        cx=bx + pad_x + tw + 18, cy=gcy,
                        size=10, color=_C_SOLVED_TEXT, width=3)

    # ── backtrack counter — bottom-right, red ────────────────────────────────
    bt_label = f'Backtracks: {bt_count}'
    bt_y = _TOP + _GRID_W + 22
    try:
        draw.text((_MARGIN + _GRID_W, bt_y), bt_label,
                  fill=_C_BT, font=_FONT_BT, anchor='rm')
    except Exception:
        draw.text((_MARGIN + _GRID_W - 120, bt_y - 8), bt_label, fill=_C_BT)

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

            show_solved = (frame >= solved_at_frame) or (state['step_idx'] >= len(steps))
            frame_arr   = _draw_frame(initial_grid, current, given,
                                      title, state['bt'], show_solved)
            writer.append_data(frame_arr)
