#!/usr/bin/env python3
"""
Cinematic AI Agent Revolution — V2
Faster pacing + dynamic evolving background + kinetic motion.
"""
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip

PROJECT  = "/home/muhammad_tayyab/bootlogix/projects/test-gatekeeper-001"
OUTPUT   = os.path.join(PROJECT, "output", "video.mp4")
FONT     = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_M   = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PORTRAIT = os.path.join(PROJECT, "portrait.jpg")
AUDIO    = os.path.join(PROJECT, "voiceover.mp3")
W, H     = 1920, 1080
FPS      = 30
SPEED    = 1.4

# ── Scene data (pre-scaled: original_seconds / SPEED) ────────────────────────
ORIG_SCENES = [
    {"start": 0.0,  "end": 4.0,  "type": "intro",         "accent": "#e63946"},
    {"start": 4.94, "end": 17.2, "type": "stat", "big": "72%",   "sub": "of enterprises now use or test AI agents",        "stat": "Up from 11% last year",              "accent": "#e63946"},
    {"start": 17.2, "end": 23.3, "type": "stat", "big": "$47B",  "sub": "projected market size by 2030",                    "stat": "$5T in global commerce by 2028",      "accent": "#f4a261"},
    {"start": 23.3, "end": 32.1, "type": "stat", "big": "32%",   "sub": "controlled by Microsoft & AWS",                    "stat": "345M Microsoft 365 seats ready",        "accent": "#2a9d8f"},
    {"start": 32.1, "end": 37.7, "type": "stat", "big": "900%",  "sub": "ROI on front desk automation",                   "stat": "20-40% cost reduction in hospitals",  "accent": "#e63946"},
    {"start": 37.7, "end": 42.8, "type": "stat", "big": "7 MO",   "sub": "capabilities double every",                      "stat": "From 30min to multi-month tasks",      "accent": "#f4a261"},
    {"start": 42.8, "end": 55.6, "type": "stat", "big": "84%",    "sub": "increasing AI agent investments this year",    "stat": "40% of Global 2000 roles by 2028",    "accent": "#2a9d8f"},
    {"start": 55.6, "end": 57.1, "type": "finale",             "accent": "#e63946"},
]
ORIG_CAPTIONS = [
    (0.0,   3.84,  "The AI agent revolution is here."),
    (4.94,  17.2,  "72% of enterprises now use or test AI agents, up from just 11% last year."),
    (17.2,  23.3,  "The market hits $47 billion by 2030."),
    (23.3,  32.1,  "Microsoft and AWS control a third of the infrastructure."),
    (32.1,  37.7,  "Healthcare sees 900% ROI."),
    (37.7,  42.8,  "Capabilities double every seven months."),
    (42.8,  55.6,  "84% of organizations are increasing investments this year."),
    (55.6,  57.1,  "It's now."),
]

# Scale times by SPEED
SCENES   = [{**s, "start": round(s["start"]/SPEED, 3), "end": round(s["end"]/SPEED, 3)} for s in ORIG_SCENES]
CAPTIONS = [(round(s/SPEED, 3), round(e/SPEED, 3), t) for s, e, t in ORIG_CAPTIONS]

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# ── Particle system ──────────────────────────────────────────────────────────
np.random.seed(42)
_PARTS = np.random.uniform(0, 1, (80, 6))
_PCOLS = [(230, 57, 70), (42, 157, 143), (244, 162, 97), (255, 255, 255)]

def _tick_parts():
    for p in _PARTS:
        p[0] += p[2] * 0.5
        p[1] += p[3] * 0.5
        p[4] += 0.016
        if p[0] < 0 or p[0] > 1: p[2] *= -1
        if p[1] < 0 or p[1] > 1: p[3] *= -1
        p[0] = max(0, min(1, p[0]))
        p[1] = max(0, min(1, p[1]))

# ── Portrait cache ──────────────────────────────────────────────────────────
_PM_CACHE = None
def _get_pm():
    global _PM_CACHE
    if _PM_CACHE is None:
        try:
            pm = Image.open(PORTRAIT).convert("RGBA")
            pm = pm.resize((200, 260), Image.LANCZOS)
            _PM_CACHE = pm
        except Exception as e:
            print(f"Portrait: {e}")
    return _PM_CACHE

# ── Core frame renderer ───────────────────────────────────────────────────────
def make_frame(t_global):
    # All drawing on PIL Image; return numpy array at end
    img = Image.new("RGB", (W, H), (4, 4, 10))
    draw = ImageDraw.Draw(img)

    # ── Dynamic evolving background ──────────────────────────────────────────
    wt = t_global * 0.4
    bg = (
        max(0, int(4  + np.sin(wt)       * 6 + np.sin(t_global*0.7) * 3)),
        max(0, int(4  + np.sin(wt+1.2)  * 4 + np.cos(t_global*0.5) * 2)),
        max(0, int(10 + np.sin(wt+2.4)  * 8 + np.cos(t_global*0.3) * 5)),
    )
    draw.rectangle([0, 0, W, H], fill=bg)

    # Moving scanline
    sy = int(t_global * 80) % H
    scan = Image.new("RGB", (W, H), (0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for dy in range(-3, 4):
        ya = (sy + dy) % H
        a = max(0, 1 - abs(dy) * 0.25)
        sd.line([(0, ya), (W, ya)], fill=(0, 180, 100), width=1)
    img = Image.blend(img, scan, 0.05)

    # Gradient blobs
    blob_configs = [
        ((230, 57, 70),  300, 0.4, 0.0),
        ((42,  157, 143), 250, 0.35, 2.1),
        ((244, 162, 97),  200, 0.5,  4.2),
    ]
    for i, cfg in enumerate(blob_configs):
        col, rad, spd, ph = cfg
        bx = int(W * (0.2 + i*0.3 + np.sin(t_global*spd+ph)*0.2))
        by = int(H * (0.3 + np.cos(t_global*spd*0.7+ph)*0.3))
        for r in range(rad, 0, -15):
            a = 0.018*(1 - r/rad)
            c = tuple(min(255, int(ch + a*255)) for ch in col)
            draw.ellipse([bx-r, by-r, bx+r, by+r], fill=c)

    # Grid
    ga = 0.035 + 0.01*np.sin(t_global*2)
    for x in range(0, W, 80):
        sh = int(np.sin(t_global + x/W*2)*3)
        draw.line([(x, 0+sh), (x, H)], fill=(20, 20, 50), width=1)
    for y in range(0, H, 80):
        sh = int(np.cos(t_global + y/H*2)*3)
        draw.line([(0+sh, y), (W, y)], fill=(20, 20, 50), width=1)

    # Particles
    _tick_parts()
    for p in _PARTS:
        px, py = int(p[0]*W), int(p[1]*H)
        sz = max(1, int(2 + p[5]*3))
        a  = max(0.1, 1.0 - p[4]/10)
        pc = _PCOLS[int(p[5]) % len(_PCOLS)]
        fc = tuple(int(c*a) for c in pc)
        draw.ellipse([px-sz, py-sz, px+sz, py+sz], fill=fc)

    # Speed burst at t=0
    if t_global < 0.4:
        intensity = (0.4 - t_global) / 0.4
        cx, cy = W//2, H//2
        for angle in range(0, 360, 12):
            rad = np.radians(angle + t_global * 150)
            for d in range(0, 600, 12):
                sx = int(cx + np.cos(rad)*d)
                sy2 = int(cy + np.sin(rad)*d)
                if 0 <= sx < W and 0 <= sy2 < H:
                    a = max(0, 1 - d/600)
                    draw.ellipse([sx-1, sy2-1, sx+1, sy2+1], fill=(255, 255, 255))

    # ── Scene overlay ───────────────────────────────────────────────────────
    active = next((s for s in SCENES if s["start"] <= t_global < s["end"]), None)
    ac = (230, 57, 70)  # default accent
    if active:
        stype   = active["type"]
        accent  = active["accent"]
        ac      = hex_to_rgb(accent)
        scene_t = t_global - active["start"]
        prog    = min(1.0, scene_t / 0.35)
        ease    = 1 - (1-prog)**3

        if stype == "intro":
            sc = int(120 * (0.7 + ease*0.3))
            draw.text((W//2, H//2 - 50),  "The Future",
                      font=ImageFont.truetype(FONT, sc), fill=(255,255,255), anchor="mm")
            lw = int(140 * ease)
            draw.rectangle([W//2-lw//2, H//2+15, W//2+lw//2, H//2+19], fill=ac)
            draw.text((W//2, H//2+55),  "Is Already Here",
                      font=ImageFont.truetype(FONT_M, 50), fill=(180,180,180), anchor="mm")

        elif stype == "finale":
            shk = int(3 * np.sin(t_global * 30) * max(0, 1 - scene_t/0.4))
            draw.text((W//2+shk, H//2-40),  "The Agents Are Here.",
                      font=ImageFont.truetype(FONT, 78), fill=(255,255,255), anchor="mm")
            draw.text((W//2+shk, H//2+60),  "The Question Is How Fast.",
                      font=ImageFont.truetype(FONT, 78), fill=ac, anchor="mm")

        else:
            sx = int(-80 * (1-ease))
            sy = int(25 * (1-ease))

            # Glow behind stat
            glow = Image.new("RGB", (W, H), (0, 0, 0))
            gd = ImageDraw.Draw(glow)
            for gr in range(180, 0, -12):
                a = 0.004*(1 - gr/180)
                gc = tuple(min(255, int(c + a*255)) for c in ac)
                gd.ellipse([60+sx-gr//2, 300+sy-gr//2,
                             260+sx+gr//2, 500+sy+gr//2], fill=gc)
            img = Image.blend(img, glow, 0.25 * ease)

            draw.text((80+sx, 250+sy),  "AI AGENTS",
                       font=ImageFont.truetype(FONT_M, 16), fill=ac)
            draw.text((80+sx, 295+sy),  active["big"],
                       font=ImageFont.truetype(FONT, 122), fill=(255,255,255))
            draw.text((80+sx, 435+sy),  active["sub"],
                       font=ImageFont.truetype(FONT_M, 30), fill=(155,155,155))
            bx, by = 70+sx, 525+sy
            draw.rounded_rectangle([bx, by, bx+420, by+42], radius=6,
                                    outline=(*ac, 60), width=1)
            draw.text((bx+10, by+9),  active["stat"],
                       font=ImageFont.truetype(FONT_M, 18), fill=(120,120,120))

    # ── Portrait ───────────────────────────────────────────────────────────
    pm = _get_pm()
    if pm is not None:
        pw, ph = pm.size
        # Glow ring
        for gr in range(pw//2+35, pw//2, -2):
            a = 0.012*(1-(gr-pw//2)/35)
            gc = tuple(min(255, int(c + a*200)) for c in ac)
            draw.ellipse([W-pw-40-gr, H-ph//2-60-gr,
                           W-pw-40+gr, H-ph//2-60+gr], fill=gc)
        img.paste(pm, (W-pw-40, H-ph-100), pm)

    # ── Caption ─────────────────────────────────────────────────────────────
    for cs, ce, ct in CAPTIONS:
        if cs <= t_global < ce:
            fade = 0.2
            if t_global - cs < fade:
                alpha = int(255 * (t_global - cs) / fade)
            elif ce - t_global < fade:
                alpha = int(255 * (ce - t_global) / fade)
            else:
                alpha = 255

            cw, ch = 960, 64
            cx_c, cy_c = (W - cw)//2, H - 90
            cap_bg = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            cbd = ImageDraw.Draw(cap_bg)
            cbd.rounded_rectangle([0, 0, cw-1, ch-1], radius=10,
                                  fill=(0, 0, 0, int(alpha * 0.82)))
            img = img.convert("RGBA")
            img.paste(cap_bg, (cx_c, cy_c), cap_bg)
            img = img.convert("RGB")
            draw = ImageDraw.Draw(img)
            draw.text((W//2, H - 58), ct,
                       font=ImageFont.truetype(FONT_M, 23), fill=(255,255,255), anchor="mm")
            break

    return np.array(img, dtype=np.uint8)

# ── Render ────────────────────────────────────────────────────────────────────
print(f"V2 Render — {SPEED}x speed")

result = subprocess.run([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", AUDIO
], capture_output=True, text=True)
audio_dur = float(result.stdout.strip())
target_dur = audio_dur / SPEED
print(f"Audio: {audio_dur:.1f}s → target: {target_dur:.1f}s")

video = (
    VideoClip()
    .with_updated_frame_function(make_frame)
    .with_duration(target_dur)
    .with_fps(FPS)
)
audio = AudioFileClip(AUDIO).with_speed_scaled(SPEED)
video = video.with_audio(audio)

TEMP = os.path.join(PROJECT, "output", "temp_v2.mp4")
video.write_videofile(TEMP, codec="libx264", audio_codec="aac",
                       preset="fast", bitrate="10000k", threads=4)
print(f"\n✅ {OUTPUT}")
