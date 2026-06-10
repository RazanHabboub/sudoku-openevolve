import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from animation.tests.conftest import TEST_PUZZLE
from animation.solvers.backtracking_record import solve
from animation.render import render_clip

def _ffmpeg_available():
    import shutil
    if shutil.which('ffmpeg') is not None:
        return True
    try:
        import imageio_ffmpeg  # noqa: F401
        return True
    except ImportError:
        return False

@pytest.mark.skipif(
    not _ffmpeg_available(),
    reason="ffmpeg not available"
)
def test_render_creates_mp4():
    _, steps, _ = solve([row[:] for row in TEST_PUZZLE])
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "test.mp4")
        render_clip(TEST_PUZZLE, steps, "Test Solver", out,
                    steps_per_frame=max(1, len(steps) // 30),
                    total_frames=30, fps=10)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 1000
