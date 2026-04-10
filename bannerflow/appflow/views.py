import json

from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import BannerTemplate
from .serializers import BannerTemplateSerializer
from .scrapers import scrape_url


def _templates_json(queryset):
    """Build a {id: canvas_data_json} dict for template previews."""
    return json.dumps({t.id: t.canvas_data for t in queryset})


def home(request):
    templates = BannerTemplate.objects.all()[:8]
    return render(request, 'banners/home.html', {
        'templates': templates,
        'templates_json': _templates_json(templates),
    })


def editor(request, template_id=None):
    template = None
    template_json = '{}'
    if template_id:
        template = get_object_or_404(BannerTemplate, pk=template_id)
        template_json = json.dumps(template.canvas_data)
    return render(request, 'banners/editor.html', {
        'template': template,
        'template_json': template_json,
    })


def library(request):
    templates = BannerTemplate.objects.all()
    predefined = templates.filter(is_predefined=True)
    custom = templates.filter(is_predefined=False)
    all_templates = list(predefined) + list(custom)
    return render(request, 'banners/library.html', {
        'predefined': predefined,
        'custom': custom,
        'all_templates_json': _templates_json(all_templates),
    })


def generate(request, template_id):
    template = get_object_or_404(BannerTemplate, pk=template_id)
    return render(request, 'banners/generate.html', {
        'template': template,
        'template_json': json.dumps(template.canvas_data),
    })


# --- API Views ---

class TemplateListCreate(generics.ListCreateAPIView):
    queryset = BannerTemplate.objects.all()
    serializer_class = BannerTemplateSerializer


class TemplateDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = BannerTemplate.objects.all()
    serializer_class = BannerTemplateSerializer


@api_view(['POST'])
def scrape_product(request):
    url = request.data.get('url', '').strip()
    if not url:
        return Response(
            {'error': 'Se requiere una URL'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        data = scrape_url(url)
        return Response(data)
    except Exception as e:
        return Response(
            {'error': f'Error al extraer datos: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
