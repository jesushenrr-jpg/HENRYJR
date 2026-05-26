"""
ui_questoes.py — Aba principal de edição de questões.

Migrado de gerenciar_imagens.py. Principais mudanças:
- App(tk.Tk) → QuestoesFrame(ttk.Frame) para uso dentro do Notebook
- Dados lidos do Supabase via data_layer (não do JSON local)
- Salvamento registra no staging (não no disco)
- Paleta atualizada para Biblioteca Cálida (dourado, sem violeta)
"""
import io
import json
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

import data_layer as dl
import staging as st

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _MATPLOTLIB_OK = True
except ImportError:
    _MATPLOTLIB_OK = False

if sys.stdout is not None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

JPEG_Q      = 92
PREVIEW_MAX = (440, 280)
THUMB_MAX   = (160, 120)
LETRAS      = ["A", "B", "C", "D", "E"]

PASTA_IMG = Path(r"C:\PROJETOS\HENRYJR\dados\imagens")


# ── Helpers de imagem ─────────────────────────────────────────────────────────
def img_path(item) -> str:
    """Extrai o path de um item de imagem (string legada ou dict novo)."""
    return item["path"] if isinstance(item, dict) else item


def img_posicao(item) -> str:
    return item.get("posicao", "") if isinstance(item, dict) else ""


def img_como_dict(item, posicao: str | None = None) -> dict:
    """Normaliza um item para dict."""
    if isinstance(item, dict):
        return item
    return {"path": item, "posicao": posicao or ""}


def proxima_idx(pasta: Path, stem: str) -> int:
    idx = 1
    while (pasta / f"{stem}_{idx}.jpg").exists():
        idx += 1
    return idx


def posicoes_para_n(n: int) -> list[tuple[str, str]]:
    """Retorna [(label, valor), ...] para N parágrafos."""
    if n == 0:
        return [("Única posição", "antes_1")]
    ops = [("Antes do §1", "antes_1")]
    for i in range(1, n):
        ops.append((f"Entre §{i} e §{i + 1}", f"entre_{i}_{i + 1}"))
    ops.append((f"Após o §{n}", "apos_ultimo"))
    return ops


# ── Mapas Unicode para sobrescrito / subscrito ────────────────────────────────
SUPER_MAP: dict[str, str] = {
    '0':'⁰','1':'¹','2':'²','3':'³','4':'⁴',
    '5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹',
    '+':'⁺','-':'⁻','=':'⁼','(':'⁽',')':'⁾',
    'a':'ᵃ','b':'ᵇ','c':'ᶜ','d':'ᵈ','e':'ᵉ',
    'f':'ᶠ','g':'ᵍ','h':'ʰ','i':'ⁱ','j':'ʲ',
    'k':'ᵏ','l':'ˡ','m':'ᵐ','n':'ⁿ','o':'ᵒ',
    'p':'ᵖ','r':'ʳ','s':'ˢ','t':'ᵗ','u':'ᵘ',
    'v':'ᵛ','w':'ʷ','x':'ˣ','y':'ʸ','z':'ᶻ',
}
SUB_MAP: dict[str, str] = {
    '0':'₀','1':'₁','2':'₂','3':'₃','4':'₄',
    '5':'₅','6':'₆','7':'₇','8':'₈','9':'₉',
    '+':'₊','-':'₋','=':'₌','(':'₍',')':'₎',
    'a':'ₐ','e':'ₑ','h':'ₕ','i':'ᵢ','j':'ⱼ',
    'k':'ₖ','l':'ₗ','m':'ₘ','n':'ₙ','o':'ₒ',
    'p':'ₚ','r':'ᵣ','s':'ₛ','t':'ₜ','u':'ᵤ',
    'v':'ᵥ','x':'ₓ',
}


def _aplicar_mapa(texto: str, mapa: dict) -> str:
    """Converte cada caractere pelo mapa; sem mapeamento mantém o original."""
    return "".join(mapa.get(c.lower(), c) for c in texto)


def pil_para_tk(img: Image.Image, max_size: tuple) -> ImageTk.PhotoImage:
    img = img.copy()
    img.thumbnail(max_size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)


# ── Janela de fórmulas LaTeX ──────────────────────────────────────────────────
class JanelaFormula(tk.Toplevel):
    """
    Inserção de fórmulas LaTeX com preview em tempo real.
    Armazena no JSON como $formula$ (inline) ou $$formula$$ (bloco).
    No frontend, usar KaTeX ou MathJax para renderizar.
    """

    TEMPLATES = [
        ("Fração",        r"\frac{a}{b}"),
        ("Raiz quadrada", r"\sqrt{x}"),
        ("Raiz n",        r"\sqrt[n]{x}"),
        ("Potência",      r"x^{n}"),
        ("Índice",        r"x_{n}"),
        ("Frac + pot.",   r"\frac{x^{a}}{y^{b}}"),
        ("π",             r"\pi"),
        ("θ",             r"\theta"),
        ("α β γ",         r"\alpha, \beta, \gamma"),
        ("Δ",             r"\Delta"),
        ("±",             r"\pm"),
        ("×",             r"\times"),
        ("÷",             r"\div"),
        ("≤ ≥",           r"\leq, \geq"),
        ("≠",             r"\neq"),
        ("∞",             r"\infty"),
        ("∑",             r"\sum_{i=1}^{n} x_i"),
        ("∫",             r"\int_{a}^{b} f(x)\,dx"),
        ("Vetor",         r"\vec{v}"),
        ("Módulo",        r"|x|"),
        ("log",           r"\log_{b}(x)"),
        ("Trigon.",       r"\sin\theta, \cos\theta"),
    ]

    def __init__(self, parent, widget_destino, cursor_pos=None):
        super().__init__(parent)
        self.title("Inserir Fórmula LaTeX")
        self.configure(bg="#161411")
        self.resizable(True, True)
        self.geometry("820x620")
        self.minsize(680, 520)
        self._destino    = widget_destino
        self._cursor_pos = cursor_pos   # posição capturada antes do focus_force
        self._preview_img = None
        self._after_id   = None
        self._build_ui()
        self.lift()
        self.focus_force()

    def _build_ui(self):
        BG, CARD = "#0E0D0B", "#161411"
        FG, FG2  = "#F2EDE4", "#A89880"
        ACC      = "#D4A853"
        EBGL     = "#1E1B17"

        # ── Cabeçalho ────────────────────────────────────────────────────────
        tk.Label(self, text="  INSERIR FÓRMULA LaTeX",
                 bg=ACC, fg="#0E0D0B",
                 font=("Segoe UI", 11, "bold")).pack(fill="x", ipady=8)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=12)

        # ── Coluna esquerda: templates ────────────────────────────────────────
        left = tk.Frame(body, bg=CARD, width=180)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        tk.Label(left, text="MODELOS RÁPIDOS", bg=CARD, fg=ACC,
                 font=("Segoe UI", 8, "bold")).pack(pady=(8, 4))

        canvas_t = tk.Canvas(left, bg=CARD, highlightthickness=0, width=170)
        sc_t = tk.Scrollbar(left, orient="vertical", command=canvas_t.yview)
        canvas_t.configure(yscrollcommand=sc_t.set)
        sc_t.pack(side="right", fill="y")
        canvas_t.pack(fill="both", expand=True)
        frame_t = tk.Frame(canvas_t, bg=CARD)
        canvas_t.create_window((0, 0), window=frame_t, anchor="nw")
        frame_t.bind("<Configure>",
            lambda e: canvas_t.configure(
                scrollregion=canvas_t.bbox("all")))

        for label, latex in self.TEMPLATES:
            tk.Button(frame_t, text=label,
                      bg="#2C2820", fg=FG, relief="flat",
                      font=("Segoe UI", 8), anchor="w", padx=8, pady=3,
                      cursor="hand2",
                      command=lambda l=latex: self._inserir_template(l)
                      ).pack(fill="x", padx=4, pady=1)

        # ── Coluna direita: editor + preview ─────────────────────────────────
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Código LaTeX:", bg=BG, fg=FG2,
                 font=("Segoe UI", 9)).pack(anchor="w")

        self._ent_latex = tk.Text(right, bg=EBGL, fg=FG,
                                   font=("Consolas", 11),
                                   height=3, wrap="word", relief="flat",
                                   insertbackground=FG,
                                   selectbackground=ACC,
                                   padx=8, pady=6)
        self._ent_latex.pack(fill="x", pady=(4, 8))
        self._ent_latex.bind("<KeyRelease>", self._agendar_preview)

        # Tipo: inline / bloco
        row_tipo = tk.Frame(right, bg=BG)
        row_tipo.pack(fill="x", pady=(0, 8))
        tk.Label(row_tipo, text="Tipo:", bg=BG, fg=FG2,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))
        self._tipo_var = tk.StringVar(value="inline")
        ttk.Radiobutton(row_tipo, text="Inline  ($...$)",
                        variable=self._tipo_var, value="inline").pack(side="left", padx=(0, 12))
        ttk.Radiobutton(row_tipo, text="Bloco  ($$...$$)",
                        variable=self._tipo_var, value="bloco").pack(side="left")

        # Preview
        tk.Label(right, text="Preview:", bg=BG, fg=FG2,
                 font=("Segoe UI", 9)).pack(anchor="w")
        self._lbl_preview = tk.Label(right, bg=EBGL, relief="flat",
                                      text="(prévia aparece aqui)",
                                      fg=FG2, font=("Segoe UI", 9))
        self._lbl_preview.pack(fill="both", expand=True, pady=(4, 12))

        if not _MATPLOTLIB_OK:
            tk.Label(right,
                     text="⚠ matplotlib não instalado — preview indisponível.\n"
                          "pip install matplotlib",
                     bg=BG, fg="#fab387",
                     font=("Segoe UI", 8, "italic")).pack(anchor="w")

        # Botões
        row_btn = tk.Frame(right, bg=BG)
        row_btn.pack(fill="x")
        tk.Button(row_btn, text="➕  Inserir fórmula",
                  bg=ACC, fg="#0E0D0B", relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  pady=7, cursor="hand2",
                  activebackground="#B8882A",
                  command=self._confirmar).pack(side="left", fill="x",
                                               expand=True, padx=(0, 6))
        tk.Button(row_btn, text="✕  Cancelar",
                  bg="#2C2820", fg="#f38ba8", relief="flat",
                  font=("Segoe UI", 9), pady=7, cursor="hand2",
                  command=self.destroy).pack(side="left")

        # Nota sobre frontend
        tk.Label(right,
                 text="ℹ  No frontend, usar KaTeX (npm install katex) para renderizar.",
                 bg=BG, fg="#585b70",
                 font=("Segoe UI", 7, "italic")).pack(anchor="w", pady=(8, 0))

    def _inserir_template(self, latex: str):
        self._ent_latex.delete("1.0", "end")
        self._ent_latex.insert("1.0", latex)
        self._ent_latex.focus_set()
        self._atualizar_preview()

    def _agendar_preview(self, *_):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(400, self._atualizar_preview)

    def _atualizar_preview(self):
        if not _MATPLOTLIB_OK:
            return
        formula = self._ent_latex.get("1.0", "end-1c").strip()
        if not formula:
            self._lbl_preview.config(image="",
                                     text="(prévia aparece aqui)")
            return
        try:
            fig = plt.figure(figsize=(7.8, 2.6))
            fig.patch.set_facecolor("#1E1B17")
            ax = fig.add_axes([0.02, 0.05, 0.96, 0.90])
            ax.set_facecolor("#1E1B17")
            ax.axis("off")
            ax.text(0.5, 0.5, f"${formula}$",
                    ha="center", va="center",
                    fontsize=24, color="#F2EDE4",
                    transform=ax.transAxes)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=120,
                        bbox_inches="tight",
                        facecolor="#1E1B17")
            plt.close(fig)
            buf.seek(0)
            img = Image.open(buf)
            self._preview_img = ImageTk.PhotoImage(img)
            self._lbl_preview.config(image=self._preview_img, text="")
        except Exception as e:
            self._lbl_preview.config(image="",
                                     text=f"Fórmula inválida: {e}")

    def _confirmar(self):
        formula = self._ent_latex.get("1.0", "end-1c").strip()
        if not formula:
            messagebox.showwarning("Aviso", "Digite a fórmula antes de inserir.",
                                   parent=self)
            return
        delim = "$" if self._tipo_var.get() == "inline" else "$$"
        texto = f"{delim}{formula}{delim}"
        try:
            dest = self._destino
            if isinstance(dest, tk.Text):
                # tk.Text: índice no formato "linha.coluna"
                pos = self._cursor_pos or dest.index("insert")
                dest.insert(pos, texto)
            else:
                # tk.Entry: índice inteiro
                pos = self._cursor_pos if self._cursor_pos is not None \
                      else dest.index(tk.INSERT)
                dest.insert(pos, texto)
        except Exception:
            pass
        self.destroy()


# ── Janela de visualização ────────────────────────────────────────────────────
class JanelaVisualizacao(tk.Toplevel):
    """Exibe a imagem em tamanho real com scroll."""

    def __init__(self, parent, path: Path):
        super().__init__(parent)
        self.title(path.name)
        self.configure(bg="#0E0D0B")
        self.resizable(True, True)

        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir:\n{e}", parent=self)
            self.destroy()
            return

        iw, ih = img.size
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        scale = min((sw * 0.85) / iw, (sh * 0.85) / ih, 1.0)
        dw, dh = max(1, int(iw * scale)), max(1, int(ih * scale))
        self.geometry(f"{dw + 24}x{dh + 56}")

        tk.Label(self, text=f"{path.name}   {iw}×{ih} px",
                 bg="#0E0D0B", fg="#A89880",
                 font=("Segoe UI", 8)).pack(pady=(8, 2))

        wrap = tk.Frame(self, bg="#0E0D0B")
        wrap.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        canvas = tk.Canvas(wrap, bg="#0E0D0B", highlightthickness=0)
        sx = tk.Scrollbar(wrap, orient="horizontal", command=canvas.xview)
        sy = tk.Scrollbar(wrap, orient="vertical",   command=canvas.yview)
        canvas.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        sx.pack(side="bottom", fill="x")
        sy.pack(side="right",  fill="y")
        canvas.pack(fill="both", expand=True)

        disp = img.copy()
        disp.thumbnail((int(sw * 0.85), int(sh * 0.85)), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(disp)
        canvas.create_image(0, 0, anchor="nw", image=self._photo)
        canvas.configure(scrollregion=canvas.bbox("all"))
        self.lift()
        self.focus_force()


# ── Janela de recorte interativo ──────────────────────────────────────────────
class JanelaRecorte(tk.Toplevel):
    """Recorte interativo: arraste para selecionar área e clique Aplicar."""

    def __init__(self, parent, path: Path, callback=None):
        super().__init__(parent)
        self.title(f"Recortar — {path.name}")
        self.configure(bg="#0E0D0B")
        self.resizable(True, True)

        self._path     = path
        self._callback = callback   # chamado com path após salvar
        self._img_orig = None
        self._photo    = None
        self._scale    = 1.0
        self._x0 = self._y0 = self._x1 = self._y1 = 0
        self._rect_id  = None
        self._drawing  = False

        try:
            self._img_orig = Image.open(path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir:\n{e}", parent=self)
            self.destroy()
            return

        self._build_ui()
        self._carregar_imagem()
        self.lift()
        self.focus_force()

    def _build_ui(self):
        tk.Label(self,
                 text="Clique e arraste para selecionar a área de recorte",
                 bg="#0E0D0B", fg="#A89880",
                 font=("Segoe UI", 9)).pack(pady=(10, 2))

        wrap = tk.Frame(self, bg="#0E0D0B")
        wrap.pack(fill="both", expand=True, padx=10)

        self._canvas = tk.Canvas(wrap, bg="#161411",
                                  cursor="crosshair",
                                  highlightthickness=1,
                                  highlightbackground="#D4A853")
        sx = tk.Scrollbar(wrap, orient="horizontal", command=self._canvas.xview)
        sy = tk.Scrollbar(wrap, orient="vertical",   command=self._canvas.yview)
        self._canvas.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        sx.pack(side="bottom", fill="x")
        sy.pack(side="right",  fill="y")
        self._canvas.pack(fill="both", expand=True)

        self._canvas.bind("<ButtonPress-1>",   self._on_press)
        self._canvas.bind("<B1-Motion>",       self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

        self.lbl_sel = tk.Label(self, text="Nenhuma seleção — arraste para recortar",
                                bg="#0E0D0B", fg="#A89880",
                                font=("Segoe UI", 8))
        self.lbl_sel.pack(pady=(4, 2))

        row = tk.Frame(self, bg="#0E0D0B")
        row.pack(pady=(4, 12))

        tk.Button(row, text="✂  Aplicar Recorte",
                  bg="#40a02b", fg="#fff", relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=16, pady=6, cursor="hand2",
                  activebackground="#2d8b1f",
                  command=self._aplicar).pack(side="left", padx=(0, 8))

        tk.Button(row, text="↺  Resetar Seleção",
                  bg="#2C2820", fg="#F2EDE4", relief="flat",
                  font=("Segoe UI", 9), padx=12, pady=6, cursor="hand2",
                  command=self._resetar).pack(side="left", padx=(0, 8))

        tk.Button(row, text="✕  Cancelar",
                  bg="#2C2820", fg="#f38ba8", relief="flat",
                  font=("Segoe UI", 9), padx=12, pady=6, cursor="hand2",
                  command=self.destroy).pack(side="left")

    def _carregar_imagem(self):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        iw, ih = self._img_orig.size
        self._scale = min((sw * 0.80) / iw, (sh * 0.72) / ih, 1.0)
        dw = max(1, int(iw * self._scale))
        dh = max(1, int(ih * self._scale))
        self.geometry(f"{dw + 60}x{dh + 160}")

        disp = self._img_orig.copy()
        disp = disp.resize((dw, dh), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(disp)
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor="nw",
                                   image=self._photo, tags="img")
        self._canvas.configure(scrollregion=(0, 0, dw, dh))
        self._rect_id = None

    def _on_press(self, event):
        self._x0 = self._canvas.canvasx(event.x)
        self._y0 = self._canvas.canvasy(event.y)
        self._drawing = True
        if self._rect_id:
            self._canvas.delete(self._rect_id)
            self._rect_id = None

    def _on_drag(self, event):
        if not self._drawing:
            return
        x1 = self._canvas.canvasx(event.x)
        y1 = self._canvas.canvasy(event.y)
        if self._rect_id:
            self._canvas.delete(self._rect_id)
        self._rect_id = self._canvas.create_rectangle(
            self._x0, self._y0, x1, y1,
            outline="#D4A853", width=2, dash=(6, 3))
        s = self._scale
        w = abs(int((x1 - self._x0) / s))
        h = abs(int((y1 - self._y0) / s))
        self.lbl_sel.config(text=f"Seleção: {w} × {h} px")

    def _on_release(self, event):
        self._x1 = self._canvas.canvasx(event.x)
        self._y1 = self._canvas.canvasy(event.y)
        self._drawing = False

    def _resetar(self):
        if self._rect_id:
            self._canvas.delete(self._rect_id)
            self._rect_id = None
        self.lbl_sel.config(text="Nenhuma seleção — arraste para recortar")
        self._x0 = self._y0 = self._x1 = self._y1 = 0

    def _aplicar(self):
        x0 = min(self._x0, self._x1)
        y0 = min(self._y0, self._y1)
        x1 = max(self._x0, self._x1)
        y1 = max(self._y0, self._y1)

        if (x1 - x0) < 5 or (y1 - y0) < 5:
            messagebox.showwarning("Seleção inválida",
                                   "Faça uma seleção maior antes de recortar.",
                                   parent=self)
            return

        s = self._scale
        box = (int(x0 / s), int(y0 / s), int(x1 / s), int(y1 / s))
        cropped = self._img_orig.crop(box)
        cropped.save(str(self._path), "JPEG", quality=JPEG_Q)

        if self._callback:
            self._callback(self._path)

        messagebox.showinfo("Recorte aplicado",
                            f"Salvo: {cropped.size[0]}×{cropped.size[1]} px",
                            parent=self)
        self.destroy()


# ── Frame principal ───────────────────────────────────────────────────────────
class QuestoesFrame(ttk.Frame):
    BG       = "#0E0D0B"
    CARD     = "#161411"
    ACC      = "#D4A853"
    FG       = "#F2EDE4"
    FG2      = "#A89880"
    ENTRY_BG = "#1E1B17"
    EDIT_BG  = "#161411"
    BTN_BG   = "#D4A853"
    BTN_FG   = "#0E0D0B"
    BTN_HOV  = "#B8882A"
    BTN_SAV  = "#40a02b"
    DANGER   = "#f38ba8"
    OK       = "#a6e3a1"
    WARN     = "#fab387"

    def __init__(self, master, on_staging_change=None, **kw):
        super().__init__(master, **kw)
        self._on_staging_change = on_staging_change   # callback → atualiza barra global

        self._questoes: list           = []
        self._q_idx: int               = 0
        self._arquivo_sel: Path | None = None
        self._preview_tk               = None
        self._thumbs: list             = []
        self._posicao_map: dict        = {}
        self._ultimo_campo             = None

        # Estado do seletor de categoria
        self._cat_atual   = "ENEM"
        self._filtros_cat = {}

        self._build_ui()
        self._carregar_categorias()
        self._bind_teclado()

    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        C = self

        # ── Cabeçalho escuro com filtros ──────────────────────────────────────
        hdr = tk.Frame(self, bg=C.CARD)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=C.CARD)
        hdr_inner.pack(fill="x", padx=14, pady=10)

        # Título à esquerda
        tk.Label(hdr_inner, text="QUESTÕES", bg=C.CARD, fg=C.ACC,
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 20))

        # Filtros em linha
        def _filter_lbl(parent, text):
            tk.Label(parent, text=text, bg=C.CARD, fg=C.FG2,
                     font=("Segoe UI", 8, "bold")).pack(side="left", padx=(8, 3))

        _filter_lbl(hdr_inner, "PROVA")
        self._var_cat = tk.StringVar(value="ENEM")
        self._cb_cat  = ttk.Combobox(hdr_inner, textvariable=self._var_cat,
                                     state="readonly", width=8,
                                     font=("Segoe UI", 9))
        self._cb_cat.pack(side="left", padx=(0, 6))
        self._cb_cat.bind("<<ComboboxSelected>>", self._ao_mudar_categoria)

        # Separador vertical
        tk.Label(hdr_inner, text="│", bg=C.CARD, fg=C.CARD[:-2]+"20",
                 font=("Segoe UI", 14)).pack(side="left", padx=2)

        self._lbl_f1 = tk.Label(hdr_inner, text="ANO", bg=C.CARD, fg=C.FG2,
                                 font=("Segoe UI", 8, "bold"))
        self._lbl_f1.pack(side="left", padx=(4, 3))
        self._var_f1 = tk.StringVar()
        self._cb_f1  = ttk.Combobox(hdr_inner, textvariable=self._var_f1,
                                     state="readonly", width=12,
                                     font=("Segoe UI", 9))
        self._cb_f1.pack(side="left", padx=(0, 6))
        self._cb_f1.bind("<<ComboboxSelected>>", self._ao_mudar_f1)

        tk.Label(hdr_inner, text="│", bg=C.CARD, fg=C.CARD[:-2]+"20",
                 font=("Segoe UI", 14)).pack(side="left", padx=2)

        self._lbl_f2 = tk.Label(hdr_inner, text="DIA", bg=C.CARD, fg=C.FG2,
                                 font=("Segoe UI", 8, "bold"))
        self._lbl_f2.pack(side="left", padx=(4, 3))
        self._var_f2 = tk.StringVar()
        self._cb_f2  = ttk.Combobox(hdr_inner, textvariable=self._var_f2,
                                     state="readonly", width=8,
                                     font=("Segoe UI", 9))
        self._cb_f2.pack(side="left", padx=(0, 6))
        self._cb_f2.bind("<<ComboboxSelected>>", self._load_questoes)

        tk.Label(hdr_inner, text="│", bg=C.CARD, fg="#2C2820",
                 font=("Segoe UI", 14)).pack(side="left", padx=2)

        tk.Label(hdr_inner, text="TIPO", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(4, 3))
        self._var_tipo = tk.StringVar(value="Todos")
        self._cb_tipo  = ttk.Combobox(hdr_inner, textvariable=self._var_tipo,
                                      state="readonly", width=10,
                                      font=("Segoe UI", 9))
        self._cb_tipo["values"] = ["Todos", "PROVA", "SIMULADO"]
        self._cb_tipo.pack(side="left", padx=(0, 6))
        self._cb_tipo.bind("<<ComboboxSelected>>", self._load_questoes)

        # Provedor — visível só para ENEM
        self._sep_provedor = tk.Label(hdr_inner, text="│", bg=C.CARD, fg="#2C2820",
                                      font=("Segoe UI", 14))
        self._lbl_provedor = tk.Label(hdr_inner, text="ELABORADOR", bg=C.CARD, fg=C.FG2,
                                       font=("Segoe UI", 8, "bold"))
        self._var_provedor = tk.StringVar(value="Todos")
        self._cb_provedor  = ttk.Combobox(hdr_inner, textvariable=self._var_provedor,
                                           state="readonly", width=11,
                                           font=("Segoe UI", 9))
        self._cb_provedor["values"] = ["Todos"]
        self._cb_provedor.bind("<<ComboboxSelected>>", self._load_questoes)
        # Inicialmente oculto; mostrado em _ao_mudar_categoria para ENEM

        # Indicador de staging à direita
        self._lbl_sync = tk.Label(hdr_inner, text="", bg=C.CARD, fg=C.FG2,
                                   font=("Segoe UI", 8))
        self._lbl_sync.pack(side="right", padx=6)

        # Linha divisória
        tk.Frame(self, bg="#2C2820", height=1).pack(fill="x")

        body = tk.Frame(self, bg=C.BG)
        body.pack(fill="both", expand=True, padx=10, pady=10)

        # ══ ESQUERDA — navegação ══════════════════════════════════════════════
        left = tk.Frame(body, bg=C.CARD, width=220)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        tk.Label(left, text="NAVEGAÇÃO", bg=C.CARD, fg=C.ACC,
                 font=("Segoe UI", 9, "bold")).pack(pady=(14, 6))

        # Questão
        row_q = tk.Frame(left, bg=C.CARD)
        row_q.pack(fill="x", padx=10, pady=2)
        tk.Label(row_q, text="Q Nº", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 9), width=4, anchor="w").pack(side="left")
        self.ent_num = tk.Entry(row_q, bg=C.ENTRY_BG, fg=C.FG,
                                insertbackground=C.FG, relief="flat",
                                font=("Segoe UI", 10), width=6)
        self.ent_num.pack(side="left")
        self.ent_num.bind("<Return>", lambda e: self._ir_para_numero())
        tk.Button(row_q, text="Ir", bg=C.BTN_BG, fg=C.BTN_FG, relief="flat",
                  font=("Segoe UI", 8, "bold"), padx=5, cursor="hand2",
                  command=self._ir_para_numero).pack(side="left", padx=(4, 0))

        nav = tk.Frame(left, bg=C.CARD)
        nav.pack(fill="x", padx=10, pady=(8, 2))
        tk.Button(nav, text="← Anterior", bg=C.ENTRY_BG, fg=C.FG,
                  relief="flat", font=("Segoe UI", 9), cursor="hand2",
                  command=self._anterior).pack(side="left", fill="x",
                                              expand=True, padx=(0, 3))
        tk.Button(nav, text="Próxima →", bg=C.ENTRY_BG, fg=C.FG,
                  relief="flat", font=("Segoe UI", 9), cursor="hand2",
                  command=self._proxima).pack(side="left", fill="x", expand=True)

        # Badge de contagem de questões
        count_wrap = tk.Frame(left, bg="#1E1B17", bd=0)
        count_wrap.pack(padx=10, pady=(2, 6), fill="x")
        self.lbl_count = tk.Label(count_wrap, text="", bg="#1E1B17", fg=C.ACC,
                                  font=("Segoe UI", 8, "bold"), pady=3)
        self.lbl_count.pack(fill="x")

        tk.Frame(left, bg=C.ACC, height=1).pack(fill="x", padx=10, pady=4)

        # ── Imagens salvas (lista com posição) ────────────────────────────────
        tk.Label(left, text="IMAGENS SALVAS", bg=C.CARD, fg=C.ACC,
                 font=("Segoe UI", 9, "bold")).pack(pady=(4, 4))

        canvas_w = tk.Frame(left, bg=C.CARD)
        canvas_w.pack(fill="both", expand=True, padx=6, pady=(0, 8))
        self._thumb_canvas = tk.Canvas(canvas_w, bg=C.CARD, highlightthickness=0)
        _sc = tk.Scrollbar(canvas_w, orient="vertical",
                           command=self._thumb_canvas.yview)
        self._thumb_canvas.configure(yscrollcommand=_sc.set)
        _sc.pack(side="right", fill="y")
        self._thumb_canvas.pack(side="left", fill="both", expand=True)
        self.frame_imgs = tk.Frame(self._thumb_canvas, bg=C.CARD)
        self._thumb_canvas.create_window((0, 0), window=self.frame_imgs, anchor="nw")
        self.frame_imgs.bind("<Configure>",
            lambda e: self._thumb_canvas.configure(
                scrollregion=self._thumb_canvas.bbox("all")))

        # ══ CENTRO — questão (com scroll vertical) ═══════════════════════════
        center_outer = tk.Frame(body, bg=C.CARD)
        center_outer.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Canvas + scrollbar para o painel central
        _csc = tk.Scrollbar(center_outer, orient="vertical", relief="flat", width=8,
                            bg=C.CARD, troughcolor=C.CARD)
        _csc.pack(side="right", fill="y")
        _cc = tk.Canvas(center_outer, bg=C.CARD, highlightthickness=0,
                        yscrollcommand=_csc.set)
        _cc.pack(side="left", fill="both", expand=True)
        _csc.config(command=_cc.yview)

        center = tk.Frame(_cc, bg=C.CARD)
        _cc_win = _cc.create_window((0, 0), window=center, anchor="nw")

        # Redimensiona o frame interno junto com o canvas
        def _on_center_configure(e):
            _cc.configure(scrollregion=_cc.bbox("all"))
        def _on_canvas_resize(e):
            _cc.itemconfig(_cc_win, width=e.width)
        center.bind("<Configure>", _on_center_configure)
        _cc.bind("<Configure>", _on_canvas_resize)

        # Scroll com roda do mouse no painel central
        def _center_scroll(e):
            _cc.yview_scroll(int(-1 * (e.delta / 120)), "units")
        _cc.bind("<MouseWheel>", _center_scroll)
        center.bind("<MouseWheel>", _center_scroll)

        # ── Cabeçalho da questão ──────────────────────────────────────────────
        tk.Label(center, text="QUESTÃO", bg=C.CARD, fg=C.ACC,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(12, 2))
        self.lbl_q_title = tk.Label(center, text="", bg=C.CARD, fg=C.FG,
                                    font=("Segoe UI", 13, "bold"))
        self.lbl_q_title.pack(anchor="w", padx=16)
        self.lbl_area = tk.Label(center, text="", bg=C.CARD, fg=C.FG2,
                                 font=("Segoe UI", 8, "italic"),
                                 wraplength=440, justify="left")
        self.lbl_area.pack(anchor="w", padx=16, pady=(0, 6))

        tk.Frame(center, bg=C.ENTRY_BG, height=1).pack(fill="x", padx=16, pady=2)

        # ── Enunciado editável ────────────────────────────────────────────────
        row_eh = tk.Frame(center, bg=C.CARD)
        row_eh.pack(fill="x", padx=16, pady=(6, 2))
        tk.Label(row_eh, text="Enunciado", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(row_eh,
                 text="  (editável · linha em branco = novo parágrafo)",
                 bg=C.CARD, fg="#585b70",
                 font=("Segoe UI", 7, "italic")).pack(side="left")

        fe = tk.Frame(center, bg=C.CARD)
        fe.pack(fill="x", padx=16, pady=(0, 4))
        se = tk.Scrollbar(fe, bg=C.CARD, troughcolor=C.CARD, relief="flat", width=8)
        self.txt_enun = tk.Text(fe, bg=C.EDIT_BG, fg=C.FG, font=("Segoe UI", 9),
                                wrap="word", relief="flat", height=7,
                                yscrollcommand=se.set, padx=8, pady=6,
                                insertbackground=C.FG, selectbackground=C.ACC)
        se.config(command=self.txt_enun.yview)
        se.pack(side="right", fill="y")
        self.txt_enun.pack(fill="x", expand=False)
        self.txt_enun.bind("<FocusOut>", lambda e: self._atualizar_posicoes())
        self.txt_enun.bind("<KeyRelease>", lambda e: self._atualizar_posicoes())
        # propaga scroll para o canvas central
        self.txt_enun.bind("<MouseWheel>", _center_scroll)

        # ── Comando ───────────────────────────────────────────────────────────
        row_cmd = tk.Frame(center, bg=C.CARD)
        row_cmd.pack(fill="x", padx=16, pady=(2, 4))
        tk.Label(row_cmd, text="Comando:", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 9, "bold"), width=9, anchor="w").pack(side="left")
        self.ent_cmd = tk.Entry(row_cmd, bg=C.EDIT_BG, fg=C.FG,
                                insertbackground=C.FG, relief="flat",
                                font=("Segoe UI", 9))
        self.ent_cmd.pack(side="left", fill="x", expand=True, ipady=4)

        tk.Button(center, text="💾  Salvar Enunciado",
                  bg=C.BTN_SAV, fg=C.BTN_FG, relief="flat",
                  font=("Segoe UI", 9, "bold"), pady=5, cursor="hand2",
                  activebackground="#2d8b1f",
                  command=self._salvar_enunciado).pack(
                  fill="x", padx=16, pady=(0, 4))
        self.lbl_enun_status = tk.Label(center, text="", bg=C.CARD, fg=C.OK,
                                        font=("Segoe UI", 8, "italic"))
        self.lbl_enun_status.pack(anchor="w", padx=16)

        tk.Frame(center, bg=C.ENTRY_BG, height=1).pack(fill="x", padx=16, pady=4)

        # ── Alternativas (editáveis) ──────────────────────────────────────────
        row_alts_hdr = tk.Frame(center, bg=C.CARD)
        row_alts_hdr.pack(fill="x", padx=16, pady=(2, 4))
        tk.Label(row_alts_hdr, text="Alternativas", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(row_alts_hdr, text="  (editável)",
                 bg=C.CARD, fg="#585b70",
                 font=("Segoe UI", 7, "italic")).pack(side="left")

        self.ent_alts: dict[str, tk.Text] = {}
        for letra in LETRAS:
            row = tk.Frame(center, bg=C.CARD)
            row.pack(fill="x", padx=16, pady=1)
            self._lbl_alt_letra = tk.Label(row, text=f" {letra} ",
                                           bg=C.ENTRY_BG, fg=C.FG,
                                           font=("Segoe UI", 9, "bold"), width=2)
            self._lbl_alt_letra.pack(side="left", anchor="n", pady=3)
            self._lbl_alt_letra._letra = letra
            txt = tk.Text(row, bg=C.EDIT_BG, fg=C.FG, font=("Segoe UI", 9),
                          wrap="word", relief="flat", height=2,
                          padx=6, pady=4,
                          insertbackground=C.FG, selectbackground=C.ACC)
            txt.pack(side="left", fill="x", expand=True)
            txt.bind("<MouseWheel>", _center_scroll)
            self.ent_alts[letra] = txt
            txt._lbl_letra = self._lbl_alt_letra

        # ── Gabarito ──────────────────────────────────────────────────────────
        row_gab = tk.Frame(center, bg=C.CARD)
        row_gab.pack(fill="x", padx=16, pady=(4, 2))
        tk.Label(row_gab, text="Gabarito:", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        self._gab_var = tk.StringVar()
        self.cb_gab = ttk.Combobox(row_gab, values=["—"] + LETRAS,
                                   textvariable=self._gab_var,
                                   width=5, state="readonly")
        self.cb_gab.pack(side="left", padx=(6, 0))
        self.cb_gab.bind("<<ComboboxSelected>>", lambda e: self._colorir_gabarito())

        # ── Botão salvar alternativas ─────────────────────────────────────────
        tk.Button(center, text="💾  Salvar Alternativas",
                  bg="#2d8b4e", fg=C.BTN_FG, relief="flat",
                  font=("Segoe UI", 9, "bold"), pady=5, cursor="hand2",
                  activebackground="#1f6436",
                  command=self._salvar_alternativas).pack(
                  fill="x", padx=16, pady=(4, 2))
        self.lbl_alts_status = tk.Label(center, text="", bg=C.CARD, fg=C.OK,
                                        font=("Segoe UI", 8, "italic"))
        self.lbl_alts_status.pack(anchor="w", padx=16, pady=(0, 12))

        # ══ DIREITA — adicionar imagem ════════════════════════════════════════
        right = tk.Frame(body, bg=C.CARD, width=290)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="ADICIONAR IMAGEM", bg=C.CARD, fg=C.ACC,
                 font=("Segoe UI", 9, "bold")).pack(pady=(14, 8))

        # Arquivo
        tk.Label(right, text="Arquivo:", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=14)
        row_arq = tk.Frame(right, bg=C.CARD)
        row_arq.pack(fill="x", padx=14, pady=(4, 6))
        self.lbl_arq = tk.Label(row_arq, text="Nenhum arquivo selecionado",
                                bg=C.ENTRY_BG, fg=C.FG2, font=("Segoe UI", 8),
                                relief="flat", anchor="w", padx=6,
                                wraplength=170, justify="left")
        self.lbl_arq.pack(side="left", fill="x", expand=True, ipady=4)
        tk.Button(row_arq, text="...", bg=C.BTN_BG, fg=C.BTN_FG, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=8, cursor="hand2",
                  command=self._procurar_arquivo).pack(side="left", padx=(4, 0))

        # Preview
        self.lbl_preview = tk.Label(right, bg=C.ENTRY_BG, relief="flat",
                                    width=26, height=9,
                                    text="Selecione uma imagem",
                                    fg=C.FG2, font=("Segoe UI", 8))
        self.lbl_preview.pack(padx=14, pady=(0, 4), fill="x")

        row_prev_btns = tk.Frame(right, bg=C.CARD)
        row_prev_btns.pack(fill="x", padx=14, pady=(0, 8))
        tk.Button(row_prev_btns, text="👁  Ver em tela cheia",
                  bg=C.ENTRY_BG, fg=C.FG, relief="flat",
                  font=("Segoe UI", 8), pady=3, cursor="hand2",
                  command=self._ver_arquivo_sel).pack(
                  side="left", fill="x", expand=True, padx=(0, 3))
        tk.Button(row_prev_btns, text="✂  Recortar",
                  bg=C.ENTRY_BG, fg=C.WARN, relief="flat",
                  font=("Segoe UI", 8), pady=3, cursor="hand2",
                  command=self._recortar_arquivo_sel).pack(
                  side="left", fill="x", expand=True)

        tk.Frame(right, bg=C.ENTRY_BG, height=1).pack(fill="x", padx=14, pady=4)

        # ── Tipo ─────────────────────────────────────────────────────────────
        tk.Label(right, text="Tipo de imagem:", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(4, 4))
        self._tipo_var = tk.StringVar(value="enunciado")
        ttk.Radiobutton(right, text="Enunciado",
                        variable=self._tipo_var, value="enunciado",
                        command=self._toggle_tipo).pack(anchor="w", padx=20)
        ttk.Radiobutton(right, text="Alternativa",
                        variable=self._tipo_var, value="alternativa",
                        command=self._toggle_tipo).pack(anchor="w", padx=20)

        row_letra = tk.Frame(right, bg=C.CARD)
        row_letra.pack(anchor="w", padx=36, pady=(4, 6))
        tk.Label(row_letra, text="Letra:", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 9)).pack(side="left")
        self._letra_var = tk.StringVar(value="A")
        self.cb_letra = ttk.Combobox(row_letra, values=LETRAS,
                                     textvariable=self._letra_var,
                                     width=4, state="disabled")
        self.cb_letra.pack(side="left", padx=(6, 0))

        tk.Frame(right, bg=C.ENTRY_BG, height=1).pack(fill="x", padx=14, pady=4)

        # ── Posição ───────────────────────────────────────────────────────────
        self.frame_posicao = tk.Frame(right, bg=C.CARD)
        self.frame_posicao.pack(fill="x", padx=14, pady=(4, 6))

        tk.Label(self.frame_posicao, text="Posição no layout:",
                 bg=C.CARD, fg=C.FG2, font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(self.frame_posicao,
                 text="(onde a imagem aparecerá entre os parágrafos)",
                 bg=C.CARD, fg="#585b70", font=("Segoe UI", 7, "italic")).pack(anchor="w")

        self._posicao_label_var = tk.StringVar()
        self.cb_posicao = ttk.Combobox(self.frame_posicao,
                                       textvariable=self._posicao_label_var,
                                       width=26, state="readonly")
        self.cb_posicao.pack(fill="x", pady=(4, 0))

        tk.Frame(right, bg=C.ENTRY_BG, height=1).pack(fill="x", padx=14, pady=8)

        # Botão adicionar
        tk.Button(right, text="➕  ADICIONAR IMAGEM",
                  bg=C.BTN_BG, fg=C.BTN_FG, relief="flat",
                  font=("Segoe UI", 10, "bold"), pady=8, cursor="hand2",
                  command=self._adicionar_imagem,
                  activebackground=C.BTN_HOV).pack(fill="x", padx=14, pady=(0, 8))

        self.lbl_status = tk.Label(right, text="", bg=C.CARD, fg=C.OK,
                                   font=("Segoe UI", 8, "italic"),
                                   wraplength=250, justify="center")
        self.lbl_status.pack(padx=14)

        tk.Frame(right, bg=C.ENTRY_BG, height=1).pack(fill="x", padx=14, pady=10)

        # Remover / Deletar
        tk.Label(right, text="Gerenciar imagem salva:", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(0, 4))
        self._img_rem_var = tk.StringVar()
        self.cb_remover = ttk.Combobox(right, textvariable=self._img_rem_var,
                                       width=28, state="readonly")
        self.cb_remover.pack(fill="x", padx=14, pady=(0, 4))

        row_rem = tk.Frame(right, bg=C.CARD)
        row_rem.pack(fill="x", padx=14)
        tk.Button(row_rem, text="Remover do registro",
                  bg="#2C2820", fg=C.FG2, relief="flat",
                  font=("Segoe UI", 8), pady=5, cursor="hand2",
                  command=self._remover_imagem
                  ).pack(side="left", fill="x", expand=True, padx=(0, 3))
        tk.Button(row_rem, text="🗑 Deletar arquivo",
                  bg="#2C2820", fg=C.DANGER, relief="flat",
                  font=("Segoe UI", 8), pady=5, cursor="hand2",
                  command=self._deletar_imagem_selecionada
                  ).pack(side="left", fill="x", expand=True)

    # ── Categorias / filtros em cascata ───────────────────────────────────────
    def _carregar_categorias(self):
        cats = dl.listar_categorias()
        if not cats:
            cats = ["ENEM"]
        self._cb_cat["values"] = cats
        self._var_cat.set(cats[0])
        self._ao_mudar_categoria()

    def _ao_mudar_categoria(self, _=None):
        cat = self._var_cat.get()
        self._cat_atual = cat
        filtros = dl.listar_filtros(cat)

        if cat == "ENEM":
            self._lbl_f1.config(text="Ano:")
            anos = [str(a) for a in filtros.get("anos", [])]
            self._cb_f1["values"] = anos
            if anos:
                self._var_f1.set(anos[0])
            self._lbl_f2.config(text="Dia:")
            dias = filtros.get("dias", ["dia1", "dia2"])
            self._cb_f2["values"] = dias
            if dias:
                self._var_f2.set(dias[0])
            # Mostra combo de elaborador
            provedores = ["Todos"] + filtros.get("provedores", [])
            self._cb_provedor["values"] = provedores
            self._var_provedor.set("Todos")
            self._sep_provedor.pack(side="left", padx=2)
            self._lbl_provedor.pack(side="left", padx=(4, 3))
            self._cb_provedor.pack(side="left", padx=(0, 6))

        elif cat == "UFT":
            self._lbl_f1.config(text="Ano:")
            anos = [str(a) for a in filtros.get("anos", [])]
            self._cb_f1["values"] = anos
            if anos:
                self._var_f1.set(anos[0])
            self._lbl_f2.config(text="Turno:")
            turnos = filtros.get("turnos", [])
            self._cb_f2["values"] = turnos
            if turnos:
                self._var_f2.set(turnos[0])
            # Oculta provedor
            self._sep_provedor.pack_forget()
            self._lbl_provedor.pack_forget()
            self._cb_provedor.pack_forget()

        else:  # EXATO
            self._lbl_f1.config(text="Evento:")
            eventos = filtros.get("eventos", [])
            self._cb_f1["values"] = eventos
            if eventos:
                self._var_f1.set(eventos[0])
            self._lbl_f2.config(text="Turno:")
            turnos = filtros.get("turnos", [])
            self._cb_f2["values"] = turnos
            if turnos:
                self._var_f2.set(turnos[0])
            # Oculta provedor
            self._sep_provedor.pack_forget()
            self._lbl_provedor.pack_forget()
            self._cb_provedor.pack_forget()

        self._load_questoes()

    def _ao_mudar_f1(self, _=None):
        self._load_questoes()

    def _load_questoes(self, _=None):
        cat = self._cat_atual
        f1  = self._var_f1.get()
        f2  = self._var_f2.get()

        if cat == "ENEM":
            try:
                filtros = {"ano": int(f1), "dia": f2}
            except ValueError:
                return
        elif cat == "UFT":
            try:
                filtros = {"ano": int(f1), "turno": f2}
            except ValueError:
                return
        else:  # EXATO
            filtros = {"evento": f1, "turno": f2}

        tipo_sel = self._var_tipo.get()
        tipo = None if tipo_sel == "Todos" else tipo_sel

        # Provedor (só ENEM)
        provedor_sel = self._var_provedor.get() if cat == "ENEM" else "Todos"
        provedor = None if provedor_sel == "Todos" else provedor_sel

        self._lbl_sync.config(text="carregando…", fg=self.WARN)
        self.update_idletasks()

        self._questoes = dl.buscar_questoes(cat, filtros, tipo=tipo, provedor=provedor)
        self._q_idx = 0
        if self._questoes:
            self._lbl_sync.config(text=f"{len(self._questoes)} questões", fg=self.FG2)
            self._atualizar_questao()
        else:
            self._lbl_sync.config(text="sem dados", fg=self.DANGER)
            self._limpar_ui()

    def _limpar_ui(self):
        """Limpa a UI quando não há questões para mostrar."""
        self.lbl_q_title.config(text="Nenhuma questão encontrada")
        self.lbl_area.config(text="")
        self.lbl_count.config(text="  ○  0 questões  ")
        try:
            self.txt_enun.delete("1.0", "end")
            self.ent_cmd.delete(0, "end")
            for letra in LETRAS:
                self.ent_alts[letra].delete("1.0", "end")
            self._gab_var.set("—")
        except Exception:
            pass
        for w in self.frame_imgs.winfo_children():
            w.destroy()
        self._thumbs = []

    # ── Dados ─────────────────────────────────────────────────────────────────
    def _atualizar_questao(self):
        if not self._questoes:
            self.lbl_q_title.config(text="Nenhuma questão encontrada")
            return

        resumo = self._questoes[self._q_idx]
        total  = len(self._questoes)

        cat = self._cat_atual
        f1  = self._var_f1.get()
        f2  = self._var_f2.get()

        self.lbl_count.config(text=f"  ◆  {self._q_idx + 1} de {total}  ")
        self.lbl_q_title.config(
            text=f"Questão {resumo['numero']:03d}  —  {cat} {f1} / {f2}")
        self.lbl_area.config(text=resumo.get("area", ""))
        self.ent_num.delete(0, "end")
        self.ent_num.insert(0, str(resumo["numero"]))
        self.lbl_enun_status.config(text="carregando…", fg=self.WARN)
        self.update_idletasks()

        # Busca dados completos (enunciado, alternativas, imagens, etc.)
        q_full = dl.buscar_questao(resumo["id"])
        if q_full:
            # Atualiza o item na lista local com dados completos (cache)
            self._questoes[self._q_idx] = q_full
            q = q_full
        else:
            q = resumo
            self.lbl_enun_status.config(text="⚠ falha ao buscar dados completos", fg=self.DANGER)

        # Enunciado
        enun = q.get("enunciado") or []
        self.txt_enun.delete("1.0", "end")
        self.txt_enun.insert("1.0",
            "\n\n".join(enun) if isinstance(enun, list) else str(enun))

        # Comando
        self.ent_cmd.delete(0, "end")
        self.ent_cmd.insert(0, q.get("comando") or "")

        # Alternativas
        alts = q.get("alternativas") or {}
        gab  = q.get("gabarito", "") or ""
        for letra in LETRAS:
            self.ent_alts[letra].delete("1.0", "end")
            self.ent_alts[letra].insert("1.0", alts.get(letra, ""))
        self._gab_var.set(gab if gab in LETRAS else "—")
        self._colorir_gabarito()

        self._atualizar_posicoes()
        self._atualizar_imgs_salvas(q)
        self.lbl_status.config(text="")
        self.lbl_enun_status.config(text="")

    def _colorir_gabarito(self, *_):
        """Destaca em verde o label da letra correta."""
        gab = self._gab_var.get()
        for letra, txt_widget in self.ent_alts.items():
            cor = self.OK if letra == gab else self.FG
            txt_widget._lbl_letra.config(fg=cor)

    def _salvar_alternativas(self):
        if not self._questoes:
            return
        q   = self._questoes[self._q_idx]
        num = q["numero"]

        alts = {}
        for letra in LETRAS:
            texto = self.ent_alts[letra].get("1.0", "end-1c").strip()
            if texto:
                alts[letra] = texto
        q["alternativas"] = alts

        gab = self._gab_var.get()
        q["gabarito"] = gab if gab in LETRAS else None

        self._salvar_questao_staging(q)
        self._colorir_gabarito()
        n = len(alts)
        self.lbl_alts_status.config(text=f"✓ {n} alternativa(s) no staging")
        self.focus_set()

    def _atualizar_posicoes(self, *_):
        """Reconstrói o dropdown de posições com base nos parágrafos atuais."""
        texto = self.txt_enun.get("1.0", "end-1c").strip()
        n = len([p for p in texto.split("\n\n") if p.strip()])
        opcoes = posicoes_para_n(n)
        labels = [lb for lb, _ in opcoes]
        self._posicao_map = {lb: val for lb, val in opcoes}
        atual = self._posicao_label_var.get()
        self.cb_posicao.config(values=labels)
        if atual in labels:
            self.cb_posicao.set(atual)
        elif labels:
            self.cb_posicao.set(labels[0])

    def _atualizar_imgs_salvas(self, q=None):
        if q is None:
            q = self._questoes[self._q_idx] if self._questoes else {}

        for w in self.frame_imgs.winfo_children():
            w.destroy()
        self._thumbs = []

        # Normalizar imagens para lista de dicts
        raw_imgs = q.get("imagens") or []
        imgs = [img_como_dict(item) for item in raw_imgs]

        alts = dict(q.get("imagens_alternativas") or {})
        alt_items = [(f"alt_{l}", r) for l, r in sorted(alts.items())]

        opcoes_remover = []  # lista de (label_display, path_rel)

        if not imgs and not alt_items:
            tk.Label(self.frame_imgs, text="Sem imagens", bg=self.CARD,
                     fg="#585b70", font=("Segoe UI", 8, "italic")).pack(pady=8)
        else:
            for item in imgs:
                path = item["path"]
                pos  = item.get("posicao") or ""
                self._render_thumb_card(path, f"enunciado · {pos or '—'}",
                                        opcoes_remover, posicao=pos)
            for tipo_label, path in alt_items:
                self._render_thumb_card(path, tipo_label, opcoes_remover, posicao="")

        # Dropdown de remoção: "posicao: filename"
        display_vals = [f"{p}: {r}" for p, r in opcoes_remover]
        self._remover_map = dict(zip(display_vals,
                                     [r for _, r in opcoes_remover]))
        self.cb_remover.config(values=display_vals)
        self.cb_remover.set(display_vals[0] if display_vals else "")

    def _render_thumb_card(self, rel: str, label: str,
                           opcoes_list: list, posicao: str = ""):
        fp = PASTA_IMG / rel
        card = tk.Frame(self.frame_imgs, bg=self.ENTRY_BG, pady=4)
        card.pack(fill="x", pady=2, padx=2)
        tk.Label(card, text=label, bg=self.ENTRY_BG, fg=self.ACC,
                 font=("Segoe UI", 7, "bold")).pack(anchor="w", padx=4)
        if fp.exists():
            try:
                th = pil_para_tk(Image.open(fp), THUMB_MAX)
                self._thumbs.append(th)
                tk.Label(card, image=th, bg=self.ENTRY_BG).pack(padx=4)
            except Exception:
                tk.Label(card, text="[erro ao ler]", bg=self.ENTRY_BG,
                         fg=self.DANGER, font=("Segoe UI", 7)).pack(padx=4)
            # ── Botões Ver / Recortar / Deletar ──────────────────────────
            row_btns = tk.Frame(card, bg=self.ENTRY_BG)
            row_btns.pack(fill="x", padx=4, pady=(2, 2))
            tk.Button(row_btns, text="👁 Ver",
                      bg="#2C2820", fg=self.FG, relief="flat",
                      font=("Segoe UI", 7), padx=4, pady=2, cursor="hand2",
                      command=lambda p=fp: JanelaVisualizacao(self, p)
                      ).pack(side="left", padx=(0, 2))
            tk.Button(row_btns, text="✂ Recortar",
                      bg="#2C2820", fg=self.WARN, relief="flat",
                      font=("Segoe UI", 7), padx=4, pady=2, cursor="hand2",
                      command=lambda p=fp: JanelaRecorte(
                          self, p,
                          callback=lambda _: self._atualizar_imgs_salvas())
                      ).pack(side="left", padx=(0, 2))
            tk.Button(row_btns, text="🗑 Deletar",
                      bg="#2C2820", fg=self.DANGER, relief="flat",
                      font=("Segoe UI", 7), padx=4, pady=2, cursor="hand2",
                      command=lambda r=rel: self._deletar_imagem(r)
                      ).pack(side="left")

            # ── Editor de posição (só para imagens de enunciado) ──────────
            if posicao is not None and not label.startswith("alt_"):
                texto = self.txt_enun.get("1.0", "end-1c").strip()
                n = len([p for p in texto.split("\n\n") if p.strip()])
                opcoes_pos = posicoes_para_n(n)
                labels_pos = [lb for lb, _ in opcoes_pos]
                pos_map    = {lb: val for lb, val in opcoes_pos}
                # Label correspondente à posição atual
                pos_label_atual = next(
                    (lb for lb, val in opcoes_pos if val == posicao),
                    labels_pos[0] if labels_pos else "")

                tk.Frame(card, bg="#2C2820", height=1).pack(
                    fill="x", padx=4, pady=(2, 4))
                tk.Label(card, text="Posição no layout:",
                         bg=self.ENTRY_BG, fg=self.FG2,
                         font=("Segoe UI", 7)).pack(anchor="w", padx=4)

                row_pos = tk.Frame(card, bg=self.ENTRY_BG)
                row_pos.pack(fill="x", padx=4, pady=(2, 2))

                pos_var = tk.StringVar(value=pos_label_atual)
                cb_pos  = ttk.Combobox(row_pos, values=labels_pos,
                                       textvariable=pos_var,
                                       width=16, state="readonly")
                cb_pos.pack(side="left", fill="x", expand=True, padx=(0, 3))

                tk.Button(row_pos, text="💾",
                          bg=self.BTN_SAV, fg=self.BTN_FG, relief="flat",
                          font=("Segoe UI", 8, "bold"), padx=5, pady=1,
                          cursor="hand2",
                          command=lambda r=rel, pv=pos_var, pm=pos_map:
                              self._salvar_posicao_imagem(r, pv.get(), pm)
                          ).pack(side="left")
        else:
            tk.Label(card, text="[arquivo não encontrado]",
                     bg=self.ENTRY_BG, fg=self.DANGER,
                     font=("Segoe UI", 7)).pack(padx=4)
        opcoes_list.append((label.split("·")[0].strip(), rel))

    def _salvar_posicao_imagem(self, rel: str, label: str, pos_map: dict):
        nova_pos = pos_map.get(label, "")
        if not nova_pos or not self._questoes:
            return
        q = self._questoes[self._q_idx]

        imgs = [img_como_dict(i) for i in (q.get("imagens") or [])]
        for item in imgs:
            if item["path"] == rel:
                item["posicao"] = nova_pos
                break
        q["imagens"] = imgs
        self._salvar_questao_staging(q)
        self.lbl_status.config(text=f"✓ Posição atualizada: {label}")
        self._atualizar_imgs_salvas(q)

    # ── Navegação ─────────────────────────────────────────────────────────────
    def _anterior(self):
        if self._questoes and self._q_idx > 0:
            self._q_idx -= 1
            self._atualizar_questao()

    def _proxima(self):
        if self._questoes and self._q_idx < len(self._questoes) - 1:
            self._q_idx += 1
            self._atualizar_questao()

    def _ir_para_numero(self):
        try:
            num = int(self.ent_num.get().strip())
        except ValueError:
            return
        for i, q in enumerate(self._questoes):
            if q["numero"] == num:
                self._q_idx = i
                self._atualizar_questao()
                return
        messagebox.showwarning("Não encontrada",
                               f"Q{num:03d} não encontrada.")

    # ── Salvar enunciado ──────────────────────────────────────────────────────
    def _salvar_enunciado(self):
        if not self._questoes:
            return
        q = self._questoes[self._q_idx]

        texto = self.txt_enun.get("1.0", "end-1c").strip()
        paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
        q["enunciado"] = paragrafos

        cmd = self.ent_cmd.get().strip()
        q["comando"] = cmd or None

        self._salvar_questao_staging(q)
        self.lbl_enun_status.config(
            text=f"✓ Staging — {len(paragrafos)} parágrafo(s)")
        self._atualizar_posicoes()
        self.focus_set()

    # ── Visualizar / recortar arquivo selecionado no painel direito ──────────
    def _ver_arquivo_sel(self):
        if not self._arquivo_sel or not self._arquivo_sel.exists():
            messagebox.showinfo("Aviso", "Selecione um arquivo de imagem primeiro.")
            return
        JanelaVisualizacao(self, self._arquivo_sel)

    def _recortar_arquivo_sel(self):
        if not self._arquivo_sel or not self._arquivo_sel.exists():
            messagebox.showinfo("Aviso", "Selecione um arquivo de imagem primeiro.")
            return

        def _apos_recorte(path: Path):
            self._arquivo_sel = path
            try:
                th = pil_para_tk(Image.open(path), PREVIEW_MAX)
                self._preview_tk = th
                self.lbl_preview.config(image=th, text="")
            except Exception:
                pass

        JanelaRecorte(self, self._arquivo_sel, callback=_apos_recorte)

    # ── Arquivo de imagem ─────────────────────────────────────────────────────
    def _procurar_arquivo(self):
        path = filedialog.askopenfilename(
            title="Selecionar imagem",
            filetypes=[("Imagens",
                        "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tif *.tiff"),
                       ("Todos", "*.*")],
        )
        if not path:
            return
        self._arquivo_sel = Path(path)
        self.lbl_arq.config(text=self._arquivo_sel.name)
        try:
            th = pil_para_tk(Image.open(self._arquivo_sel), PREVIEW_MAX)
            self._preview_tk = th
            self.lbl_preview.config(image=th, text="")
        except Exception as e:
            self.lbl_preview.config(text=f"Erro: {e}", image="")

    def _toggle_tipo(self):
        is_alt = self._tipo_var.get() == "alternativa"
        self.cb_letra.config(state="readonly" if is_alt else "disabled")
        # Posição só faz sentido para enunciado
        for w in self.frame_posicao.winfo_children():
            w.configure(state="disabled" if is_alt else "normal")
        self.cb_posicao.config(state="disabled" if is_alt else "readonly")

    # ── Adicionar imagem ──────────────────────────────────────────────────────
    def _adicionar_imagem(self):
        if not self._questoes:
            messagebox.showerror("Erro", "Nenhuma questão carregada.")
            return
        if not self._arquivo_sel or not self._arquivo_sel.exists():
            messagebox.showerror("Erro", "Selecione um arquivo de imagem.")
            return

        q    = self._questoes[self._q_idx]
        tipo = self._tipo_var.get()

        # Para ENEM extraímos ano/dia; para EXATO usamos evento/turno no path
        cat = self._cat_atual
        f1  = self._var_f1.get()
        f2  = self._var_f2.get()
        num = q["numero"]

        if cat == "ENEM":
            pasta_dest = PASTA_IMG / f1 / f2
        else:
            pasta_dest = PASTA_IMG / "exato" / f1.lower() / f2.lower()
        pasta_dest.mkdir(parents=True, exist_ok=True)

        if tipo == "enunciado":
            posicao_label = self._posicao_label_var.get()
            posicao_val   = self._posicao_map.get(posicao_label, "")

            if not posicao_val:
                messagebox.showerror("Erro", "Selecione uma posição para a imagem.")
                return

            # Normalizar imagens existentes para lista de dicts
            raw = q.get("imagens") or []
            imgs = [img_como_dict(i) for i in raw]

            # Verificar se já existe imagem nessa posição → substituir
            idx_existente = next(
                (i for i, it in enumerate(imgs) if it.get("posicao") == posicao_val),
                None)

            if idx_existente is not None:
                path_antigo = imgs[idx_existente]["path"]
                fp_antigo = PASTA_IMG / path_antigo
                if fp_antigo.exists():
                    fp_antigo.unlink()
                nome = Path(path_antigo).name
            else:
                idx  = proxima_idx(pasta_dest, f"q{num:03d}")
                nome = f"q{num:03d}_{idx}.jpg"

            if cat == "ENEM":
                rel = f"{f1}/{f2}/{nome}"
            else:
                rel = f"exato/{f1.lower()}/{f2.lower()}/{nome}"

            img_pil = Image.open(self._arquivo_sel).convert("RGB")
            img_pil.save(str(pasta_dest / nome), "JPEG", quality=JPEG_Q)

            img_bytes = (pasta_dest / nome).read_bytes()
            self._sync_supabase_imagem(img_bytes, rel)

            novo_item = {"path": rel, "posicao": posicao_val}

            if idx_existente is not None:
                imgs[idx_existente] = novo_item
            else:
                imgs.append(novo_item)

            q["imagens"]    = imgs
            q["tem_imagem"] = True

            msg = f"✓ Imagem no staging!\n{rel}\nPosição: {posicao_label}"

        else:  # alternativa
            letra = self._letra_var.get()
            nome  = f"q{num:03d}_alt_{letra.lower()}.jpg"
            if cat == "ENEM":
                rel = f"{f1}/{f2}/{nome}"
            else:
                rel = f"exato/{f1.lower()}/{f2.lower()}/{nome}"

            alts = dict(q.get("imagens_alternativas") or {})

            rel_antigo = alts.get(letra)
            if rel_antigo:
                fp = PASTA_IMG / rel_antigo
                if fp.exists():
                    fp.unlink()

            img_pil = Image.open(self._arquivo_sel).convert("RGB")
            img_pil.save(str(pasta_dest / nome), "JPEG", quality=JPEG_Q)

            img_bytes = (pasta_dest / nome).read_bytes()
            self._sync_supabase_imagem(img_bytes, rel)

            alts[letra] = rel
            q["imagens_alternativas"] = alts
            q["tem_imagem"] = True

            msg = f"✓ Alt {letra} no staging!\n{rel}"

        self._salvar_questao_staging(q)
        self.lbl_status.config(text=msg)
        self._atualizar_imgs_salvas(q)
        self._arquivo_sel = None
        self.lbl_arq.config(text="Nenhum arquivo selecionado")
        self.lbl_preview.config(image="", text="Selecione uma imagem")
        self._preview_tk = None

    # ── Remover imagem ────────────────────────────────────────────────────────
    def _remover_imagem(self):
        if not self._questoes:
            return
        display = self._img_rem_var.get()
        if not display:
            messagebox.showinfo("Aviso", "Nenhuma imagem selecionada.")
            return
        rel = self._remover_map.get(display, "")
        if not rel:
            return
        if not messagebox.askyesno("Confirmar",
                                   f"Remover '{rel}' do registro?\n"
                                   "(arquivo no disco não será deletado)"):
            return

        q = self._questoes[self._q_idx]

        # Remover de imagens (aceita string ou dict)
        raw  = q.get("imagens") or []
        imgs = [i for i in raw if img_path(i) != rel]
        q["imagens"] = imgs

        alts = dict(q.get("imagens_alternativas") or {})
        alts = {k: v for k, v in alts.items() if v != rel}
        q["imagens_alternativas"] = alts or None

        if not imgs and not alts:
            q["tem_imagem"] = False

        self._salvar_questao_staging(q)
        self.lbl_status.config(text="✓ Referência removida (staging).")
        self._atualizar_imgs_salvas(q)

    def _deletar_imagem(self, rel: str):
        """Remove da questão e apaga o arquivo do disco."""
        if not messagebox.askyesno(
            "Confirmar exclusão permanente",
            f"Deletar permanentemente:\n\n{rel}\n\n"
            "Remove do registro e apaga o arquivo do disco.\n"
            "Esta ação não pode ser desfeita.",
            icon="warning"
        ):
            return
        q = self._questoes[self._q_idx]

        imgs = [i for i in (q.get("imagens") or []) if img_path(i) != rel]
        q["imagens"] = imgs
        alts = {k: v for k, v in (q.get("imagens_alternativas") or {}).items()
                if v != rel}
        q["imagens_alternativas"] = alts or None
        if not imgs and not alts:
            q["tem_imagem"] = False

        self._salvar_questao_staging(q)

        fp = PASTA_IMG / rel
        if fp.exists():
            fp.unlink()

        self.lbl_status.config(text="🗑 Imagem deletada do disco (staging).")
        self._atualizar_imgs_salvas(q)

    def _deletar_imagem_selecionada(self):
        """Deleta a imagem escolhida no dropdown do painel direito."""
        display = self._img_rem_var.get()
        if not display:
            messagebox.showinfo("Aviso", "Nenhuma imagem selecionada.")
            return
        rel = self._remover_map.get(display, "")
        if rel:
            self._deletar_imagem(rel)

    # ── Salvamento via staging ────────────────────────────────────────────────
    def _salvar_questao_staging(self, q: dict):
        """Registra questão no staging e atualiza barra global."""
        st.registrar_questao(q)
        self._lbl_sync.config(text="● staging +1", fg=self.WARN)
        if self._on_staging_change:
            self._on_staging_change()

    def _sync_supabase_imagem(self, img_bytes: bytes, caminho_remoto: str):
        """Registra imagem no staging (sem gravar diretamente no Supabase)."""
        st.registrar_imagem(caminho_remoto, img_bytes)
        self._lbl_sync.config(text="● img staging", fg=self.WARN)
        if self._on_staging_change:
            self._on_staging_change()

    # ── Atalhos de teclado ────────────────────────────────────────────────────
    def _bind_teclado(self):
        self.bind("<Left>",  self._tecla_esquerda)
        self.bind("<Right>", self._tecla_direita)
        self.bind("<Up>",    self._tecla_cima)
        self.bind("<Down>",  self._tecla_baixo)
        # Ctrl+S e Ctrl+M no nível do frame
        for seq in ("<Control-s>", "<Control-S>"):
            self.bind(seq, lambda e: self._salvar_tudo() or "break")
        for seq in ("<Control-m>", "<Control-M>", "<Control-Return>"):
            self.bind(seq, lambda e: self._abrir_formula() or "break")
        self.bind("<Control-Shift-plus>",
                  lambda e: self._aplicar_formato("sup") or "break")
        self.bind("<Control-Shift-minus>",
                  lambda e: self._aplicar_formato("sub") or "break")
        self.bind("<Control-underscore>",
                  lambda e: self._aplicar_formato("sub") or "break")
        self.after(100, self._configurar_tab)

    def _configurar_tab(self):
        """Define ciclo de TAB entre os campos editáveis do painel central."""
        self._campos_texto = [
            self.txt_enun,
            self.ent_cmd,
            *[self.ent_alts[l] for l in LETRAS],
        ]
        self._tab_order = self._campos_texto + [self.cb_gab]

        for i, widget in enumerate(self._tab_order):
            prox = self._tab_order[(i + 1) % len(self._tab_order)]
            ant  = self._tab_order[(i - 1) % len(self._tab_order)]
            widget.bind("<Tab>",       lambda e, p=prox: self._focar(p) or "break")
            widget.bind("<Shift-Tab>", lambda e, a=ant:  self._focar(a) or "break")
            for seq in ("<Control-s>", "<Control-S>"):
                widget.bind(seq, lambda e: self._salvar_tudo() or "break")
            for seq in ("<Control-m>", "<Control-M>", "<Control-Return>"):
                widget.bind(seq, lambda e: self._abrir_formula() or "break")

        for w in self._campos_texto:
            w.bind("<FocusIn>", lambda e, campo=w: self._registrar_campo(campo), add="+")

        for cls in ("Text", "Entry"):
            for seq in ("<Control-s>", "<Control-S>"):
                self.txt_enun.bind_class(cls, seq,
                    lambda e: self._salvar_tudo() or "break", add="+")
            for seq in ("<Control-m>", "<Control-M>", "<Control-Return>"):
                self.txt_enun.bind_class(cls, seq,
                    lambda e: self._abrir_formula() or "break", add="+")

    def _registrar_campo(self, widget):
        """Atualiza qual campo editável está ativo — usado por _abrir_formula."""
        self._ultimo_campo = widget

    def _focar(self, widget):
        widget.focus_set()
        if isinstance(widget, tk.Text):
            widget.mark_set("insert", "end-1c")
            widget.see("end")

    def _abrir_formula(self):
        """Abre janela de fórmula atrelada ao último campo editável com foco."""
        try:
            campos = set(getattr(self, "_campos_texto", []))
            w = self.focus_get()
            if w not in campos:
                w = self._ultimo_campo
            if w is None or w not in campos:
                w = self.txt_enun

            if isinstance(w, tk.Text):
                cursor_pos = w.index("insert")
            else:
                cursor_pos = w.index(tk.INSERT)

            JanelaFormula(self, w, cursor_pos)
        except Exception as exc:
            messagebox.showerror("Erro — fórmula", str(exc))

    def _salvar_tudo(self):
        try:
            self._salvar_enunciado()
            self._salvar_alternativas()
            self.lbl_status.config(text="✓ Enunciado + alternativas no staging!")
        except Exception as exc:
            messagebox.showerror("Erro — salvar", str(exc))

    def _aplicar_formato(self, tipo: str):
        """
        Sobrescrito (sup) ou subscrito (sub) no campo de texto com foco.
        """
        w = self.focus_get()
        if not isinstance(w, tk.Text):
            return
        mapa      = SUPER_MAP if tipo == "sup" else SUB_MAP
        latex_cmd = "^"       if tipo == "sup" else "_"

        try:
            ini = w.index("sel.first")
            fim = w.index("sel.last")
            sel = w.get(ini, fim)

            todos_unicode = all(
                mapa.get(c.lower()) is not None
                for c in sel if not c.isspace()
            )

            if todos_unicode:
                convertido = _aplicar_mapa(sel, mapa)
                w.delete(ini, fim)
                w.insert(ini, convertido)
                w.tag_add("sel", ini, f"{ini}+{len(convertido)}c")
            else:
                latex = f"${latex_cmd}{{{sel}}}$"
                w.delete(ini, fim)
                w.insert(ini, latex)
                w.tag_add("sel", ini, f"{ini}+{len(latex)}c")

        except tk.TclError:
            placeholder = f"${latex_cmd}{{}}$"
            pos = w.index("insert")
            w.insert(pos, placeholder)
            w.mark_set("insert", f"{pos}+{len(latex_cmd) + 2}c")

    def _em_campo_texto(self) -> bool:
        """True se o foco está em campo de texto — setas devem funcionar normalmente."""
        return isinstance(self.focus_get(), (tk.Text, tk.Entry, ttk.Combobox))

    def _tecla_esquerda(self, event):
        if not self._em_campo_texto():
            self._anterior()

    def _tecla_direita(self, event):
        if not self._em_campo_texto():
            self._proxima()

    def _tecla_cima(self, event):
        if not self._em_campo_texto():
            self._prova_anterior()

    def _tecla_baixo(self, event):
        if not self._em_campo_texto():
            self._proxima_prova()

    def _proxima_prova(self):
        """Avança para o próximo subfiltro (dia/turno)."""
        f2_vals = list(self._cb_f2["values"])
        f2_atual = self._var_f2.get()
        if not f2_vals:
            return
        idx = f2_vals.index(f2_atual) if f2_atual in f2_vals else 0
        if idx < len(f2_vals) - 1:
            self._var_f2.set(f2_vals[idx + 1])
            self._load_questoes()
        else:
            # Tenta avançar no f1
            f1_vals = list(self._cb_f1["values"])
            f1_atual = self._var_f1.get()
            if f1_atual in f1_vals:
                idx1 = f1_vals.index(f1_atual)
                if idx1 < len(f1_vals) - 1:
                    self._var_f1.set(f1_vals[idx1 + 1])
                    if f2_vals:
                        self._var_f2.set(f2_vals[0])
                    self._load_questoes()

    def _prova_anterior(self):
        """Retrocede para o subfiltro anterior (dia/turno)."""
        f2_vals = list(self._cb_f2["values"])
        f2_atual = self._var_f2.get()
        if not f2_vals:
            return
        idx = f2_vals.index(f2_atual) if f2_atual in f2_vals else 0
        if idx > 0:
            self._var_f2.set(f2_vals[idx - 1])
            self._load_questoes()
        else:
            f1_vals = list(self._cb_f1["values"])
            f1_atual = self._var_f1.get()
            if f1_atual in f1_vals:
                idx1 = f1_vals.index(f1_atual)
                if idx1 > 0:
                    self._var_f1.set(f1_vals[idx1 - 1])
                    if f2_vals:
                        self._var_f2.set(f2_vals[-1])
                    self._load_questoes()
