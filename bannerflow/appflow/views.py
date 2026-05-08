import json
import base64
import uuid
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import BannerTemplate, UserProfile, GeneratedBanner
from .serializers import BannerTemplateSerializer
from .scrapers import scrape_url
from .utils import clean_affiliate_url


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


@login_required
def banner_history(request):
    store_query = request.GET.get('store', '').strip()
    date_str = request.GET.get('date', '').strip()

    banners = GeneratedBanner.objects.filter(owner=request.user).select_related('template')

    if store_query:
        banners = banners.filter(store_name__icontains=store_query)

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    selected_date = None
    if date_str:
        try:
            from datetime import date as date_type
            selected_date = date_type.fromisoformat(date_str)
            banners = banners.filter(created_at__date=selected_date)
        except ValueError:
            selected_date = None

    grouped = []
    groups_map = {}

    for banner in banners:
        local_dt = timezone.localtime(banner.created_at)
        d = local_dt.date()
        if d == today:
            label = 'Hoy'
        elif d == yesterday:
            label = 'Ayer'
        else:
            label = d.strftime('%d/%m/%Y')

        key = d.isoformat()
        if key not in groups_map:
            groups_map[key] = {
                'key': key,
                'label': label,
                'items': [],
            }
            grouped.append(groups_map[key])

        groups_map[key]['items'].append(banner)

    return render(request, 'banners/history.html', {
        'grouped_banners': grouped,
        'store_query': store_query,
        'selected_date': date_str,
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
    profile = getattr(request.user, 'userprofile', None)
    clean_url, affiliate_warning = clean_affiliate_url(url, profile)
    try:
        data = scrape_url(clean_url)
        if affiliate_warning:
            data['affiliate_warning'] = affiliate_warning
        return Response(data)
    except Exception as e:
        return Response(
            {'error': f'Error al extraer datos: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
def save_generated_banner(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Autenticación requerida'}, status=status.HTTP_401_UNAUTHORIZED)

    template_id = request.data.get('template_id')
    image_data = request.data.get('image_data', '')
    ratio = (request.data.get('ratio') or '1:1').strip()
    title = (request.data.get('title') or '').strip()
    store_name = (request.data.get('store_name') or '').strip()
    offer_price = request.data.get('offer_price')
    source_url = (request.data.get('source_url') or '').strip()

    if not image_data or not isinstance(image_data, str) or ',' not in image_data:
        return Response({'error': 'La imagen generada es inválida.'}, status=status.HTTP_400_BAD_REQUEST)

    template = None
    if template_id:
        template = get_object_or_404(_user_templates(request.user), pk=template_id)

    try:
        header, encoded = image_data.split(',', 1)
        if 'image/png' not in header and 'image/jpeg' not in header:
            return Response({'error': 'Formato de imagen no soportado.'}, status=status.HTTP_400_BAD_REQUEST)
        raw = base64.b64decode(encoded)
    except Exception:
        return Response({'error': 'No se pudo procesar la imagen generada.'}, status=status.HTTP_400_BAD_REQUEST)

    fname = f'generated_{request.user.id}_{uuid.uuid4().hex[:10]}.png'
    offer_price_value = '' if offer_price is None else str(offer_price)

    banner = GeneratedBanner(
        owner=request.user,
        template=template,
        title=title,
        store_name=store_name,
        offer_price=offer_price_value,
        source_url=source_url,
        ratio=ratio,
    )
    banner.image.save(fname, ContentFile(raw), save=True)

    return Response({
        'id': banner.id,
        'created_at': timezone.localtime(banner.created_at).isoformat(),
        'image_url': banner.image.url,
    }, status=status.HTTP_201_CREATED)


# --- Affiliate settings ---

@login_required
def affiliate_settings(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.awin_prefix = request.POST.get('awin_prefix', '').strip()
        profile.sodimac_suffix_trigger = request.POST.get('sodimac_suffix_trigger', '').strip()
        profile.save()
        messages.success(request, 'Configuración de afiliado guardada correctamente.')
        return redirect('banners:affiliate-settings')
    return render(request, 'banners/affiliate.html', {'profile': profile})


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
