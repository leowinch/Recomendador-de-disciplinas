from django.contrib import admin
from django.urls import path, include
from django.apps import apps
from rest_framework import serializers, viewsets, routers
import os

from django.views.generic import RedirectView, TemplateView

from core.views import RecomendacaoView, HistoricoView, ObrigatoriasPendentesView, BuscaDisciplinaView, DetalheDisciplinaView

router = routers.DefaultRouter()

app_models = apps.get_app_config('core').get_models()

for model in app_models:
    serializer_cls = type(
        f'{model.__name__}Serializer',
        (serializers.ModelSerializer,),
        {'Meta': type('Meta', (), {'model': model, 'fields': '__all__'})}
    )
    
    viewset_cls = type(
        f'{model.__name__}ViewSet',
        (viewsets.ReadOnlyModelViewSet,),
        {'queryset': model.objects.all(), 'serializer_class': serializer_cls}
    )
    
    # 3. Registra a rota automática baseada no nome da tabela/modelo
    router.register(model._meta.model_name, viewset_cls, basename=model._meta.model_name)

# Em produção a raiz redireciona para o frontend (Static Site no Render).
# Sem FRONTEND_URL definida (ex.: desenvolvimento local), continua servindo o protótipo antigo.
FRONTEND_URL = os.getenv('FRONTEND_URL', '').strip()
home_view = (RedirectView.as_view(url=FRONTEND_URL, permanent=False) if FRONTEND_URL
             else TemplateView.as_view(template_name='prototipo.html'))

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/recomendar/', RecomendacaoView.as_view(), name='recomendar'),
    path('api/importar-historico/', HistoricoView.as_view(), name='importar-historico'),
    path('api/obrigatorias-pendentes/', ObrigatoriasPendentesView.as_view(), name='obrigatorias-pendentes'),
    path('api/buscar-disciplinas/', BuscaDisciplinaView.as_view(), name='buscar-disciplinas'),
    path('api/detalhe-disciplina/<str:codigo>/', DetalheDisciplinaView.as_view(), name='detalhe-disciplina'),
]