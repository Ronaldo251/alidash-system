from django import forms
from .models import Cliente, EquipamentoCliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'cpf', 'endereco', 'pppoe_user', 'pppoe_password']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'bg-gray-700 text-white border border-gray-600 rounded p-2 w-full'}),
            'cpf': forms.TextInput(attrs={'class': 'bg-gray-700 text-white border border-gray-600 rounded p-2 w-full'}),
            'endereco': forms.TextInput(attrs={'class': 'bg-gray-700 text-white border border-gray-600 rounded p-2 w-full'}),
            'pppoe_user': forms.TextInput(attrs={'class': 'bg-gray-700 text-white border border-gray-600 rounded p-2 w-full'}),
            'pppoe_password': forms.PasswordInput(attrs={'class': 'bg-gray-700 text-white border border-gray-600 rounded p-2 w-full'}),
        }