from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Chamado, Comentario, Notificacao, Agente

# 1. Quando um NOVO CHAMADO é criado
@receiver(post_save, sender=Chamado)
def notificar_novo_chamado(sender, instance, created, **kwargs):
    if created:
        # Notifica TODOS os Superusuários (Admins)
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notificacao.objects.create(
                destinatario=admin,
                titulo="Novo Chamado Aberto",
                mensagem=f"Ticket #{instance.id}: {instance.titulo} ({instance.get_origem_display()})",
                link=f"/chamados/{instance.id}/"
            )

# 2. Quando um NOVO COMENTÁRIO é feito (Chat)
@receiver(post_save, sender=Comentario)
def notificar_nova_mensagem(sender, instance, created, **kwargs):
    if created:
        chamado = instance.chamado
        
        # Se foi o CLIENTE (autor=None) que mandou, avisa o Agente/Admin
        if instance.autor is None:
            # Se alguém já assumiu o chamado, avisa só ele
            if chamado.atribuido_a:
                Notificacao.objects.create(
                    destinatario=chamado.atribuido_a,
                    titulo="Nova Mensagem do Cliente",
                    mensagem=f"No chamado #{chamado.id}: {instance.texto[:30]}...",
                    link=f"/chamados/{chamado.id}/"
                )
            else:
                # Se ninguém assumiu, avisa os Admins
                admins = User.objects.filter(is_superuser=True)
                for admin in admins:
                    Notificacao.objects.create(
                        destinatario=admin,
                        titulo="Nova Resposta do Cliente",
                        mensagem=f"Ticket #{chamado.id} tem nova interação.",
                        link=f"/chamados/{chamado.id}/"
                    )
                    
@receiver(post_save, sender=User)
def criar_perfil_agente(sender, instance, created, **kwargs):
    if created:
        # Se o usuário foi criado mas não tem Agente, cria um padrão
        # Verifica se já existe para evitar erro
        if not hasattr(instance, 'agente'):
            Agente.objects.create(
                user=instance,
                nome=instance.username.capitalize(),
                ramal="0000", # Ramal provisório
                status="offline"
            )