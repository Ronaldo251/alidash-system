from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
DEPARTAMENTO_CHOICES = [
    ('comercial', 'Comercial'),
    ('administrativo', 'Administrativo'),
    ('tecnico', 'Técnico'),
]
class Agente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    STATUS_CHOICES = [
        ('online', 'Disponível'),
        ('pausa', 'Pausa'),
        ('ocupado', 'Em Chamada'),
        ('offline', 'Offline'),
    ]

    nome = models.CharField(max_length=100)
    ramal = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    tempo_logado = models.DurationField(null=True, blank=True, help_text="Ex: 04:00:00")
    atendimentos = models.IntegerField(default=0)
    departamento = models.CharField(max_length=20, choices=DEPARTAMENTO_CHOICES, default='tecnico')
    def __str__(self):
        return f"{self.nome} ({self.ramal})"

    # Lógica Visual: Define a cor do CSS baseada no status direto no banco
    @property
    def cor_badge_css(self):
        cores = {
            'online': 'bg-green-900/40 text-neonGreen border-green-800',
            'pausa': 'bg-red-900/40 text-alertRed border-red-800',
            'ocupado': 'bg-yellow-900/40 text-warnYellow border-yellow-800',
            'offline': 'bg-gray-800 text-gray-500 border-gray-700',
        }
        return cores.get(self.status, 'bg-gray-800 text-white')
    
class AccessPoint(models.Model):
    STATUS_AP = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('alerta', 'Alerta/Lento'),
    ]

    nome = models.CharField(max_length=50, help_text="Ex: U6-Pro")
    localizacao = models.CharField(max_length=50, default="Setor A", help_text="Ex: Setor A-1")
    ip_address = models.GenericIPAddressField(protocol='IPv4')
    status = models.CharField(max_length=20, choices=STATUS_AP, default='online')
    
    # Métricas de Performance
    usuarios_conectados = models.IntegerField(default=0)
    cpu_usage = models.IntegerField(default=10, help_text="Uso em %")
    memory_usage = models.IntegerField(default=30, help_text="Uso em %") # Novo campo!
    
    def __str__(self):
        return f"{self.nome} - {self.localizacao}"

    @property
    def cor_status(self):
        if self.status == 'online': return 'text-neonGreen border-neonGreen bg-green-900/20'
        if self.status == 'offline': return 'text-alertRed border-alertRed bg-red-900/20'
        return 'text-warnYellow border-warnYellow bg-yellow-900/20'
    
    @property
    def cor_barra_cpu(self):
        if self.cpu_usage > 80: return 'bg-alertRed'
        if self.cpu_usage > 50: return 'bg-warnYellow'
        return 'bg-neonBlue'
    
class SecurityLog(models.Model):
    SEVERIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    tipo = models.CharField(max_length=50, help_text="Ex: Brute Force, Port Scan")
    origem = models.CharField(max_length=50, help_text="IP ou Usuário (Ex: 192.168.1.50)")
    destino = models.CharField(max_length=50, default="Firewall")
    severidade = models.CharField(max_length=10, choices=SEVERIDADE_CHOICES, default='baixa')
    status = models.BooleanField(default=False, verbose_name="Resolvido?")
    data_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.severidade.upper()}] {self.tipo} - {self.origem}"

    @property
    def cor_badge(self):
        cores = {
            'baixa': 'text-neonBlue border-neonBlue bg-blue-900/20',
            'media': 'text-warnYellow border-warnYellow bg-yellow-900/20',
            'alta': 'text-orange-500 border-orange-500 bg-orange-900/20',
            'critica': 'text-alertRed border-alertRed bg-red-900/20 animate-pulse', # Crítico pisca!
        }
        return cores.get(self.severidade, 'text-gray-400')

class HistoricoOperacao(models.Model):
    data_hora = models.DateTimeField(help_text="Data e Hora da medição")
    chamadas_ativas = models.IntegerField(default=0)
    trafego_rede_mbps = models.IntegerField(default=0, help_text="Uso em Mbps")

    class Meta:
        ordering = ['data_hora'] # Garante que o gráfico siga a ordem cronológica
        verbose_name = "Histórico de Operação"
        verbose_name_plural = "Histórico de Operações"

    def __str__(self):
        return f"{self.data_hora.strftime('%d/%m %H:%M')} - {self.chamadas_ativas} Calls"

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, unique=True) # Vamos usar como chave de busca
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    empresa = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.nome} ({self.empresa})"
        
class Chamado(models.Model):
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
    ]

    ORIGEM_CHOICES = [
        ('interno', 'Painel Interno'),
        ('whatsapp', 'WhatsApp Bot'),
        ('site', 'Widget do Site'),
    ]

    titulo = models.CharField(max_length=100)
    descricao = models.TextField(verbose_name="Descrição Detalhada")
    departamento = models.CharField(max_length=20, choices=DEPARTAMENTO_CHOICES, default='tecnico')
    
    # Quem pediu? (Geralmente o Agente)
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # NOVO: Vínculo com Cliente Externo
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)
    
    # NOVO: Saber de onde veio
    origem = models.CharField(max_length=10, choices=ORIGEM_CHOICES, default='interno')
    
    # Quem vai resolver? (Pode ser nulo no começo)
    atribuido_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chamados_atribuidos')
    
    data_inicio_atendimento = models.DateTimeField(null=True, blank=True, help_text="Momento que o agente assumiu")
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aberto')
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"#{self.id} - {self.titulo}"

    @property
    def cor_badge(self):
        # Cores para Status
        if self.status == 'aberto': return 'bg-red-900/30 text-alertRed border-red-800'
        if self.status == 'andamento': return 'bg-yellow-900/30 text-warnYellow border-yellow-800'
        return 'bg-green-900/30 text-neonGreen border-green-800'
    @property
    def icone_origem(self):
        if self.origem == 'whatsapp': return 'fa-whatsapp text-green-500'
        if self.origem == 'site': return 'fa-globe text-blue-400'
        return 'fa-user text-gray-400'
    
class Comentario(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    texto = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentário de {self.autor.username} em #{self.chamado.id}"
    
class Notificacao(models.Model):
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    mensagem = models.TextField()
    link = models.CharField(max_length=200, blank=True, null=True) # Para onde vai ao clicar
    lida = models.BooleanField(default=False)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Para {self.destinatario}: {self.titulo}"