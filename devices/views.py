# devices/views.py
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Cliente, EquipamentoCliente
from .services import MikrotikService
from .forms import *
import random 
from django.utils import timezone

def action_bloquear_cliente(request, cliente_id):
    # Verifica permissão do usuário logado (Apenas Admin ou Financeiro)
    if not request.user.has_perm('devices.can_block'):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    cliente = Cliente.objects.get(id=cliente_id)
    equipamento = cliente.equipamentos.first() # Pega o roteador principal
    
    if equipamento and equipamento.concentrador:
        mk = MikrotikService(equipamento.concentrador)
        sucesso = mk.bloquear_cliente(cliente.pppoe_user)
        
        if sucesso:
            cliente.is_blocked = True
            cliente.save()
            return JsonResponse({'status': 'Cliente Bloqueado com Sucesso'})
    
    return JsonResponse({'error': 'Erro ao comunicar com concentrador'}, status=500)


@login_required
def lista_clientes_isp(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '') # 'bloqueado', 'ativo', 'online', 'offline'
    
    # Começa com todos (otimizando a busca com select_related)
    clientes = Cliente.objects.all().prefetch_related('equipamentos').order_by('nome')

    # 1. Filtro de Busca (Nome, CPF ou Usuário PPPoE)
    if query:
        clientes = clientes.filter(
            Q(nome__icontains=query) | 
            Q(cpf__icontains=query) | 
            Q(pppoe_user__icontains=query)
        )

    # 2. Filtro de Status
    if status_filter == 'bloqueado':
        clientes = clientes.filter(is_blocked=True)
    elif status_filter == 'ativo':
        clientes = clientes.filter(is_blocked=False)
    # (Filtros de online/offline seriam nos equipamentos, podemos refinar depois)

    context = {
        'clientes': clientes,
        'query': query
    }
    return render(request, 'devices/lista_clientes.html', context)

@login_required
def detalhe_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    equipamento = cliente.equipamentos.first()
    
    # --- SIMULAÇÃO DE TELEMETRIA (ISSO VIRIA DO MIKROTIK/TR-069) ---
    
    # 1. Sinal (dBm): Quanto mais próximo de 0, melhor. -20 é excelente, -80 é péssimo.
    sinal_atual = -random.randint(18, 28) # Simula um sinal bom entre -18 e -28
    
    # 2. Dados para o Gráfico de Consumo (Últimas 10 leituras)
    historico_consumo = []
    labels_tempo = []
    for i in range(10):
        # Simula download variando entre 50mb e 100mb
        historico_consumo.append(random.randint(50, 100)) 
        # Horários passados (10 min atrás, 9 min atrás...)
        hora = (timezone.now() - timezone.timedelta(minutes=10-i)).strftime("%H:%M")
        labels_tempo.append(hora)

    context = {
        'cliente': cliente,
        'equipamento': equipamento,
        'sinal_atual': sinal_atual,
        'chart_labels': labels_tempo,
        'chart_data': historico_consumo,
        # Calcula a cor do sinal para o template
        'sinal_status': 'Bom' if abs(sinal_atual) < 25 else 'Regular',
        'sinal_cor': 'text-neonGreen' if abs(sinal_atual) < 25 else 'text-warnYellow'
    }
    
    return render(request, 'devices/detalhe_cliente.html', context)

@login_required
def novo_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('devices:lista_clientes')
    else:
        form = ClienteForm()
    
    return render(request, 'devices/cliente_form.html', {'form': form})