# generate_icons.py
# run this in your extension/ folder

from PIL import Image, ImageDraw
import os

os.makedirs("icons", exist_ok=True)

def create_icon(size):
    # dark background
    img  = Image.new("RGB", (size, size), color="#0f1117")
    draw = ImageDraw.Draw(img)

    # draw a simple lightning bolt ⚡ as rectangle
    margin = size // 6
    draw.rectangle(
        [margin, margin, size - margin, size - margin],
        fill    = "#00d4ff",
        outline = "#a78bfa",
        width   = max(1, size // 16)
    )

    # inner square
    inner = size // 3
    draw.rectangle(
        [inner, inner, size - inner, size - inner],
        fill = "#0f1117"
    )

    img.save(f"icons/icon{size}.png")
    print(f"✅ Created icons/icon{size}.png")

create_icon(16)
create_icon(48)
create_icon(128)

print("✅ All icons created!")