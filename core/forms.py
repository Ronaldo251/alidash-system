from django import forms
from django.contrib.auth.models import User
from .models import Agente, Chamado, Comentario, DEPARTAMENTO_CHOICES

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

        agente = super().save(commit=False)
        agente.user = user
        if commit:
            agente.save()
        return agente
class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['titulo', 'prioridade', 'descricao','departamento']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full bg-dark border border-borderCol text-white p-2 rounded focus:border-neonBlue outline-none'}),
            'departamento': forms.Select(attrs={'class': 'w-full bg-dark border border-borderCol text-white p-2 rounded focus:border-neonBlue outline-none'}),
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