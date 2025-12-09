import csv
from .forms import NovoUsuarioForm, ChamadoForm, ComentarioForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from .models import *
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Avg, F, DurationField, ExpressionWrapper, Q
from devices.models import EquipamentoCliente, Cliente


@login_required
def home(request):
    # LÓGICA DE SEPARAÇÃO (Se for Agente, joga pro painel dele)
    if not request.user.is_superuser:
        return redirect('painel_agente')

    # --- MÉTRICAS DE HELPDESK (JÁ EXISTENTES) ---
    total_agentes = Agente.objects.count()
    agentes_online = Agente.objects.filter(status='online').count()
    total_aps = AccessPoint.objects.count() # APs da infraestrutura interna
    aps_offline = AccessPoint.objects.filter(status='offline').count()
    incidentes_criticos = SecurityLog.objects.filter(severidade='critica', status=False).count()
    
    # --- NOVAS MÉTRICAS DE ISP (ROTEADORES DOS CLIENTES) ---
    # Contagem total de ONUs/Roteadores instalados em clientes
    total_roteadores_clientes = EquipamentoCliente.objects.count()
    
    # Quantos desses estão respondendo (Online)
    roteadores_online_clientes = EquipamentoCliente.objects.filter(online=True).count()
    
    # Clientes inadimplentes/bloqueados no Mikrotik
    clientes_bloqueados = Cliente.objects.filter(is_blocked=True).count()

    # --- CÁLCULO TMA/TME (HELPDESK) ---
    tma_calc = Chamado.objects.filter(status='concluido', data_inicio_atendimento__isnull=False).aggregate(
        media=Avg(F('data_conclusao') - F('data_inicio_atendimento'))
    )
    tma_valor = tma_calc['media']

    tme_calc = Chamado.objects.filter(data_inicio_atendimento__isnull=False).aggregate(
        media=Avg(F('data_inicio_atendimento') - F('data_abertura'))
    )
    tme_valor = tme_calc['media']

    def formatar_delta(delta):
        if not delta: return "00:00:00"
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    # --- GRÁFICOS ---
    historico = HistoricoOperacao.objects.all().order_by('-data_hora')[:10]
    historico = reversed(historico)
    labels_hora = []
    dados_chamadas = []
    dados_rede = []
    for registro in historico:
        labels_hora.append(registro.data_hora.strftime("%H:%M"))
        dados_chamadas.append(registro.chamadas_ativas)
        dados_rede.append(registro.trafego_rede_mbps)
    
    # --- CONTEXTO FINAL ---
    contexto = {
        # Helpdesk
        'total_agentes': total_agentes,
        'agentes_online': agentes_online,
        'total_aps': total_aps,
        'aps_offline': aps_offline,
        'incidentes_criticos': incidentes_criticos,
        
        # ISP / Clientes (NOVOS DADOS)
        'total_roteadores_clientes': total_roteadores_clientes,
        'roteadores_online_clientes': roteadores_online_clientes,
        'clientes_bloqueados': clientes_bloqueados,

        # Métricas
        'tma_real': formatar_delta(tma_valor),
        'tme_real': formatar_delta(tme_valor),
        
        # Gráficos
        'chart_labels': labels_hora,
        'chart_chamadas': dados_chamadas,
        'chart_rede': dados_rede,
    }
    
    return render(request, 'home.html', contexto)
def conectividade(request):
    status_filter = request.GET.get('status', '') # Ex: ?status=offline
    
    lista_aps = AccessPoint.objects.all()
    
    # Filtro por Status (Clicando nos botões do topo)
    if status_filter:
        lista_aps = lista_aps.filter(status=status_filter)
        
    # Contadores (sempre pegam o total geral)
    total_online = AccessPoint.objects.filter(status='online').count()
    total_offline = AccessPoint.objects.filter(status='offline').count()
    
    contexto = {
        'aps': lista_aps,
        'online_count': total_online,
        'offline_count': total_offline,
    }
    return render(request, 'conectividade.html', contexto)

def callcenter(request):
    # Pega o termo digitado (se não tiver nada, vem vazio)
    termo_busca = request.GET.get('q', '')
    
    if termo_busca:
        # Busca por Nome OU Ramal (icontains = ignora maiúscula/minúscula)
        lista_agentes = Agente.objects.filter(
            Q(nome__icontains=termo_busca) | Q(ramal__icontains=termo_busca)
        )
    else:
        lista_agentes = Agente.objects.all()
    
    contexto = {
        'agentes': lista_agentes,
        'termo_busca': termo_busca # Devolvemos para o template manter escrito no input
    }
    return render(request, 'callcenter.html', contexto)

def seguranca(request):
    # Pega os últimos 20 logs
    logs = SecurityLog.objects.all().order_by('-data_hora')[:20]
    
    # Contadores para o Topo da Página
    ameacas_ativas = SecurityLog.objects.filter(status=False).count()
    criticas = SecurityLog.objects.filter(severidade='critica', status=False).count()
    
    contexto = {
        'logs': logs,
        'ameacas_ativas': ameacas_ativas,
        'criticas': criticas
    }
    return render(request, 'seguranca.html', contexto)

def exportar_csv_agentes(request):
    # Configura o tipo de arquivo que o navegador vai receber
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="relatorio_agentes.csv"'

    writer = csv.writer(response)
    
    # 1. Escreve o Cabeçalho (Títulos das Colunas)
    writer.writerow(['Nome do Agente', 'Ramal', 'Status Atual', 'Total Atendimentos', 'Tempo Logado'])

    # 2. Busca os dados no banco
    agentes = Agente.objects.all()

    # 3. Escreve linha por linha
    for agente in agentes:
        writer.writerow([
            agente.nome, 
            agente.ramal, 
            agente.get_status_display(), # Pega o texto bonito ('Disponível') e não o código ('online')
            agente.atendimentos,
            agente.tempo_logado
        ])

    return response

def configuracoes(request):
    # Se o usuário enviou o formulário de senha
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Mantém o usuário logado depois de trocar a senha
            update_session_auth_hash(request, user) 
            messages.success(request, 'Sua senha foi alterada com sucesso!')
        else:
            messages.error(request, 'Erro ao alterar senha. Verifique os campos.')
    else:
        form = PasswordChangeForm(request.user)

    contexto = {
        'form': form
    }
    return render(request, 'configuracoes.html', contexto)

def detalhe_agente(request, id):
    # Busca o agente pelo ID ou dá erro 404 se não existir
    agente = get_object_or_404(Agente, id=id)

    # Lógica de Ação (Se clicou no botão de mudar status)
    if request.method == 'POST':
        novo_status = request.POST.get('acao_status')
        if novo_status:
            agente.status = novo_status
            agente.save()
            # Recarrega a página para mostrar a mudança
            return redirect('detalhe_agente', id=id)

    # Simulando um histórico de chamadas recentes (apenas visual)
    historico_recente = [
        {'hora': '10:45', 'duracao': '05:22', 'cliente': 'Mariana (Financeiro)', 'resultado': 'Resolvido'},
        {'hora': '10:30', 'duracao': '02:10', 'cliente': 'Pedro (Suporte)', 'resultado': 'Transferido'},
        {'hora': '10:15', 'duracao': '08:45', 'cliente': 'Carlos (Vendas)', 'resultado': 'Resolvido'},
    ]

    contexto = {
        'agente': agente,
        'historico': historico_recente
    }
    return render(request, 'detalhe_agente.html', contexto)

# Função auxiliar para checar se é admin (Segurança)
def check_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(check_admin) # Só admin acessa
def lista_usuarios(request):
    # Vamos listar os Agentes, pois todo user funcional terá um perfil Agente
    usuarios = Agente.objects.all().select_related('user')
    return render(request, 'usuarios_list.html', {'usuarios': usuarios})

@login_required
@user_passes_test(check_admin)
def criar_usuario(request):
    if request.method == 'POST':
        form = NovoUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_usuarios')
    else:
        form = NovoUsuarioForm()
    
    return render(request, 'usuarios_form.html', {'form': form})

@login_required
def painel_agente(request):
    # Pega o perfil de Agente do usuário logado
    # O try/except evita erro se o usuário não tiver perfil criado
    try:
        agente = request.user.agente 
    except Agente.DoesNotExist:
        return HttpResponse("Erro: Seu usuário não tem perfil de Agente configurado.")

    # Lógica para mudar o PRÓPRIO status
    if request.method == 'POST':
        novo_status = request.POST.get('meu_status')
        if novo_status:
            agente.status = novo_status
            agente.save()
            return redirect('painel_agente')

    contexto = {
        'agente': agente,
    }
    return render(request, 'painel_agente.html', contexto)

@login_required
def lista_chamados(request):
    # Lógica de Permissão
    if request.user.is_superuser:
        # Admin vê tudo
        chamados = Chamado.objects.all().order_by('-data_abertura')
    else:
        # Agente vê só os seus
        chamados = Chamado.objects.filter(solicitante=request.user).order_by('-data_abertura')
    
    return render(request, 'chamados_lista.html', {'chamados': chamados})

@login_required
def novo_chamado(request):
    if request.method == 'POST':
        form = ChamadoForm(request.POST)
        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.solicitante = request.user # Preenche automático quem está logado
            chamado.save()
            return redirect('lista_chamados')
    else:
        form = ChamadoForm()
    
    return render(request, 'chamados_form.html', {'form': form})

@login_required
def detalhe_chamado(request, id):
    chamado = get_object_or_404(Chamado, id=id)
    
    # ---------------------------------------------------------
    # 1. LÓGICA DE POST: NOVOS COMENTÁRIOS
    # ---------------------------------------------------------
    if request.method == 'POST' and 'btn_comentario' in request.POST:
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.chamado = chamado
            comentario.autor = request.user
            comentario.save()
            return redirect('detalhe_chamado', id=id)

    # ---------------------------------------------------------
    # 2. LÓGICA DE POST: MUDANÇA DE STATUS (PLAY/STOP)
    # ---------------------------------------------------------
    if request.method == 'POST' and 'btn_status' in request.POST:
        novo_status = request.POST.get('novo_status')
        if novo_status:
            chamado.status = novo_status
            
            # Se for iniciar atendimento (Play) e ainda não tiver data de início
            if novo_status == 'andamento' and chamado.data_inicio_atendimento is None:
                chamado.data_inicio_atendimento = timezone.now()
                # Se ninguém assumiu ainda, quem clicou assume
                if not chamado.atribuido_a:
                    chamado.atribuido_a = request.user 
            
            # Se for concluir, grava a data final
            if novo_status == 'concluido':
                chamado.data_conclusao = timezone.now()

            chamado.save()
            return redirect('detalhe_chamado', id=id)

    # ---------------------------------------------------------
    # 3. CÁLCULO DA DURAÇÃO DO ATENDIMENTO
    # ---------------------------------------------------------
    duracao_atendimento = "--"
    
    # Só calcula se o atendimento já começou (tem data de início)
    if chamado.data_inicio_atendimento:
        # Se já acabou, usa a data final. Se não (está rodando), usa AGORA.
        data_final = chamado.data_conclusao if chamado.data_conclusao else timezone.now()
        
        # Diferença entre os dois horários
        diff = data_final - chamado.data_inicio_atendimento
        
        # Matemática para formatar bonito (Dias, Horas, Minutos)
        total_seconds = int(diff.total_seconds())
        m, s = divmod(total_seconds, 60)
        h, m = divmod(m, 60)
        
        if h > 0:
            duracao_atendimento = f"{h}h {m}m"
        else:
            duracao_atendimento = f"{m}m {s}s"

    # ---------------------------------------------------------
    # 4. PREPARAÇÃO DOS DADOS PARA O TEMPLATE
    # ---------------------------------------------------------
    form = ComentarioForm()
    # Pega comentários ordenados por data
    comentarios = chamado.comentarios.all().order_by('data')

    contexto = {
        'chamado': chamado,
        'comentarios': comentarios,
        'form': form,
        'duracao_atendimento': duracao_atendimento, # Variável enviada para o card lateral
    }
    
    return render(request, 'chamado_detalhe.html', contexto)

def teste_widget(request):
    return render(request, 'widget_demo.html')

@login_required
def historico_chamados(request):
    # Regra de Permissão:
    # Admin vê TODO o histórico.
    # Agente vê apenas o histórico DOS SEUS chamados.
    
    if request.user.is_superuser:
        chamados = Chamado.objects.filter(status='concluido').order_by('-data_conclusao')
    else:
        chamados = Chamado.objects.filter(solicitante=request.user, status='concluido').order_by('-data_conclusao')
    
    # Calcular duração para cada chamado na lista
    for c in chamados:
        if c.data_inicio_atendimento and c.data_conclusao:
            diff = c.data_conclusao - c.data_inicio_atendimento
            # Formatação manual bonita (ex: "05m 22s")
            total_seconds = int(diff.total_seconds())
            m, s = divmod(total_seconds, 60)
            h, m = divmod(m, 60)
            c.duracao_formatada = f"{h}h {m}m" if h > 0 else f"{m}m {s}s"
        else:
            c.duracao_formatada = "--"

    return render(request, 'chamados_historico.html', {'chamados': chamados})

@login_required
@user_passes_test(check_admin)
def lista_usuarios(request):
    # Lista 1: Equipe Interna (Agentes e Admins)
    colaboradores = Agente.objects.all().select_related('user').order_by('nome')
    
    # Lista 2: Clientes Externos (Cadastrados via Chat/Ticket)
    clientes = Cliente.objects.all().order_by('nome')
    
    contexto = {
        'colaboradores': colaboradores,
        'clientes': clientes
    }
    return render(request, 'usuarios_list.html', contexto)

def widget_atendimento(request):
    """
    View pública para o Widget do Cliente.
    Não exige login (usa CPF para identificar).
    """
    step = 1 # Passo 1: Identificação, Passo 2: Chat
    cliente_identificado = None
    mensagem_erro = None
    
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        # --- FASE 1: IDENTIFICAÇÃO ---
        if acao == 'identificar':
            cpf = request.POST.get('cpf_login')
            # Remove pontos e traços para busca
            # (Adicione logica de limpeza de string se necessario)
            
            try:
                # Busca o cliente no banco do ISP
                cliente = Cliente.objects.get(cpf=cpf)
                
                # Sucesso: Avança para o chat
                step = 2
                cliente_identificado = cliente
                
            except Cliente.DoesNotExist:
                mensagem_erro = "CPF não encontrado na nossa base."

        # --- FASE 2: ABRIR O CHAMADO ---
        elif acao == 'abrir_chamado':
            cliente_id = request.POST.get('cliente_id')
            assunto = request.POST.get('assunto')
            mensagem = request.POST.get('mensagem')
            
            # Busca o cliente
            cliente = Cliente.objects.get(id=cliente_id)
            
            # Garante usuário genérico
            usuario_web, created = User.objects.get_or_create(username='cliente_via_site')
            
            # Cria o Ticket
            novo_ticket = Chamado.objects.create(
                titulo=f"Via Widget: {assunto}",
                descricao=mensagem,
                solicitante=usuario_web,
                
                cliente_isp_id=cliente.id,
                # ----------------------------------------------
                
                status='aberto',
                categoria='wifi',
                prioridade='normal'
            )
            
            return JsonResponse({
                'success': True, 
                'ticket_id': novo_ticket.id,
                'message': 'Solicitação recebida com sucesso!'
            })

    context = {
        'step': step,
        'cliente': cliente_identificado,
        'erro': mensagem_erro
    }
    return render(request, 'widget.html', context)