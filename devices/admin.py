from django.contrib import admin
from .models import Cliente, Concentrador, EquipamentoCliente

@admin.register(Concentrador)
class ConcentradorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ip_address', 'api_port')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pppoe_user', 'is_blocked')
    search_fields = ('nome', 'cpf', 'pppoe_user')
    list_filter = ('is_blocked',)

@admin.register(EquipamentoCliente)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tipo', 'mac_address', 'online', 'ip_atual')
    list_filter = ('tipo', 'online')