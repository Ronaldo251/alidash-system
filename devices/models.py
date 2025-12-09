# devices/models.py
from django.db import models
from django.contrib.auth.models import User

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, unique=True)
    endereco = models.CharField(max_length=255)
    pppoe_user = models.CharField(max_length=50, unique=True) # Usuário de autenticação na rede
    pppoe_password = models.CharField(max_length=50)
    is_blocked = models.BooleanField(default=False) # Status financeiro
    
    def __str__(self):
        return f"{self.nome} ({self.pppoe_user})"

class Concentrador(models.Model):
    """Representa o Roteador Principal do Provedor (Ex: Mikrotik da Torre)"""
    nome = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    api_user = models.CharField(max_length=50)
    api_password = models.CharField(max_length=50)
    api_port = models.IntegerField(default=8728) # Porta padrão API Mikrotik

    def __str__(self):
        return self.nome

class EquipamentoCliente(models.Model):
    """O Roteador dentro da casa do cliente"""
    TIPO_CHOICES = [
        ('ONT', 'Fibra Óptica (ONU)'),
        ('ROUTER', 'Roteador Wi-Fi'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='equipamentos')
    concentrador = models.ForeignKey(Concentrador, on_delete=models.SET_NULL, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    mac_address = models.CharField(max_length=17, unique=True) # Ex: AA:BB:CC:DD:EE:FF
    modelo = models.CharField(max_length=50, blank=True)
    ip_atual = models.GenericIPAddressField(null=True, blank=True) # IP pego via integração
    online = models.BooleanField(default=False)
    ultimo_sinal = models.CharField(max_length=20, null=True, blank=True) # Ex: -20dBm

    def __str__(self):
        return f"{self.tipo} - {self.cliente.nome}"