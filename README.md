# 🚀 AliDash - Plataforma SaaS de Atendimento Omnichannel

**AliDash** é um sistema completo de Helpdesk e Atendimento ao Cliente desenvolvido para centralizar solicitações via Chat em Tempo Real e Tickets. A plataforma oferece painéis distintos para Administradores e Agentes, gestão de filas por prioridade, métricas operacionais (TMA/TME) e integração externa via API Restful.

---

## 📋 Funcionalidades Principais

### 🏢 Painel Administrativo & Gestão
- **Dashboard Executivo:** Gráficos de tráfego, KPIs em tempo real e status da infraestrutura.
- **Gestão de Usuários (RBAC):** Controle granular entre Administradores e Agentes Operacionais.
- **Auditoria:** Histórico completo de chamados encerrados com cálculo automático de duração.
- **Monitoramento de Rede:** Módulo para gestão de Access Points (APs) e status de conectividade.

### 🎧 Área do Agente (Cockpit)
- **Fila Inteligente (FIFO):** Ordenação automática de chamados por tempo de espera e prioridade.
- **Chat em Tempo Real:** Conversa bidirecional com o cliente sem recarregar a página (Polling otimizado).
- **Controle de Status:** Botões de ação para definir disponibilidade (Online, Pausa, Offline).
- **Segmentação por Departamento:** Agentes visualizam apenas chamados do seu setor (Comercial, Técnico, Administrativo).

### 🌍 Interface do Cliente (Widget Externo)
- **Widget Flutuante:** Código JS puro para incorporar em qualquer site externo.
- **Validação de Segurança:** Verificação matemática de CPF e persistência de sessão (o chat não fecha se der F5).
- **Auto-Atendimento:** Formulário inicial com seleção de departamento e identificação.
- **Inatividade Inteligente:** Encerramento automático de sessão caso o cliente abandone o chat.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.11+, Django 5, Django Rest Framework (DRF).
- **Frontend:** HTML5, Tailwind CSS, JavaScript (Vanilla), Chart.js.
- **Banco de Dados:** SQLite (Desenvolvimento) / Compatível com PostgreSQL.
- **Segurança:** Django Signals, CSRF Protection, Validação de CPF.
- **Interface Admin:** Django Jazzmin (Tema Dark).

---

## ⚙️ Instalação e Configuração

Siga os passos abaixo para rodar o projeto localmente.

## 1. Pré-requisitos
Certifique-se de ter o **Python** e o **Git** instalados em sua máquina.

## 2. Clonar o Repositório
```bash
git clone [https://github.com/SEU_USUARIO/alidash-system.git](https://github.com/SEU_USUARIO/alidash-system.git)
cd alidash-system
```

## 3. Criar Ambiente Virtual
Recomendado para isolar as dependências.

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate3. Criar Ambiente VirtualRecomendado para isolar as dependências.Windows:Bashpython -m venv venv
venv\Scripts\activate
Linux/Mac:Bashpython3 -m venv venv
source venv/bin/activate
```
## 4. Instalar Dependências
```bash
pip install -r requirements.txt
```
## 5. Configurar Banco de Dados
Crie as tabelas iniciais do sistema.
```bash
python manage.py migrate
```
## 6. Criar Superusuário (Admin)
```bash
python manage.py createsuperuser
```
# Siga as instruções para definir usuário e senha
## 7. Iniciar o Servidor
```bash
python manage.py runserver
```
O sistema estará acessível em: http://127.0.0.1:8000/
# 🚀 Como Utilizar
## 👨‍💻 Acesso Admin
- 1.Acesse http://127.0.0.1:8000/admin/ ou faça login na Home.
- 2.Utilize as credenciais criadas no passo 6.
- 3.Cadastre novos agentes na aba Gestão > Usuários > Novo Colaborador.
### 🧩 Simulando um Cliente (Widget)
Para testar o chat como se fosse um cliente final:
1. Acesse http://127.0.0.1:8000/teste-widget/ em uma aba anônima.
2. Clique no botão flutuante azul.
3. Selecione o departamento, preencha os dados (CPF válido necessário) e inicie o chat.
### 🎧 Acesso do Agente
Crie um usuário no painel Admin com o tipo "Agente Operacional".
Faça login com este usuário em http://127.0.0.1:8000/login/.
Você será redirecionado para o "Meu Painel" e verá os chamados na aba "Meus Chamados".
### 🔌 Documentação da API
O sistema possui endpoints públicos para integração com Bots (WhatsApp/Telegram) e Sites.

| Contexto | Método | Endpoint | Descrição | Autenticação |
| :--- | :--- | :--- | :--- | :---: |
| **Widget** | `GET` | `/api/v1/departments/` | Lista departamentos ativos para o formulário | Não |
| **Widget** | `POST` | `/api/v1/chat/init/` | Inicia sessão e cria o "Lead" | Não |
| **Chat** | `GET` | `/api/v1/chat/{uuid}/history/` | Recupera histórico de mensagens | Token (Session) |
| **Chat** | `POST` | `/api/v1/chat/{uuid}/message/` | Envia mensagem (Cliente ou Agente) | Token (Session) |
| **Chat** | `POST` | `/api/v1/chat/{uuid}/end/` | Encerra o atendimento (Calcula TME) | Token (Session) |
| **Agente** | `GET` | `/api/v1/agent/queue/` | Lista chamados aguardando na fila | **Sim (Agente)** |
| **Agente** | `POST` | `/api/v1/agent/status/` | Altera status (Online, Pausa, Offline) | **Sim (Agente)** |
| **Admin** | `GET` | `/api/v1/dashboard/metrics/` | Retorna KPIs (TMA, TME, Volumetria) | **Sim (Admin)** |
| **Admin** | `GET` | `/api/v1/users/{id}` | Gerencia perfil e permissões de usuários | **Sim (Admin)** |
