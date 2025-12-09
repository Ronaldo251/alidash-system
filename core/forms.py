from django import forms
from django.contrib.auth.models import User
from .models import Agente, Chamado, Comentario, DEPARTAMENTO_CHOICES
from devices.models import Cliente

class NovoUsuarioForm(forms.ModelForm):
    username = forms.CharField(label="Usuário (Login)", widget=forms.TextInput(attrs={'class': 'w-full bg-dark border border-borderCol text-white text-sm rounded p-2 focus:border-neonBlue focus:outline-none'}))
    password = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={'class': 'w-full bg-dark border border-borderCol text-white text-sm rounded p-2 focus:border-neonBlue focus:outline-none'}))
    email = forms.EmailField(label="Email", required=False, widget=forms.EmailInput(attrs={'class': 'w-full bg-dark border border-borderCol text-white text-sm rounded p-2 focus:border-neonBlue focus:outline-none'}))
    
    # Campo Tipo de Acesso (Agente vs Admin)
    tipo_usuario = forms.ChoiceField(
        label="Tipo de Acesso",
        choices=[('agente', 'Agente Operacional'), ('admin', 'Administrador')],
        widget=forms.Select(attrs={'class': 'w-full bg-dark border border-borderCol text-white text-sm rounded p-2 focus:border-neonBlue focus:outline-none'})
    )

    # CORREÇÃO: Forçando o campo Departamento a ser um Select com as opções corretas
    departamento = forms.ChoiceField(
        label="Departamento",
        choices=DEPARTAMENTO_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full bg-dark border border-borderCol text-white text-sm rounded p-2 focus:border-neonBlue focus:outline-none'})
    )

    class Meta:
        model = Agente
        fields = ['nome', 'ramal', 'departamento']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full bg-dark border border-borderCol text-white text-sm rounded p-2 focus:border-neonBlue focus:outline-none'}),
            'ramal': forms.TextInput(attrs={'class': 'w-full bg-dark border border-borderCol text-white text-sm rounded p-2 focus:border-neonBlue focus:outline-none'}),
        }

    def save(self, commit=True):
        # 1. Cria o Usuário
        # (Neste momento, o SIGNAL dispara e cria um Agente vazio no banco automaticamente)
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['nome'].split()[0]
        )
        
        tipo = self.cleaned_data['tipo_usuario']
        if tipo == 'admin':
            user.is_staff = True
            user.is_superuser = True
        user.save()

        # 2. ATUALIZA O AGENTE EXISTENTE
        # Em vez de criar um novo (super().save), pegamos o que o Signal criou
        if hasattr(user, 'agente'):
            agente = user.agente
            agente.nome = self.cleaned_data['nome']
            agente.ramal = self.cleaned_data['ramal']
            agente.departamento = self.cleaned_data['departamento']
            if commit:
                agente.save()
        else:
            # Fallback: Se por algum motivo o signal falhar, criamos manualmente
            agente = super().save(commit=False)
            agente.user = user
            if commit:
                agente.save()
                
        return agente
    
class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['titulo', 'cliente_isp', 'descricao', 'prioridade', 'categoria']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full bg-dark border border-borderCol text-white p-2 rounded focus:border-neonBlue outline-none'}),
            'departamento': forms.Select(attrs={'class': 'w-full bg-dark border border-borderCol text-white p-2 rounded focus:border-neonBlue outline-none'}),
            'prioridade': forms.Select(attrs={'class': 'w-full bg-dark border border-borderCol text-white p-2 rounded focus:border-neonBlue outline-none'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full bg-dark border border-borderCol text-white p-2 rounded focus:border-neonBlue outline-none', 'rows': 4}),
        }
    def __init__(self, *args, **kwargs):
        super(ChamadoForm, self).__init__(*args, **kwargs)
        # Estilização para ficar escuro (Tailwind Style)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'bg-gray-800 border border-gray-600 text-white text-sm rounded-lg focus:ring-neonBlue focus:border-neonBlue block w-full p-2.5'
            })
        # O campo de cliente pode ser um select pesquisável no futuro, por enquanto é Select padrão
        self.fields['cliente_isp'].empty_label = "Selecione um Assinante (Opcional)"

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'w-full bg-dark border border-borderCol text-white p-3 rounded focus:border-neonBlue outline-none resize-none', 
                'rows': 3,
                'placeholder': 'Escreva uma resposta ou atualização...'
            }),
        }