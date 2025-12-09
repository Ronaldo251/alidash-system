from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    # A lista principal
    path('assinantes/', views.lista_clientes_isp, name='lista_clientes'),
    # Ações
    path('bloquear/<int:cliente_id>/', views.action_bloquear_cliente, name='bloquear_cliente'),
    path('cliente/<int:cliente_id>/detalhes/', views.detalhe_cliente, name='detalhe_cliente'),
    path('novo/', views.novo_cliente, name='novo_cliente'),    
]