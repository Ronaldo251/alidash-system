# devices/services.py
import routeros_api

class MikrotikService:
    def __init__(self, concentrador):
        self.connection = routeros_api.RouterOsApiPool(
            concentrador.ip_address,
            username=concentrador.api_user,
            password=concentrador.api_password,
            port=concentrador.api_port,
            plaintext_login=True
        )
        self.api = self.connection.get_api()

    def bloquear_cliente(self, pppoe_user):
        """
        Desabilita o segredo PPPoE do cliente e derruba a conexão ativa
        """
        # 1. Achar o cadastro do cliente no Mikrotik
        secrets = self.api.get_resource('/ppp/secret')
        user = secrets.get(name=pppoe_user)
        
        if user:
            # Opção A: Desabilitar o login
            secrets.set(id=user[0]['id'], disabled='yes')
            
            # Opção B (Melhor): Mudar perfil para 'bloqueio' (Redireciona para aviso)
            # secrets.set(id=user[0]['id'], profile='profile_bloqueio')
            
            # 2. Derrubar a conexão ativa para forçar o bloqueio imediato
            active_connections = self.api.get_resource('/ppp/active')
            active = active_connections.get(name=pppoe_user)
            if active:
                active_connections.remove(id=active[0]['id'])
                
            return True
        return False

    def liberar_cliente(self, pppoe_user):
        """Reabilita o cliente"""
        secrets = self.api.get_resource('/ppp/secret')
        user = secrets.get(name=pppoe_user)
        
        if user:
            secrets.set(id=user[0]['id'], disabled='no') # ou profile='default'
            return True
        return False
        
    def obter_status_conexao(self, pppoe_user):
        """Pega IP atual, Uptime e MAC Address"""
        active_connections = self.api.get_resource('/ppp/active')
        active = active_connections.get(name=pppoe_user)
        
        if active:
            dados = active[0]
            return {
                'ip': dados.get('address'),
                'uptime': dados.get('uptime'),
                'mac': dados.get('caller-id'),
                'online': True
            }
        return {'online': False}