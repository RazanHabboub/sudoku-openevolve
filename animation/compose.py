import subprocess

try:
    import imageio_ffmpeg
    _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    _FFMPEG = 'ffmpeg'


def compose_4up(clips, output_path):
    """Tile four clips in a 2x2 grid. All clips must have the same duration."""
    a, b, c, d = clips
    cmd = [
        _FFMPEG, '-y',
        '-i', a, '-i', b, '-i', c, '-i', d,
        '-filter_complex',
        '[0:v][1:v][2:v][3:v]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]',
        '-map', '[v]',
        '-vcodec', 'libx264', '-pix_fmt', 'yuv420p',
        output_path,
    ]
    subprocess.run(cmd, check=True)


def compose_2up(clip1, clip2, output_path):
    """Place two clips side by side. Both clips must have the same duration."""
    cmd = [
        _FFMPEG, '-y',
        '-i', clip1, '-i', clip2,
        '-filter_complex', '[0:v][1:v]hstack=inputs=2[v]',
        '-map', '[v]',
        '-vcodec', 'libx264', '-pix_fmt', 'yuv420p',
        output_path,
    ]
    subprocess.run(cmd, check=True)
