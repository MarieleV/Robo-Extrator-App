import threading
import customtkinter as ctk
from tkinter import messagebox
from src.automacao import executar_robo_completo
from src.agendador import agendador_global

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppRobo(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Robô Águas de Joinville - Extrator")
        self.geometry("450x650")
        self.resizable(False, False)

        # --- Título ---
        self.label_titulo = ctk.CTkLabel(self, text="Configuração do Robô", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_titulo.pack(pady=(20, 10))

        # --- Bloco: Credenciais Sansys ---
        self.frame_sansys = ctk.CTkFrame(self)
        self.frame_sansys.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.frame_sansys, text="Credenciais Sansys", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.entrada_user_san = ctk.CTkEntry(self.frame_sansys, placeholder_text="Usuário (ex: joao.silva)")
        self.entrada_user_san.pack(pady=5, padx=20, fill="x")
        
        self.entrada_senha_san = ctk.CTkEntry(self.frame_sansys, placeholder_text="Senha Sansys", show="*")
        self.entrada_senha_san.pack(pady=(5, 15), padx=20, fill="x")

        # --- Bloco: Credenciais SharePoint ---
        self.frame_sp = ctk.CTkFrame(self)
        self.frame_sp.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.frame_sp, text="Credenciais SharePoint", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.entrada_email_sp = ctk.CTkEntry(self.frame_sp, placeholder_text="E-mail corporativo")
        self.entrada_email_sp.pack(pady=5, padx=20, fill="x")
        
        self.entrada_senha_sp = ctk.CTkEntry(self.frame_sp, placeholder_text="Senha SharePoint", show="*")
        self.entrada_senha_sp.pack(pady=(5, 15), padx=20, fill="x")

        # --- Configurações de Execução ---
        self.switch_invisivel = ctk.CTkSwitch(self, text="Rodar no modo invisível (Recomendado)")
        self.switch_invisivel.select() # Vem marcado por padrão
        self.switch_invisivel.pack(pady=10)

        # --- Agendamento ---
        self.frame_agenda = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_agenda.pack(pady=5)
        
        self.switch_agendar = ctk.CTkSwitch(self.frame_agenda, text="Agendar Diariamente às:", command=self.alternar_modo_agendamento)
        self.switch_agendar.pack(side="left", padx=5)
        
        self.entrada_horario = ctk.CTkEntry(self.frame_agenda, width=60, placeholder_text="08:00")
        self.entrada_horario.insert(0, "08:00")
        self.entrada_horario.configure(state="disabled") # Bloqueado até ligar a chave
        self.entrada_horario.pack(side="left", padx=5)

        # --- Botão Ação ---
        self.btn_executar = ctk.CTkButton(self, text="▶ Executar Agora", height=40, command=self.iniciar_processo)
        self.btn_executar.pack(pady=20)

        # --- Status ---
        self.label_status = ctk.CTkLabel(self, text="Status: Aguardando...", text_color="gray")
        self.label_status.pack(side="bottom", pady=10)

    def alternar_modo_agendamento(self):
        """Muda a cara do botão dependendo se o agendamento está ligado ou não."""
        if self.switch_agendar.get() == 1:
            self.entrada_horario.configure(state="normal")
            self.btn_executar.configure(text="🕒 Ativar Agendamento", fg_color="#2FA572", hover_color="#106A43")
        else:
            self.entrada_horario.configure(state="disabled")
            self.btn_executar.configure(text="▶ Executar Agora", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#325882", "#14375e"])
            agendador_global.parar_agendamento()
            self.atualizar_status("Agendamento cancelado.")

    def iniciar_processo(self):
        """Coleta os dados e decide se roda agora ou agenda."""
        user_san = self.entrada_user_san.get().strip()
        senha_san = self.entrada_senha_san.get().strip()
        email_sp = self.entrada_email_sp.get().strip()
        senha_sp = self.entrada_senha_sp.get().strip()
        invisivel = self.switch_invisivel.get() == 1

        if not all([user_san, senha_san, email_sp, senha_sp]):
            messagebox.showwarning("Aviso", "Por favor, preencha todos os campos de usuário e senha.")
            return

        # Modo Agendamento
        if self.switch_agendar.get() == 1:
            horario = self.entrada_horario.get().strip()
            if len(horario) != 5 or ":" not in horario:
                messagebox.showerror("Erro", "Formato de hora inválido. Use HH:MM (ex: 08:30).")
                return
            
            agendador_global.iniciar_agendamento(horario, user_san, senha_san, email_sp, senha_sp, invisivel)
            self.atualizar_status(f"Robô armado para rodar às {horario} diariamente.")
            messagebox.showinfo("Agendado", f"O robô vai rodar todo dia às {horario}.\nMantenha este aplicativo aberto/minimizado.")
        
        # Modo Executar Agora
        else:
            self.atualizar_status("Executando robô... Aguarde.")
            self.btn_executar.configure(state="disabled") # Bloqueia o botão para não clicar 2x
            
            # Roda a automação numa thread separada para a tela não congelar
            thread_robo = threading.Thread(
                target=self._rodar_automacao_thread, 
                args=(user_san, senha_san, email_sp, senha_sp, invisivel),
                daemon=True
            )
            thread_robo.start()

    def _rodar_automacao_thread(self, user_san, senha_san, email_sp, senha_sp, invisivel):
        """Função que roda nos bastidores enquanto a tela fica livre."""
        sucesso, mensagem = executar_robo_completo(user_san, senha_san, email_sp, senha_sp, invisivel)
        
        # Como o tkinter não gosta que outras threads mexam na tela, 
        # agendamos a atualização da UI para a thread principal (after)
        if sucesso:
            self.after(0, lambda: self.atualizar_status("✅ Sucesso! Última execução finalizada."))
            self.after(0, lambda: messagebox.showinfo("Sucesso", mensagem))
        else:
            self.after(0, lambda: self.atualizar_status("❌ Erro na última execução."))
            self.after(0, lambda: messagebox.showerror("Erro", mensagem))
            
        self.after(0, lambda: self.btn_executar.configure(state="normal"))

    def atualizar_status(self, texto):
        self.label_status.configure(text=f"Status: {texto}")

def iniciar_app():
    app = AppRobo()
    app.mainloop()

if __name__ == "__main__":
    iniciar_app()