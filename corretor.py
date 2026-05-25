"""
corretor.py — Ponto de entrada do CORRETOR - HenryJr.

Monta a janela principal com Notebook de três abas:
  - Questões (editor completo)
  - Frases (gerenciamento de frases livres)
  - Upload (progresso de envio em batch)

Menu: Configurações → Gerenciar Provas
Barra global no topo: mostra pendentes em tempo real.
"""
import sys
import tkinter as tk
from tkinter import ttk, messagebox

import config as cfg
import data_layer as dl
import staging

BG      = "#0E0D0B"
CARD    = "#161411"
SURFACE = "#1E1B17"
FG      = "#F2EDE4"
FG2     = "#A89880"
ACC     = "#D4A853"
WARN    = "#fab387"


# ── Tela de configuração inicial ──────────────────────────────────────────────

class TelaConfig(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CORRETOR - HenryJr — Configuração")
        self.geometry("460x260")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._ok = False
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="CORRETOR - HenryJr", bg=BG, fg=ACC,
                 font=("Segoe UI", 16, "bold")).pack(pady=(24, 4))
        tk.Label(self, text="Configure as credenciais do Supabase para começar.",
                 bg=BG, fg=FG2, font=("Segoe UI", 9)).pack(pady=(0, 16))

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="x", padx=40)

        def lbl(t):
            tk.Label(frame, text=t, bg=BG, fg=FG2,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(6, 1))

        lbl("SUPABASE URL")
        self._ent_url = tk.Entry(frame, bg=SURFACE, fg=FG, insertbackground=FG,
                                  relief="flat", font=("Segoe UI", 10))
        self._ent_url.pack(fill="x", ipady=5)

        lbl("SUPABASE SERVICE KEY")
        self._ent_key = tk.Entry(frame, bg=SURFACE, fg=FG, insertbackground=FG,
                                  relief="flat", font=("Segoe UI", 10), show="•")
        self._ent_key.pack(fill="x", ipady=5)

        self._lbl_err = tk.Label(frame, text="", bg=BG, fg="#f38ba8",
                                  font=("Segoe UI", 8))
        self._lbl_err.pack(fill="x", pady=(4, 0))

        tk.Button(self, text="Conectar", bg=ACC, fg="#0E0D0B", relief="flat",
                  cursor="hand2", font=("Segoe UI", 11, "bold"),
                  command=self._conectar).pack(pady=14)

    def _conectar(self):
        url = self._ent_url.get().strip()
        key = self._ent_key.get().strip()
        if not url or not key:
            self._lbl_err.config(text="URL e Key são obrigatórios.")
            return
        cfg.salvar(url, key)
        dl.init()
        cats = dl.listar_categorias()
        if not cats:
            self._lbl_err.config(
                text="Conexão falhou — verifique URL e Key.")
            return
        self._ok = True
        self.destroy()


# ── Janela principal ──────────────────────────────────────────────────────────

class Corretor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CORRETOR - HenryJr")
        self.geometry("1380x840")
        self.minsize(1100, 700)
        self.configure(bg=BG)
        self._build_ui()
        self._atualizar_barra()

    def _build_ui(self):
        # ── Menu ─────────────────────────────────────────────────────────────
        menubar = tk.Menu(self, bg=BG, fg=FG, activebackground=ACC,
                          activeforeground="#0E0D0B", relief="flat")
        config_menu = tk.Menu(menubar, tearoff=0, bg=SURFACE, fg=FG,
                               activebackground=ACC, activeforeground="#0E0D0B")
        config_menu.add_command(label="Gerenciar Provas",
                                command=self._abrir_gerenciar_provas)
        config_menu.add_separator()
        config_menu.add_command(label="Reconfigurar credenciais",
                                command=self._reconfigurar)
        menubar.add_cascade(label="Configurações", menu=config_menu)
        self.config(menu=menubar)

        # ── Barra superior de status ──────────────────────────────────────────
        self._barra = tk.Frame(self, bg=CARD, height=28)
        self._barra.pack(fill="x")
        self._barra.pack_propagate(False)

        self._lbl_titulo = tk.Label(
            self._barra, text="  CORRETOR - HenryJr",
            bg=CARD, fg=ACC, font=("Segoe UI", 10, "bold"))
        self._lbl_titulo.pack(side="left", padx=4)

        self._lbl_pendentes = tk.Label(
            self._barra, text="", bg=CARD, fg=FG2, font=("Segoe UI", 9))
        self._lbl_pendentes.pack(side="right", padx=12)

        # ── Notebook ──────────────────────────────────────────────────────────
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",       background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",   background=SURFACE, foreground=FG2,
                         padding=[14, 6], font=("Segoe UI", 9))
        style.map("TNotebook.Tab",
                  background=[("selected", CARD)],
                  foreground=[("selected", ACC)])
        style.configure("Dark.TFrame",     background=BG)
        style.configure("TCombobox",
                        fieldbackground=SURFACE, background=SURFACE,
                        foreground=FG, selectbackground=ACC, arrowcolor=FG)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Importações locais (evita circular antes de terem sido definidas)
        from ui_questoes import QuestoesFrame
        from ui_frases   import FrasesFrame
        from ui_upload   import UploadFrame

        self._tab_q = QuestoesFrame(nb, on_staging_change=self._atualizar_barra,
                                     style="Dark.TFrame")
        self._tab_f = FrasesFrame(nb, on_staging_change=self._atualizar_barra,
                                   style="Dark.TFrame")
        self._tab_u = UploadFrame(nb, on_staging_change=self._atualizar_barra,
                                   style="Dark.TFrame")

        nb.add(self._tab_q, text="  Questões  ")
        nb.add(self._tab_f, text="  Frases  ")
        nb.add(self._tab_u, text="  Upload  ")

        nb.bind("<<NotebookTabChanged>>", self._ao_mudar_aba)

    def _ao_mudar_aba(self, _=None):
        self._tab_u.atualizar_pendentes()

    def _atualizar_barra(self):
        """Atualiza o texto de pendentes na barra global."""
        p = staging.listar_pendentes()
        total = p["questoes"] + p["imagens"] + p["frases"]
        if total == 0:
            self._lbl_pendentes.config(text="● 0 alterações pendentes", fg=FG2)
        else:
            partes = []
            if p["questoes"]: partes.append(f"{p['questoes']} questão(ões)")
            if p["imagens"]:  partes.append(f"{p['imagens']} imagem(ns)")
            if p["frases"]:   partes.append(f"{p['frases']} frase(s)")
            self._lbl_pendentes.config(
                text="● " + " · ".join(partes) + " pendentes", fg=WARN)

    def _abrir_gerenciar_provas(self):
        from ui_gerenciar_provas import JanelaGerenciarProvas
        JanelaGerenciarProvas(self)

    def _reconfigurar(self):
        if messagebox.askyesno("Reconfigurar",
                               "Isso encerrará o Corretor para reconfigurar as credenciais."):
            import os
            p = cfg._config_path()
            if p.exists():
                p.unlink()
            self.destroy()


# ── Inicialização ─────────────────────────────────────────────────────────────

def main():
    # Se não tem credenciais, mostrar tela de configuração
    if not cfg.credenciais_ok():
        tela = TelaConfig()
        tela.mainloop()
        if not tela._ok:
            sys.exit(0)

    # Inicializar data_layer com credenciais salvas
    if not dl.init():
        import tkinter.messagebox as mb
        mb.showerror("Erro", "Não foi possível carregar as credenciais.\n"
                             "Delete config.json e tente novamente.")
        sys.exit(1)

    app = Corretor()
    app.mainloop()


if __name__ == "__main__":
    main()
