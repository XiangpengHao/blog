#!/usr/bin/env python3
"""Render q8_0.excalidraw and q4_k.excalidraw to PNG for visual verification.

This is NOT the same as the proper Excalidraw export (it produces a flat,
non-rough preview), but it lets us catch layout problems before manually
exporting from the Excalidraw web app.
"""
import json
import os
from PIL import Image, ImageDraw, ImageFont

MARGIN = 40
SCALE  = 2

FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"

def load_font(size):
    return ImageFont.truetype(FONT_PATH, int(size * SCALE))

def measure(draw, text, font):
    if "\n" in text:
        lines = text.split("\n")
        wmax = 0
        h = 0
        for l in lines:
            bbox = draw.textbbox((0, 0), l, font=font)
            wmax = max(wmax, bbox[2] - bbox[0])
            h += bbox[3] - bbox[1] + 4
        return wmax, h
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def draw_multiline_centered(draw, cx, cy, text, font, color):
    lines = text.split("\n")
    sizes = [draw.textbbox((0, 0), l, font=font) for l in lines]
    heights = [s[3] - s[1] for s in sizes]
    total_h = sum(heights) + 4 * (len(lines) - 1)
    y = cy - total_h / 2
    for l, h in zip(lines, heights):
        w = draw.textbbox((0, 0), l, font=font)[2]
        draw.text((cx - w/2, y), l, fill=color, font=font)
        y += h + 4

def render(path, out_path):
    with open(path) as f:
        doc = json.load(f)
    els = doc["elements"]
    minx = min(e["x"] for e in els)
    miny = min(e["y"] for e in els)
    maxx = max(e["x"] + e["width"] for e in els)
    maxy = max(e["y"] + e["height"] for e in els)
    W = int((maxx - minx) + 2 * MARGIN) * SCALE
    H = int((maxy - miny) + 2 * MARGIN) * SCALE
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    def tx(x): return int((x - minx + MARGIN) * SCALE)
    def ty(y): return int((y - miny + MARGIN) * SCALE)

    # rectangles
    for e in els:
        if e["type"] != "rectangle": continue
        x0, y0 = tx(e["x"]), ty(e["y"])
        x1, y1 = tx(e["x"]+e["width"]), ty(e["y"]+e["height"])
        bg = e["backgroundColor"] if e["backgroundColor"] != "transparent" else None
        r = 8 * SCALE if e.get("roundness") else 0
        draw.rounded_rectangle([x0, y0, x1, y1], radius=r,
                               fill=bg, outline=e["strokeColor"],
                               width=int(e["strokeWidth"] * SCALE))

    # arrows
    for e in els:
        if e["type"] != "arrow": continue
        pts = [(tx(e["x"]+p[0]), ty(e["y"]+p[1])) for p in e["points"]]
        for i in range(len(pts)-1):
            draw.line([pts[i], pts[i+1]], fill=e["strokeColor"],
                      width=int(e["strokeWidth"] * SCALE))
        # arrowhead at last point
        if len(pts) >= 2 and e.get("endArrowhead") == "arrow":
            import math
            x0, y0 = pts[-2]; x1, y1 = pts[-1]
            ang = math.atan2(y1 - y0, x1 - x0)
            L = 12 * SCALE
            a1 = ang + math.radians(150)
            a2 = ang - math.radians(150)
            draw.polygon([(x1, y1),
                          (x1 + L * math.cos(a1), y1 + L * math.sin(a1)),
                          (x1 + L * math.cos(a2), y1 + L * math.sin(a2))],
                         fill=e["strokeColor"])

    # bound text (centered inside container)
    bound = [e for e in els if e["type"] == "text" and e.get("containerId")]
    free  = [e for e in els if e["type"] == "text" and not e.get("containerId")]
    for e in bound:
        font = load_font(e["fontSize"])
        cx = tx(e["x"] + e["width"]/2)
        cy = ty(e["y"] + e["height"]/2)
        draw_multiline_centered(draw, cx, cy, e["text"], font, e["strokeColor"])
    # free-floating text -- top-left anchored
    for e in free:
        font = load_font(e["fontSize"])
        x = tx(e["x"]); y = ty(e["y"])
        align = e.get("textAlign", "left")
        if align == "center":
            cx = tx(e["x"] + e["width"]/2)
            cy = ty(e["y"] + e["height"]/2)
            draw_multiline_centered(draw, cx, cy, e["text"], font, e["strokeColor"])
        else:
            draw.text((x, y), e["text"], fill=e["strokeColor"], font=font)

    img.save(out_path, "PNG")
    print(f"wrote {out_path}  {W}x{H}")

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    render(os.path.join(here, "q8_0.excalidraw"),
           os.path.join(here, "_preview_q8_0.png"))
    render(os.path.join(here, "q4_k.excalidraw"),
           os.path.join(here, "_preview_q4_k.png"))
