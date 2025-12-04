from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Chamado, Cliente, Comentario
from rest_framework.authentication import SessionAuthentication
# ==============================================================================
# 1. ABRIR CHAMADO (Público - Widget e WhatsApp)
# ==============================================================================
@api_view(['POST'])
@authentication_classes([]) # Desativa exigência de autenticação (evita erro CSRF)
@permission_classes([AllowAny]) # Permite acesso anônimo (qualquer um)
def abrir_chamado_externo(request):
    """
    Recebe JSON: { "cpf": "...", "mensagem": "...", "origem": "whatsapp/site", "nome": "..." }
    """
    data = request.data
    cpf_recebido = data.get('cpf')
    mensagem = data.get('mensagem')
    origem = data.get('origem', 'site')
    nome_visitante = data.get('nome', 'Visitante Desconhecido')

    if not mensagem:
        return Response({"erro": "Mensagem é obrigatória"}, status=400)

    # 1. Busca ou Cria Cliente
    cliente = None
    if cpf_recebido:
        # Remove tudo que não for número
        cpf_limpo = ''.join(filter(str.isdigit, str(cpf_recebido)))
        
        # Cria ou pega existente
        cliente, created = Cliente.objects.get_or_create(
            cpf=cpf_limpo,
            defaults={'nome': nome_visitante}
        )
    
    # 2. Cria o Chamado
    novo_chamado = Chamado.objects.create(
        titulo=f"Suporte via {origem.title()}",
        descricao=mensagem,
        cliente=cliente,
        origem=origem,
        prioridade='media',
        status='aberto'
    )

    return Response({
        "sucesso": True,
        "chamado_id": novo_chamado.id,
        "mensagem": f"Chamado #{novo_chamado.id} criado com sucesso."
    })


# ==============================================================================
# 2. LER MENSAGENS (Polling do Widget)
# ==============================================================================
@api_view(['GET'])
@authentication_classes([SessionAuthentication]) # <--- Permite que o Django reconheça o Agente logado
@permission_classes([AllowAny])
def verificar_mensagens(request, chamado_id):
    cpf_cliente = request.GET.get('cpf')
    chamado = get_object_or_404(Chamado, id=chamado_id)
    
    # Lógica de Permissão Híbrida:
    # 1. Se for Agente/Admin logado -> Libera
    # 2. Se for Cliente Externo -> Exige CPF
    if not request.user.is_authenticated:
        # É visitante? Valida CPF
        if chamado.cliente:
            cpf_limpo_url = ''.join(filter(str.isdigit, str(cpf_cliente)))
            cpf_limpo_banco = ''.join(filter(str.isdigit, str(chamado.cliente.cpf)))
            if cpf_limpo_url != cpf_limpo_banco:
                return Response({"erro": "Acesso negado"}, status=403)

    # Pega mensagens
    mensagens = chamado.comentarios.all().order_by('data')
    
    dados_msg = []
    for msg in mensagens:
        dados_msg.append({
            "autor": msg.autor.username if msg.autor else (chamado.cliente.nome if chamado.cliente else "Cliente"),
            "texto": msg.texto,
            "eh_agente": msg.autor is not None,
            "data": msg.data.strftime("%H:%M")
        })
        
    return Response({
        "status_chamado": chamado.status,
        "mensagens": dados_msg
    })


# ==============================================================================
# 3. ENVIAR MENSAGEM (Cliente respondendo)
# ==============================================================================
@api_view(['POST'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def enviar_mensagem_externa(request, chamado_id):
    """
    Cliente envia msg para o chamado existente
    """
    chamado = get_object_or_404(Chamado, id=chamado_id)
    cpf = request.data.get('cpf')
    texto = request.data.get('mensagem')

    # Validação
    if chamado.cliente:
        cpf_limpo_post = ''.join(filter(str.isdigit, str(cpf)))
        cpf_limpo_banco = ''.join(filter(str.isdigit, str(chamado.cliente.cpf)))
        
        if cpf_limpo_post != cpf_limpo_banco:
            return Response({"erro": "Acesso negado"}, status=403)

    # Cria comentário sem autor (autor=None)
    Comentario.objects.create(
        chamado=chamado,
        autor=None,
        texto=texto
    )
    
    return Response({"sucesso": True})