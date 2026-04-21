#!/usr/bin/env python3
"""
Cinematic AI Agent Revolution video renderer.
MoviePy 2.x API — fast CPU rendering.
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

SCENES = [
    {"start": 0.0,  "end": 4.0,  "type": "intro",         "accent": "#e63946"},
    {"start": 4.94, "end": 17.2, "type": "stat", "big": "72%",   "sub": "of enterprises now use or test AI agents",        "stat": "Up from 11% last year",              "accent": "#e63946"},
    {"start": 17.2, "end": 23.3, "type": "stat", "big": "$47B",  "sub": "projected market size by 2030",                    "stat": "$5T in global commerce by 2028",      "accent": "#f4a261"},
    {"start": 23.3, "end": 32.1, "type": "stat", "big": "32%",   "sub": "controlled by Microsoft & AWS",                    "stat": "345M Microsoft 365 seats ready",        "accent": "#2a9d8f"},
    {"start": 32.1, "end": 37.7, "type": "stat", "big": "900%",   "sub": "ROI on front desk automation",                   "stat": "20-40% cost reduction in hospitals",  "accent": "#e63946"},
    {"start": 37.7, "end": 42.8, "type": "stat", "big": "7 MO",   "sub": "capabilities double every",                      "stat": "From 30min to multi-month tasks",      "accent": "#f4a261"},
    {"start": 42.8, "end": 55.6, "type": "stat", "big": "84%",    "sub": "increasing AI agent investments this year",    "stat": "40% of Global 2000 roles by 2028",    "accent": "#2a9d8f"},
    {"start": 55.6, "end": 57.1, "type": "finale",             "accent": "#e63946"},
]

CAPTIONS = [
    (0.0,   3.84,  "The AI agent revolution is here."),
    (4.94,  17.2,  "72% of enterprises now use or test AI agents, up from just 11% last year."),
    (17.2,  23.3,  "The market hits $47 billion by 2030."),
    (23.3,  32.1,  "Microsoft and AWS control a third of the infrastructure."),
    (32.1,  37.7,  "Healthcare sees 900% ROI."),
    (37.7,  42.8,  "Capabilities double every seven months."),
    (42.8,  55.6,  "84% of organizations are increasing investments this year."),
    (55.6,  57.1,  "It's now."),
]

def hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# Pre-compute & cache portrait overlay (no per-frame reload)
_portrait_cache = [None, None]  # [rgba_array, mask_array]

def get_portrait():
    if _portrait_cache[0] is None:
        try:
            pm = Image.open(PORTRAIT).convert("RGBA")
            pw, ph = 220, 280
            pm = pm.resize((pw, ph), Image.LANCZOS)
            _portrait_cache[0] = pm
        except Exception as e:
            print(f"Portrait load error: {e}")
            return None, None
    return _portrait_cache[0], None

def pil_frame(t):
    img = Image.new("RGB", (W, H), (5, 5, 8))
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(0, H, 2):
        ratio = y / H
        draw.line([(0, y), (W, y)], fill=(int(5+ratio*5), int(5+ratio*3), int(8+ratio*16)))

    # Animated orbs
    t_n = t % 10.0
    cx1 = int(W * 0.3 + np.sin(t_n * 0.4) * 80)
    cy1 = int(H * 0.3 + np.cos(t_n * 0.3) * 60)
    cx2 = int(W * 0.7 + np.cos(t_n * 0.35) * 70)
    cy2 = int(H * 0.65 + np.sin(t_n * 0.25) * 50)

    for cx, cy, color, radius in [(cx1, cy1, (230, 57, 70), 220), (cx2, cy2, (42, 157, 143), 180)]:
        for r in range(radius, 0, -12):
            alpha = int(55 * (1 - r / radius))
            col = tuple(max(0, min(255, c + alpha)) for c in color)
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=col)

    # Active scene
    active = next((s for s in SCENES if s["start"] <= t < s["end"]), None)
    if not active:
        return np.array(img)

    stype, accent = active["type"], active["accent"]
    ac = hex_to_rgb(accent)

    if stype == "intro":
        draw.text((W//2, H//2 - 50),  "The Future",      font=ImageFont.truetype(FONT,  110), fill=(255,255,255), anchor="mm")
        draw.rectangle([W//2-60, H//2+10, W//2+60, H//2+14], fill=ac)
        draw.text((W//2, H//2 + 50),  "Is Already Here", font=ImageFont.truetype(FONT_M,  54),  fill=(180,180,180), anchor="mm")

    elif stype == "finale":
        draw.text((W//2, H//2 - 40),  "The Agents Are Here.",      font=ImageFont.truetype(FONT, 80), fill=(255,255,255), anchor="mm")
        draw.text((W//2, H//2 + 60),  "The Question Is How Fast.",  font=ImageFont.truetype(FONT, 80), fill=ac,            anchor="mm")

    else:
        draw.text((80, 270), "AI AGENTS",        font=ImageFont.truetype(FONT_M, 18), fill=ac)
        draw.text((80, 320), active["big"],      font=ImageFont.truetype(FONT, 130),  fill=(255,255,255))
        draw.text((80, 470), active["sub"],      font=ImageFont.truetype(FONT_M, 34), fill=(170,170,170))
        draw.rounded_rectangle([70, 560, 470, 605], radius=8, outline=(255,255,255,40), width=1)
        draw.text((80, 570), active["stat"],     font=ImageFont.truetype(FONT_M, 20), fill=(130,130,130))

    # Portrait overlay — using composite (safe)
    pm, _ = get_portrait()
    if pm is not None:
        try:
            pw, ph = pm.size
            # Shadow
            shadow = Image.new("RGBA", (pw+20, ph+20), (0,0,0,0))
            sd = ImageDraw.Draw(shadow)
            sd.rounded_rectangle([10, 10, pw+10, ph+10], radius=16, fill=(0,0,0,130))
            # Mask
            mask = Image.new("L", (pw+20, ph+20), 0)
            md = ImageDraw.Draw(mask)
            md.rounded_rectangle([0, 0, pw+19, ph+19], radius=16, fill=255)
            shadow.putalpha(mask)
            # Composite onto base
            base = Image.fromarray(np.array(img))
            base.paste(shadow, (W-pw-50, H-ph-120), shadow)
            base.paste(pm, (W-pw-40, H-ph-110), pm)
            img = np.array(base.convert("RGB"))
            draw = ImageDraw.Draw(img)
        except Exception as e:
            print(f"Portrait error: {e}")

    # Caption
    for cs, ce, ct in CAPTIONS:
        if cs <= t < ce:
            fade_dur = 0.3
            alpha = 255
            if t - cs < fade_dur:
                alpha = int(255 * (t - cs) / fade_dur)
            elif ce - t < fade_dur:
                alpha = int(255 * (ce - t) / fade_dur)

            cw, ch = 960, 72
            cx_c, cy_c = (W - cw)//2, H - 110
            bg = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            bd = ImageDraw.Draw(bg)
            bd.rounded_rectangle([0, 0, cw-1, ch-1], radius=12, fill=(0, 0, 0, int(alpha * 0.8)))
            base = Image.fromarray(np.array(img))
            base.paste(bg, (cx_c, cy_c), bg)
            img = np.array(base.convert("RGB"))
            draw = ImageDraw.Draw(img)
            draw.text((W//2, H - 74), ct, font=ImageFont.truetype(FONT_M, 25), fill=(255, 255, 255), anchor="mm")
            break

    return np.array(img)

# ── Render ────────────────────────────────────────────────────────────────────
print("Building cinematic video...")

result = subprocess.run([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", AUDIO
], capture_output=True, text=True)
audio_dur = float(result.stdout.strip())
print(f"Audio duration: {audio_dur}s")

video = (
    VideoClip()
    .with_updated_frame_function(lambda t: pil_frame(t))
    .with_duration(audio_dur)
    .with_fps(FPS)
)
audio = AudioFileClip(AUDIO)
video = video.with_audio(audio)

print("Writing video + audio...")
TEMP = os.path.join(PROJECT, "output", "temp_video.mp4")
video.write_videofile(
    TEMP, codec="libx264", audio_codec="aac",
    preset="fast", bitrate="8000k", threads=4,
)
print(f"\n✅ Done! Output: {OUTPUT}")
