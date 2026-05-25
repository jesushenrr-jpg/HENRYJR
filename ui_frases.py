"""
ui_frases.py — Aba de gerenciamento de frases livres.

Frases são independentes de prova: cada uma tem titulo, texto e categoria livre.
Ao salvar, registra no staging (não sobe imediatamente ao Supabase).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

import data_layer as dl
import staging

# ── Paleta ────────────────────────────────────────────────────────────────────
BG      = "#0E0D0B"
CARD    = "#161411"
BORDER  = "#2C2820"
SURFACE = "#1E1B17"
FG      = "#F2EDE4"
FG2     = "#A89880"
ACC     = "#D4A853"
ACC_HOV = "#B8882A"
DANGER  = "#f38ba8"
OK      = "#a6e3a1"


class FrasesFrame(ttk.Frame):
    def __init__(self, master, on_staging_change: Callable | None = None, **kw):
        super().__init__(master, **kw)
        self.configure(style="Dark.TFrame")
        self._on_staging_change = on_staging_change
        self._frases_cache: list[dict] = []
        self._sel_idx: int | None = None
        self._build_ui()
        self._carregar()

    def _build_ui(self):
        self.configure(padding=0)

        # ── Cabeçalho ──────────────────────────────────────────────────────
        header = tk.Frame(self, bg=CARD)
        header.pack(fill="x")

        inner_h = tk.Frame(header, bg=CARD)
        inner_h.pack(fill="x", padx=16, pady=10)

        tk.Label(inner_h, text="FRASES", bg=CARD, fg=ACC,
                 font=("Segoe UI", 12, "bold")).pack(side="left")

        # Botões à direita (ordem inversa do pack side=right)
        tk.Button(inner_h, text="↻ Atualizar", bg=SURFACE, fg=FG2, relief="flat",
                  cursor="hand2", font=("Segoe UI", 9), padx=10, pady=5,
                  activebackground=SURFACE, activeforeground=FG,
                  command=self._carregar).pack(side="right", padx=(4, 0))
        tk.Button(inner_h, text="🗑 Deletar", bg=SURFACE, fg=DANGER, relief="flat",
                  cursor="hand2", font=("Segoe UI", 9), padx=10, pady=5,
                  activebackground=SURFACE, activeforeground=DANGER,
                  command=self._deletar).pack(side="right", padx=4)
        tk.Button(inner_h, text="💾 Salvar", bg=ACC, fg="#0E0D0B", relief="flat",
                  cursor="hand2", font=("Segoe UI", 10, "bold"), padx=14, pady=5,
                  activebackground=ACC_HOV, activeforeground="#0E0D0B",
                  command=self._salvar).pack(side="right", padx=4)
        tk.Button(inner_h, text="+ Nova frase", bg=SURFACE, fg=FG, relief="flat",
                  cursor="hand2", font=("Segoe UI", 9), padx=10, pady=5,
                  activebackground=SURFACE, activeforeground=ACC,
                  command=self._nova).pack(side="right", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Corpo: lista + editor ──────────────────────────────────────────────
        pane = tk.Frame(self, bg=BG)
        pane.pack(fill="both", expand=True)

        # ── Lista à esquerda ──────────────────────────────────────────────────
        lista_wrap = tk.Frame(pane, bg=CARD, width=240)
        lista_wrap.pack(side="left", fill="y")
        lista_wrap.pack_propagate(False)

        tk.Label(lista_wrap, text="FRASES CADASTRADAS", bg=CARD, fg=FG2,
                 font=("Segoe UI", 7, "bold")).pack(fill="x", padx=10, pady=(8, 2))

        tk.Frame(lista_wrap, bg=BORDER, height=1).pack(fill="x", padx=10)

        sb_lista = tk.Scrollbar(lista_wrap, orient="vertical", bg=CARD,
                                 troughcolor=CARD, relief="flat", bd=0)
        self._lista = tk.Listbox(
            lista_wrap, yscrollcommand=sb_lista.set, width=28,
            bg=CARD, fg=FG, selectbackground=ACC, selectforeground="#0E0D0B",
            activestyle="none", borderwidth=0, highlightthickness=0,
            font=("Segoe UI", 9),
        )
        sb_lista.config(command=self._lista.yview)
        sb_lista.pack(side="right", fill="y")
        self._lista.pack(side="left", fill="both", expand=True, padx=(0, 0))
        self._lista.bind("<<ListboxSelect>>", self._ao_selecionar)

        # Separador vertical
        tk.Frame(pane, bg=BORDER, width=1).pack(side="left", fill="y")

        # ── Editor à direita ──────────────────────────────────────────────────
        editor = tk.Frame(pane, bg=BG)
        editor.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        def lbl(texto):
            tk.Label(editor, text=texto, bg=BG, fg=FG2,
                     font=("Segoe UI", 7, "bold"), anchor="w").pack(fill="x", pady=(8, 2))

        lbl("TÍTULO")
        self._ent_titulo = tk.Entry(editor, bg=SURFACE, fg=FG, insertbackground=FG,
                                    relief="flat", font=("Segoe UI", 10),
                                    highlightthickness=1,
                                    highlightbackground=BORDER,
                                    highlightcolor=ACC)
        self._ent_titulo.pack(fill="x", ipady=5)

        lbl("CATEGORIA")
        self._ent_cat = tk.Entry(editor, bg=SURFACE, fg=FG, insertbackground=FG,
                                  relief="flat", font=("Segoe UI", 10),
                                  highlightthickness=1,
                                  highlightbackground=BORDER,
                                  highlightcolor=ACC)
        self._ent_cat.pack(fill="x", ipady=5)

        lbl("TEXTO")
        txt_wrap = tk.Frame(editor, bg=BORDER, bd=1)
        txt_wrap.pack(fill="both", expand=True, pady=(0, 0))
        self._txt = tk.Text(txt_wrap, bg=SURFACE, fg=FG, insertbackground=FG,
                             relief="flat", font=("Source Serif 4", 11),
                             wrap="word", height=12,
                             padx=8, pady=8,
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             highlightcolor=ACC)
        self._txt.pack(fill="both", expand=True)

        # Barra de status colorida
        self._lbl_status = tk.Label(editor, text="", bg=BG, fg=FG2,
                                    font=("Segoe UI", 8), anchor="w")
        self._lbl_status.pack(fill="x", pady=(6, 0))

        self._frase_id: int | None = None  # id da frase em edição (None = nova)

    def _carregar(self):
        self._frases_cache = dl.listar_frases()
        self._lista.delete(0, "end")
        for f in self._frases_cache:
            self._lista.insert("end", f"  {f.get('titulo', '—')}")
        n = len(self._frases_cache)
        self._lbl_status.config(
            text=f"{'◆' if n else '○'}  {n} frase{'s' if n != 1 else ''} carregada{'s' if n != 1 else ''}",
            fg=FG2)

    def _ao_selecionar(self, _=None):
        sel = self._lista.curselection()
        if not sel:
            return
        self._sel_idx = sel[0]
        f = self._frases_cache[self._sel_idx]
        self._frase_id = f.get("id")
        self._ent_titulo.delete(0, "end")
        self._ent_titulo.insert(0, f.get("titulo", ""))
        self._ent_cat.delete(0, "end")
        self._ent_cat.insert(0, f.get("categoria", ""))
        self._txt.delete("1.0", "end")
        self._txt.insert("1.0", f.get("texto", ""))

    def _nova(self):
        self._frase_id = None
        self._sel_idx = None
        self._lista.selection_clear(0, "end")
        self._ent_titulo.delete(0, "end")
        self._ent_cat.delete(0, "end")
        self._txt.delete("1.0", "end")
        self._ent_titulo.focus()

    def _salvar(self):
        titulo = self._ent_titulo.get().strip()
        texto  = self._txt.get("1.0", "end").strip()
        cat    = self._ent_cat.get().strip()
        if not titulo or not texto:
            messagebox.showwarning("Atenção", "Título e Texto são obrigatórios.")
            return
        dados: dict = {"titulo": titulo, "texto": texto, "categoria": cat}
        if self._frase_id is not None:
            dados["id"] = self._frase_id
        staging.registrar_frase(dados)
        self._lbl_status.config(text="✓ Frase registrada no staging", fg=OK)
        if self._on_staging_change:
            self._on_staging_change()

    def _deletar(self):
        if self._frase_id is None:
            messagebox.showwarning("Atenção", "Selecione uma frase existente para deletar.")
            return
        if not messagebox.askyesno("Confirmar", "Deletar esta frase do Supabase agora?"):
            return
        ok, msg = dl.deletar_frase(self._frase_id)
        if ok:
            self._lbl_status.config(text="Frase deletada", fg=OK)
            self._nova()
            self._carregar()
        else:
            self._lbl_status.config(text=f"Erro: {msg}", fg=DANGER)
