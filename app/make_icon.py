"""Generate the app icon (gradient squircle + lyric bars) -> AppIcon.icns."""
import os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFilter

S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
grad = Image.new("RGB", (S, S))
px = grad.load()
for y in range(S):
    for x in range(S):
        t = (x + y) / (2 * S)
        px[x, y] = (int(60 + 180 * t), int(20 + 40 * t), int(110 - 20 * t))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((90, 90, S - 90, S - 90), radius=200, fill=255)
img.paste(grad, (0, 0), mask)
d = ImageDraw.Draw(img)
rows = [(0.30, 0.55, 110), (0.47, 0.72, 255), (0.64, 0.45, 110)]
for y, w, a in rows:
    x0 = 220
    d.rounded_rectangle((x0, S * y, x0 + (S - 440) * w, S * y + 70), radius=35, fill=(255, 255, 255, a))
glow = img.filter(ImageFilter.GaussianBlur(18))
out = Image.alpha_composite(glow, img)
tmp = tempfile.mkdtemp()
iconset = os.path.join(tmp, "AppIcon.iconset")
os.makedirs(iconset)
for size in (16, 32, 128, 256, 512):
    out.resize((size, size), Image.LANCZOS).save(f"{iconset}/icon_{size}x{size}.png")
    out.resize((size * 2, size * 2), Image.LANCZOS).save(f"{iconset}/icon_{size}x{size}@2x.png")
subprocess.run(["iconutil", "-c", "icns", iconset, "-o", "AppIcon.icns"], check=True)
