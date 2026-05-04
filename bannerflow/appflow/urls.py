from django.urls import path
from . import views

app_name = 'banners'

urlpatterns = [
    # Public
    path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Protected pages
    path('home/', views.home, name='home'),
    path('editor/', views.editor, name='editor'),
    path('editor/<int:template_id>/', views.editor, name='editor-edit'),
    path('library/', views.library, name='library'),
    path('generate/<int:template_id>/', views.generate, name='generate'),

    # Admin — user management
    path('admin-panel/users/', views.user_management, name='user-management'),
    path('admin-panel/users/<int:user_id>/delete/', views.user_delete, name='user-delete'),

    # Contact (public)
    path('contact/', views.contact, name='contact'),

    # API
    path('api/templates/', views.TemplateListCreate.as_view(), name='api-templates'),
    path('api/templates/<int:pk>/', views.TemplateDetail.as_view(), name='api-template-detail'),
    path('api/scrape/', views.scrape_product, name='api-scrape'),
]
