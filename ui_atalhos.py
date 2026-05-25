"""
ui_atalhos.py — Aba de referência de atalhos de teclado.
"""
import tkinter as tk
from tkinter import ttk

BG      = "#0E0D0B"
CARD    = "#161411"
BORDER  = "#2C2820"
SURFACE = "#1E1B17"
FG      = "#F2EDE4"
FG2     = "#A89880"
ACC     = "#D4A853"

# ── Definição dos atalhos ─────────────────────────────────────────────────────

SECOES = [
    ("Navegação entre questões", [
        ("←  /  →",            "Questão anterior / próxima"),
        ("↑  /  ↓",            "Questão anterior / próxima (alternativo)"),
        ("Campo  Nº  + Enter", "Ir direto para o número digitado"),
    ]),
    ("Edição e salvamento", [
        ("Ctrl + S",           "Salvar enunciado + alternativas (staging)"),
        ("Tab",                "Próximo campo editável  (Enunciado → Comando → A → B → … → Gabarito)"),
        ("Shift + Tab",        "Campo editável anterior"),
    ]),
    ("Fórmulas LaTeX", [
        ("Ctrl + M",           "Abrir janela de inserção de fórmula LaTeX"),
        ("Ctrl + Enter",       "Abrir janela de inserção de fórmula LaTeX (alternativo)"),
    ]),
    ("Formatação de texto", [
        ("Ctrl + Shift + +",   "Sobrescrito  (ex: x²  →  x$^{2}$)"),
        ("Ctrl + _",           "Subscrito    (ex: H₂  →  H$_{2}$)"),
    ]),
    ("Upload", [
        ("(botão) Enviar pacote", "Envia todas as alterações em staging para o Supabase"),
    ]),
    ("Dicas gerais", [
        ("Salvar ≠ Enviar",    "Salvar registra localmente no staging; Enviar sobe para o banco"),
        ("Scroll central",     "Role a roda do mouse sobre o painel central para ver todos os campos"),
        ("Cache de questões",  "Questões já abertas ficam em memória; navegar de volta é instantâneo"),
    ]),
]


class AtalhoFrame(ttk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.configure(style="Dark.TFrame")
        self._build_ui()

    def _build_ui(self):
        # ── Cabeçalho ──────────────────────────────────────────────────────
        header = tk.Frame(self, bg=CARD)
        header.pack(fill="x")
        inner_h = tk.Frame(header, bg=CARD)
        inner_h.pack(fill="x", padx=16, pady=10)

        tk.Label(inner_h, text="ATALHOS", bg=CARD, fg=ACC,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        tk.Label(inner_h, text="  Referência rápida de teclado",
                 bg=CARD, fg=FG2, font=("Segoe UI", 9)).pack(side="left")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Área com scroll ────────────────────────────────────────────────
        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="both", expand=True)

        sc = ttk.Scrollbar(wrap, orient="vertical")
        sc.pack(side="right", fill="y")
        canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0,
                           yscrollcommand=sc.set)
        canvas.pack(side="left", fill="both", expand=True)
        sc.config(command=canvas.yview)

        body = tk.Frame(canvas, bg=BG)
        win  = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_body_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_cfg(e):
            canvas.itemconfig(win, width=e.width)
        def _on_scroll(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        body.bind("<Configure>", _on_body_cfg)
        canvas.bind("<Configure>", _on_canvas_cfg)
        canvas.bind("<MouseWheel>", _on_scroll)
        body.bind("<MouseWheel>", _on_scroll)

        # ── Seções de atalhos ──────────────────────────────────────────────
        for titulo, atalhos in SECOES:
            sec = tk.Frame(body, bg=BG)
            sec.pack(fill="x", padx=24, pady=(16, 4))

            # Título da seção
            tk.Label(sec, text=titulo.upper(), bg=BG, fg=ACC,
                     font=("Segoe UI", 8, "bold")).pack(anchor="w")
            tk.Frame(sec, bg=BORDER, height=1).pack(fill="x", pady=(2, 6))

            # Linhas de atalho
            for tecla, descricao in atalhos:
                row = tk.Frame(sec, bg=BG)
                row.pack(fill="x", pady=3)

                # Badge da tecla
                badge = tk.Label(row, text=tecla, bg=SURFACE, fg=FG,
                                 font=("Consolas", 9, "bold"),
                                 padx=10, pady=4, relief="flat",
                                 anchor="w", width=28)
                badge.pack(side="left")

                # Separador pontilhado
                tk.Label(row, text="  →  ", bg=BG, fg=BORDER,
                         font=("Segoe UI", 9)).pack(side="left")

                # Descrição
                tk.Label(row, text=descricao, bg=BG, fg=FG2,
                         font=("Segoe UI", 9), anchor="w",
                         justify="left").pack(side="left", fill="x", expand=True)

                row.bind("<MouseWheel>", _on_scroll)
                badge.bind("<MouseWheel>", _on_scroll)

        # Padding no final
        tk.Frame(body, bg=BG, height=24).pack()
