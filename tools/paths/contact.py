"""Contact sheet of shots: python tools/paths/contact.py out.jpg a.jpg b.jpg ... (2 columns, 640 px wide each)."""
import sys
from PIL import Image
out, fs = sys.argv[1], sys.argv[2:]
ims = [Image.open(f).convert("RGB").resize((640, 360)) for f in fs]
cols = 2
rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (640 * cols, 360 * rows))
for i, im in enumerate(ims):
    S.paste(im, ((i % cols) * 640, (i // cols) * 360))
S.save(out, quality=88)
