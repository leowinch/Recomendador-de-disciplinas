from django.contrib import admin
from django.urls import path, include
from django.apps import apps
from rest_framework import serializers, viewsets, routers
from django.views.generic import TemplateView

from core.views import RecomendacaoView

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

urlpatterns = [
    path('', TemplateView.as_view(template_name='prototipo.html'), name='home'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/recomendar/', RecomendacaoView.as_view(), name='recomendar'),
]