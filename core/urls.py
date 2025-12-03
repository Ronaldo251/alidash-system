from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='dashboard'),
    path('conectividade/', views.conectividade, name='conectividade'),
    path('callcenter/', views.callcenter, name='callcenter'),
    path('callcenter/agente/<int:id>/', views.detalhe_agente, name='detalhe_agente'),
    path('seguranca/', views.seguranca, name='seguranca'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/novo/', views.criar_usuario, name='criar_usuario'),
    path('meu-painel/', views.painel_agente, name='painel_agente'),
    path('chamados/', views.lista_chamados, name='lista_chamados'),
    path('chamados/novo/', views.novo_chamado, name='novo_chamado'),
    
    # Nova Rota de Exportação
    path('exportar/agentes/', views.exportar_csv_agentes, name='exportar_agentes'),
]