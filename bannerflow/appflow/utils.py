"""Thumbnail generation for BannerTemplate using Pillow."""
import io
import re

from django.core.files.base import ContentFile


def _parse_color(color_str, default=None):
    """Parse hex, rgb(), rgba() to (R, G, B) tuple. Returns default on failure."""
    if not color_str or color_str == 'transparent':
        return default
    color_str = color_str.strip()

    if color_str.startswith('#'):
        h = color_str.lstrip('#')
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        if len(h) == 6:
            try:
                return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
            except ValueError:
                pass
        return default

    m = re.match(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_str)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    return default


def _blend(fg, bg, opacity):
    """Blend fg color onto bg using opacity."""
    return tuple(int(bg_c * (1 - opacity) + fg_c * opacity) for bg_c, fg_c in zip(bg, fg))


def generate_thumbnail(template):
    """
    Render a 270x270 PNG thumbnail from canvas_data and save to template.thumbnail.
    Uses Pillow — does nothing if Pillow is not installed.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return

    canvas_data = template.canvas_data or {}
    bg_rgb = _parse_color(canvas_data.get('background', '#1a1a2e'), default=(26, 26, 46))

    SIZE = 270
    scale = SIZE / 540.0

    img = Image.new('RGB', (SIZE, SIZE), bg_rgb)
    draw = ImageDraw.Draw(img)

    for obj in canvas_data.get('objects', []):
        obj_type = obj.get('type', '')
        opacity = float(obj.get('opacity', 1.0))
        x = int(obj.get('left', 0) * scale)
        y = int(obj.get('top', 0) * scale)

        if obj_type == 'rect':
            w = max(1, int(obj.get('width', 0) * scale))
            h = max(1, int(obj.get('height', 0) * scale))
            fill_str = obj.get('fill')
            if fill_str and fill_str != 'transparent':
                fill = _parse_color(fill_str)
                if fill:
                    if opacity < 0.99:
                        fill = _blend(fill, bg_rgb, opacity)
                    draw.rectangle([x, y, x + w, y + h], fill=fill)
            stroke_str = obj.get('stroke')
            stroke_w = obj.get('strokeWidth', 0)
            if stroke_str and stroke_str != 'transparent' and stroke_w > 0:
                sc = _parse_color(stroke_str)
                if sc:
                    sw = max(1, int(stroke_w * scale))
                    draw.rectangle([x, y, x + w, y + h], outline=sc, width=sw)

        elif obj_type == 'circle':
            r = max(1, int(obj.get('radius', 0) * scale))
            fill_str = obj.get('fill')
            if fill_str and fill_str != 'transparent':
                fill = _parse_color(fill_str)
                if fill:
                    if opacity < 0.99:
                        fill = _blend(fill, bg_rgb, opacity)
                    draw.ellipse([x, y, x + 2 * r, y + 2 * r], fill=fill)

        elif obj_type in ('i-text', 'text'):
            text = str(obj.get('text', ''))[:40]
            if not text:
                continue
            fill = _parse_color(obj.get('fill', '#ffffff'), default=(255, 255, 255))
            font_size = max(6, int(obj.get('fontSize', 16) * scale))
            font = None
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                try:
                    font = ImageFont.truetype("Arial.ttf", font_size)
                except Exception:
                    try:
                        font = ImageFont.load_default(size=font_size)
                    except Exception:
                        font = ImageFont.load_default()

            if obj.get('originX') == 'center':
                try:
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_w = bbox[2] - bbox[0]
                except Exception:
                    text_w = len(text) * font_size // 2
                x = x - text_w // 2

            try:
                draw.text((x, y), text, fill=fill, font=font)
            except Exception:
                pass

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    buf.seek(0)

    fname = f'thumb_{template.pk}.png'
    template.thumbnail.save(fname, ContentFile(buf.read()), save=True)
