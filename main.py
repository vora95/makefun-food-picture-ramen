"""Food-picture-01 entry: copy the picture beside this file to /output/entry.png.

The picture (entry.png, JPEG bytes) was drawn procedurally by gen_ramen.py in
this repository: a steaming bowl of ramen, every pixel computed in code, no
photo, no external asset, no paid service. This program only copies it, so
both grader runs write identical bytes.

Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent

out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
out_dir.mkdir(parents=True, exist_ok=True)
target = out_dir / "entry.png"
shutil.copyfile(HERE / "entry.png", target)
# The gate reads exactly these bytes; fail loudly instead of writing nothing.
size = target.stat().st_size
assert size > 0, "entry.png was copied empty"
print(f"wrote {target} ({size} bytes)")
