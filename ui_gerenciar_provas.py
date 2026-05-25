"""
ui_gerenciar_provas.py — Janela Configurações → Gerenciar Provas.

Permite renomear subfiltros (evento, turno, dia) e adicionar novas categorias.
Operações de rename vão para o staging via data_layer diretamente
(UPDATE em batch — não passa pelo staging de questões individuais).
"""
import tkinter as tk
from tkinter import ttk, messagebox

import data_layer as dl

BG      = "#0E0D0B"
CARD    = "#161411"
SURFACE = "#1E1B17"
FG      = "#F2EDE4"
FG2     = "#A89880"
ACC     = "#D4A853"
DANGER  = "#f38ba8"
OK      = "#a6e3a1"


class JanelaGerenciarProvas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gerenciar Provas")
        self.geometry("640x480")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build_ui()
        self._carregar()

    def _build_ui(self):
        # ── Título ────────────────────────────────────────────────────────────
        tk.Label(self, text="GERENCIAR PROVAS E CATEGORIAS",
                 bg=BG, fg=ACC, font=("Segoe UI", 11, "bold")).pack(
                 fill="x", padx=14, pady=(12, 6))

        # ── Árvore de categorias/subfiltros ───────────────────────────────────
        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        cols = ("categoria", "campo", "valor", "questoes")
        self._tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        self._tree.heading("categoria", text="Categoria")
        self._tree.heading("campo",     text="Campo")
        self._tree.heading("valor",     text="Valor atual")
        self._tree.heading("questoes",  text="Questões")
        self._tree.column("categoria", width=100)
        self._tree.column("campo",     width=100)
        self._tree.column("valor",     width=220)
        self._tree.column("questoes",  width=80, anchor="center")

        sb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        # ── Botões ────────────────────────────────────────────────────────────
        bot = tk.Frame(self, bg=BG)
        bot.pack(fill="x", padx=14, pady=8)

        tk.Button(bot, text="✏ Renomear selecionado", bg=SURFACE, fg=FG,
                  relief="flat", cursor="hand2",
                  command=self._renomear).pack(side="left", padx=(0, 6))
        tk.Button(bot, text="↻ Atualizar", bg=SURFACE, fg=FG,
                  relief="flat", cursor="hand2",
                  command=self._carregar).pack(side="left")

        self._lbl_status = tk.Label(bot, text="", bg=BG, fg=FG2,
                                    font=("Segoe UI", 8))
        self._lbl_status.pack(side="right")

    def _carregar(self):
        for row in self._tree.get_children():
            self._tree.delete(row)

        categorias = dl.listar_categorias()
        for cat in categorias:
            filtros = dl.listar_filtros(cat)
            if cat == "ENEM":
                for ano in filtros.get("anos", []):
                    n = dl.contar_questoes_por_subfiltro(cat, "ano", str(ano))
                    self._tree.insert("", "end", values=(cat, "ano", ano, n))
            else:
                for ev in filtros.get("eventos", []):
                    n = dl.contar_questoes_por_subfiltro(cat, "evento", ev)
                    self._tree.insert("", "end", values=(cat, "evento", ev, n))
                for tu in filtros.get("turnos", []):
                    n = dl.contar_questoes_por_subfiltro(cat, "turno", tu)
                    self._tree.insert("", "end", values=(cat, "turno", tu, n))

        self._lbl_status.config(text=f"{len(categorias)} categoria(s) carregada(s)", fg=FG2)

    def _renomear(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um item para renomear.")
            return
        vals = self._tree.item(sel[0], "values")
        cat, campo, valor_atual, n_questoes = vals

        jan = tk.Toplevel(self)
        jan.title("Renomear")
        jan.configure(bg=BG)
        jan.geometry("380x160")
        jan.resizable(False, False)

        tk.Label(jan, text=f"Renomear '{valor_atual}' ({n_questoes} questões)",
                 bg=BG, fg=FG, font=("Segoe UI", 10)).pack(padx=14, pady=(14, 6))
        ent = tk.Entry(jan, bg=SURFACE, fg=FG, insertbackground=FG,
                       relief="flat", font=("Segoe UI", 11))
        ent.insert(0, valor_atual)
        ent.pack(fill="x", padx=14, ipady=5)

        def _confirmar():
            novo = ent.get().strip()
            if not novo or novo == valor_atual:
                jan.destroy()
                return
            if not messagebox.askyesno(
                "Confirmar",
                f"Isso atualizará {n_questoes} questão(ões) no banco.\n"
                f"'{valor_atual}' → '{novo}'\n\nContinuar?",
                parent=jan,
            ):
                return
            ok, msg, n = dl.renomear_subfiltro(cat, campo, valor_atual, novo)
            if ok:
                self._lbl_status.config(text=f"✓ {msg} ({n} atualizadas)", fg=OK)
                jan.destroy()
                self._carregar()
            else:
                self._lbl_status.config(text=f"❌ {msg}", fg=DANGER)
                jan.destroy()

        tk.Button(jan, text="Confirmar", bg=ACC, fg="#0E0D0B", relief="flat",
                  cursor="hand2", font=("Segoe UI", 10, "bold"),
                  command=_confirmar).pack(pady=10)

    def _nova_categoria(self):
        messagebox.showinfo(
            "Nova categoria",
            "Para adicionar uma nova categoria, insira questões com\n"
            "fonte='NOVA_CATEGORIA' via script de importação.\n"
            "A categoria aparecerá automaticamente aqui.",
        )
