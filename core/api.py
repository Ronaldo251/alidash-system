from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Chamado, Cliente, Comentario, Notificacao
from rest_framework.authentication import SessionAuthentication
from django.db.models import Q

def cpf_valido(cpf_input):
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, str(cpf_input)))
    
    # Verifica tamanho e se todos os números são iguais (ex: 111.111.111-11)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    # Cálculo do 1º Dígito Verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito1 = 0 if resto == 10 else resto
    
    if digito1 != int(cpf[9]):
        return False

    # Cálculo do 2º Dígito Verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito2 = 0 if resto == 10 else resto
    
    if digito2 != int(cpf[10]):
        return False

    return True

# ==============================================================================
# 1. ABRIR CHAMADO (Público - Widget e WhatsApp)
# ==============================================================================
@api_view(['POST'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def abrir_chamado_externo(request):
    data = request.data
    cpf_recebido = data.get('cpf')
    mensagem = data.get('mensagem')
    origem = data.get('origem', 'site')
    nome_visitante = data.get('nome', 'Visitante Desconhecido')
    departamento = data.get('departamento', 'tecnico')
    
    if not mensagem:
        return Response({"erro": "Mensagem é obrigatória"}, status=400)
    
    if not cpf_recebido:
        return Response({"erro": "CPF é obrigatório"}, status=400)

    # 1. Limpa e Valida CPF
    cpf_limpo = ''.join(filter(str.isdigit, str(cpf_recebido)))
    
    if not cpf_valido(cpf_limpo):
        return Response({"erro": "CPF inválido. Verifique os números."}, status=400)

    # 2. Busca ou Cria Cliente (Agora seguro)
    # update_or_create garante que se o cliente voltar com nome diferente, atualizamos o nome
    cliente, created = Cliente.objects.update_or_create(
        cpf=cpf_limpo,
        defaults={'nome': nome_visitante} 
    )
    
    # 3. Cria o Chamado
    novo_chamado = Chamado.objects.create(
        titulo=f"Suporte via {data.get('origem', 'site').title()}",
        descricao=data.get('mensagem'),
        cliente=cliente,
        origem=data.get('origem', 'site'),
        departamento=departamento, # <--- AQUI
        prioridade='media',
        status='aberto'
    )

    # Cria comentário inicial
    Comentario.objects.create(chamado=novo_chamado, autor=None, texto=mensagem)

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

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([AllowAny])
def checar_notificacoes(request):
    if not request.user.is_authenticated:
        return Response({"count": 0, "itens": []})
    
    # 1. Pega todas as não lidas
    nao_lidas = Notificacao.objects.filter(destinatario=request.user, lida=False).order_by('-data')
    
    # 2. Conta total
    qtd = nao_lidas.count()
    
    # 3. Serializa as últimas 5 para mostrar no dropdown
    itens = []
    for n in nao_lidas[:5]:
        itens.append({
            "id": n.id,
            "titulo": n.titulo,
            "mensagem": n.mensagem,
            "link": n.link,
            "tempo": n.data.strftime("%H:%M")
        })

    return Response({"count": qtd, "itens": itens})

@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([AllowAny])
def marcar_como_lida(request):
    if not request.user.is_authenticated:
        return Response({})
    
    # Marca tudo como lido (simplificação para o MVP)
    Notificacao.objects.filter(destinatario=request.user, lida=False).update(lida=True)
    return Response({"sucesso": True})

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def encerrar_chamado_externo(request, chamado_id):
    """
    Permite que o Widget encerre o chamado por inatividade ou botão 'Sair'.
    """
    chamado = get_object_or_404(Chamado, id=chamado_id)
    cpf = request.data.get('cpf')

    # Validação de Segurança
    if chamado.cliente:
        cpf_limpo_post = ''.join(filter(str.isdigit, str(cpf)))
        cpf_limpo_banco = ''.join(filter(str.isdigit, str(chamado.cliente.cpf)))
        if cpf_limpo_post != cpf_limpo_banco:
            return Response({"erro": "Acesso negado"}, status=403)

    chamado.status = 'concluido'
    chamado.save()
    
    # Opcional: Criar comentário de sistema
    Comentario.objects.create(
        chamado=chamado,
        autor=None,
        texto="[SISTEMA] Chamado encerrado por inatividade ou desconexão do usuário."
    )
    
    return Response({"sucesso": True})

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([AllowAny]) # Controlamos permissão dentro da lógica
def listar_chamados_dinamico(request):
    if not request.user.is_authenticated:
        return Response({"erro": "Login necessário"}, status=403)

    # 1. ADMIN (Superusuário) -> Vê tudo
    if request.user.is_superuser:
        chamados = Chamado.objects.exclude(status='concluido').order_by('data_abertura')
    
    # 2. AGENTE / COLABORADOR -> Filtro Inteligente
    else:
        # Tenta pegar o perfil do agente
        if hasattr(request.user, 'agente'):
            meu_depto = request.user.agente.departamento
            
            # A Lógica Poderosa:
            # Mostra o chamado SE:
            # - É do meu departamento
            # - OU fui eu que abri (solicitante)
            # - OU está atribuído a mim (sou o responsável)
            chamados = Chamado.objects.filter(
                Q(departamento=meu_depto) | 
                Q(solicitante=request.user) |
                Q(atribuido_a=request.user)
            ).exclude(status='concluido').order_by('data_abertura')
            
        else:
            # Fallback (caso o usuário não tenha perfil de Agente, vê só os seus)
            chamados = Chamado.objects.filter(solicitante=request.user).exclude(status='concluido')
    dados = []
    for c in chamados:
        # Define qual timer está rodando
        if c.status == 'aberto':
            # Timer de Espera: Agora - Abertura
            base_time = c.data_abertura
            tipo_timer = 'espera'
        elif c.status == 'andamento':
            # Timer de Atendimento: Agora - Início Atendimento
            base_time = c.data_inicio_atendimento if c.data_inicio_atendimento else c.data_abertura
            tipo_timer = 'atendimento'
        else:
            base_time = None
            tipo_timer = 'parado'

        dados.append({
            "id": c.id,
            "titulo": c.titulo,
            "solicitante": c.cliente_isp.nome if c.cliente_isp else c.solicitante.username,
            "origem_icone": c.icone_origem,
            "prioridade": c.get_prioridade_display(),
            "status": c.get_status_display(),
            "status_code": c.status, # para classe CSS
            "cor_badge": c.cor_badge,
            "departamento": c.get_departamento_display(),
            "timestamp_base": base_time.isoformat() if base_time else None, # Data ISO para o JS calcular
            "tipo_timer": tipo_timer
        })
        
    return Response(dados)

@api_view(['GET'])
@permission_classes([AllowAny]) # Permite acesso público (o cliente do site)
def listar_comentarios_chat(request, chamado_id):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    
    # Pega todos os comentários ordenados por data
    comentarios = chamado.comentarios.all().order_by('data')
    
    data = []
    for c in comentarios:
        # Define quem está falando para pintar o balão certo no JS
        # Se for superuser ou staff, é o Agente.
        is_staff = c.autor.is_superuser or c.autor.is_staff
        
        data.append({
            "id": c.id,
            "texto": c.texto,
            "autor": c.autor.first_name or c.autor.username, # Nome bonito
            "is_staff": is_staff, 
            "hora": c.data.strftime("%H:%M")
        })
        
    return Response(data)