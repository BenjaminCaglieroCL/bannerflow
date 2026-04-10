from django.urls import path
from . import views

app_name = 'banners'

urlpatterns = [
    # Pages
    path('', views.home, name='home'),
    path('editor/', views.editor, name='editor'),
    path('editor/<int:template_id>/', views.editor, name='editor-edit'),
    path('library/', views.library, name='library'),
    path('generate/<int:template_id>/', views.generate, name='generate'),

    # API
    path('api/templates/', views.TemplateListCreate.as_view(), name='api-templates'),
    path('api/templates/<int:pk>/', views.TemplateDetail.as_view(), name='api-template-detail'),
    path('api/scrape/', views.scrape_product, name='api-scrape'),
]
