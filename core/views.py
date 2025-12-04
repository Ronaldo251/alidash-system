import csv
from .forms import NovoUsuarioForm, ChamadoForm, ComentarioForm
from django.http import HttpResponse
from django.shortcuts import render
from .models import Agente, AccessPoint, SecurityLog, HistoricoOperacao, Chamado, Comentario
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect


def home(request):
    # LÓGICA DE SEPARAÇÃO:
    # Se NÃO for superusuário (é Agente), joga para o painel dele
    if not request.user.is_superuser:
        return redirect('painel_agente')

    # --- LÓGICA ORIGINAL DO DASHBOARD DE ADMIN ---
    total_agentes = Agente.objects.count()
    agentes_online = Agente.objects.filter(status='online').count()
    total_aps = AccessPoint.objects.count()
    aps_offline = AccessPoint.objects.filter(status='offline').count()
    incidentes_criticos = SecurityLog.objects.filter(severidade='critica', status=False).count()

    # Gráfico
    historico = HistoricoOperacao.objects.all().order_by('-data_hora')[:10]
    historico = reversed(historico)
    labels_hora = []
    dados_chamadas = []
    dados_rede = []
    for registro in historico:
        labels_hora.append(registro.data_hora.strftime("%H:%M"))
        dados_chamadas.append(registro.chamadas_ativas)
        dados_rede.append(registro.trafego_rede_mbps)

    contexto = {
        'total_agentes': total_agentes,
        'agentes_online': agentes_online,
        'total_aps': total_aps,
        'aps_offline': aps_offline,
        'incidentes_criticos': incidentes_criticos,
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
    # Busca o chamado (e garante que o usuário tem permissão para ver)
    chamado = get_object_or_404(Chamado, id=id)
    
    # Segurança: Se não for admin E não for o dono do chamado, bloqueia
    if not request.user.is_superuser and chamado.solicitante != request.user:
        return redirect('lista_chamados')

    # Lógica 1: Processar Novo Comentário
    if request.method == 'POST' and 'btn_comentario' in request.POST:
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.chamado = chamado
            comentario.autor = request.user
            comentario.save()
            return redirect('detalhe_chamado', id=id)

    # Lógica 2: Processar Mudança de Status (Só Admin ou Dono pode fechar?)
    # Vamos permitir que Admin mude tudo, e usuário apenas reabra ou feche.
    if request.method == 'POST' and 'btn_status' in request.POST:
        novo_status = request.POST.get('novo_status')
        if novo_status:
            chamado.status = novo_status
            chamado.save()
            return redirect('detalhe_chamado', id=id)

    form = ComentarioForm()
    comentarios = chamado.comentarios.all().order_by('data')

    contexto = {
        'chamado': chamado,
        'comentarios': comentarios,
        'form': form
    }
    return render(request, 'chamado_detalhe.html', contexto)

def teste_widget(request):
    return render(request, 'widget_demo.html')