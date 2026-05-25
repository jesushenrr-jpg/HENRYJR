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
        self.configure(padding=12)

        # ── Topo: botões ──────────────────────────────────────────────────────
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="FRASES", bg=BG, fg=ACC,
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Button(top, text="↻ Atualizar", bg=SURFACE, fg=FG, relief="flat",
                  cursor="hand2", command=self._carregar).pack(side="right", padx=4)
        tk.Button(top, text="🗑 Deletar", bg=SURFACE, fg=DANGER, relief="flat",
                  cursor="hand2", command=self._deletar).pack(side="right", padx=4)
        tk.Button(top, text="💾 Salvar", bg=ACC, fg="#0E0D0B", relief="flat",
                  cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=self._salvar).pack(side="right", padx=4)
        tk.Button(top, text="+ Nova", bg=SURFACE, fg=FG, relief="flat",
                  cursor="hand2", command=self._nova).pack(side="right", padx=4)

        # ── Lista à esquerda ──────────────────────────────────────────────────
        pane = tk.Frame(self, bg=BG)
        pane.pack(fill="both", expand=True)

        lista_frame = tk.Frame(pane, bg=CARD, bd=1, relief="flat")
        lista_frame.pack(side="left", fill="y", padx=(0, 8))

        sb = tk.Scrollbar(lista_frame, orient="vertical")
        self._lista = tk.Listbox(
            lista_frame, yscrollcommand=sb.set, width=32,
            bg=CARD, fg=FG, selectbackground=ACC, selectforeground="#0E0D0B",
            activestyle="none", borderwidth=0, highlightthickness=0,
            font=("Segoe UI", 9),
        )
        sb.config(command=self._lista.yview)
        sb.pack(side="right", fill="y")
        self._lista.pack(side="left", fill="both", expand=True)
        self._lista.bind("<<ListboxSelect>>", self._ao_selecionar)

        # ── Editor à direita ──────────────────────────────────────────────────
        editor = tk.Frame(pane, bg=BG)
        editor.pack(side="left", fill="both", expand=True)

        def lbl(texto):
            tk.Label(editor, text=texto, bg=BG, fg=FG2,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(6, 1))

        lbl("TÍTULO")
        self._ent_titulo = tk.Entry(editor, bg=SURFACE, fg=FG, insertbackground=FG,
                                    relief="flat", font=("Segoe UI", 10))
        self._ent_titulo.pack(fill="x", ipady=4)

        lbl("CATEGORIA")
        self._ent_cat = tk.Entry(editor, bg=SURFACE, fg=FG, insertbackground=FG,
                                  relief="flat", font=("Segoe UI", 10))
        self._ent_cat.pack(fill="x", ipady=4)

        lbl("TEXTO")
        self._txt = tk.Text(editor, bg=SURFACE, fg=FG, insertbackground=FG,
                             relief="flat", font=("Source Serif 4", 11),
                             wrap="word", height=12)
        self._txt.pack(fill="both", expand=True)

        self._lbl_status = tk.Label(editor, text="", bg=BG, fg=FG2,
                                    font=("Segoe UI", 8), anchor="w")
        self._lbl_status.pack(fill="x", pady=(4, 0))

        self._frase_id: int | None = None  # id da frase em edição (None = nova)

    def _carregar(self):
        self._frases_cache = dl.listar_frases()
        self._lista.delete(0, "end")
        for f in self._frases_cache:
            self._lista.insert("end", f.get("titulo", "—"))
        self._lbl_status.config(text=f"{len(self._frases_cache)} frases carregadas", fg=FG2)

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
