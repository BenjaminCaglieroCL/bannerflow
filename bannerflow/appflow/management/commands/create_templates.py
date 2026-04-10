"""Management command to create predefined banner templates."""
import json
from django.core.management.base import BaseCommand
from appflow.models import BannerTemplate


PREDEFINED_TEMPLATES = [
    {
        "name": "🔥 Oferta Bold",
        "canvas_data": {
            "version": "5.3.1",
            "background": "#1a1a2e",
            "objects": [
                {
                    "type": "rect",
                    "left": 0, "top": 0, "width": 540, "height": 540,
                    "fill": "#1a1a2e", "selectable": False
                },
                {
                    "type": "rect",
                    "left": 20, "top": 20, "width": 500, "height": 90,
                    "fill": "#e74c3c", "rx": 12, "ry": 12, "opacity": 0.95
                },
                {
                    "type": "i-text", "text": "¡SUPER OFERTA!",
                    "left": 270, "top": 45, "originX": "center",
                    "fontSize": 36, "fontWeight": "900", "fontFamily": "Poppins",
                    "fill": "#ffffff", "dataType": "badge"
                },
                {
                    "type": "rect",
                    "left": 120, "top": 130, "width": 300, "height": 220,
                    "fill": "rgba(255,255,255,0.08)", "stroke": "#7c3aed",
                    "strokeWidth": 2, "strokeDashArray": [8, 4], "rx": 12, "ry": 12,
                    "dataType": "product_image"
                },
                {
                    "type": "i-text", "text": "Nombre del Producto",
                    "left": 270, "top": 375, "originX": "center",
                    "fontSize": 22, "fontWeight": "700", "fontFamily": "Poppins",
                    "fill": "#ffffff", "dataType": "title", "textAlign": "center"
                },
                {
                    "type": "i-text", "text": "$99.990",
                    "left": 270, "top": 420, "originX": "center",
                    "fontSize": 20, "fontWeight": "400", "fontFamily": "Inter",
                    "fill": "#9ca3af", "linethrough": True, "dataType": "original_price"
                },
                {
                    "type": "i-text", "text": "$49.990",
                    "left": 270, "top": 455, "originX": "center",
                    "fontSize": 44, "fontWeight": "900", "fontFamily": "Poppins",
                    "fill": "#f472b6", "dataType": "offer_price"
                },
                {
                    "type": "i-text", "text": "Tienda",
                    "left": 270, "top": 510, "originX": "center",
                    "fontSize": 14, "fontWeight": "500", "fontFamily": "Inter",
                    "fill": "#6b7280", "dataType": "store_name"
                }
            ]
        }
    },
    {
        "name": "💎 Minimalista Elegante",
        "canvas_data": {
            "version": "5.3.1",
            "background": "#fafafa",
            "objects": [
                {
                    "type": "rect",
                    "left": 20, "top": 20, "width": 500, "height": 500,
                    "fill": "transparent", "stroke": "#e5e7eb", "strokeWidth": 1
                },
                {
                    "type": "rect",
                    "left": 140, "top": 50, "width": 260, "height": 260,
                    "fill": "#f3f4f6", "stroke": "#d1d5db",
                    "strokeWidth": 1, "strokeDashArray": [4, 4], "rx": 8, "ry": 8,
                    "dataType": "product_image"
                },
                {
                    "type": "i-text", "text": "Nombre del Producto",
                    "left": 270, "top": 335, "originX": "center",
                    "fontSize": 20, "fontWeight": "600", "fontFamily": "Inter",
                    "fill": "#1f2937", "dataType": "title", "textAlign": "center"
                },
                {
                    "type": "i-text", "text": "$99.990",
                    "left": 270, "top": 390, "originX": "center",
                    "fontSize": 16, "fontWeight": "400", "fontFamily": "Inter",
                    "fill": "#9ca3af", "linethrough": True, "dataType": "original_price"
                },
                {
                    "type": "i-text", "text": "$49.990",
                    "left": 270, "top": 420, "originX": "center",
                    "fontSize": 38, "fontWeight": "800", "fontFamily": "Poppins",
                    "fill": "#111827", "dataType": "offer_price"
                },
                {
                    "type": "i-text", "text": "Tienda",
                    "left": 270, "top": 485, "originX": "center",
                    "fontSize": 12, "fontWeight": "500", "fontFamily": "Inter",
                    "fill": "#9ca3af", "dataType": "store_name"
                }
            ]
        }
    },
    {
        "name": "🌈 Gradiente Vibrante",
        "canvas_data": {
            "version": "5.3.1",
            "background": "#7c3aed",
            "objects": [
                {
                    "type": "rect",
                    "left": 120, "top": 40, "width": 300, "height": 250,
                    "fill": "rgba(255,255,255,0.15)", "rx": 20, "ry": 20,
                    "dataType": "product_image"
                },
                {
                    "type": "circle",
                    "left": -60, "top": -60, "radius": 180,
                    "fill": "rgba(255,255,255,0.08)"
                },
                {
                    "type": "circle",
                    "left": 380, "top": 380, "radius": 200,
                    "fill": "rgba(255,255,255,0.06)"
                },
                {
                    "type": "i-text", "text": "Nombre del Producto",
                    "left": 270, "top": 320, "originX": "center",
                    "fontSize": 24, "fontWeight": "800", "fontFamily": "Poppins",
                    "fill": "#ffffff", "dataType": "title", "textAlign": "center"
                },
                {
                    "type": "rect",
                    "left": 130, "top": 370, "width": 280, "height": 80,
                    "fill": "rgba(0,0,0,0.25)", "rx": 16, "ry": 16
                },
                {
                    "type": "i-text", "text": "$99.990",
                    "left": 200, "top": 390, "originX": "center",
                    "fontSize": 18, "fontWeight": "400", "fontFamily": "Inter",
                    "fill": "rgba(255,255,255,0.6)", "linethrough": True, "dataType": "original_price"
                },
                {
                    "type": "i-text", "text": "$49.990",
                    "left": 360, "top": 382, "originX": "center",
                    "fontSize": 36, "fontWeight": "900", "fontFamily": "Poppins",
                    "fill": "#ffffff", "dataType": "offer_price"
                },
                {
                    "type": "i-text", "text": "OFERTA ESPECIAL",
                    "left": 270, "top": 470, "originX": "center",
                    "fontSize": 14, "fontWeight": "700", "fontFamily": "Inter",
                    "fill": "rgba(255,255,255,0.7)", "dataType": "badge",
                    "charSpacing": 400
                },
                {
                    "type": "i-text", "text": "Tienda",
                    "left": 270, "top": 500, "originX": "center",
                    "fontSize": 16, "fontWeight": "600", "fontFamily": "Poppins",
                    "fill": "#ffffff", "dataType": "store_name"
                }
            ]
        }
    },
    {
        "name": "⚡ Neon Cyber",
        "canvas_data": {
            "version": "5.3.1",
            "background": "#0a0a0f",
            "objects": [
                {
                    "type": "rect",
                    "left": 15, "top": 15, "width": 510, "height": 510,
                    "fill": "transparent", "stroke": "#06b6d4", "strokeWidth": 2
                },
                {
                    "type": "rect",
                    "left": 120, "top": 50, "width": 300, "height": 230,
                    "fill": "rgba(6,182,212,0.05)", "stroke": "#06b6d4",
                    "strokeWidth": 1, "rx": 4, "ry": 4,
                    "dataType": "product_image"
                },
                {
                    "type": "i-text", "text": "Nombre del Producto",
                    "left": 270, "top": 310, "originX": "center",
                    "fontSize": 22, "fontWeight": "700", "fontFamily": "Inter",
                    "fill": "#e0f2fe", "dataType": "title", "textAlign": "center"
                },
                {
                    "type": "i-text", "text": "$99.990",
                    "left": 270, "top": 360, "originX": "center",
                    "fontSize": 18, "fontWeight": "400", "fontFamily": "Inter",
                    "fill": "#475569", "linethrough": True, "dataType": "original_price"
                },
                {
                    "type": "i-text", "text": "$49.990",
                    "left": 270, "top": 395, "originX": "center",
                    "fontSize": 48, "fontWeight": "900", "fontFamily": "Poppins",
                    "fill": "#06b6d4", "dataType": "offer_price"
                },
                {
                    "type": "i-text", "text": "⚡ CYBER DEAL ⚡",
                    "left": 270, "top": 465, "originX": "center",
                    "fontSize": 16, "fontWeight": "800", "fontFamily": "Inter",
                    "fill": "#f472b6", "dataType": "badge", "charSpacing": 200
                },
                {
                    "type": "i-text", "text": "Tienda",
                    "left": 270, "top": 500, "originX": "center",
                    "fontSize": 13, "fontWeight": "500", "fontFamily": "Inter",
                    "fill": "#64748b", "dataType": "store_name"
                }
            ]
        }
    },
    {
        "name": "🍊 Naranja Fresh",
        "canvas_data": {
            "version": "5.3.1",
            "background": "#ff6b35",
            "objects": [
                {
                    "type": "rect",
                    "left": 30, "top": 30, "width": 480, "height": 480,
                    "fill": "#ffffff", "rx": 24, "ry": 24
                },
                {
                    "type": "rect",
                    "left": 50, "top": 320, "width": 440, "height": 6,
                    "fill": "#ff6b35", "rx": 3, "ry": 3
                },
                {
                    "type": "rect",
                    "left": 145, "top": 55, "width": 250, "height": 240,
                    "fill": "#fff7ed", "rx": 16, "ry": 16,
                    "dataType": "product_image"
                },
                {
                    "type": "i-text", "text": "Nombre del Producto",
                    "left": 270, "top": 345, "originX": "center",
                    "fontSize": 20, "fontWeight": "700", "fontFamily": "Poppins",
                    "fill": "#1f2937", "dataType": "title", "textAlign": "center"
                },
                {
                    "type": "i-text", "text": "$99.990",
                    "left": 270, "top": 385, "originX": "center",
                    "fontSize": 16, "fontWeight": "400", "fontFamily": "Inter",
                    "fill": "#9ca3af", "linethrough": True, "dataType": "original_price"
                },
                {
                    "type": "i-text", "text": "$49.990",
                    "left": 270, "top": 415, "originX": "center",
                    "fontSize": 40, "fontWeight": "900", "fontFamily": "Poppins",
                    "fill": "#ff6b35", "dataType": "offer_price"
                },
                {
                    "type": "i-text", "text": "Tienda",
                    "left": 270, "top": 475, "originX": "center",
                    "fontSize": 14, "fontWeight": "600", "fontFamily": "Inter",
                    "fill": "#6b7280", "dataType": "store_name"
                }
            ]
        }
    },
    {
        "name": "🖤 Dark Premium",
        "canvas_data": {
            "version": "5.3.1",
            "background": "#111111",
            "objects": [
                {
                    "type": "rect",
                    "left": 0, "top": 0, "width": 540, "height": 8,
                    "fill": "#d4af37"
                },
                {
                    "type": "rect",
                    "left": 130, "top": 40, "width": 280, "height": 260,
                    "fill": "rgba(212,175,55,0.05)", "stroke": "#d4af37",
                    "strokeWidth": 1, "rx": 8, "ry": 8,
                    "dataType": "product_image"
                },
                {
                    "type": "i-text", "text": "Nombre del Producto",
                    "left": 270, "top": 325, "originX": "center",
                    "fontSize": 22, "fontWeight": "600", "fontFamily": "Inter",
                    "fill": "#f5f5f5", "dataType": "title", "textAlign": "center"
                },
                {
                    "type": "i-text", "text": "$99.990",
                    "left": 270, "top": 370, "originX": "center",
                    "fontSize": 18, "fontWeight": "400", "fontFamily": "Inter",
                    "fill": "#666666", "linethrough": True, "dataType": "original_price"
                },
                {
                    "type": "i-text", "text": "$49.990",
                    "left": 270, "top": 405, "originX": "center",
                    "fontSize": 44, "fontWeight": "900", "fontFamily": "Poppins",
                    "fill": "#d4af37", "dataType": "offer_price"
                },
                {
                    "type": "i-text", "text": "PREMIUM DEAL",
                    "left": 270, "top": 465, "originX": "center",
                    "fontSize": 12, "fontWeight": "700", "fontFamily": "Inter",
                    "fill": "#d4af37", "dataType": "badge", "charSpacing": 500
                },
                {
                    "type": "i-text", "text": "Tienda",
                    "left": 270, "top": 500, "originX": "center",
                    "fontSize": 14, "fontWeight": "500", "fontFamily": "Inter",
                    "fill": "#888888", "dataType": "store_name"
                }
            ]
        }
    },
]


class Command(BaseCommand):
    help = 'Create predefined banner templates'

    def handle(self, *args, **options):
        created = 0
        for tpl_data in PREDEFINED_TEMPLATES:
            obj, was_created = BannerTemplate.objects.update_or_create(
                name=tpl_data['name'],
                defaults={
                    'canvas_data': tpl_data['canvas_data'],
                    'is_predefined': True,
                }
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {tpl_data["name"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Updated: {tpl_data["name"]}'))

        self.stdout.write(self.style.SUCCESS(f'\nDone! {created} new templates created.'))
