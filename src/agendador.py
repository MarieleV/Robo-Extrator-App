import schedule
import time
import threading
from src.automacao import executar_robo_completo

class AgendadorRobo:
    def __init__(self):
        self.agendamento_ativo = False
        self.thread_agendamento = None

    def _rotina_diaria(self, user_san, senha_san, email_sp, senha_sp, invisivel):
        """A rotina que será chamada no horário agendado."""
        print("\n[AGENDADOR] Iniciando execução agendada...")
        sucesso, mensagem = executar_robo_completo(user_san, senha_san, email_sp, senha_sp, invisivel)
        
        if sucesso:
            print("[AGENDADOR] Sucesso:", mensagem)
        else:
            print("[AGENDADOR] Erro:", mensagem)

    def _loop_verificacao(self):
        """Loop infinito que checa se já deu a hora (roda em segundo plano)."""
        while self.agendamento_ativo:
            schedule.run_pending()
            time.sleep(1) # Dorme 1 segundo para não fritar o processador

    def iniciar_agendamento(self, horario, user_san, senha_san, email_sp, senha_sp, invisivel=True):
        """Configura a tarefa e liga o loop em uma nova thread."""
        self.agendamento_ativo = True
        
        # Limpa agendamentos antigos para não rodar duplicado
        schedule.clear()
        
        # Define a regra: Todo dia no horário X, chame a rotina
        schedule.every().day.at(horario).do(
            self._rotina_diaria, user_san, senha_san, email_sp, senha_sp, invisivel
        )
        
        print(f"[AGENDADOR] Robô programado para rodar todos os dias às {horario}.")

        # Inicia a thread que fica verificando o relógio
        self.thread_agendamento = threading.Thread(target=self._loop_verificacao, daemon=True)
        self.thread_agendamento.start()

    def parar_agendamento(self):
        """Desliga o agendamento."""
        self.agendamento_ativo = False
        schedule.clear()
        print("[AGENDADOR] Agendamento cancelado.")

# Instância global para ser usada pela interface
agendador_global = AgendadorRobo()