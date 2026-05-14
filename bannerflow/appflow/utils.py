"""Utilities: affiliate URL cleaning + thumbnail generation for BannerTemplate."""
import io
import re
from urllib.parse import urlparse, parse_qs, unquote, quote


# ─────────────────────────────────────────────────────────────────────────────
#  Affiliate URL helpers
# ─────────────────────────────────────────────────────────────────────────────

def clean_affiliate_url(url, profile=None):
    """
    Detect and strip affiliate tracking from a URL.

    Supports:
    - Awin (prefix): URL starts with awin1.com, real product URL is in the
      ``ued`` query parameter URL-encoded.
    - Sodimac (suffix): URL contains a ``?eid=`` suffix appended to the
      product URL.

    Returns:
        (clean_url: str, warning: str|None)
        ``warning`` is a human-readable Spanish message when a mismatch is
        detected between the URL and the user's saved configuration.
    """
    if not url:
        return url, None

    parsed = urlparse(url)

    # --- Awin / Adidas prefix ---
    if 'awin1.com' in (parsed.netloc or ''):
        qs = parse_qs(parsed.query)
        ued_values = qs.get('ued', [])
        if ued_values:
            clean_url = unquote(ued_values[0])
            warning = None
            if profile is not None:
                saved = (profile.awin_prefix or '').strip()
                if not saved:
                    warning = (
                        'Se detectó un enlace de afiliado Awin, pero no tienes '
                        'configurado un prefijo Awin en tu perfil de afiliado.'
                    )
                elif not url.startswith(saved):
                    warning = (
                        'El enlace Awin no coincide con el prefijo guardado en tu '
                        'configuración de afiliado. El producto se extrajo de todas formas.'
                    )
            return clean_url, warning
        # Awin URL but no 'ued' param — can't extract product URL
        return url, 'Se detectó un enlace Awin pero no se pudo extraer la URL del producto.'

    # --- Sodimac suffix ---
    if 'sodimac.cl' in (parsed.netloc or ''):
        # Find where the affiliate suffix starts.  Use configured trigger if
        # available, otherwise fall back to the standard '?eid=' marker.
        trigger = None
        if profile is not None:
            trigger = (profile.sodimac_suffix_trigger or '').strip() or None

        # Determine the index at which the affiliate suffix begins.
        cut_index = None
        if trigger and trigger in url:
            cut_index = url.index(trigger)
        elif '?eid=' in url:
            cut_index = url.index('?eid=')

        if cut_index is not None:
            clean_url = url[:cut_index]
            warning = None
            if profile is not None:
                saved_trigger = (profile.sodimac_suffix_trigger or '').strip()
                if not saved_trigger:
                    warning = (
                        'Se detectó un enlace de afiliado Sodimac, pero no tienes '
                        'configurado un sufijo Sodimac en tu perfil de afiliado.'
                    )
                elif saved_trigger not in url:
                    warning = (
                        'El sufijo de afiliado Sodimac no coincide con el guardado en '
                        'tu configuración. El producto se extrajo de todas formas.'
                    )
            return clean_url, warning

    return url, None


def _detect_store_from_url_or_name(url, store_name=''):
    domain = (urlparse(url).netloc or '').lower()
    name = (store_name or '').lower()

    if 'adidas' in domain or 'adidas' in name or 'awin1.com' in domain:
        return 'adidas'
    if 'sodimac' in domain or 'homecenter' in domain or 'sodimac' in name:
        return 'sodimac'
    if 'mercadolibre' in domain or 'mercadoli' in domain or 'meli.la' in domain or 'mercadolibre' in name:
        return 'meli'
    if 'falabella' in domain or 'falabella' in name:
        return 'falabella'
    return 'other'


def _append_sodimac_suffix(product_url, suffix):
    if not suffix:
        return product_url

    base = (product_url or '').strip()
    extra = suffix.strip()
    if not base:
        return base

    if extra.startswith('?'):
        if '?' not in base:
            return f'{base}{extra}'
        if base.endswith('?') or base.endswith('&'):
            return f'{base}{extra[1:]}'
        return f'{base}&{extra[1:]}'

    if not extra.startswith('&'):
        extra = '&' + extra
    if '?' not in base:
        return f'{base}?{extra.lstrip("&")}'
    return f'{base}{extra}'


def resolve_affiliate_link(original_url, clean_url=None, store_name='', profile=None):
    """
    Build the affiliate URL to show in the generated-banner list.

    Returns a dict:
        {
            'affiliate_link': str,
            'affiliate_warning': str|None,
            'store_key': str,
        }
    """
    source = (original_url or '').strip()
    product_url = (clean_url or original_url or '').strip()
    store_key = _detect_store_from_url_or_name(source or product_url, store_name=store_name)

    if not source and not product_url:
        return {
            'affiliate_link': '',
            'affiliate_warning': 'No se recibió una URL para construir el link de afiliado.',
            'store_key': store_key,
        }

    # MercadoLibre / Falabella: return as-is.
    if store_key in ('meli', 'falabella', 'other'):
        return {
            'affiliate_link': source or product_url,
            'affiliate_warning': None,
            'store_key': store_key,
        }

    # Adidas
    if store_key == 'adidas':
        if 'awin1.com' in (urlparse(source).netloc or '').lower():
            return {
                'affiliate_link': source,
                'affiliate_warning': None,
                'store_key': store_key,
            }

        prefix = ((profile.awin_prefix if profile else '') or '').strip()
        if not prefix:
            return {
                'affiliate_link': '',
                'affiliate_warning': 'Configura primero tu prefijo Awin en Configuración de Afiliado para generar el link de Adidas.',
                'store_key': store_key,
            }

        target = product_url
        if re.search(r'ued=https%3A%2F%2F$', prefix, flags=re.I):
            target = re.sub(r'^https?://', '', target, flags=re.I)
            target = quote(target, safe='')

        return {
            'affiliate_link': f'{prefix}{target}',
            'affiliate_warning': None,
            'store_key': store_key,
        }

    # Sodimac
    if store_key == 'sodimac':
        lower_source = source.lower()
        if '?eid=' in lower_source or '&eid=' in lower_source:
            return {
                'affiliate_link': source,
                'affiliate_warning': None,
                'store_key': store_key,
            }

        suffix = ((profile.sodimac_suffix_trigger if profile else '') or '').strip()
        if not suffix or suffix.lower() in ('?eid=', 'eid=', '&eid='):
            return {
                'affiliate_link': '',
                'affiliate_warning': 'Configura primero tu sufijo completo de Sodimac en Configuración de Afiliado para generar el link.',
                'store_key': store_key,
            }

        return {
            'affiliate_link': _append_sodimac_suffix(product_url, suffix),
            'affiliate_warning': None,
            'store_key': store_key,
        }

    return {
        'affiliate_link': source or product_url,
        'affiliate_warning': None,
        'store_key': store_key,
    }

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
