from django.urls import path
from . import views, api

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
    path('chamados/<int:id>/', views.detalhe_chamado, name='detalhe_chamado'),
    
    
    # Nova Rota de Exportação
    path('exportar/agentes/', views.exportar_csv_agentes, name='exportar_agentes'),

    # API ENDPOINTS (Públicos)
    path('api/abrir-chamado/', api.abrir_chamado_externo, name='api_abrir_chamado'),
    path('teste-widget/', views.teste_widget),
    path('api/chat/<int:chamado_id>/mensagens/', api.verificar_mensagens),
    path('api/chat/<int:chamado_id>/enviar/', api.enviar_mensagem_externa),
    path('api/chat/<int:chamado_id>/encerrar/', api.encerrar_chamado_externo),
    path('api/notificacoes/checar/', api.checar_notificacoes),
    path('api/notificacoes/limpar/', api.marcar_como_lida),
    path('api/chamados/listar/', api.listar_chamados_dinamico, name='api_listar_chamados'),
    path('api/chamados/<int:chamado_id>/comentarios/', api.listar_comentarios_chat, name='api_chat_comentarios'),
    path('chamados/historico/', views.historico_chamados, name='historico_chamados'),
    path('suporte-online/', views.widget_atendimento, name='widget_cliente'),
]