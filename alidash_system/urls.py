from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Importamos as views de autenticação

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rota de Login Personalizada
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    
    # Rota de Logout (Simples)
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', include('core.urls')),
    path('devices/', include('devices.urls')),
]