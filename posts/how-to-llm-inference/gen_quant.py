#!/usr/bin/env python3
"""Generate q8_0.excalidraw and q4_k.excalidraw.

Each figure has two panels stacked vertically inside one frame:

  1. Storage layout    -- how the block's bytes are laid out
  2. Worked example    -- 8 concrete weights going through
                          f32 -> quantized -> f32 again

Example values are precomputed with numpy (seed=7 for Q8_0, seed=13 for
Q4_K) and hardcoded here so the script has no runtime dependencies.
"""
import json

# ---------------------------------------------------------------- palette
INK    = "#1e1e1e"
GRAY   = "#868e96"
FRAME  = "#ced4da"
BLUE   = "#1971c2"
ORANGE = "#f08c00"
PURPLE = "#7048e8"

WHITE    = "#ffffff"
SCALE_BG = "#a5d8ff"   # blue tint -- fp16 scales
QUANT_BG = "#ffec99"   # yellow    -- quantized values (int8 / 4-bit)
META_BG  = "#d3f9d8"   # green tint -- packed scales/mins (Q4_K)
HAT_BG   = "#f1f3f5"   # very light gray -- dequantized f32 (the "result")

FONT     = 6
FS_TITLE = 26
FS_LABEL = 18    # in-box labels (the layout row)
FS_CELL  = 16    # in-box values  (the zoom row)
FS_ROWL  = 16    # row labels on the left of the zoom rows
FS_BYTES = 15    # byte-count labels under boxes
FS_NOTE  = 16    # formula / annotations
LH       = 1.25

# ---------------------------------------------------------------- engine
elements = []
_idx = [0]; _seed = [777000]

def nxt_index():
    s = f"b{_idx[0]:04d}"; _idx[0] += 1; return s
def seed():
    _seed[0] += 7; return _seed[0]
def uid(prefix):
    _idx[0] += 1
    return f"{prefix}_{_idx[0]:04d}"

def base(extra):
    e = {"angle": 0, "strokeColor": INK, "backgroundColor": "transparent",
         "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
         "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
         "index": nxt_index(), "roundness": None, "seed": seed(),
         "version": 1, "versionNonce": seed(), "isDeleted": False,
         "boundElements": [], "updated": 1780770446206, "link": None,
         "locked": False}
    e.update(extra); return e

def rect(id, x, y, w, h, stroke=INK, bg=WHITE, sw=2, rounded=True, text_id=None):
    e = base({"id": id, "type": "rectangle", "x": x, "y": y, "width": w,
              "height": h, "strokeColor": stroke, "backgroundColor": bg,
              "strokeWidth": sw,
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

def bytes_label(cx, y, text):
    place_centered(cx, y, text, BLUE, FS_BYTES)

# ---------------------------------------------------------------- zoom row
def zoom_row(x, y, row_label, values, label_w=80, cell_w=72, cell_h=40,
             gap=6, cell_bg=WHITE, row_color=GRAY):
    """Draw `[row_label] [c0] [c1] ... [cN-1]` left-to-right.
    Returns total width consumed."""
    place_text(row_label, x, y + cell_h/2 - FS_ROWL/2, row_color,
               FS_ROWL, align="left")
    for i, val in enumerate(values):
        cx = x + label_w + i * (cell_w + gap)
        cid = uid("c")
        tid = f"{cid}__t"
        elements.append(rect(cid, cx, y, cell_w, cell_h,
                             stroke=INK, bg=cell_bg, sw=1.5,
                             rounded=True, text_id=tid))
        elements.append(bound_text(tid, cid, cx + cell_w/2, y + cell_h/2,
                                   cell_w - 6, cell_h, val, INK, FS_CELL))
    return label_w + len(values) * cell_w + (len(values) - 1) * gap

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

# ---------------------------------------------------------------- audits
def bbox_rect(el):
    return (el["x"], el["y"], el["x"]+el["width"], el["y"]+el["height"])

def audit(name):
    rects = [e for e in elements if e["type"] == "rectangle"]
    texts = [e for e in elements
             if e["type"] == "text" and e.get("containerId") is None]
    partial = []
    for i in range(len(rects)):
        for j in range(i+1, len(rects)):
            a = bbox_rect(rects[i]); b = bbox_rect(rects[j])
            ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
            iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
            if ix > 2 and iy > 2:
                ax_in = a[0] >= b[0]-1 and a[2] <= b[2]+1 \
                        and a[1] >= b[1]-1 and a[3] <= b[3]+1
                bx_in = b[0] >= a[0]-1 and b[2] <= a[2]+1 \
                        and b[1] >= a[1]-1 and b[3] <= a[3]+1
                if not (ax_in or bx_in):
                    partial.append((rects[i]["id"], rects[j]["id"]))
    tcol = []
    for i in range(len(texts)):
        a = bbox_rect(texts[i])
        for r in rects:
            b = bbox_rect(r)
            ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
            iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
            if ix > 2 and iy > 2:
                ax_in = a[0] >= b[0]-1 and a[2] <= b[2]+1 \
                        and a[1] >= b[1]-1 and a[3] <= b[3]+1
                if not ax_in:
                    tcol.append((texts[i]["text"][:24], r["id"]))
        for j in range(i+1, len(texts)):
            b = bbox_rect(texts[j])
            ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
            iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
            if ix > 2 and iy > 2:
                tcol.append((texts[i]["text"][:20],
                             texts[j]["text"][:20]))
    print(f"[{name}] rects={len(rects)} texts={len(texts)}  "
          f"partial-rect-overlap={partial or 'none'}  "
          f"text-collision={tcol or 'none'}")

# ================================================================ DATA
# Hardcoded worked-example values (precomputed offline, see header).

# Q8_0:  32 random gaussians (seed=7, sigma=0.55).
# d = max(|w|) / 127 = 1.2586 / 127 = 0.009910.  Display 8 indices that
# span the range, including the argmax (which saturates at -127).
Q8_DISPLAY_IDX = [0, 1, 4, 7, 13, 18, 23, 27]
Q8_W   = ["+0.930", "-0.256", "-0.434", "-0.965",
          "-0.144", "+0.151", "+1.116", "-1.259"]
Q8_Q   = [   "+94",    "-26",    "-44",    "-97",
              "-15",    "+15",   "+113",   "-127"]   # -127 saturates
Q8_WH  = ["+0.932", "-0.258", "-0.436", "-0.961",
          "-0.149", "+0.149", "+1.120", "-1.259"]
Q8_AMAX = "1.259"
Q8_D    = "0.00991"

# Q4_K:  256 random gaussians (seed=13, sigma=0.40), focus on sub-block 3.
# Sub-block 3 minmax  ->  scale_eff and offset_eff
#   scale_eff_max / 63 = 0.002256  =>  d    (fp16, shared)
#   |offset_eff|_max / 63 = 0.01473  =>  dmin (fp16, shared)
#   scale_3 = 40 (6-bit),  min_3 = 63 (6-bit)
#   d_eff = d * scale_3 = 0.09023,   m_eff = dmin * min_3 = 0.9279
# Display 8 indices that include both saturation points (q=0 at i=15,
# q=15 at i=17) plus a spread of others.
Q4_DISPLAY_IDX = [0, 2, 7, 11, 15, 17, 23, 27]
Q4_W   = ["+0.074", "-0.448", "-0.166", "+0.127",
          "-0.928", "+0.436", "+0.327", "-0.306"]
Q4_Q   = [    "11",      "5",      "8",     "12",
               "0",     "15",     "14",      "7"]   # 0 and 15 saturate
Q4_WH  = ["+0.064", "-0.477", "-0.206", "+0.155",
          "-0.928", "+0.426", "+0.335", "-0.296"]
Q4_D    = "0.00226"
Q4_DMIN = "0.01473"
Q4_SC3  = "40"
Q4_M3   = "63"
Q4_DEFF = "0.0902"
Q4_MEFF = "0.928"

# ================================================================ Q8_0
def build_q8_0():
    reset()

    FRAME_X = 80
    FRAME_Y = 80
    PAD_X   = 40
    TITLE_H = 56

    # ---- LAYOUT panel geometry (single row of 2 boxes)
    BYTE_W = 18
    H_BOX  = 64

    W_D  = 2 * BYTE_W * 1.6
    GAP  = 14
    W_Q  = 32 * BYTE_W           # = 576

    # ---- ZOOM panel geometry (3 rows of 8 cells)
    Z_LABEL_W = 112
    Z_CELL_W  = 72
    Z_CELL_H  = 44
    Z_GAP     = 6
    Z_ROW_GAP = 38               # vertical gap between value rows (for op label)
    zoom_W = Z_LABEL_W + 8 * Z_CELL_W + 7 * Z_GAP

    # ---- frame width: max of the two panels' widths
    layout_W = W_D + GAP + W_Q
    content_W = max(layout_W, zoom_W)

    # ---- vertical plan
    layout_top    = FRAME_Y + TITLE_H + 32       # "storage layout:" header
    layout_box_y  = layout_top + 26
    layout_bot    = layout_box_y + H_BOX + 28    # box + byte labels
    section_gap   = 32
    zoom_top      = layout_bot + section_gap     # "example values" header
    zoom_first_y  = zoom_top + 30                # first row of cells
    zoom_row_pitch = Z_CELL_H + Z_ROW_GAP
    zoom_last_y    = zoom_first_y + 2 * zoom_row_pitch
    formula_y      = zoom_last_y + Z_CELL_H + 32

    FRAME_W = content_W + 2 * (PAD_X + 24)
    FRAME_H = (formula_y + 28) - FRAME_Y + 24

    # ---- outer frame
    elements.append(rect("q8_frame", FRAME_X, FRAME_Y, FRAME_W, FRAME_H,
                         stroke=FRAME, bg=WHITE, sw=1.5, rounded=True))

    # ---- title + subtitle
    place_text("Q8_0  block", FRAME_X + 22, FRAME_Y + 16,
               ORANGE, FS_TITLE, align="left")
    sub = "32 weights  →  34 bytes   (8.5 bits / weight)"
    place_text(sub,
               FRAME_X + FRAME_W - 22 - int(len(sub) * FS_NOTE * 0.58),
               FRAME_Y + 22, GRAY, FS_NOTE, align="left")

    # ============== LAYOUT panel ====================================
    place_text("storage layout", FRAME_X + 22, layout_top, GRAY, FS_NOTE)

    # center the layout row inside the frame
    layout_left = FRAME_X + (FRAME_W - layout_W) / 2

    x = layout_left
    labeled_box("q8_d", x, layout_box_y, W_D, H_BOX, "d\nfp16",
                SCALE_BG, fs=FS_LABEL)
    bytes_label(x + W_D/2, layout_box_y + H_BOX + 10, "2 B")
    x += W_D + GAP

    labeled_box("q8_q", x, layout_box_y, W_Q, H_BOX,
                "q[0]  q[1]  q[2]   ...   q[30]  q[31]   (32 × int8)",
                QUANT_BG, fs=FS_LABEL)
    bytes_label(x + W_Q/2, layout_box_y + H_BOX + 10, "32 B")

    # ============== ZOOM panel ======================================
    place_text(f"example values  (showing 8 of 32; "
               f"indices {', '.join(str(i) for i in Q8_DISPLAY_IDX)})",
               FRAME_X + 22, zoom_top, GRAY, FS_NOTE)

    # center the zoom row inside the frame
    zoom_left = FRAME_X + (FRAME_W - zoom_W) / 2

    # row 1: original f32 weights
    zoom_row(zoom_left, zoom_first_y, "w  (f32)", Q8_W,
             label_w=Z_LABEL_W, cell_w=Z_CELL_W, cell_h=Z_CELL_H,
             gap=Z_GAP, cell_bg=WHITE)

    # op label between row 1 and row 2
    place_text("quantize:    q[i]  =  round( w[i] / d )",
               zoom_left + Z_LABEL_W,
               zoom_first_y + Z_CELL_H + (Z_ROW_GAP - FS_NOTE) / 2 - 2,
               BLUE, FS_NOTE)

    # row 2: int8 quants
    row2_y = zoom_first_y + zoom_row_pitch
    zoom_row(zoom_left, row2_y, "q  (int8)", Q8_Q,
             label_w=Z_LABEL_W, cell_w=Z_CELL_W, cell_h=Z_CELL_H,
             gap=Z_GAP, cell_bg=QUANT_BG)

    # op label between row 2 and row 3
    place_text("dequantize:    ŵ[i]  =  d · q[i]",
               zoom_left + Z_LABEL_W,
               row2_y + Z_CELL_H + (Z_ROW_GAP - FS_NOTE) / 2 - 2,
               BLUE, FS_NOTE)

    # row 3: reconstructed f32
    row3_y = zoom_first_y + 2 * zoom_row_pitch
    zoom_row(zoom_left, row3_y, "ŵ  (f32)", Q8_WH,
             label_w=Z_LABEL_W, cell_w=Z_CELL_W, cell_h=Z_CELL_H,
             gap=Z_GAP, cell_bg=HAT_BG)

    # ============== formula / constants =============================
    place_text(
        f"d  =  max|w| / 127  =  {Q8_AMAX} / 127  =  {Q8_D}"
        f"        (fp16, shared by the block)",
        FRAME_X + 22, formula_y, INK, FS_NOTE)

    audit("Q8_0")
    write_doc("q8_0.excalidraw")

# ================================================================ Q4_K
def build_q4_k():
    reset()

    FRAME_X = 80
    FRAME_Y = 80
    PAD_X   = 40
    TITLE_H = 56

    # ---- LAYOUT panel: header row + sub-block row
    H_BOX = 64
    W_D    = 78
    W_DMIN = 88
    W_SM   = 360
    HGAP   = 14
    HEADER_W = W_D + HGAP + W_DMIN + HGAP + W_SM

    SUB_W   = 108
    SUB_GAP = 10
    DATA_ROW_W = 8 * SUB_W + 7 * SUB_GAP

    # ---- ZOOM panel geometry
    Z_LABEL_W = 112
    Z_CELL_W  = 72
    Z_CELL_H  = 44
    Z_GAP     = 6
    Z_ROW_GAP = 38
    zoom_W = Z_LABEL_W + 8 * Z_CELL_W + 7 * Z_GAP

    layout_W = max(HEADER_W, DATA_ROW_W)
    content_W = max(layout_W, zoom_W)

    # ---- vertical plan
    layout_top  = FRAME_Y + TITLE_H + 32              # "storage layout:" header
    H_ROW_Y     = layout_top + 26                     # header boxes
    D_ROW_Y     = H_ROW_Y + H_BOX + 28 + 18           # sub-block boxes (after byte labels)
    layout_bot  = D_ROW_Y + H_BOX + 28                # sub-block byte label
    section_gap = 30
    zoom_top    = layout_bot + section_gap            # "zoom in: sub-block 3"
    # annotation has 3 lines (~22 px each); leave generous room before first cell row
    annot_y       = zoom_top + 24
    ANNOT_LINES   = 3
    ANNOT_H       = ANNOT_LINES * FS_BYTES * LH + 4
    zoom_first_y  = annot_y + ANNOT_H + 18
    zoom_row_pitch = Z_CELL_H + Z_ROW_GAP
    zoom_last_y    = zoom_first_y + 2 * zoom_row_pitch
    formula_y      = zoom_last_y + Z_CELL_H + 32

    FRAME_W = content_W + 2 * (PAD_X + 24)
    FRAME_H = (formula_y + 28) - FRAME_Y + 24

    # ---- outer frame
    elements.append(rect("q4_frame", FRAME_X, FRAME_Y, FRAME_W, FRAME_H,
                         stroke=FRAME, bg=WHITE, sw=1.5, rounded=True))

    # ---- title + subtitle
    place_text("Q4_K  super-block", FRAME_X + 22, FRAME_Y + 16,
               PURPLE, FS_TITLE, align="left")
    sub = "256 weights  →  144 bytes   (4.5 bits / weight)"
    place_text(sub,
               FRAME_X + FRAME_W - 22 - int(len(sub) * FS_NOTE * 0.58),
               FRAME_Y + 22, GRAY, FS_NOTE, align="left")

    # ============== LAYOUT panel ====================================
    place_text("storage layout", FRAME_X + 22, layout_top, GRAY, FS_NOTE)

    # header row -- centered
    header_left = FRAME_X + (FRAME_W - HEADER_W) / 2
    x = header_left
    labeled_box("q4_d", x, H_ROW_Y, W_D, H_BOX, "d\nfp16",
                SCALE_BG, fs=FS_LABEL)
    bytes_label(x + W_D/2, H_ROW_Y + H_BOX + 10, "2 B")
    x += W_D + HGAP
    labeled_box("q4_dmin", x, H_ROW_Y, W_DMIN, H_BOX, "dmin\nfp16",
                SCALE_BG, fs=FS_LABEL)
    bytes_label(x + W_DMIN/2, H_ROW_Y + H_BOX + 10, "2 B")
    x += W_DMIN + HGAP
    labeled_box("q4_sm", x, H_ROW_Y, W_SM, H_BOX,
                "scales[8]  +  mins[8]\n(8 + 8  ×  6-bit, packed)",
                META_BG, fs=FS_LABEL)
    bytes_label(x + W_SM/2, H_ROW_Y + H_BOX + 10, "12 B")

    # sub-block row -- centered
    data_left = FRAME_X + (FRAME_W - DATA_ROW_W) / 2
    Z_J = 3                                          # the zoomed sub-block
    for j in range(8):
        xj = data_left + j * (SUB_W + SUB_GAP)
        # subtle highlight on the zoomed sub-block
        bg = "#fff3bf" if j == Z_J else QUANT_BG
        stroke_w = 3 if j == Z_J else 2
        cid = f"q4_sub{j}"
        tid = f"{cid}__t"
        elements.append(rect(cid, xj, D_ROW_Y, SUB_W, H_BOX,
                             stroke=INK, bg=bg, sw=stroke_w,
                             rounded=True, text_id=tid))
        elements.append(bound_text(tid, cid, xj + SUB_W/2, D_ROW_Y + H_BOX/2,
                                   SUB_W - 8, H_BOX, f"sub {j}\n32 × 4-bit",
                                   INK, FS_LABEL - 2))
    place_centered(data_left + DATA_ROW_W/2,
                   D_ROW_Y + H_BOX + 10,
                   "8  ×  16 B  =  128 B",
                   BLUE, FS_BYTES)

    # ============== ZOOM panel ======================================
    place_text(f"zoom into sub-block {Z_J}  (showing 8 of 32 weights; "
               f"indices {', '.join(str(i) for i in Q4_DISPLAY_IDX)})",
               FRAME_X + 22, zoom_top, GRAY, FS_NOTE)

    # side-annotations: derived constants for this sub-block
    annot = (f"shared (fp16):     d = {Q4_D},     dmin = {Q4_DMIN}\n"
             f"sub {Z_J} (6-bit):     scale[{Z_J}] = {Q4_SC3},     "
             f"min[{Z_J}] = {Q4_M3}\n"
             f"effective:     d · scale[{Z_J}] = {Q4_DEFF},     "
             f"dmin · min[{Z_J}] = {Q4_MEFF}")
    place_text(annot, FRAME_X + 22, annot_y, INK, FS_BYTES)

    zoom_left = FRAME_X + (FRAME_W - zoom_W) / 2

    # row 1: original f32 weights
    zoom_row(zoom_left, zoom_first_y, "w  (f32)", Q4_W,
             label_w=Z_LABEL_W, cell_w=Z_CELL_W, cell_h=Z_CELL_H,
             gap=Z_GAP, cell_bg=WHITE)

    place_text("quantize:    q[i]  =  round( ( w[i] + dmin·min ) "
               "/ ( d·scale ) ),   clip to [0, 15]",
               zoom_left + Z_LABEL_W,
               zoom_first_y + Z_CELL_H + (Z_ROW_GAP - FS_NOTE) / 2 - 2,
               BLUE, FS_NOTE)

    # row 2: 4-bit quants
    row2_y = zoom_first_y + zoom_row_pitch
    zoom_row(zoom_left, row2_y, "q  (4-bit)", Q4_Q,
             label_w=Z_LABEL_W, cell_w=Z_CELL_W, cell_h=Z_CELL_H,
             gap=Z_GAP, cell_bg=QUANT_BG)

    place_text("dequantize:    ŵ[i]  =  d · scale · q[i]  −  dmin · min",
               zoom_left + Z_LABEL_W,
               row2_y + Z_CELL_H + (Z_ROW_GAP - FS_NOTE) / 2 - 2,
               BLUE, FS_NOTE)

    # row 3: reconstructed f32
    row3_y = zoom_first_y + 2 * zoom_row_pitch
    zoom_row(zoom_left, row3_y, "ŵ  (f32)", Q4_WH,
             label_w=Z_LABEL_W, cell_w=Z_CELL_W, cell_h=Z_CELL_H,
             gap=Z_GAP, cell_bg=HAT_BG)

    # ============== formula / summary ===============================
    place_text(
        f"d, dmin are picked so the 8 per-sub-block scales (and mins) "
        f"fit in 6 bits each.",
        FRAME_X + 22, formula_y, INK, FS_NOTE)

    audit("Q4_K")
    write_doc("q4_k.excalidraw")

# ---------------------------------------------------------------- main
if __name__ == "__main__":
    build_q8_0()
    build_q4_k()
    print("wrote q8_0.excalidraw, q4_k.excalidraw")
