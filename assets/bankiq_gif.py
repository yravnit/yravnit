"""Renders bankiq.gif: a dithered ripple field with the BankIQ name and the role in front of it.
Nothing about the work itself appears in the image.

    python bankiq_gif.py

Needs: pip install pillow numpy
Fonts in fonts/: Ethnocentric-Regular.ttf (your own copy, not included), JetBrainsMono-Medium.ttf and Inter-SemiBold.ttf (included)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
ETHNO, MONO = (os.path.join(FONTS, f) for f in ("Ethnocentric-Regular.ttf", "JetBrainsMono-Medium.ttf"))
for f in (ETHNO, MONO):
    if not os.path.exists(f): sys.exit(f"Missing font file: {f}")

WORDMARK, ROLE = "BANKIQ", "AI ENGINEER INTERN"
N, W, H, CELL, MS = 72, 800, 432, 4, 80               # frames, size, dither cell, frame time
GW, GH = W // CELL, H // CELL
PAL = np.array([(0x06,0x05,0x0d),(0x1b,0x11,0x4a),(0x5a,0x34,0xd4),(0xb5,0x9a,0xff),(0xf3,0xec,0xff)], dtype=np.uint8)

def bayer(n):
    m = np.array([[0]])
    while m.shape[0] < n: m = np.block([[4*m, 4*m+2], [4*m+3, 4*m+1]])
    return (m + .5) / (n*n)
T = np.tile(bayer(8), (GH//8 + 1, GW//8 + 1))[:GH, :GW]

def quant(lum):
    lv = len(PAL) - 1; s = np.clip(lum, 0, 1) * lv; b = np.floor(s)
    return np.clip(b + ((s - b) > T), 0, lv).astype(int)

def ripple(phase):
    """Two wave sources whose rings interfere. phase runs through whole cycles, so the loop is seamless."""
    yy, xx = np.mgrid[0:GH, 0:GW].astype(np.float32)
    cx, cy, d = GW/2, GH/2, GW*.16
    r1, r2 = np.hypot(xx - (cx - d), yy - cy), np.hypot(xx - (cx + d), yy - cy)
    k = 2*np.pi / (GW*.05); s = np.sin(k*r1 - phase) + np.sin(k*r2 - phase)
    rc = np.hypot((xx - cx)/(GW*.5), (yy - cy)/(GH*.5*1.05))
    lum = np.exp(-(rc/.95)**2.2) * (.5 + .25*s)
    return np.clip((lum - .2)/.65, 0, 1) ** 1.15

def wordmark():
    f = ImageFont.truetype(ETHNO, 100); f = ImageFont.truetype(ETHNO, int(100*600/(f.getlength(WORDMARK) + 6)))   # 600px wide
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), WORDMARK, font=f, stroke_width=3)
    d.text(((W - (bb[2] - bb[0]))/2 - bb[0], 150 - bb[1]), WORDMARK, font=f, fill=255, stroke_width=3, stroke_fill=255)
    return np.asarray(im.resize((GW, GH), Image.BOX), np.float32)/255, bb[3] - bb[1]
COV, WORD_H = wordmark()
HALO = np.asarray(Image.fromarray((COV*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3.2)), np.float32)/255

def spaced(d, x, y, s, font, fill, sp):
    for c in s: d.text((x, y), c, font=font, fill=fill); x += font.getlength(c) + sp

def frame(i):
    lum = ripple(2*2*math.pi*i/N) * (1 - np.clip(HALO*3.4, 0, .94))            # ring pattern fades out behind the letters
    idx = quant(lum); idx[COV > .42] = 4
    im = Image.fromarray(PAL[idx]).resize((W, H), Image.NEAREST).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    f = ImageFont.truetype(MONO, 16); w = sum(f.getlength(c) + 4 for c in ROLE) - 4; y = 150 + WORD_H + 34
    d.rounded_rectangle([W/2 - w/2 - 18, y - 11, W/2 + w/2 + 18, y + 31], 10, fill=(6, 5, 13, 235), outline=(0x2a, 0x26, 0x44, 255))
    spaced(d, W/2 - w/2, y, ROLE, f, (0xd8, 0xd0, 0xff), 4)
    return im

if __name__ == "__main__":
    frames = [frame(i) for i in range(N)]
    sample = frames[::6]; mos = Image.new("RGB", (W, H*len(sample)))
    for k, s in enumerate(sample): mos.paste(s, (0, k*H))
    pal = mos.quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    out = os.path.join(HERE, "bankiq.gif")
    q[0].save(out, save_all=True, append_images=q[1:], duration=MS, loop=0, optimize=True, disposal=1)
    print("bankiq.gif", len(frames), "frames", os.path.getsize(out)//1024, "KB")
