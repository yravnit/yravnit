"""Renders hero.gif from a black hole GIF: Bayer-dithered into five violet tones on 4px cells.

    python hero.py path/to/blackhole.gif

Needs: pip install pillow numpy"""
import os, sys
import numpy as np
from PIL import Image, ImageSequence

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "blackhole.gif")
OUT_W, OUT_H, CELL = 1200, 400, 4          # output size and dither cell size in px
GW, GH = OUT_W // CELL, OUT_H // CELL

PAL = np.array([(0x06,0x05,0x0d),(0x1b,0x11,0x4a),(0x5a,0x34,0xd4),(0xb5,0x9a,0xff),(0xf3,0xec,0xff)], dtype=np.uint8)

def bayer(n):
    m = np.array([[0]])
    while m.shape[0] < n: m = np.block([[4*m, 4*m+2], [4*m+3, 4*m+1]])
    return (m + .5) / (n*n)
T = np.tile(bayer(8), (GH//8 + 1, GW//8 + 1))[:GH, :GW]

def frame(im):
    im = im.convert("RGB").crop((0, 90, 736, 336)).resize((GW, GH), Image.LANCZOS)    # crop keeps the whole ring in frame
    a = np.asarray(im).astype(np.float32) / 255
    lum = .2126*a[..., 0] + .7152*a[..., 1] + .0722*a[..., 2]
    lum = np.clip(.75*lum + .45*a[..., 2]*a[..., 0], 0, 1)                             # the blue glow carries detail luma flattens
    lum = np.clip((lum - .03) / .80, 0, 1) ** .85
    lv = len(PAL) - 1; s = lum * lv; b = np.floor(s)
    idx = np.clip(b + ((s - b) > T), 0, lv).astype(int)
    return Image.fromarray(PAL[idx]).resize((OUT_W, OUT_H), Image.NEAREST)

if __name__ == "__main__":
    frames = [frame(f.copy()) for i, f in enumerate(ImageSequence.Iterator(Image.open(SRC))) if i % 2 == 0]
    pal = Image.new("P", (1, 1)); pal.putpalette(list(PAL.flatten()) + [0]*(768 - PAL.size))
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    q[0].save(os.path.join(HERE, "hero.gif"), save_all=True, append_images=q[1:], duration=100, loop=0, optimize=True, disposal=1)
    print(len(frames), "frames")
