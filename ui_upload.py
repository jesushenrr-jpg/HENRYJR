"""
ui_upload.py — Aba de acompanhamento de upload em batch.

Botão "Enviar pacote" dispara staging.enviar_tudo() em thread separada.
Barra de progresso e tabela atualizadas em tempo real via after().
"""
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from datetime import datetime

import staging

BG      = "#0E0D0B"
CARD    = "#161411"
SURFACE = "#1E1B17"
FG      = "#F2EDE4"
FG2     = "#A89880"
ACC     = "#D4A853"
DANGER  = "#f38ba8"
OK      = "#a6e3a1"
WARN    = "#fab387"


class UploadFrame(ttk.Frame):
    def __init__(self, master, on_staging_change: Callable | None = None, **kw):
        super().__init__(master, **kw)
        self._on_staging_change = on_staging_change
        self._historico: list[dict] = []   # {desc, ok, ts}
        self._enviando = False
        self._build_ui()

    def _build_ui(self):
        self.configure(padding=0)

        # ── Cabeçalho escuro ──────────────────────────────────────────────────
        header = tk.Frame(self, bg=CARD)
        header.pack(fill="x")

        inner_h = tk.Frame(header, bg=CARD)
        inner_h.pack(fill="x", padx=16, pady=10)

        # Título + subtítulo
        title_col = tk.Frame(inner_h, bg=CARD)
        title_col.pack(side="left", fill="y")
        tk.Label(title_col, text="UPLOAD", bg=CARD, fg=ACC,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self._lbl_pendentes = tk.Label(
            title_col, text="Nenhuma alteração pendente",
            bg=CARD, fg=FG2, font=("Segoe UI", 8))
        self._lbl_pendentes.pack(anchor="w")

        # Botões à direita
        btn_col = tk.Frame(inner_h, bg=CARD)
        btn_col.pack(side="right")

        self._btn_relatorio = tk.Button(
            btn_col, text="📊 Relatório", bg=SURFACE, fg=FG2, relief="flat",
            cursor="hand2", font=("Segoe UI", 9), padx=10, pady=5,
            activebackground=SURFACE, activeforeground=FG,
            command=self._ver_relatorio)
        self._btn_relatorio.pack(side="left", padx=(0, 6))

        self._btn_enviar = tk.Button(
            btn_col, text="📤  Enviar pacote", bg=ACC, fg="#0E0D0B", relief="flat",
            cursor="hand2", font=("Segoe UI", 10, "bold"), padx=14, pady=5,
            activebackground="#B8882A", activeforeground="#0E0D0B",
            command=self._iniciar_upload)
        self._btn_enviar.pack(side="left")

        # Linha divisória
        tk.Frame(self, bg="#2C2820", height=1).pack(fill="x")

        # ── Área de conteúdo ──────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Barra de progresso + label ────────────────────────────────────────
        prog_row = tk.Frame(body, bg=BG)
        prog_row.pack(fill="x", pady=(0, 4))

        self._lbl_prog = tk.Label(prog_row, text="", bg=BG, fg=FG2,
                                   font=("Segoe UI", 8))
        self._lbl_prog.pack(side="right")

        self._progress = ttk.Progressbar(body, mode="determinate", maximum=100)
        self._progress.pack(fill="x", pady=(0, 12))

        # ── Tabela de histórico ───────────────────────────────────────────────
        tree_frame = tk.Frame(body, bg=CARD, bd=0)
        tree_frame.pack(fill="both", expand=True)

        cols = ("status", "item", "horario")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                   height=18, selectmode="browse")
        self._tree.heading("status",  text="")
        self._tree.heading("item",    text="Item")
        self._tree.heading("horario", text="Horário")
        self._tree.column("status",  width=32,  anchor="center", stretch=False)
        self._tree.column("item",    width=460, anchor="w")
        self._tree.column("horario", width=80,  anchor="center", stretch=False)

        # Tags de cor para linhas ok / erro
        self._tree.tag_configure("ok",  foreground=OK)
        self._tree.tag_configure("err", foreground=DANGER)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

    def atualizar_pendentes(self):
        """Chamado pelo corretor.py para atualizar o resumo de pendentes."""
        p = staging.listar_pendentes()
        partes = []
        if p["questoes"]: partes.append(f"{p['questoes']} questão(ões)")
        if p["imagens"]:  partes.append(f"{p['imagens']} imagem(ns)")
        if p["frases"]:   partes.append(f"{p['frases']} frase(s)")
        if partes:
            self._lbl_pendentes.config(
                text="Pendentes: " + " · ".join(partes), fg=WARN)
        else:
            self._lbl_pendentes.config(text="Nenhuma alteração pendente", fg=FG2)

    def _iniciar_upload(self):
        if self._enviando:
            return
        total = staging.total_pendentes()
        if total == 0:
            messagebox.showinfo("Upload", "Nenhuma alteração pendente.")
            return
        self._enviando = True
        self._btn_enviar.config(state="disabled")
        self._progress["value"] = 0
        self._progress["maximum"] = total
        self._n_enviados = 0

        threading.Thread(
            target=self._thread_upload,
            daemon=True,
        ).start()

    def _thread_upload(self):
        def _cb(desc: str, ok: bool):
            self.after(0, lambda d=desc, o=ok: self._on_item_enviado(d, o))

        staging.enviar_tudo(callback=_cb)
        self.after(0, self._upload_concluido)

    def _on_item_enviado(self, desc: str, ok: bool):
        self._n_enviados += 1
        self._progress["value"] = self._n_enviados
        icone = "✔" if ok else "✗"
        tag   = "ok" if ok else "err"
        ts = datetime.now().strftime("%H:%M:%S")
        self._tree.insert("", 0, values=(icone, desc, ts), tags=(tag,))
        self._historico.append({"desc": desc, "ok": ok, "ts": ts})
        total = int(self._progress["maximum"])
        self._lbl_prog.config(
            text=f"{self._n_enviados} / {total} itens enviados")

    def _upload_concluido(self):
        self._enviando = False
        self._btn_enviar.config(state="normal")
        ok_n  = sum(1 for h in self._historico if h["ok"])
        err_n = sum(1 for h in self._historico if not h["ok"])
        self._lbl_prog.config(
            text=f"Concluído — ✔ {ok_n} enviados  ✗ {err_n} erros")
        self.atualizar_pendentes()
        if self._on_staging_change:
            self._on_staging_change()

    def _ver_relatorio(self):
        if not self._historico:
            messagebox.showinfo("Relatório", "Nenhum upload realizado nesta sessão.")
            return
        ok_q = sum(1 for h in self._historico if h["ok"] and "Q" in h["desc"])
        er_q = sum(1 for h in self._historico if not h["ok"] and "Q" in h["desc"])
        ok_i = sum(1 for h in self._historico if h["ok"] and "img" in h["desc"])
        er_i = sum(1 for h in self._historico if not h["ok"] and "img" in h["desc"])
        ok_f = sum(1 for h in self._historico if h["ok"] and "frase" in h["desc"])
        er_f = sum(1 for h in self._historico if not h["ok"] and "frase" in h["desc"])
        ts_ultimo = self._historico[-1]["ts"] if self._historico else "—"

        msg = (
            f"📊 RELATÓRIO DA SESSÃO\n"
            f"{'─'*35}\n"
            f"Questões:  ✅ {ok_q}  ❌ {er_q}\n"
            f"Imagens:   ✅ {ok_i}  ❌ {er_i}\n"
            f"Frases:    ✅ {ok_f}  ❌ {er_f}\n"
            f"{'─'*35}\n"
            f"Total:     ✅ {ok_q+ok_i+ok_f}  ❌ {er_q+er_i+er_f}\n"
            f"Último:    {ts_ultimo}"
        )
        messagebox.showinfo("Relatório de Upload", msg)
