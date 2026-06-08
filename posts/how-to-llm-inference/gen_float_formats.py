#!/usr/bin/env python3
"""Generate float-formats.excalidraw.

A ladder of IEEE-754-style floating formats showing how each step down
in bits splits into two variants — one that keeps fp32's range, one that
keeps more precision.

Layout (top to bottom, all rows aligned at the same bit-origin x):

  fp32   : 1 + 8 + 23 = 32 bits             range / precision brackets
  ── cut to 16 bits, two ways ──
  bf16   : 1 + 8 +  7 = 16 bits             keeps fp32's exponent
  fp16   : 1 + 5 + 10 = 16 bits             shrinks exponent
  ── cut to 8 bits, two ways ──
  fp8 e5m2 : 1 + 5 + 2 = 8 bits             keeps fp16's exponent
  fp8 e4m3 : 1 + 4 + 3 = 8 bits             shrinks exponent further

Uses the same engine and palette as gen_quant.py so the figure feels
like a sibling of q8_0 / q4_k.
"""
import json

# ---------------------------------------------------------------- palette
INK    = "#1e1e1e"
GRAY   = "#868e96"
FRAME  = "#ced4da"
BLUE   = "#1971c2"
ORANGE = "#f08c00"
PURPLE = "#7048e8"
GREEN  = "#2f9e44"
RED    = "#d9480f"

WHITE   = "#ffffff"
SIGN_BG = "#dee2e6"   # gray   -- sign bit
EXP_BG  = "#ffec99"   # yellow -- exponent (range)
MANT_BG = "#d3f9d8"   # green  -- mantissa (precision)

FONT     = 6
FS_TITLE = 26
FS_LABEL = 18
FS_CELL  = 16
FS_NOTE  = 16
FS_SMALL = 14
LH       = 1.25

# ---------------------------------------------------------------- engine
elements = []
_idx = [0]; _seed = [777000]

def nxt_index():
    s = f"b{_idx[0]:04d}"; _idx[0] += 1; return s
def seed():
    _seed[0] += 7; return _seed[0]

def base(extra):
    e = {"angle": 0, "strokeColor": INK, "backgroundColor": "transparent",
         "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
         "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
         "index": nxt_index(), "roundness": None, "seed": seed(),
         "version": 1, "versionNonce": seed(), "isDeleted": False,
         "boundElements": [], "updated": 1780770446206, "link": None,
         "locked": False}
    e.update(extra); return e

def rect(id, x, y, w, h, stroke=INK, bg=WHITE, sw=2, rounded=True,
         text_id=None, style="solid"):
    e = base({"id": id, "type": "rectangle", "x": x, "y": y, "width": w,
              "height": h, "strokeColor": stroke, "backgroundColor": bg,
              "strokeWidth": sw, "strokeStyle": style,
              "roundness": {"type": 3} if rounded else None})
    if text_id:
        e["boundElements"] = [{"type": "text", "id": text_id}]
    return e

def bound_text(id, cid, cx, cy, w, h, text, color=INK, fs=FS_LABEL):
    lines = text.split("\n")
    th = len(lines) * fs * LH
    return base({"id": id, "type": "text", "x": cx - w/2,
                 "y": cy - th/2, "width": w, "height": th,
                 "strokeColor": color, "text": text, "originalText": text,
                 "fontSize": fs, "fontFamily": FONT, "textAlign": "center",
                 "verticalAlign": "middle", "containerId": cid,
                 "autoResize": False, "lineHeight": LH})

def free_text(text, color=INK, fs=FS_LABEL, align="left"):
    lines = text.split("\n")
    w = int(max(len(l) for l in lines) * fs * 0.58) + 6
    h = int(len(lines) * fs * LH) + 2
    el = base({"id": f"t{_idx[0]}", "type": "text", "x": 0, "y": 0,
               "width": w, "height": h, "strokeColor": color, "text": text,
               "originalText": text, "fontSize": fs, "fontFamily": FONT,
               "textAlign": align, "verticalAlign": "top",
               "containerId": None, "autoResize": True, "lineHeight": LH})
    return el, w, h

def place_text(text, x, y, color=INK, fs=FS_LABEL, align="left"):
    el, w, h = free_text(text, color, fs, align)
    el["x"] = x; el["y"] = y
    elements.append(el)
    return w, h

def place_centered(cx, cy, text, color=INK, fs=FS_LABEL):
    el, w, h = free_text(text, color, fs, align="center")
    el["x"] = cx - w/2; el["y"] = cy - h/2; el["textAlign"] = "center"
    elements.append(el)
    return w, h

def labeled_box(id, x, y, w, h, label, bg, stroke=INK, fs=FS_LABEL):
    tid = f"{id}__t"
    elements.append(rect(id, x, y, w, h, stroke=stroke, bg=bg,
                         sw=2, rounded=True, text_id=tid))
    elements.append(bound_text(tid, id, x + w/2, y + h/2, w - 8, h,
                               label, INK, fs))

def hline(id, x, y, length, color=GRAY, sw=1.5, style="solid"):
    e = base({"id": id, "type": "line", "x": x, "y": y,
              "width": length, "height": 0,
              "strokeColor": color, "strokeWidth": sw, "strokeStyle": style,
              "roundness": {"type": 2},
              "points": [[0, 0], [length, 0]],
              "lastCommittedPoint": None,
              "startBinding": None, "endBinding": None,
              "startArrowhead": None, "endArrowhead": None})
    elements.append(e)

def vline(id, x, y, length, color=GRAY, sw=1.5, style="solid"):
    e = base({"id": id, "type": "line", "x": x, "y": y,
              "width": 0, "height": length,
              "strokeColor": color, "strokeWidth": sw, "strokeStyle": style,
              "roundness": {"type": 2},
              "points": [[0, 0], [0, length]],
              "lastCommittedPoint": None,
              "startBinding": None, "endBinding": None,
              "startArrowhead": None, "endArrowhead": None})
    elements.append(e)

def bracket_under(id, x0, x1, y, depth=8, color=GRAY, sw=1.5):
    pts = [[0, 0], [0, depth], [x1 - x0, depth], [x1 - x0, 0]]
    e = base({"id": id, "type": "line", "x": x0, "y": y,
              "width": x1 - x0, "height": depth,
              "strokeColor": color, "strokeWidth": sw, "strokeStyle": "solid",
              "roundness": {"type": 2},
              "points": pts,
              "lastCommittedPoint": None,
              "startBinding": None, "endBinding": None,
              "startArrowhead": None, "endArrowhead": None})
    elements.append(e)

# ---------------------------------------------------------------- writer
def reset():
    elements.clear()
    _idx[0] = 0
    _seed[0] = 777000

def write_doc(path):
    doc = {"type": "excalidraw", "version": 2,
           "source": "https://github.com/excalidraw/excalidraw",
           "elements": list(elements),
           "appState": {"gridSize": 20, "gridStep": 5,
                        "gridModeEnabled": False,
                        "viewBackgroundColor": "#ffffff"},
           "files": {}}
    with open(path, "w") as f:
        json.dump(doc, f, indent=2)


# ---------------------------------------------------------------- row helper
def draw_format_row(name, info, y, bit_w, cell_h, sign_bits, exp_bits, mant_bits,
                    cap_red, cap_ink, bits_x0=220, left_label_x=110, cap_x=None,
                    exp_label=None, mant_label=None):
    """Draw a single format row.  Returns (exp_x0, exp_x1) for alignment."""
    place_text(name, left_label_x, y + 8, INK, FS_LABEL)
    place_text(info, left_label_x, y + 32, GRAY, FS_SMALL)

    x = bits_x0
    labeled_box(f"{name}_s", x, y, sign_bits * bit_w, cell_h, "S", SIGN_BG, fs=FS_CELL)
    x += sign_bits * bit_w
    exp_x0 = x
    if exp_label is None:
        exp_label = f"exp  •  {exp_bits}"
    labeled_box(f"{name}_exp", x, y, exp_bits * bit_w, cell_h,
                exp_label, EXP_BG, fs=FS_CELL)
    x += exp_bits * bit_w
    exp_x1 = x
    if mant_label is None:
        mant_label = f"mant  •  {mant_bits}"
    labeled_box(f"{name}_man", x, y, mant_bits * bit_w, cell_h,
                mant_label, MANT_BG, fs=FS_CELL)
    x += mant_bits * bit_w

    if cap_x is not None:
        place_text(cap_red, cap_x, y + 4, RED, FS_SMALL)
        place_text(cap_ink, cap_x, y + 26, INK, FS_SMALL)
    return exp_x0, exp_x1

# ---------------------------------------------------------------- figure
def build():
    reset()

    FRAME_X = 80
    FRAME_Y = 80
    TITLE_H = 60
    BIT_W   = 20
    CELL_H  = 44
    BITS_X0 = 220
    LEFT_LABEL_X = 110
    SIDE_CAP_W = 290

    # vertical plan
    fp32_y = FRAME_Y + TITLE_H + 38
    fp32_bracket_y = fp32_y + CELL_H + 12
    fp32_bracket_label_y = fp32_bracket_y + 14
    fp32_bottom = fp32_bracket_label_y + 22

    div16_y = fp32_bottom + 26
    bf16_y  = div16_y + 50
    fp16_y  = bf16_y + CELL_H + 38

    div8_y  = fp16_y + CELL_H + 38
    e5m2_y  = div8_y + 50
    e4m3_y  = e5m2_y + CELL_H + 38
    bottom  = e4m3_y + CELL_H + 30

    # frame
    FRAME_W = (BITS_X0 - FRAME_X) + 32 * BIT_W + 24 + SIDE_CAP_W
    FRAME_H = bottom + 60 - FRAME_Y

    elements.append(rect("frame", FRAME_X, FRAME_Y, FRAME_W, FRAME_H,
                         stroke=FRAME, bg=WHITE, sw=1.5, rounded=True))

    # title + subtitle
    place_text("Float formats", FRAME_X + 22, FRAME_Y + 16,
               PURPLE, FS_TITLE, align="left")
    place_text("range vs precision, all the way down to 8 bits",
               FRAME_X + 240, FRAME_Y + 24, GRAY, FS_NOTE)

    CAP_X = BITS_X0 + 32 * BIT_W + 30

    # ====================== FP32 =====================================
    fp32_exp_x0, fp32_exp_x1 = draw_format_row(
        "fp32", "32 bits", fp32_y, BIT_W, CELL_H,
        sign_bits=1, exp_bits=8, mant_bits=23,
        cap_red="", cap_ink="",
        exp_label="exponent  •  8", mant_label="mantissa  •  23")

    # brackets + labels
    fp32_man_x0 = fp32_exp_x1
    fp32_man_x1 = fp32_man_x0 + 23 * BIT_W
    bracket_under("fp32_exp_brk", fp32_exp_x0, fp32_exp_x1,
                  fp32_bracket_y, depth=8, color=RED, sw=1.5)
    place_centered((fp32_exp_x0 + fp32_exp_x1) / 2,
                   fp32_bracket_label_y + 8,
                   "range  →  ±3.4 × 10³⁸", RED, FS_SMALL)
    bracket_under("fp32_man_brk", fp32_man_x0, fp32_man_x1,
                  fp32_bracket_y, depth=8, color=GREEN, sw=1.5)
    place_centered((fp32_man_x0 + fp32_man_x1) / 2,
                   fp32_bracket_label_y + 8,
                   "precision  →  ~7 decimal digits", GREEN, FS_SMALL)

    # ====================== 16-bit divider ===========================
    hline("div16", FRAME_X + 30, div16_y, FRAME_W - 60,
          color=FRAME, sw=1.2, style="dashed")
    place_text("cut to 16 bits, two ways:",
               FRAME_X + 30, div16_y + 8, GRAY, FS_NOTE)

    # ====================== BF16 =====================================
    bf16_exp_x0, bf16_exp_x1 = draw_format_row(
        "bf16", "16 bits", bf16_y, BIT_W, CELL_H,
        sign_bits=1, exp_bits=8, mant_bits=7,
        cap_x=CAP_X,
        cap_red="keeps fp32's exponent",
        cap_ink="→ same range, less precision",
        exp_label="exponent  •  8", mant_label="mant  •  7")

    # alignment guides from fp32 exponent to bf16 exponent
    vline("guide_fp32_l", fp32_exp_x0, fp32_y + CELL_H,
          bf16_y - (fp32_y + CELL_H), color=FRAME, sw=1, style="dashed")
    vline("guide_fp32_r", fp32_exp_x1, fp32_y + CELL_H,
          bf16_y - (fp32_y + CELL_H), color=FRAME, sw=1, style="dashed")

    # ====================== FP16 =====================================
    fp16_exp_x0, fp16_exp_x1 = draw_format_row(
        "fp16", "16 bits", fp16_y, BIT_W, CELL_H,
        sign_bits=1, exp_bits=5, mant_bits=10,
        cap_x=CAP_X,
        cap_red="shrinks the exponent",
        cap_ink="→ range only ±6.5 × 10⁴, more precision",
        exp_label="exp  •  5", mant_label="mantissa  •  10")

    # ====================== 8-bit divider ============================
    hline("div8", FRAME_X + 30, div8_y, FRAME_W - 60,
          color=FRAME, sw=1.2, style="dashed")
    place_text("cut to 8 bits, two ways:",
               FRAME_X + 30, div8_y + 8, GRAY, FS_NOTE)

    # ====================== fp8 e5m2 =================================
    e5m2_exp_x0, e5m2_exp_x1 = draw_format_row(
        "fp8 e5m2", "8 bits", e5m2_y, BIT_W, CELL_H,
        sign_bits=1, exp_bits=5, mant_bits=2,
        cap_x=CAP_X,
        cap_red="keeps fp16's exponent",
        cap_ink="→ range ±5.7 × 10⁴, only ~1 digit",
        exp_label="exp  •  5", mant_label="m·2")

    # alignment guide from fp16's exponent to e5m2's exponent
    vline("guide_fp16_l", fp16_exp_x0, fp16_y + CELL_H,
          e5m2_y - (fp16_y + CELL_H), color=FRAME, sw=1, style="dashed")
    vline("guide_fp16_r", fp16_exp_x1, fp16_y + CELL_H,
          e5m2_y - (fp16_y + CELL_H), color=FRAME, sw=1, style="dashed")

    # ====================== fp8 e4m3 =================================
    draw_format_row(
        "fp8 e4m3", "8 bits", e4m3_y, BIT_W, CELL_H,
        sign_bits=1, exp_bits=4, mant_bits=3,
        cap_x=CAP_X,
        cap_red="shrinks exponent further",
        cap_ink="→ range only ±448, slightly more precision",
        exp_label="exp •4", mant_label="mant •3")

    # ====================== bottom takeaway ==========================
    take_y = bottom + 12
    place_text(
        "each step halves the bits;  each pair trades range for precision.",
        FRAME_X + 30, take_y, INK, FS_NOTE)

    write_doc("float-formats.excalidraw")


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build()
    print(f"wrote float-formats.excalidraw  ({len(elements)} elements)")
