# image-generator

Procedural image generation in Python. Each scene is a standalone script that
draws an image with code (no AI image models) and saves a PNG.

## Layout
- `lotus.py` — renders a lotus on a lake at dawn → `lotus_lake.png`
- `photos/` — reference photographs; sources and licences in `photos/CREDITS.md`

## Stack
- Python 3, Pillow (`PIL`), NumPy
- Run a scene: `python lotus.py`

## Conventions
- Fixed random seeds (`random.seed`, `np.random.seed`) so renders are reproducible.
- Draw at `SS`× supersampling, then downscale for smooth edges.
- Canvas size and layout constants (`W`, `H`, `HORIZON`) live at the top of the script.
- Any photo added to `photos/` must get an entry in `photos/CREDITS.md`
  (author, source URL, licence).
- After changing a scene, re-render it and look at the PNG before committing.
