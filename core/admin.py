from django.contrib import admin
from .models import Agente, AccessPoint, SecurityLog, HistoricoOperacao

@admin.register(Agente)
class AgenteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ramal', 'status', 'atendimentos')
    list_filter = ('status',)
    search_fields = ('nome', 'ramal')

@admin.register(AccessPoint)
class AccessPointAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ip_address', 'status', 'usuarios_conectados', 'cpu_usage')
    list_filter = ('status',)

@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'tipo', 'origem', 'severidade', 'status')
    list_filter = ('severidade', 'status')
    ordering = ('-data_hora',) # Mais recentes primeiro

@admin.register(HistoricoOperacao)
class HistoricoAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'chamadas_ativas', 'trafego_rede_mbps')

