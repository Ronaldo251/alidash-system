from django import forms
from django.contrib.auth.models import User
from .models import Agente, Chamado, Comentario

class NovoUsuarioForm(forms.ModelForm):
    # Campos extras que não estão no modelo Agente direto
    username = forms.CharField(label="Usuário (Login)", widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(label="Email", required=False, widget=forms.EmailInput(attrs={'class': 'form-input'}))
    tipo_usuario = forms.ChoiceField(
        label="Tipo de Acesso",
        choices=[('agente', 'Agente Operacional'), ('admin', 'Administrador')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Agente
        fields = ['nome', 'ramal'] # Campos do perfil Agente

    def save(self, commit=True):
        # 1. Cria o Usuário de Login (User)
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['nome'].split()[0] # Pega o primeiro nome
        )
        
        # 2. Define se é Superusuário (Admin) ou não
        tipo = self.cleaned_data['tipo_usuario']
        if tipo == 'admin':
            user.is_staff = True
            user.is_superuser = True
        user.save()

        # 3. Cria o Perfil de Agente vinculado
        agente = super().save(commit=False)
        agente.user = user
        if commit:
            agente.save()
        return agente
    
class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['titulo', 'prioridade', 'descricao']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full bg-dark border border-borderCol text-white p-2 rounded focus:border-neonBlue outline-none'}),
            'prioridade': forms.Select(attrs={'class': 'w-full bg-dark border border-borderCol text-white p-2 rounded focus:border-neonBlue outline-none'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full bg-dark border border-borderCol text-white p-2 rounded focus:border-neonBlue outline-none', 'rows': 4}),
        }

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