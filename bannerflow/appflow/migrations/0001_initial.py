import django.db.models.deletion
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone

# ─────────────────────────────────────────────────────────────────────────────
#  Fabric.js 5.x canvas-JSON helpers  (display units: 540 px wide)
#  Format heights → 1:1=540  1.91:1=283  4:5=675  9:16=960
# ─────────────────────────────────────────────────────────────────────────────

_SH = {
    "color": "rgba(0,0,0,0.55)", "blur": 8,
    "offsetX": 2, "offsetY": 2,
    "affectStroke": False, "nonScaling": False,
}


def _r(left, top, w, h, fill,
       rx=0, stroke=None, sw=0, dash=None, op=1.0, ang=0):
    o = {
        "type": "rect", "version": "5.3.1",
        "originX": "left", "originY": "top",
        "left": left, "top": top, "width": w, "height": h,
        "fill": fill, "rx": rx, "ry": rx,
        "strokeWidth": sw, "stroke": stroke,
        "opacity": op, "angle": ang,
        "scaleX": 1, "scaleY": 1,
        "selectable": True, "evented": True,
    }
    if dash:
        o["strokeDashArray"] = dash
    return o


def _c(left, top, radius, fill, op=1.0):
    """Circle — left/top are top-left corner of bounding box."""
    return {
        "type": "circle", "version": "5.3.1",
        "originX": "left", "originY": "top",
        "left": left, "top": top, "radius": radius,
        "fill": fill, "strokeWidth": 0, "stroke": None,
        "opacity": op, "angle": 0,
        "scaleX": 1, "scaleY": 1,
        "selectable": True, "evented": True,
    }


def _t(text, left, top, size, fill="#ffffff", weight="400",
       family="Poppins", align="left", through=False, dtype=None, op=1.0):
    o = {
        "type": "i-text", "version": "5.3.1",
        "originX": "left", "originY": "top",
        "left": left, "top": top,
        "fill": fill, "fontSize": size,
        "fontWeight": weight, "fontFamily": family,
        "fontStyle": "normal", "textAlign": align,
        "linethrough": through, "underline": False,
        "shadow": _SH,
        "opacity": op, "angle": 0,
        "scaleX": 1, "scaleY": 1,
        "text": text,
        "selectable": True, "evented": True,
    }
    if dtype:
        o["dataType"] = dtype
    return o


def _img(left, top, w, h, stroke_color, rx=12):
    """Dashed product-image placeholder."""
    o = _r(left, top, w, h,
           fill="rgba(255,255,255,0.05)",
           rx=rx, stroke=stroke_color, sw=2, dash=[8, 4])
    o["dataType"] = "product_image"
    return o


def _cv(objects, bg):
    return {"version": "5.3.1", "objects": objects, "background": bg}


# ─────────────────────────────────────────────────────────────────────────────
#  Default template definitions — 5 templates × 4 formats
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATES_DATA = [

    # ══════════════════════════════════════════════
    # 1.  OFERTA FLASH  ·  red / orange
    # ══════════════════════════════════════════════
    {
        "name": "Oferta Flash",
        "canvas_data": {
            "1:1": _cv([
                _r(0, 0, 540, 540, "#1a0505"),
                _r(0, 0, 540, 5, "#e53e3e"),
                _r(0, 535, 540, 5, "#e53e3e"),
                _c(310, -120, 220, "#e53e3e", 0.13),
                _c(-110, 350, 160, "#ff8c00", 0.09),
                _img(278, 68, 234, 242, "#e53e3e"),
                _c(22, 22, 52, "#e53e3e"),
                _t("¡-50%", 34, 42, 19, "#ffffff", "800", align="center", dtype="badge"),
                _t("Título del Producto", 22, 96, 27, "#ffffff", "800", dtype="title"),
                _t("Descripción corta del artículo", 22, 136, 13, "#cccccc"),
                _t("$99.990", 22, 163, 21, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 22, 197, 52, "#ff8c00", "800", dtype="offer_price"),
                _t("Tu Tienda", 22, 506, 15, "#aaaaaa", dtype="store_name"),
            ], "#0f0000"),

            "1.91:1": _cv([
                _r(0, 0, 540, 283, "#1a0505"),
                _r(0, 0, 540, 4, "#e53e3e"),
                _r(0, 279, 540, 4, "#e53e3e"),
                _c(340, -90, 180, "#e53e3e", 0.12),
                _img(302, 26, 216, 222, "#e53e3e"),
                _c(22, 18, 38, "#e53e3e"),
                _t("¡50%", 30, 30, 14, "#ffffff", "800", align="center", dtype="badge"),
                _t("Título del\nProducto", 20, 66, 21, "#ffffff", "800", dtype="title"),
                _t("$99.990", 20, 118, 16, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 20, 142, 40, "#ff8c00", "800", dtype="offer_price"),
                _t("Tu Tienda", 20, 252, 12, "#aaaaaa", dtype="store_name"),
            ], "#0f0000"),

            "4:5": _cv([
                _r(0, 0, 540, 675, "#1a0505"),
                _r(0, 0, 540, 5, "#e53e3e"),
                _r(0, 670, 540, 5, "#e53e3e"),
                _c(320, -110, 210, "#e53e3e", 0.11),
                _c(-110, 540, 180, "#ff8c00", 0.07),
                _img(120, 54, 300, 292, "#e53e3e"),
                _c(22, 62, 48, "#e53e3e"),
                _t("¡-50%", 28, 80, 17, "#ffffff", "800", align="center", dtype="badge"),
                _r(40, 360, 460, 2, "#e53e3e", op=0.35),
                _t("Título del Producto", 22, 378, 28, "#ffffff", "800", dtype="title"),
                _t("$99.990", 22, 420, 20, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 22, 450, 54, "#ff8c00", "800", dtype="offer_price"),
                _t("Tu Tienda", 22, 632, 16, "#aaaaaa", dtype="store_name"),
            ], "#0f0000"),

            "9:16": _cv([
                _r(0, 0, 540, 960, "#1a0505"),
                _r(0, 0, 540, 6, "#e53e3e"),
                _r(0, 954, 540, 6, "#e53e3e"),
                _c(310, -120, 280, "#e53e3e", 0.11),
                _c(-100, 810, 210, "#ff8c00", 0.08),
                _img(95, 88, 350, 372, "#e53e3e", rx=16),
                _c(22, 96, 50, "#e53e3e"),
                _t("¡-50%", 28, 116, 18, "#ffffff", "800", align="center", dtype="badge"),
                _r(40, 478, 460, 2, "#e53e3e", op=0.35),
                _t("Título del Producto", 36, 498, 32, "#ffffff", "800", dtype="title"),
                _t("Descripción del artículo", 36, 546, 15, "#cccccc"),
                _t("$99.990", 36, 578, 22, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 36, 614, 60, "#ff8c00", "800", dtype="offer_price"),
                _r(36, 718, 468, 62, "#e53e3e", rx=12),
                _t("¡Compra Ahora!", 148, 739, 21, "#ffffff", "800"),
                _t("Tu Tienda", 36, 900, 18, "#aaaaaa", dtype="store_name"),
            ], "#0f0000"),
        },
    },

    # ══════════════════════════════════════════════
    # 2.  PREMIUM GOLD  ·  black / gold
    # ══════════════════════════════════════════════
    {
        "name": "Premium Gold",
        "canvas_data": {
            "1:1": _cv([
                _r(0, 0, 540, 540, "#0a0805"),
                _r(0, 0, 540, 4, "#d4af37"),
                _r(0, 536, 540, 4, "#d4af37"),
                _r(0, 0, 4, 540, "#d4af37"),
                _r(536, 0, 4, 540, "#d4af37"),
                _r(18, 18, 504, 504, "rgba(212,175,55,0.06)", rx=8,
                   stroke="#d4af37", sw=1),
                _c(110, -120, 290, "rgba(212,175,55,0.05)"),
                _img(262, 80, 252, 258, "#d4af37", rx=8),
                _t("PREMIUM COLLECTION", 22, 32, 11, "#d4af37", "600"),
                _t("Título del Producto", 22, 86, 27, "#ffffff", "800", dtype="title"),
                _t("Artículo de alta calidad", 22, 126, 13, "#b0a080"),
                _t("$99.990", 22, 160, 21, "#666666", through=True, dtype="original_price"),
                _t("$49.990", 22, 194, 52, "#d4af37", "800", dtype="offer_price"),
                _r(22, 362, 210, 1, "#d4af37", op=0.6),
                _t("Tu Tienda", 22, 506, 15, "#9a9070", dtype="store_name"),
            ], "#050505"),

            "1.91:1": _cv([
                _r(0, 0, 540, 283, "#0a0805"),
                _r(0, 0, 540, 4, "#d4af37"),
                _r(0, 279, 540, 4, "#d4af37"),
                _r(0, 0, 4, 283, "#d4af37"),
                _r(536, 0, 4, 283, "#d4af37"),
                _r(14, 14, 512, 255, "rgba(212,175,55,0.06)", rx=6,
                   stroke="#d4af37", sw=1),
                _img(300, 30, 216, 208, "#d4af37", rx=8),
                _t("PREMIUM", 22, 28, 10, "#d4af37", "600"),
                _t("Título del\nProducto", 22, 60, 21, "#ffffff", "800", dtype="title"),
                _t("$99.990", 22, 116, 16, "#666666", through=True, dtype="original_price"),
                _t("$49.990", 22, 140, 40, "#d4af37", "800", dtype="offer_price"),
                _t("Tu Tienda", 22, 252, 12, "#9a9070", dtype="store_name"),
            ], "#050505"),

            "4:5": _cv([
                _r(0, 0, 540, 675, "#0a0805"),
                _r(0, 0, 540, 4, "#d4af37"),
                _r(0, 671, 540, 4, "#d4af37"),
                _r(0, 0, 4, 675, "#d4af37"),
                _r(536, 0, 4, 675, "#d4af37"),
                _r(18, 18, 504, 639, "rgba(212,175,55,0.06)", rx=8,
                   stroke="#d4af37", sw=1),
                _c(110, -100, 280, "rgba(212,175,55,0.05)"),
                _img(120, 52, 300, 290, "#d4af37", rx=8),
                _t("PREMIUM COLLECTION", 22, 34, 11, "#d4af37", "600"),
                _r(38, 360, 464, 1, "#d4af37", op=0.5),
                _t("Título del Producto", 22, 378, 28, "#ffffff", "800", dtype="title"),
                _t("Artículo de alta calidad", 22, 418, 14, "#b0a080"),
                _t("$99.990", 22, 448, 20, "#666666", through=True, dtype="original_price"),
                _t("$49.990", 22, 478, 54, "#d4af37", "800", dtype="offer_price"),
                _t("Tu Tienda", 22, 632, 16, "#9a9070", dtype="store_name"),
            ], "#050505"),

            "9:16": _cv([
                _r(0, 0, 540, 960, "#0a0805"),
                _r(0, 0, 540, 5, "#d4af37"),
                _r(0, 955, 540, 5, "#d4af37"),
                _r(0, 0, 5, 960, "#d4af37"),
                _r(535, 0, 5, 960, "#d4af37"),
                _r(20, 20, 500, 920, "rgba(212,175,55,0.06)", rx=10,
                   stroke="#d4af37", sw=1),
                _c(110, -100, 310, "rgba(212,175,55,0.05)"),
                _img(95, 78, 350, 365, "#d4af37", rx=10),
                _t("PREMIUM COLLECTION", 120, 46, 12, "#d4af37", "600"),
                _r(40, 462, 460, 1, "#d4af37", op=0.5),
                _t("Título del Producto", 36, 482, 32, "#ffffff", "800", dtype="title"),
                _t("Artículo de alta calidad", 36, 528, 16, "#b0a080"),
                _t("$99.990", 36, 560, 22, "#666666", through=True, dtype="original_price"),
                _t("$49.990", 36, 596, 60, "#d4af37", "800", dtype="offer_price"),
                _r(36, 710, 468, 58, "rgba(212,175,55,0.12)", rx=10,
                   stroke="#d4af37", sw=1),
                _t("Comprar Ahora", 182, 731, 18, "#d4af37", "600"),
                _t("Tu Tienda", 36, 900, 18, "#9a9070", dtype="store_name"),
            ], "#050505"),
        },
    },

    # ══════════════════════════════════════════════
    # 3.  FRESH SUMMER  ·  navy / cyan
    # ══════════════════════════════════════════════
    {
        "name": "Fresh Summer",
        "canvas_data": {
            "1:1": _cv([
                _r(0, 0, 540, 540, "#002a4a"),
                _r(0, 0, 540, 7, "#00b4d8"),
                _r(0, 533, 540, 7, "#00b4d8"),
                _c(300, -110, 230, "#00b4d8", 0.13),
                _c(-100, 370, 180, "#90e0ef", 0.10),
                _r(0, 390, 540, 150, "rgba(0,180,216,0.08)"),
                _img(278, 68, 234, 244, "#00b4d8"),
                _r(22, 22, 172, 34, "#00b4d8", rx=17),
                _t("VERANO 2026", 30, 30, 13, "#ffffff", "700"),
                _t("Título del Producto", 22, 90, 27, "#ffffff", "800", dtype="title"),
                _t("La mejor opción esta temporada", 22, 130, 13, "#90e0ef"),
                _t("$99.990", 22, 160, 21, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 22, 194, 52, "#00b4d8", "800", dtype="offer_price"),
                _t("Tu Tienda", 22, 508, 15, "#90e0ef", dtype="store_name"),
            ], "#001a33"),

            "1.91:1": _cv([
                _r(0, 0, 540, 283, "#002a4a"),
                _r(0, 0, 540, 6, "#00b4d8"),
                _r(0, 277, 540, 6, "#00b4d8"),
                _c(330, -80, 190, "#00b4d8", 0.13),
                _r(0, 180, 540, 103, "rgba(0,180,216,0.08)"),
                _img(302, 24, 216, 220, "#00b4d8"),
                _r(20, 20, 150, 30, "#00b4d8", rx=15),
                _t("VERANO 2026", 28, 26, 11, "#ffffff", "700"),
                _t("Título del\nProducto", 20, 68, 21, "#ffffff", "800", dtype="title"),
                _t("$99.990", 20, 120, 16, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 20, 144, 40, "#00b4d8", "800", dtype="offer_price"),
                _t("Tu Tienda", 20, 252, 12, "#90e0ef", dtype="store_name"),
            ], "#001a33"),

            "4:5": _cv([
                _r(0, 0, 540, 675, "#002a4a"),
                _r(0, 0, 540, 7, "#00b4d8"),
                _r(0, 668, 540, 7, "#00b4d8"),
                _c(310, -100, 220, "#00b4d8", 0.13),
                _c(-100, 550, 180, "#90e0ef", 0.08),
                _r(0, 390, 540, 285, "rgba(0,180,216,0.08)"),
                _img(120, 52, 300, 292, "#00b4d8"),
                _r(22, 60, 172, 32, "#00b4d8", rx=16),
                _t("VERANO 2026", 30, 67, 12, "#ffffff", "700"),
                _t("Título del Producto", 22, 374, 28, "#ffffff", "800", dtype="title"),
                _t("La mejor opción esta temporada", 22, 414, 14, "#90e0ef"),
                _t("$99.990", 22, 446, 20, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 22, 476, 54, "#00b4d8", "800", dtype="offer_price"),
                _t("Tu Tienda", 22, 632, 16, "#90e0ef", dtype="store_name"),
            ], "#001a33"),

            "9:16": _cv([
                _r(0, 0, 540, 960, "#002a4a"),
                _r(0, 0, 540, 7, "#00b4d8"),
                _r(0, 953, 540, 7, "#00b4d8"),
                _c(300, -100, 290, "#00b4d8", 0.13),
                _c(-100, 820, 210, "#90e0ef", 0.08),
                _r(0, 510, 540, 450, "rgba(0,180,216,0.08)"),
                _img(95, 86, 350, 372, "#00b4d8", rx=16),
                _r(36, 98, 188, 36, "#00b4d8", rx=18),
                _t("VERANO 2026", 48, 107, 14, "#ffffff", "700"),
                _t("Título del Producto", 36, 498, 32, "#ffffff", "800", dtype="title"),
                _t("La mejor opción esta temporada", 36, 546, 15, "#90e0ef"),
                _t("$99.990", 36, 578, 22, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 36, 614, 60, "#00b4d8", "800", dtype="offer_price"),
                _r(36, 718, 468, 60, "#00b4d8", rx=12),
                _t("¡Descubrir Ahora!", 152, 738, 18, "#ffffff", "700"),
                _t("Tu Tienda", 36, 902, 18, "#90e0ef", dtype="store_name"),
            ], "#001a33"),
        },
    },

    # ══════════════════════════════════════════════
    # 4.  BLACK FRIDAY  ·  black / yellow
    # ══════════════════════════════════════════════
    {
        "name": "Black Friday",
        "canvas_data": {
            "1:1": _cv([
                _r(0, 0, 540, 540, "#111111"),
                _r(0, 0, 540, 7, "#ffd60a"),
                _r(0, 533, 540, 7, "#ffd60a"),
                _c(300, -110, 240, "#ffd60a", 0.07),
                _c(-100, 370, 190, "#ffd60a", 0.05),
                _img(278, 68, 234, 248, "#ffd60a"),
                _r(0, 0, 200, 56, "#ffd60a"),
                _t("BLACK FRIDAY", 8, 18, 18, "#000000", "900", "Impact"),
                _t("Título del Producto", 22, 94, 27, "#ffffff", "800", dtype="title"),
                _t("$99.990", 22, 132, 21, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 22, 165, 54, "#ffd60a", "900", "Impact", dtype="offer_price"),
                _r(22, 330, 200, 4, "#ffd60a"),
                _t("Tu Tienda", 22, 506, 15, "#aaaaaa", dtype="store_name"),
            ], "#000000"),

            "1.91:1": _cv([
                _r(0, 0, 540, 283, "#111111"),
                _r(0, 0, 540, 6, "#ffd60a"),
                _r(0, 277, 540, 6, "#ffd60a"),
                _c(320, -80, 190, "#ffd60a", 0.07),
                _img(302, 24, 216, 220, "#ffd60a"),
                _r(0, 0, 182, 46, "#ffd60a"),
                _t("BLACK FRIDAY", 6, 14, 14, "#000000", "900", "Impact"),
                _t("Título del\nProducto", 20, 64, 21, "#ffffff", "800", dtype="title"),
                _t("$99.990", 20, 118, 16, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 20, 142, 42, "#ffd60a", "900", "Impact", dtype="offer_price"),
                _t("Tu Tienda", 20, 252, 12, "#aaaaaa", dtype="store_name"),
            ], "#000000"),

            "4:5": _cv([
                _r(0, 0, 540, 675, "#111111"),
                _r(0, 0, 540, 7, "#ffd60a"),
                _r(0, 668, 540, 7, "#ffd60a"),
                _c(310, -100, 230, "#ffd60a", 0.07),
                _c(-100, 560, 190, "#ffd60a", 0.05),
                _img(120, 52, 300, 294, "#ffd60a"),
                _r(0, 0, 236, 52, "#ffd60a"),
                _t("BLACK FRIDAY", 8, 16, 18, "#000000", "900", "Impact"),
                _r(0, 360, 540, 4, "rgba(255,214,10,0.30)"),
                _t("Título del Producto", 22, 378, 28, "#ffffff", "800", dtype="title"),
                _t("$99.990", 22, 418, 20, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 22, 448, 56, "#ffd60a", "900", "Impact", dtype="offer_price"),
                _t("Tu Tienda", 22, 630, 16, "#aaaaaa", dtype="store_name"),
            ], "#000000"),

            "9:16": _cv([
                _r(0, 0, 540, 960, "#111111"),
                _r(0, 0, 540, 8, "#ffd60a"),
                _r(0, 952, 540, 8, "#ffd60a"),
                _c(300, -110, 290, "#ffd60a", 0.07),
                _c(-100, 820, 230, "#ffd60a", 0.05),
                _img(95, 84, 350, 378, "#ffd60a", rx=8),
                _r(0, 0, 292, 62, "#ffd60a"),
                _t("BLACK FRIDAY", 8, 18, 24, "#000000", "900", "Impact"),
                _r(0, 480, 540, 4, "rgba(255,214,10,0.30)"),
                _t("Título del Producto", 36, 500, 32, "#ffffff", "800", dtype="title"),
                _t("Solo por tiempo limitado", 36, 546, 15, "#cccccc"),
                _t("$99.990", 36, 578, 22, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 36, 614, 62, "#ffd60a", "900", "Impact", dtype="offer_price"),
                _r(36, 716, 468, 62, "#ffd60a", rx=8),
                _t("¡COMPRAR AHORA!", 120, 737, 20, "#000000", "900", "Impact"),
                _t("Tu Tienda", 36, 900, 18, "#aaaaaa", dtype="store_name"),
            ], "#000000"),
        },
    },

    # ══════════════════════════════════════════════
    # 5.  VIOLETA MODERNO  ·  purple / pink
    # ══════════════════════════════════════════════
    {
        "name": "Violeta Moderno",
        "canvas_data": {
            "1:1": _cv([
                _r(0, 0, 540, 540, "#16002e"),
                _c(300, -120, 270, "#7c3aed", 0.20),
                _c(-100, 360, 230, "#f472b6", 0.14),
                _r(0, 370, 540, 170, "rgba(124,58,237,0.10)"),
                _r(0, 0, 540, 6, "#7c3aed"),
                _r(0, 534, 540, 6, "#f472b6"),
                _img(278, 68, 234, 244, "#7c3aed"),
                _r(22, 22, 148, 34, "rgba(124,58,237,0.55)", rx=17,
                   stroke="#7c3aed", sw=1),
                _t("NUEVO  ✦", 30, 29, 13, "#e9d5ff", "600"),
                _t("Título del Producto", 22, 92, 27, "#ffffff", "800", dtype="title"),
                _t("Diseño exclusivo para ti", 22, 132, 13, "#d8b4fe"),
                _t("$99.990", 22, 162, 21, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 22, 196, 52, "#f472b6", "800", dtype="offer_price"),
                _t("Tu Tienda", 22, 506, 15, "#c084fc", dtype="store_name"),
            ], "#1a1a2e"),

            "1.91:1": _cv([
                _r(0, 0, 540, 283, "#16002e"),
                _c(310, -80, 210, "#7c3aed", 0.20),
                _c(-80, 180, 170, "#f472b6", 0.13),
                _r(0, 0, 540, 5, "#7c3aed"),
                _r(0, 278, 540, 5, "#f472b6"),
                _img(302, 26, 216, 218, "#7c3aed"),
                _r(20, 20, 138, 28, "rgba(124,58,237,0.55)", rx=14,
                   stroke="#7c3aed", sw=1),
                _t("NUEVO  ✦", 28, 24, 11, "#e9d5ff", "600"),
                _t("Título del\nProducto", 20, 66, 21, "#ffffff", "800", dtype="title"),
                _t("$99.990", 20, 120, 16, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 20, 144, 40, "#f472b6", "800", dtype="offer_price"),
                _t("Tu Tienda", 20, 252, 12, "#c084fc", dtype="store_name"),
            ], "#1a1a2e"),

            "4:5": _cv([
                _r(0, 0, 540, 675, "#16002e"),
                _c(310, -110, 260, "#7c3aed", 0.20),
                _c(-100, 540, 220, "#f472b6", 0.13),
                _r(0, 380, 540, 295, "rgba(124,58,237,0.09)"),
                _r(0, 0, 540, 6, "#7c3aed"),
                _r(0, 669, 540, 6, "#f472b6"),
                _img(120, 50, 300, 292, "#7c3aed"),
                _r(22, 58, 148, 30, "rgba(124,58,237,0.55)", rx=15,
                   stroke="#7c3aed", sw=1),
                _t("NUEVO  ✦", 30, 65, 12, "#e9d5ff", "600"),
                _r(40, 358, 460, 2, "#7c3aed", op=0.4),
                _t("Título del Producto", 22, 376, 28, "#ffffff", "800", dtype="title"),
                _t("Diseño exclusivo para ti", 22, 416, 14, "#d8b4fe"),
                _t("$99.990", 22, 448, 20, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 22, 478, 54, "#f472b6", "800", dtype="offer_price"),
                _t("Tu Tienda", 22, 632, 16, "#c084fc", dtype="store_name"),
            ], "#1a1a2e"),

            "9:16": _cv([
                _r(0, 0, 540, 960, "#16002e"),
                _c(300, -110, 310, "#7c3aed", 0.20),
                _c(-100, 810, 250, "#f472b6", 0.13),
                _r(0, 490, 540, 470, "rgba(124,58,237,0.09)"),
                _r(0, 0, 540, 7, "#7c3aed"),
                _r(0, 953, 540, 7, "#f472b6"),
                _img(95, 84, 350, 375, "#7c3aed", rx=16),
                _r(36, 96, 162, 34, "rgba(124,58,237,0.55)", rx=17,
                   stroke="#7c3aed", sw=1),
                _t("NUEVO  ✦", 44, 104, 13, "#e9d5ff", "600"),
                _r(40, 476, 460, 2, "#7c3aed", op=0.4),
                _t("Título del Producto", 36, 496, 32, "#ffffff", "800", dtype="title"),
                _t("Diseño exclusivo para ti", 36, 544, 15, "#d8b4fe"),
                _t("$99.990", 36, 576, 22, "#888888", through=True, dtype="original_price"),
                _t("$49.990", 36, 612, 60, "#f472b6", "800", dtype="offer_price"),
                _r(36, 714, 468, 62, "rgba(124,58,237,0.45)", rx=12,
                   stroke="#7c3aed", sw=1),
                _t("Explorar Ahora", 180, 735, 18, "#ffffff", "700"),
                _t("Tu Tienda", 36, 902, 18, "#c084fc", dtype="store_name"),
            ], "#1a1a2e"),
        },
    },
]


# ─────────────────────────────────────────────────────────────────────────────
#  Data migration functions
# ─────────────────────────────────────────────────────────────────────────────

def create_admin(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(app_label, model_name)

    username_field = getattr(User, 'USERNAME_FIELD', 'username')
    lookup = {username_field: 'admin'}
    if User.objects.filter(**lookup).exists():
        return

    user = User(**lookup)
    if hasattr(user, 'email'):
        user.email = ''
    if hasattr(user, 'is_staff'):
        user.is_staff = True
    if hasattr(user, 'is_superuser'):
        user.is_superuser = True
    if hasattr(user, 'is_active'):
        user.is_active = True

    now = timezone.now()
    if hasattr(user, 'last_login') and getattr(user, 'last_login', None) is None:
        user.last_login = now
    if hasattr(user, 'date_joined') and getattr(user, 'date_joined', None) is None:
        user.date_joined = now

    if hasattr(user, 'password'):
        user.password = make_password('admin')
    user.save()


def create_default_templates(apps, schema_editor):
    BannerTemplate = apps.get_model('appflow', 'BannerTemplate')
    if BannerTemplate.objects.filter(is_predefined=True).exists():
        return  # already seeded — idempotent
    for tpl in TEMPLATES_DATA:
        BannerTemplate.objects.create(
            name=tpl['name'],
            canvas_data=tpl['canvas_data'],
            is_predefined=True,
            owner=None,
        )


# ─────────────────────────────────────────────────────────────────────────────

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BannerTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('canvas_data', models.JSONField(default=dict, help_text='Fabric.js canvas JSON data')),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='thumbnails/')),
                ('is_predefined', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='templates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.RunPython(create_admin, migrations.RunPython.noop),
        migrations.RunPython(create_default_templates, migrations.RunPython.noop),
    ]
