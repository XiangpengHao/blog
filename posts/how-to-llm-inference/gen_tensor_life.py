#!/usr/bin/env python3
"""Generate tensor-life.excalidraw.

Idea (matches the blog's "life of a tensor" framing): the *shape* is the
node, the *matrix multiply* is the edge (labelled with the weight shape).
Op names (RoPE/softmax/RMSNorm/SiLU/...) are deliberately omitted -- only
shapes matter. Each block is an INDEPENDENT panel; blocks are not connected.
"""
import json

# ---------------------------------------------------------------- geometry
PANEL_LEFT = 90
COL_W   = 235          # horizontal pitch between shape columns
ROW_H   = 90           # vertical pitch between fan-out lanes
TITLE_H = 56
PAD     = 34
GAP     = 70           # vertical gap between independent panels
COL0    = 96           # x of first column centre, from panel content-left
ROW0    = 50           # y of first lane centre, from panel content-top

FONT     = 6
FS_TITLE = 22
FS_NODE  = 18
FS_LABEL = 15
FS_NOTE  = 14
LH       = 1.25

# ---------------------------------------------------------------- palette
INK   = "#1e1e1e"
BLUE  = "#1971c2"      # matrix-multiply edges + weight-shape labels
GRAY  = "#868e96"      # non-matmul edges + notes
ACT   = "#ffec99"      # the activation tensor [1, 2048] (the shared interface)
ACTBD = "#f08c00"
MID   = "#ffffff"      # intermediate shapes
WHITE = "#ffffff"

ACCENT = {                 # per-panel title / frame accent
    "EMB":  "#f08c00",
    "DN":   "#2f9e44",
    "ATTN": "#1971c2",
    "MOE":  "#7048e8",
    "OUT":  "#f08c00",
}

# ---------------------------------------------------------------- content
# node:  id, col, row, kind ("act"|"mid"), text
# edge:  src, dst, kind ("mm"|"other"), label
# note:  anchor_node, dx, dy, text
PANELS = [
    dict(key="EMB", title="Token embedding", nodes=[
            ("e_tok", 0, 0, "act", "[1]"),
            ("e_act", 1, 0, "act", "[1, 2048]"),
         ], edges=[
            ("e_tok", "e_act", "other", "lookup"),
         ], notes=[
            ("e_tok", 117, 44, "embedding table  [248320, 2048]"),
         ]),

    dict(key="DN", title="DeltaNet", nodes=[
            ("d_in",  0, 1.5, "act", "[1, 2048]"),
            ("d_8192",1, 0.0, "mid", "[1, 8192]"),
            ("d_4096",1, 1.0, "mid", "[1, 4096]"),
            ("d_32a", 1, 2.0, "mid", "[1, 32]"),
            ("d_32b", 1, 3.0, "mid", "[1, 32]"),
            ("d_mrg", 2, 1.5, "mid", "[1, 4096]"),
            ("d_out", 3, 1.5, "act", "[1, 2048]"),
         ], edges=[
            ("d_in","d_8192","mm","[2048, 8192]"),
            ("d_in","d_4096","mm","[2048, 4096]"),
            ("d_in","d_32a","mm","[2048, 32]"),
            ("d_in","d_32b","mm","[2048, 32]"),
            ("d_8192","d_mrg","other",""),
            ("d_4096","d_mrg","other",""),
            ("d_32a","d_mrg","other",""),
            ("d_32b","d_mrg","other",""),
            ("d_mrg","d_out","mm","[4096, 2048]"),
         ], notes=[
            ("d_mrg", 0, 44, "(other math, shape only)"),
         ]),

    dict(key="ATTN", title="Attention", nodes=[
            ("a_in",  0, 1.5, "act", "[1, 2048]"),
            ("a_q",   1, 0.0, "mid", "[1, 4096]"),
            ("a_g",   1, 1.0, "mid", "[1, 4096]"),
            ("a_k",   1, 2.0, "mid", "[1, 512]"),
            ("a_v",   1, 3.0, "mid", "[1, 512]"),
            ("a_mrg", 2, 1.5, "mid", "[1, 4096]"),
            ("a_out", 3, 1.5, "act", "[1, 2048]"),
         ], edges=[
            ("a_in","a_q","mm","[2048, 4096]"),
            ("a_in","a_g","mm","[2048, 4096]"),
            ("a_in","a_k","mm","[2048, 512]"),
            ("a_in","a_v","mm","[2048, 512]"),
            ("a_q","a_mrg","other",""),
            ("a_g","a_mrg","other",""),
            ("a_k","a_mrg","other",""),
            ("a_v","a_mrg","other",""),
            ("a_mrg","a_out","mm","[4096, 2048]"),
         ], notes=[
            ("a_mrg", 0, 44, "(other math + KV cache)"),
         ]),

    dict(key="MOE", title="MoE", nodes=[
            ("m_in",  0, 1.0, "act", "[1, 2048]"),
            ("m_sel", 1, 0.0, "mid", "[1, 256]"),
            ("m_h",   1, 1.0, "mid", "[1, 512]"),
            ("m_eo",  2, 1.0, "mid", "[1, 2048]"),
            ("m_out", 3, 1.0, "act", "[1, 2048]"),
         ], edges=[
            ("m_in","m_sel","mm","[2048, 256]"),
            ("m_in","m_h","mm","[2048, 512]"),
            ("m_h","m_eo","mm","[512, 2048]"),
            ("m_eo","m_out","other","sum"),
         ], notes=[
            ("m_sel", 0, -38, "selects 8 of 256 experts"),
            ("m_h",  118, 40, "one expert   (8 run + 1 always active)"),
         ]),

    dict(key="OUT", title="Final output", nodes=[
            ("o_in",  0, 0, "act", "[1, 2048]"),
            ("o_out", 1, 0, "act", "[1, 248320]"),
         ], edges=[
            ("o_in","o_out","mm","[2048, 248320]"),
         ], notes=[
            ("o_out", 0, 40, "one weight per vocabulary token"),
         ]),
]

# ---------------------------------------------------------------- engine
elements = []
arrows_meta = []
labels_meta = []
_idx = [0]; _seed = [777000]

def nxt_index():
    s = f"b{_idx[0]:04d}"; _idx[0] += 1; return s
def seed():
    _seed[0] += 7; return _seed[0]

def base(extra):
    e = {"angle": 0, "strokeColor": INK, "backgroundColor": "transparent",
         "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
         "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
         "index": nxt_index(), "roundness": None, "seed": seed(), "version": 1,
         "versionNonce": seed(), "isDeleted": False, "boundElements": [],
         "updated": 1780770446206, "link": None, "locked": False}
    e.update(extra); return e

def rect(id, x, y, w, h, stroke, bg, sw=2, rounded=True, text_id=None):
    e = base({"id": id, "type": "rectangle", "x": x, "y": y, "width": w, "height": h,
              "strokeColor": stroke, "backgroundColor": bg, "strokeWidth": sw,
              "roundness": {"type": 3} if rounded else None})
    if text_id:
        e["boundElements"] = [{"type": "text", "id": text_id}]
    return e

def bound_text(id, cid, cx, cy, w, h, text, color, fs):
    th = len(text.split("\n")) * fs * LH
    return base({"id": id, "type": "text", "x": cx - w/2, "y": cy - th/2,
                 "width": w, "height": th, "strokeColor": color, "text": text,
                 "originalText": text, "fontSize": fs, "fontFamily": FONT,
                 "textAlign": "center", "verticalAlign": "middle",
                 "containerId": cid, "autoResize": False, "lineHeight": LH})

def free_text(text, color, fs, align="left"):
    lines = text.split("\n")
    w = int(max(len(l) for l in lines) * fs * 0.56) + 6
    h = int(len(lines) * fs * LH) + 2
    el = base({"id": f"t{_idx[0]}", "type": "text", "x": 0, "y": 0,
               "width": w, "height": h, "strokeColor": color, "text": text,
               "originalText": text, "fontSize": fs, "fontFamily": FONT,
               "textAlign": align, "verticalAlign": "top", "containerId": None,
               "autoResize": True, "lineHeight": LH})
    return el, w, h

def label_centered(cx, cy, text, color, fs=FS_LABEL):
    if not text:
        return
    el, w, h = free_text(text, color, fs, align="center")
    el["x"] = cx - w/2; el["y"] = cy - h/2; el["textAlign"] = "center"
    elements.append(el)
    labels_meta.append((text, el["x"], el["y"], w, h))

def arrow(id, pts, color, dashed=False, width=2.4):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = pts[0]
    rel = [[p[0]-x0, p[1]-y0] for p in pts]
    return base({"id": id, "type": "arrow", "x": x0, "y": y0,
                 "width": max(xs)-min(xs), "height": max(ys)-min(ys),
                 "strokeColor": color, "strokeWidth": width,
                 "strokeStyle": "dashed" if dashed else "solid",
                 "roundness": {"type": 2}, "points": rel,
                 "lastCommittedPoint": None, "startBinding": None,
                 "endBinding": None, "startArrowhead": None,
                 "endArrowhead": "arrow", "elbowed": False})

def node_w(text):
    return max(116, int(max(len(l) for l in text.split("\n")) * FS_NODE * 0.62) + 30)
NODE_H = 50

# ---- layout -------------------------------------------------------------
node = {}
cursorY = 150
panel_box = {}
for p in PANELS:
    content_top = cursorY + TITLE_H
    rows = [n[2] for n in p["nodes"]]
    for nid, col, row, kind, text in p["nodes"]:
        w = node_w(text)
        cx = PANEL_LEFT + PAD + COL0 + col * COL_W
        cy = content_top + ROW0 + row * ROW_H
        node[nid] = dict(id=nid, panel=p["key"], cx=cx, cy=cy, w=w, h=NODE_H,
                         kind=kind, text=text)
    ids = [n[0] for n in p["nodes"]]
    left   = min(node[i]["cx"] - node[i]["w"]/2 for i in ids) - PAD
    right  = max(node[i]["cx"] + node[i]["w"]/2 for i in ids) + PAD
    top    = cursorY
    bottom = max(node[i]["cy"] + node[i]["h"]/2 for i in ids) + PAD
    panel_box[p["key"]] = [left, top, right, bottom]
    cursorY = bottom + GAP

def anchor(nid, side):
    n = node[nid]; cx, cy, w, h = n["cx"], n["cy"], n["w"], n["h"]
    return {"l": (cx-w/2, cy), "r": (cx+w/2, cy),
            "t": (cx, cy-h/2), "b": (cx, cy+h/2), "c": (cx, cy)}[side]

# ---- panels (behind) ----------------------------------------------------
for p in PANELS:
    k = p["key"]; l, t, r, b = panel_box[k]
    elements.append(rect(f"box_{k}", l, t, r-l, b-t, "#ced4da", WHITE,
                         sw=1.5, rounded=True))
    tt, tw, th = free_text(p["title"], ACCENT[k], FS_TITLE, align="left")
    tt["x"] = l + 22; tt["y"] = t + 16
    elements.append(tt)

# ---- shape nodes --------------------------------------------------------
for p in PANELS:
    for nid, col, row, kind, text in p["nodes"]:
        n = node[nid]
        x = n["cx"] - n["w"]/2; y = n["cy"] - n["h"]/2
        stroke = ACTBD if kind == "act" else "#868e96"
        bg = ACT if kind == "act" else MID
        tid = f"{nid}__t"
        elements.append(rect(nid, x, y, n["w"], n["h"], stroke, bg, sw=2,
                             rounded=True, text_id=tid))
        elements.append(bound_text(tid, nid, n["cx"], n["cy"], n["w"]-10,
                                   n["h"], text, INK, FS_NODE))

# ---- edges --------------------------------------------------------------
for p in PANELS:
    for src, dst, kind, label in p["edges"]:
        s = node[src]; d = node[dst]
        color = BLUE if kind == "mm" else GRAY
        dashed = kind == "other"
        sx, sy = anchor(src, "r"); ex, ey = anchor(dst, "l")
        pts = [(sx, sy), (ex, ey)]
        elements.append(arrow(f"e_{src}_{dst}", pts, color, dashed=dashed,
                              width=2.6 if kind == "mm" else 2.0))
        arrows_meta.append((f"e_{src}_{dst}", pts, {src, dst}))
        if label:
            mx, my = (sx+ex)/2, (sy+ey)/2
            off = 34 if kind == "mm" else 20
            label_centered(mx, my - off, label,
                           BLUE if kind == "mm" else GRAY,
                           FS_LABEL if kind == "mm" else FS_NOTE)

# ---- notes --------------------------------------------------------------
for p in PANELS:
    for anc, dx, dy, text in p.get("notes", []):
        n = node[anc]
        label_centered(n["cx"] + dx, n["cy"] + dy, text, GRAY, FS_NOTE)

# ---- legend + title -----------------------------------------------------
gl = min(panel_box[k][0] for k in ACCENT)
tt, tw, th = free_text("The life of a tensor", INK, 30, align="left")
tt["x"] = gl; tt["y"] = 40; elements.append(tt)
leg, lw, lh = free_text(
    "box = tensor shape      blue arrow = matrix multiply (weight shape shown)"
    "      grey arrow = other math (shape only)", GRAY, 15, align="left")
leg["x"] = gl; leg["y"] = 84; elements.append(leg)

# ---- audits -------------------------------------------------------------
def bbox(nid):
    n = node[nid]
    return (n["cx"]-n["w"]/2, n["cy"]-n["h"]/2, n["cx"]+n["w"]/2, n["cy"]+n["h"]/2)
ids = list(node)
overlaps = []
for i in range(len(ids)):
    for j in range(i+1, len(ids)):
        a, b = bbox(ids[i]), bbox(ids[j])
        if max(0, min(a[2],b[2])-max(a[0],b[0])) > 2 and \
           max(0, min(a[3],b[3])-max(a[1],b[1])) > 2:
            overlaps.append((ids[i], ids[j]))

def seg_hits(p0, p1, r, inset=4):
    rx0, ry0, rx1, ry1 = r[0]+inset, r[1]+inset, r[2]-inset, r[3]-inset
    if rx1 <= rx0 or ry1 <= ry0:
        return False
    for s in range(41):
        t = s/40
        x = p0[0]+(p1[0]-p0[0])*t; y = p0[1]+(p1[1]-p0[1])*t
        if rx0 < x < rx1 and ry0 < y < ry1:
            return True
    return False
node_rects = {i: bbox(i) for i in ids}
arrow_warns = []
for aid, pts, excl in arrows_meta:
    for k in range(len(pts)-1):
        for nid, r in node_rects.items():
            if nid in excl:
                continue
            if seg_hits(pts[k], pts[k+1], r):
                arrow_warns.append((aid, nid))

def ov(a, b, m=0):
    return not (a[2]-m <= b[0] or b[2]-m <= a[0] or a[3]-m <= b[1] or b[3]-m <= a[1])
label_warns = []
for li, (txt, lx, ly, lw_, lh_) in enumerate(labels_meta):
    lr = (lx, ly, lx+lw_, ly+lh_)
    for nid, r in node_rects.items():
        if ov(lr, r, m=2):
            label_warns.append((txt, "node:"+nid))
    for lj in range(li+1, len(labels_meta)):
        t2, x2, y2, w2, h2 = labels_meta[lj]
        if ov(lr, (x2, y2, x2+w2, y2+h2), m=2):
            label_warns.append((txt, "label:"+t2))

doc = {"type": "excalidraw", "version": 2,
       "source": "https://github.com/excalidraw/excalidraw",
       "elements": elements,
       "appState": {"gridSize": 20, "gridStep": 5, "gridModeEnabled": False,
                    "viewBackgroundColor": "#ffffff"},
       "files": {}}
with open("tensor-life.excalidraw", "w") as f:
    json.dump(doc, f, indent=2)

print(f"elements: {len(elements)}  nodes: {len(node)}")
print(f"canvas: {int(max(panel_box[k][2] for k in ACCENT))} x {int(cursorY)}")
print(f"node overlaps:    {overlaps or 'none'}")
print(f"arrow-thru-box:   {arrow_warns or 'none'}")
print(f"label collisions: {label_warns or 'none'}")
for k in ACCENT:
    l, t, r, b = panel_box[k]
    print(f"  {k:5s} x[{int(l)},{int(r)}] y[{int(t)},{int(b)}]")
