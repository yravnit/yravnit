# Rebuilding the profile assets

Everything in this folder is generated. `README.md` one level up is written by `build.py`.

    pip install pillow numpy fonttools
    python build.py

Before the first run, put your own `Ethnocentric-Regular.ttf` in `fonts/` and keep it out of the commit.

## Files

- `build.py` writes the cards, the name box, the stack grid, the link tiles, the project media and `../README.md`.
- `hero.py` renders `hero.gif` from a black hole GIF: `python hero.py path/to/blackhole.gif`.
- `bankiq_gif.py` renders `bankiq.gif`. Change `WORDMARK` or `ROLE` at the top, then run it.
- `drag.gif`, `psh.gif`, `snag.gif` are the project recordings. A `.jpeg`, `.jpg` or `.png` with the same name works when there is no GIF. A GIF wins.
- `icons.json` holds the logos. Sources and licenses are in `ICONS-LICENSE.txt`.

## Switches in build.py

- `relay=True` makes the GIFs take turns in one 59 second loop. `relay=False` lets them all play at once.
- `url=None` on a project draws a dashed PRIVATE REPO strip. Set a link to get OPEN REPO.
- `logos` lists the icon names drawn in each card strip. Any name in `icons.json` works.
- `name` under CONFIG sets the font file and width for the name.
