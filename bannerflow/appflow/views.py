import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import BannerTemplate
from .serializers import BannerTemplateSerializer
from .scrapers import scrape_url


def _templates_json(queryset):
    """Build a {id: canvas_data_json} dict for template previews."""
    return json.dumps({t.id: t.canvas_data for t in queryset})


def _user_templates(user):
    """Return templates visible to a user (all for staff, own for regular)."""
    if user.is_staff:
        return BannerTemplate.objects.all()
    return BannerTemplate.objects.filter(owner=user)


# ===== Public views =====

def landing(request):
    if request.user.is_authenticated:
        return redirect('banners:home')
    return render(request, 'landing.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('banners:home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or ''
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('banners:home')
        else:
            return render(request, 'auth/login.html', {
                'next': request.GET.get('next', ''),
                'login_error': 'Usuario o contraseña incorrectos.',
            })
    return render(request, 'auth/login.html', {
        'next': request.GET.get('next', ''),
    })


def logout_view(request):
    logout(request)
    return redirect('banners:landing')


# ===== Protected views =====

@login_required
def home(request):
    templates = _user_templates(request.user)[:8]
    return render(request, 'banners/home.html', {
        'templates': templates,
        'templates_json': _templates_json(templates),
    })


@login_required
def editor(request, template_id=None):
    template = None
    template_json = '{}'
    if template_id:
        template = get_object_or_404(_user_templates(request.user), pk=template_id)
        template_json = json.dumps(template.canvas_data)
    return render(request, 'banners/editor.html', {
        'template': template,
        'template_json': template_json,
    })


@login_required
def library(request):
    templates = _user_templates(request.user)
    predefined = templates.filter(is_predefined=True)
    custom = templates.filter(is_predefined=False)
    all_templates = list(predefined) + list(custom)
    return render(request, 'banners/library.html', {
        'predefined': predefined,
        'custom': custom,
        'all_templates_json': _templates_json(all_templates),
    })


@login_required
def generate(request, template_id):
    template = get_object_or_404(_user_templates(request.user), pk=template_id)
    return render(request, 'banners/generate.html', {
        'template': template,
        'template_json': json.dumps(template.canvas_data),
    })


# --- API Views ---

class TemplateListCreate(generics.ListCreateAPIView):
    serializer_class = BannerTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _user_templates(self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TemplateDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BannerTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _user_templates(self.request.user)


@api_view(['POST'])
def scrape_product(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Autenticación requerida'}, status=status.HTTP_401_UNAUTHORIZED)
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


# --- Admin: user management ---

@login_required
def user_management(request):
    if not request.user.is_staff:
        return HttpResponseForbidden('Acceso restringido a administradores.')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            is_staff  = request.POST.get('is_staff') == '1'

            if not username or not password:
                messages.error(request, 'Usuario y contraseña son obligatorios.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, f'El usuario "{username}" ya existe.')
            else:
                if is_staff:
                    User.objects.create_superuser(username=username, email='', password=password)
                else:
                    User.objects.create_user(username=username, email='', password=password)
                messages.success(request, f'Usuario "{username}" creado correctamente.')
            return redirect('banners:user-management')

        elif action == 'reset_password':
            user_id  = request.POST.get('user_id')
            new_pass = request.POST.get('new_password', '').strip()
            target   = get_object_or_404(User, pk=user_id)
            if not new_pass:
                messages.error(request, 'La nueva contraseña no puede estar vacía.')
            else:
                target.set_password(new_pass)
                target.save()
                messages.success(request, f'Contraseña de "{target.username}" actualizada.')
            return redirect('banners:user-management')

    users = User.objects.all().order_by('id')
    return render(request, 'admin/user_management.html', {'users': users})


@login_required
def user_delete(request, user_id):
    if not request.user.is_staff:
        return HttpResponseForbidden('Acceso restringido a administradores.')
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        messages.error(request, 'No puedes eliminarte a ti mismo.')
    else:
        username = target.username
        target.delete()
        messages.success(request, f'Usuario "{username}" eliminado.')
    return redirect('banners:user-management')


def contact(request):
    return render(request, 'contact.html')
