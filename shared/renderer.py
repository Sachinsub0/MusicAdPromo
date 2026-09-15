from __future__ import annotations
import os, math, tempfile, subprocess
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

W, H, FPS = 540, 960, 30

# Keep every lyric safely inside the vertical-video frame.
SAFE_X = 34
MAX_TEXT_W = W - SAFE_X * 2
MAX_LINES = 4
MAX_FONT = 64
MIN_FONT = 28
LINE_GAP = 12
WORD_GAP = 14

def _font(n):
    for p in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, n)
            except Exception:
                pass
    return ImageFont.load_default()

def _pulse(t, events, width=.12):
    return max([max(0, 1 - abs(t-e)/width) for e in events] + [0])

def _measure(draw, word, font):
    b = draw.textbbox((0, 0), word, font=font)
    return b[2] - b[0], b[3] - b[1]

def _wrap_words(draw, words, font_size):
    """Greedy wrap that guarantees each line is within MAX_TEXT_W."""
    f = _font(font_size)
    lines, line = [], []
    line_w = 0

    for w in words:
        ww, _ = _measure(draw, w["word"], f)

        # A single unusually long token must still fit.
        if ww > MAX_TEXT_W:
            return None

        proposed = ww if not line else line_w + WORD_GAP + ww
        if line and proposed > MAX_TEXT_W:
            lines.append(line)
            line = [w]
            line_w = ww
        else:
            line.append(w)
            line_w = proposed

    if line:
        lines.append(line)

    return lines if len(lines) <= MAX_LINES else None

def _layout_phrase(draw, words):
    """
    Calculate the phrase layout ONCE.
    Try the largest font first, wrap to <=4 centered lines,
    then shrink until the entire phrase fits the safe area.
    """
    chosen_size = MIN_FONT
    chosen_lines = None

    for size in range(MAX_FONT, MIN_FONT - 1, -2):
        lines = _wrap_words(draw, words, size)
        if lines is not None:
            chosen_size = size
            chosen_lines = lines
            break

    # Extreme fallback: keep shrinking rather than crop any lyric.
    if chosen_lines is None:
        size = MIN_FONT
        while size >= 16:
            lines = _wrap_words(draw, words, size)
            if lines is not None:
                chosen_size, chosen_lines = size, lines
                break
            size -= 2

    if chosen_lines is None:
        chosen_size = 16
        chosen_lines = [[w] for w in words]

    f = _font(chosen_size)
    _, line_h = _measure(draw, "Ag", f)
    block_h = len(chosen_lines) * line_h + (len(chosen_lines)-1) * LINE_GAP
    top = max(120, min(H - 120 - block_h, (H - block_h) / 2 + 65))

    positions = {}
    for li, line in enumerate(chosen_lines):
        widths = [_measure(draw, w["word"], f)[0] for w in line]
        total = sum(widths) + WORD_GAP * max(0, len(line)-1)
        x = (W - total) / 2
        y = top + li * (line_h + LINE_GAP)

        for w, ww in zip(line, widths):
            # Store a fixed center so active-word scaling never reflows neighbors.
            positions[id(w)] = {
                "cx": x + ww/2,
                "cy": y + line_h/2,
                "base_w": ww,
                "font_size": chosen_size,
            }
            x += ww + WORD_GAP

    return positions

def render(plan, audio, out, background=None):
    tmp = tempfile.mkdtemp(prefix="v6_")
    fd = os.path.join(tmp, "f")
    os.makedirs(fd)

    duration = float(plan["duration"])
    words = plan["words"]
    beats = plan["timeline"]["beats"]
    ons = plan["timeline"]["onsets"]

    if background and os.path.exists(background):
        bg = Image.open(background).convert("RGB")
        ratio = max(W/bg.width, H/bg.height)
        bg = bg.resize(
            (int(bg.width*ratio), int(bg.height*ratio)),
            Image.Resampling.LANCZOS
        )
        left = (bg.width-W)//2
        top = (bg.height-H)//2
        bg = bg.crop((left, top, left+W, top+H))
    else:
        bg = Image.new("RGB", (W, H), (10, 10, 18))

    # Phrase segmentation stays timing-aware, but phrase layout is now responsive.
    groups, g = [], []
    for w in words:
        # Allow longer groups now; wrapping handles the screen width.
        if g and (len(g) >= 10 or w["start"] - g[-1]["end"] > .55):
            groups.append(g)
            g = []
        g.append(w)
    if g:
        groups.append(g)

    # Precompute stable layouts. No word can push another word off-screen mid-animation.
    probe = Image.new("RGB", (W, H))
    probe_draw = ImageDraw.Draw(probe)
    layouts = {id(g): _layout_phrase(probe_draw, g) for g in groups}

    for fi in range(round(duration*FPS)):
        t = fi/FPS
        beatp = _pulse(t, beats, .09)
        onp = _pulse(t, ons, .07)

        # Restrained animated-cover-art background.
        scale = 1.035 + .018*(t/duration) + .008*beatp
        nw, nh = int(W*scale), int(H*scale)
        im = bg.resize((nw, nh), Image.Resampling.LANCZOS)
        x = (nw-W)//2 + int(math.sin(t*.35)*4)
        y = (nh-H)//2
        im = im.crop((x, y, x+W, y+H))

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 75))
        im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
        d = ImageDraw.Draw(im)

        active = next(
            (g for g in groups if g[0]["start"]-.12 <= t <= g[-1]["end"]+.25),
            None
        )

        if active:
            positions = layouts[id(active)]

            for w in active:
                pos = positions[id(w)]
                is_active = w["start"] <= t <= w["end"]

                # Fixed slot + center-based animation.
                base_size = pos["font_size"]
                sc = 1.0
                dx = dy = 0.0
                local = (t-w["start"]) / max(.04, w["end"]-w["start"])

                if is_active:
                    # Beat/onset changes HOW the word moves, never its timestamp.
                    sc += .10*beatp + .08*onp
                    if w["effect"] == "shake":
                        dx = math.sin(t*60)*7
                    elif w["effect"] == "fall":
                        dy = -28*(1-max(0, min(1, local)))
                    elif w["effect"] == "rise":
                        dy = 28*(1-max(0, min(1, local)))
                    elif w["effect"] == "bounce":
                        dy = -abs(math.sin(local*math.pi*2))*20
                    elif w["effect"] == "stretch":
                        sc += .10*max(0, min(1, local))
                    elif w["effect"] == "pulse":
                        sc += .07*math.sin(max(0, local)*math.pi)

                ff = _font(max(14, int(base_size*sc)))
                bb = d.textbbox((0, 0), w["word"], font=ff)
                tw, th = bb[2]-bb[0], bb[3]-bb[1]

                # Upcoming words remain visible but subdued.
                if t < w["start"]:
                    fill = (160, 160, 165)
                elif is_active:
                    fill = (255, 232, 180)
                else:
                    fill = (220, 220, 220)

                tx = pos["cx"] - tw/2 + dx
                ty = pos["cy"] - th/2 + dy

                # Final defensive clamp: rendered glyph itself cannot leave safe margins.
                tx = max(SAFE_X, min(tx, W-SAFE_X-tw))

                d.text(
                    (tx, ty),
                    w["word"],
                    font=ff,
                    fill=fill,
                    stroke_width=2,
                    stroke_fill=(0, 0, 0),
                )

        im.save(os.path.join(fd, f"{fi:05d}.jpg"), quality=92)

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    silent = os.path.join(tmp, "silent.mp4")
    subprocess.run([
        ff, "-y", "-loglevel", "error",
        "-framerate", str(FPS),
        "-i", os.path.join(fd, "%05d.jpg"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", silent
    ], check=True)

    subprocess.run([
        ff, "-y", "-loglevel", "error",
        "-i", silent,
        "-ss", str(plan["clip_start"]), "-t", str(duration),
        "-i", audio,
        "-map", "0:v", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", out
    ], check=True)
    return out
