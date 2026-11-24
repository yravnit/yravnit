"""Regenerates every SVG, thumbnail and the README one level up. Edit CONFIG, then run: python build.py
Needs: pip install pillow numpy fonttools

Project media: drop <slug>.gif (first choice) or <slug>.jpeg / .jpg / .png (second choice) next to this file,
for example drag.gif, psh.jpeg, snag.gif. build.py crops it to the card ratio and writes media-<slug>.*.
Without a file, a dithered placeholder is generated. A project can also name a file with media="path".
With relay=True the GIFs take turns instead of all playing at once.
The hero GIF comes from hero.py and the BankIQ image from bankiq_gif.py."""
import base64, io, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from xml.sax.saxutils import escape as esc
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))

CONFIG = dict(
    links=[  # (label, url, icon)
        ("github.com/yravnit", "https://github.com/yravnit/", "github"),
        ("linkedin.com/in/yravnit", "https://www.linkedin.com/in/yravnit/", "linkedin"),
        ("leetcode.com/u/ravnit", "https://leetcode.com/u/ravnit/", "leetcode"),
        ("yravnit@gmail.com", "mailto:yravnit@gmail.com", "gmail"),
    ],
    relay=True,   # True: the project GIFs take turns. False: they all play at once.
    tagline=["Pursuing Engineering in Mumbai", "AI Engineer Intern at BankIQ", "Love making Full Stack Systems and AI Applications"],
    # font is your own Ethnocentric file (kept out of the repo, see fonts/README.txt). width is the name width in px.
    name=dict(text="RAVNIT YADAV", font="fonts/Ethnocentric-Regular.ttf", width=960, tracking=.07, weight=2.5),
)

# logos = icon slugs from icons.json, drawn left-aligned in the strip. url = source repo (the open repo strip). live = where the media image links, defaults to url.
# url=None draws a disabled "PRIVATE REPO" strip. placeholder=False hides the PLACEHOLDER ART tag on generated art.
PROJECTS = [
    dict(slug="bankiq", name="BANKIQ", kind="pipeline", placeholder=False,
         desc=["LLM-powered authoring assistant for fraud rules.",
               "Natural language goes through an intermediate form,",
               "schema validation and a deterministic DSL renderer."],
         logos=["python", "nodedotjs", "typescript", "llm"], url=None),
    dict(slug="drag", name="DRAG", kind="graph", placeholder=True,
         desc=["Developer RAG platform over GitHub repositories.",
               "Tree-sitter parses 13 languages into semantic chunks.",
               "98.6% Hit@5 held-out, reindexing 4.3x faster."],
         logos=["nextdotjs", "typescript", "postgresql", "vercel"], url="https://github.com/yravnit/drag"),
    dict(slug="psh", name="PSH", kind="terminal", placeholder=True, poster="fullest",
         desc=["POSIX-inspired interactive shell in Python.",
               "State-machine parser at 23k+ ops/sec, OS-level pipelines.",
               "170+ tests, differentially tested against bash and dash."],
         logos=["python"], url="https://github.com/yravnit/PSH"),
    dict(slug="snag", name="SNAG", kind="signal", placeholder=True, wip=True,
         desc=["QA and PM agent for B2B SaaS product research.",
               "Turns customer reviews into bugs ranked P0/P1 and",
               "RICE-scored initiatives, with user stories and exports."],
         logos=["nextdotjs", "typescript", "googlegemini", "firecrawl", "zod"],
         url="https://github.com/yravnit/snag"),
]

# (row label, [(chip label, icon slug)]) taken from the resume skills and project bullets
STACK = [
    ("languages", [("python", "python"), ("typescript", "typescript"), ("javascript", "javascript"), ("c++", "cplusplus"), ("sql", "sql")]),
    ("frameworks", [("react", "react"), ("next.js", "nextdotjs"), ("node", "nodedotjs"), ("express", "express")] ),
    ("data / apis", [("postgresql", "postgresql"), ("pgvector", "waypoints"), ("mongodb", "mongodb"), ("rest apis", "swagger")]),
    ("infra", [("docker", "docker"), ("ci/cd", "githubactions"), ("cloudflare workers", "cloudflareworkers"), ("git", "git"), ("github", "github"), ("vercel workflows", "vercel")]),
    ("ai / ml", [("langgraph", "langgraph"), ("langchain", "langchain"), ("hugging face", "huggingface"), ("rag", "rag"), ("vector databases", "vectordb")]),
]

# palette
BG, PANEL, LINE = "#0a0911", "#0d0c16", "#2a2644"
VOID = "#06050d"
DIM, TEXT, ACC, CHIP = "#7c77a3", "#ece8ff", "#b59aff", "#14122a"
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono","DejaVu Sans Mono",monospace'
SANS = 'Inter,"Helvetica Neue",Helvetica,Arial,sans-serif'
PAL = np.array([(0x06,0x05,0x0d),(0x1b,0x11,0x4a),(0x5a,0x34,0xd4),(0xb5,0x9a,0xff),(0xf3,0xec,0xff)], dtype=np.uint8)
LINE_RGB = (0x2a, 0x26, 0x44)

ICONS = json.load(open(os.path.join(HERE, "icons.json"), encoding="utf-8"))

def icon(slug, x, y, size=16):
    """Inline logo. Brand color, lifted when the brand color is too dark for a dark tile."""
    ic = ICONS[slug]; k = size/24
    tr = f'transform="translate({x} {y}) scale({k:.4f})"'
    if ic["type"] == "fill":
        hx = ic["hex"]; r, g, b = (int(hx[i:i+2], 16) for i in (0, 2, 4))
        lum = .2126*r + .7152*g + .0722*b
        if lum < 90: col = TEXT
        elif lum < 125: col = "#%02x%02x%02x" % tuple(int(c + (255 - c)*.45) for c in (r, g, b))
        else: col = "#" + hx
        return f'<path {tr} d="{ic["path"]}" fill="{col}"/>'
    if ic["type"] == "stroke":
        return f'<g {tr} fill="none" stroke="{ACC}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ic["inner"]}</g>'
    if ic["type"] == "body":                      # multi-color logo from another icon set, any viewBox size
        k = size/max(ic["w"], ic["h"])
        ox, oy = x + (size - ic["w"]*k)/2, y + (size - ic["h"]*k)/2
        return f'<g transform="translate({ox:.2f} {oy:.2f}) scale({k:.4f})">{ic["body"]}</g>'
    return f'<g {tr}>{ic["inner"]}</g>'

def write(name, s):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f: f.write(s)

def svg(w, h, body, title, border="all", fill=PANEL):
    edges = {"all": [(0,0,w,0),(0,h,w,h),(0,0,0,h),(w,0,w,h)], "lrb": [(0,h,w,h),(0,0,0,h),(w,0,w,h)], "b": [(0,h,w,h)]}[border]
    ln = "".join(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" stroke-width="2"/>' for x1,y1,x2,y2 in edges)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
            f'<title>{esc(title)}</title><rect width="{w}" height="{h}" fill="{fill}"/>{body}{ln}</svg>')

def label(x, y, t, size=11, fill=DIM, anchor="start", ls=2):
    return (f'<text x="{x}" y="{y}" font-family=\'{MONO}\' font-size="{size}" fill="{fill}" '
            f'letter-spacing="{ls}" text-anchor="{anchor}">{esc(t)}</text>')

def text(x, y, t, size, fill=TEXT, family=MONO, weight=400, anchor="start", ls=0):
    return (f'<text x="{x}" y="{y}" font-family=\'{family}\' font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" letter-spacing="{ls}" text-anchor="{anchor}">{esc(t)}</text>')

def line(x1, y1, x2, y2): return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}"/>'

# ---------- dither ----------
def bayer(n):
    m = np.array([[0]])
    while m.shape[0] < n: m = np.block([[4*m, 4*m+2], [4*m+3, 4*m+1]])
    return (m + .5) / (n*n)

def dither(lum, cell=3):
    gh, gw = lum.shape
    T = np.tile(bayer(8), (gh//8+1, gw//8+1))[:gh, :gw]
    lv = len(PAL) - 1
    s = np.clip(lum, 0, 1) * lv
    idx = np.clip(np.floor(s) + ((s - np.floor(s)) > T), 0, lv).astype(int)
    return Image.fromarray(PAL[idx]).resize((gw*cell, gh*cell), Image.NEAREST)

def fbm(gw, gh, rng, octaves=5):
    out = np.zeros((gh, gw), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = 3 * 2**o
        small = Image.fromarray((rng.random((n, int(n*gw/gh)+2))*255).astype(np.uint8))
        out += amp * np.asarray(small.resize((gw, gh), Image.BICUBIC), np.float32)/255
        tot += amp; amp *= .5
    return out / tot

GW, GH, CELL = 198, 76, 3      # 594 x 228 thumbnails

def thumb_terrain():
    rng = np.random.default_rng(26001)
    h = fbm(GW, GH, rng); h = (h - h.min()) / (h.max() - h.min())
    r = 1 - np.abs(2*h - 1)                       # ridged
    gy, gx = np.gradient(h)
    shade = np.clip(.5 + (gx*-9 + gy*-6), 0, 1)
    contour = ((h*14) % 1 < .09).astype(np.float32)
    lum = .02 + .85*(r**1.8)*h + .30*shade*h**2 + .22*contour*h**1.5
    yy, xx = np.mgrid[0:GH, 0:GW]
    for cx, cy in [(120, 34), (66, 50), (150, 54)]:          # sensor halos
        d = np.hypot(xx-cx, (yy-cy)*1.4)
        lum += .9*np.exp(-(d/2.2)**2) + .25*np.exp(-(d/9)**2)
    return dither(lum, CELL)

def thumb_graph():
    rng = np.random.default_rng(15)
    pts = rng.random((90, 2)) * [GW, GH]
    q = np.array([GW*.62, GH*.46])
    yy, xx = np.mgrid[0:GH, 0:GW]
    lum = np.zeros((GH, GW), np.float32)
    for p in pts:
        d = np.hypot(xx-p[0], yy-p[1]); lum += .5*np.exp(-(d/1.6)**2)
    d = np.hypot(xx-q[0], (yy-q[1])*1.6)
    lum += .5*np.exp(-(d/38)**2) + .8*np.exp(-(d/3)**2)
    im = Image.fromarray((np.clip(lum,0,1)*255).astype(np.uint8)); dr = ImageDraw.Draw(im)
    near = np.argsort(np.hypot(*(pts-q).T))[:9]
    for i in near: dr.line([tuple(q), tuple(pts[i])], fill=190, width=1)
    for i in near: dr.ellipse([pts[i][0]-2, pts[i][1]-2, pts[i][0]+2, pts[i][1]+2], fill=255)
    return dither(np.asarray(im, np.float32)/255 + .06, CELL)

def thumb_terminal():
    W, H = GW*CELL, GH*CELL
    im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 17)
    rows = ["psh$ echo $HOME | tr a-z A-Z", "/HOME/RVNT", "psh$ cd src && ls", "lexer  parser  jobs  builtins",
            "psh$ sleep 30 &", "[1] 4021", "psh$ jobs", "[1]+ Running   sleep 30 &", "psh$ _"]
    for i, r in enumerate(rows):
        dr.text((22, 14 + i*23), r, font=f, fill=255 if r.startswith("psh") else 170)
    gw, gh = W//2, H//2                                        # 2px cells, text stays readable
    lum = np.asarray(im.resize((gw, gh), Image.BOX), np.float32)/255 * 2.1
    lum *= (.8 + .2*(np.arange(gh)[:, None] % 2))              # scanlines
    yy, xx = np.mgrid[0:gh, 0:gw]
    lum += .2*np.exp(-(((xx-gw*.4)/(gw*.6))**2 + ((yy-gh*.5)/(gh*.8))**2))
    return dither(lum, 2)

def thumb_swiss():
    im = Image.new("L", (GW, GH), 30); dr = ImageDraw.Draw(im)
    yy, xx = np.mgrid[0:GH, 0:GW]
    sweep = (np.clip((xx*.9 + yy*1.6)/(GW*.9 + GH*1.6), 0, 1)*110).astype(np.uint8)
    im = Image.fromarray(sweep + 25); dr = ImageDraw.Draw(im)
    for x in range(10, GW, 33): dr.line([(x, 0), (x, GH)], fill=150)
    for y in range(8, GH, 17): dr.line([(0, y), (GW, y)], fill=150)
    cx, cy, R = 64, 40, 26
    d = np.hypot(xx-cx, yy-cy); lum = np.asarray(im, np.float32)/255
    lum += (d < R) * (.35 + .55*(1 - d/R)) + .5*np.exp(-((d-R)/1.2)**2)
    dr = ImageDraw.Draw(im := Image.fromarray((np.clip(lum,0,1)*255).astype(np.uint8)))
    for y in range(4, GH-4, 3): dr.line([(GW-14, y), (GW-14+(7 if y % 9 == 4 else 3), y)], fill=255)
    dr.rectangle([112, 14, 170, 22], fill=255); dr.rectangle([112, 28, 150, 31], fill=200); dr.rectangle([112, 36, 160, 39], fill=200)
    return dither(np.asarray(im, np.float32)/255, CELL)

def thumb_pipeline():
    from PIL import ImageFilter
    rng = np.random.default_rng(7)
    base = fbm(GW, GH, rng, 3)
    im = Image.new("L", (GW, GH), 0); dr = ImageDraw.Draw(im)
    xs, y0, y1 = [10, 48, 86, 124, 162], 24, 52
    for x in range(0, GW, 4):                                   # dotted rails
        dr.point((x, 12), fill=120); dr.point((x, GH-13), fill=120)
    for i, x in enumerate(xs):
        dr.rectangle([x, y0, x+26, y1], outline=255, fill=40 + i*22)
        if i == 0:
            for j, w in enumerate((16, 11, 18)): dr.line([(x+5, 31+j*7), (x+5+w, 31+j*7)], fill=255)
        if i == 1:
            dr.rectangle([x+6, y0+6, x+20, y1-6], outline=255); dr.rectangle([x+10, y0+10, x+16, y1-10], fill=255)
        if i == 2: dr.line([(x+6, 39), (x+11, 45), (x+21, 31)], fill=255, width=2)
        if i == 3:
            dr.line([(x+10, 30), (x+6, 30), (x+6, 46), (x+10, 46)], fill=255); dr.line([(x+16, 30), (x+20, 30), (x+20, 46), (x+16, 46)], fill=255)
        if i == 4:
            for a in range(3):
                for b in range(3): dr.rectangle([x+6+a*6, y0+6+b*6, x+7+a*6, y0+7+b*6], fill=255)
        if i < 4:
            dr.line([(x+27, 38), (xs[i+1]-2, 38)], fill=220); dr.line([(xs[i+1]-4, 36), (xs[i+1]-2, 38), (xs[i+1]-4, 40)], fill=220)
    glow = np.asarray(im.filter(ImageFilter.GaussianBlur(4)), np.float32)/255
    lum = .05 + .12*base + .75*glow + .95*(np.asarray(im, np.float32)/255)*.9
    return dither(lum, CELL)



def thumb_signal():
    """Snag placeholder: review signals on the left funnel into ranked bars on the right."""
    rng = np.random.default_rng(3)
    im = Image.new("L", (GW, GH), 0); dr = ImageDraw.Draw(im)
    for _ in range(95):                                                   # review signals
        x, y = rng.integers(6, 78), rng.integers(8, GH-8); dr.rectangle([x, y, x+1, y], fill=int(rng.integers(110, 255)))
    for yy in range(10, GH-10, 6):                                        # funnel lines
        t = (yy - GH/2) / (GH/2)
        dr.line([(80, yy), (104, int(GH/2 + t*7))], fill=90)
    lens = [70, 58, 49, 38, 30, 21]                                       # RICE-ranked initiatives
    for i, ln in enumerate(lens):
        y = 12 + i*10
        dr.rectangle([112, y, 112+ln, y+5], fill=60 + i*18, outline=255 if i < 2 else 170)
        dr.rectangle([112+ln-3, y, 112+ln, y+5], fill=255)
    dr.rectangle([104, GH//2-1, 110, GH//2+1], fill=255)
    lum = np.asarray(im, np.float32)/255
    from PIL import ImageFilter
    lum = .05 + .8*lum + .5*np.asarray(im.filter(ImageFilter.GaussianBlur(3)), np.float32)/255
    return dither(lum, CELL)

THUMBS = dict(pipeline=thumb_pipeline, terrain=thumb_terrain, graph=thumb_graph, terminal=thumb_terminal, swiss=thumb_swiss, signal=thumb_signal)

# ---------- media ----------
MEDIA_EXT = (".gif", ".jpeg", ".jpg", ".png", ".webp")      # first match wins, so a gif beats a jpeg
RATIO = 594/321                                             # card image shape, close to a 1080p recording
GIF_W, STILL_W, HOLD_MS, MIN_FRAME_MS = 800, 1188, 1500, 70

def find_media(p):
    if p.get("media") and os.path.exists(os.path.join(HERE, p["media"])): return os.path.join(HERE, p["media"])
    for ext in MEDIA_EXT:
        path = os.path.join(HERE, p["slug"] + ext)
        if os.path.exists(path): return path
    return None

def cover(im, w, h):
    s = max(w/im.width, h/im.height)
    im = im.resize((max(w, round(im.width*s)), max(h, round(im.height*s))), Image.LANCZOS)
    l, t = (im.width - w)//2, (im.height - h)//2
    return im.crop((l, t, l+w, t+h))

def outline(im):
    ImageDraw.Draw(im).rectangle([0, 0, im.width-1, im.height-1], outline=LINE_RGB, width=2)
    return im

def load_gif(path, W, H):
    """Cover-crops every frame to the card shape and maps them all onto one shared palette, so colors do not flicker."""
    g = Image.open(path); n = g.n_frames; proc = lambda fr: outline(cover(fr.convert("RGB"), W, H))
    idx = sorted({round(i*(n - 1)/11) for i in range(12)})
    mosaic = Image.new("RGB", (W, H*len(idx)))
    for k, i in enumerate(idx): g.seek(i); mosaic.paste(proc(g), (0, k*H))
    pal = mosaic.quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    frames, durs, acc = [], [], 0
    for fr in ImageSequence.Iterator(g):
        q = proc(fr).quantize(palette=pal, dither=Image.Dither.NONE); q.info = {}          # drop transparency inherited from the source frame
        d = fr.info.get("duration", 100) or 100
        if frames and acc < MIN_FRAME_MS: durs[-1] += d; acc += d; continue              # fold fast frames together, UI recordings do not need 25 fps
        frames.append(q); durs.append(d); acc = d
    return frames, durs

def poster_index(frames, mode):
    """The frame a GIF rests on while another one plays. 'last' is the final frame. 'fullest' is the last frame with the most
    light pixels, which suits a terminal that clears itself at the end."""
    if mode != "fullest": return len(frames) - 1
    counts = [int((np.asarray(f.convert("L")) > 130).sum()) for f in frames]; best = max(counts)
    return max(i for i, c in enumerate(counts) if c >= .97*best)

def placeholder_media(p, W, H):
    art = THUMBS[p["kind"]]().resize((W, round(W*228/594)), Image.NEAREST)          # generated art is a wide strip, so it sits letterboxed
    im = Image.new("RGB", (W, H), tuple(PAL[0])); im.paste(art, (0, (H - art.height)//2))
    if p.get("placeholder", True):
        d = ImageDraw.Draw(im)
        try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 22)
        except OSError: f = ImageFont.load_default()
        d.rectangle([W-290, 18, W-18, 56], fill=(10, 9, 17)); d.text((W-276, 26), "PLACEHOLDER ART", font=f, fill=(0xb5, 0x9a, 0xff))
    return outline(im)

def build_media(projects):
    """Writes media-<slug>.* for every project. With CONFIG['relay'] on, the animated ones take turns:
    every GIF gets the same loop length, plays only in its own slot and rests on its poster frame the rest of the time."""
    for old in os.listdir(HERE):
        if old.startswith("media-"): os.remove(os.path.join(HERE, old))
    gifs, out = {}, {}
    for p in projects:
        src = find_media(p); H = round(GIF_W/RATIO)
        if src and src.lower().endswith(".gif"):
            frames, durs = load_gif(src, GIF_W, H); pi = poster_index(frames, p.get("poster", "last"))
            gifs[p["slug"]] = (frames, durs, pi)
        elif src:
            name = f"media-{p['slug']}.png"; outline(cover(Image.open(src).convert("RGB"), STILL_W, round(STILL_W/RATIO))).save(os.path.join(HERE, name), optimize=True); out[p["slug"]] = (name, "your image")
        else:
            name = f"media-{p['slug']}.png"; placeholder_media(p, STILL_W, round(STILL_W/RATIO)).save(os.path.join(HERE, name), optimize=True); out[p["slug"]] = (name, "generated art")
    relay = CONFIG.get("relay", False) and len(gifs) > 1
    plays = {k: (fr[:pi + 1], du[:pi + 1]) for k, (fr, du, pi) in gifs.items()} if relay else {k: (fr, du) for k, (fr, du, pi) in gifs.items()}
    lens = {k: sum(du) + HOLD_MS for k, (fr, du) in plays.items()}; total = sum(lens.values()); t0 = 0
    for p in projects:
        k = p["slug"]
        if k not in gifs: continue
        frames, durs, pi = gifs[k]; seq = []
        if relay:
            pf = frames[pi]; pf_frames, pf_durs = plays[k]
            if t0: seq.append((pf, t0))
            seq += list(zip(pf_frames, pf_durs)); seq.append((pf, total - t0 - sum(pf_durs))); t0 += lens[k]
        else: seq = list(zip(frames, durs))
        name = f"media-{k}.gif"; path = os.path.join(HERE, name)
        ims, ds = zip(*seq); ims[0].save(path, save_all=True, append_images=list(ims[1:]), duration=[int(d) for d in ds], loop=0, optimize=True, disposal=1)
        out[k] = (name, f"your gif, {'relay slot' if relay else 'plays on its own'}")
    if relay: print(f"relay loop: {total/1000:.1f}s across {len(gifs)} gifs")
    return out

# ---------- tiles ----------
def card(p):
    W, H = 594, 196
    b = text(24, 50, p["name"], 32, TEXT, SANS, 500, ls=-1)
    if p.get("wip"):
        bx, by, bw, bh = W-24-184, 22, 184, 28
        b += (f'<defs><pattern id="wip" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">'
              f'<rect width="4" height="8" fill="{ACC}"/></pattern></defs>'
              f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{BG}" stroke="{ACC}"/>'
              f'<rect x="{bx}" y="{by}" width="30" height="{bh}" fill="url(#wip)"/>'
              f'<line x1="{bx+30}" y1="{by}" x2="{bx+30}" y2="{by+bh}" stroke="{ACC}"/>'
              + text(bx+30+(bw-30)/2, by+18, "WORK IN PROGRESS", 11, ACC, MONO, 700, "middle", 1.2))
    for i, l in enumerate(p["desc"]): b += text(24, 82 + i*21, l, 13.5, "#b9b4d8")
    b += line(0, 148, W, 148)
    lx = 24
    for slug in p["logos"]:
        b += icon(slug, lx, 160, 24); lx += 24 + 14
    if p.get("url"):
        lab = "OPEN REPO ->"; bw = 40 + 9.2*len("OPEN REPO") + 22
        b += f'<rect x="{W-24-bw}" y="159" width="{bw}" height="26" fill="{ACC}"/>' + text(W-24-bw/2, 177, lab, 12, BG, MONO, 700, "middle", 1)
    else:
        lab = "PRIVATE REPO"; bw = 40 + 9.2*len("PRIVATE REPO") + 22
        b += f'<rect x="{W-24-bw}" y="159.5" width="{bw}" height="25" fill="none" stroke="{DIM}" stroke-dasharray="4 3"/>' + text(W-24-bw/2, 177, lab, 12, DIM, MONO, 700, "middle", 1)
    write(f"card-{p['slug']}.svg", svg(W, H, b, f"{p['name']}: {' '.join(p['desc'])}", "lrb"))

def name_path():
    """The name as vector outlines, so it looks the same without the font installed. Returns (path data, cap height)."""
    cfg = CONFIG["name"]
    f = TTFont(os.path.join(HERE, cfg["font"])); gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f["head"].unitsPerEm
    glyphs = [cmap[ord(c)] for c in cfg["text"]]
    adv = [f["hmtx"][g][0]/upm for g in glyphs]
    size = cfg["width"] / (sum(adv) + cfg["tracking"]*(len(glyphs) - 1))
    x, d = (1200 - cfg["width"])/2, ""
    for g, a in zip(glyphs, adv):
        pen = SVGPathPen(gs); gs[g].draw(TransformPen(pen, (size/upm, 0, 0, -size/upm, x, 0)))
        d += pen.getCommands(); x += (a + cfg["tracking"])*size
    cap = (getattr(f["OS/2"], "sCapHeight", 0) or .72*upm)/upm*size
    return d, cap

def identity():
    d, cap = name_path(); lines = CONFIG["tagline"]
    base = 56 + cap
    ys = [base + 56 + 28*i for i in range(len(lines))]
    b = (f'<path transform="translate(0 {base:.1f})" d="{d}" fill="{TEXT}" stroke="{TEXT}" '
         f'stroke-width="{CONFIG["name"]["weight"]}" stroke-linejoin="round"/>')
    for i, (t, y) in enumerate(zip(lines, ys)):
        b += text(600, round(y, 1), t, 17, "#cfc8f5", MONO, 400, "middle")
    write("identity.svg", svg(1200, round(ys[-1] + 48), b, f"{CONFIG['name']['text'].title()}. " + ", ".join(lines)))

def stack():
    rows = len(STACK); H = 52 + rows*58
    b = text(24, 33, "stack", 14) + text(1176, 33, "what I reach for", 13, DIM, anchor="end") + line(0, 52, 1200, 52)
    for r, (name, chips) in enumerate(STACK):
        y = 52 + r*58
        if r: b += line(0, y, 1200, y)
        b += label(24, y+34, name.upper(), 11) + line(190, y, 190, y+58)
        x = 214
        for t, slug in chips:
            w = 14 + 16 + 9 + 8.1*len(t) + 14
            b += f'<rect x="{x}" y="{y+13}" width="{w:.0f}" height="32" fill="{CHIP}" stroke="#2f2a55"/>'
            b += icon(slug, x+14, y+21, 16) + text(x+39, y+34, t, 13.5)
            x += w + 10
    write("stack.svg", svg(1200, H, b, "Stack: " + "; ".join(f"{n}: " + ", ".join(c for c, _ in cs) for n, cs in STACK)))

def links():
    for i, (t, _, ic) in enumerate(CONFIG["links"]):
        b = icon(ic, 20, 23, 18) + text(50, 38, t, 13) + text(280, 38, "->", 14, ACC, anchor="end")
        write(f"link-{i}.svg", svg(300, 64, b, t))

def readme(media):
    img = lambda f, alt, w="100%": f'<img align="top" src="assets/{f}" width="{w}" alt="{esc(alt, {chr(34): "&quot;"})}">'
    wrap = lambda href, tag: f'<a href="{href}">{tag}</a>' if href else tag
    L = ['<p align="center">',
         img("hero.gif", "A black hole in dithered violet and white on black"),
         '<br>' + img("identity.svg", f"{CONFIG['name']['text'].title()}. " + ", ".join(CONFIG["tagline"]))]
    for i in range(0, len(PROJECTS), 2):
        pair = PROJECTS[i:i+2]
        L.append('<br>' + "".join(wrap(p.get("live") or p.get("url"), img(media[p["slug"]], f"{p['name']} preview", "49.9%")) for p in pair))
        L.append('<br>' + "".join(wrap(p.get("url"), img(f"card-{p['slug']}.svg", f"{p['name']}: {p['desc'][0]}", "49.9%")) for p in pair))
    L += ['<br>' + img("stack.svg", "Stack: " + ", ".join(c for _, cs in STACK for c, _ in cs)),
          '<br>' + "".join(wrap(u, img(f"link-{i}.svg", t, "24.9%")) for i, (t, u, _) in enumerate(CONFIG["links"])),
          '</p>', '']
    write("../README.md", "\n".join(L))

if __name__ == "__main__":
    for p in PROJECTS: card(p)
    media = {}
    for k, (name, how) in build_media(PROJECTS).items():
        media[k] = name; print(f"{k}: {how} -> {name}")
    identity(); stack(); links(); readme(media)
    print("done")
