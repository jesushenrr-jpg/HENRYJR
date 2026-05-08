import sys, fitz, pytesseract, re
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

ZOOM = 300/72
doc = fitz.open(r"C:\Projetos\henryjr\dados\provas\2010\dia1.pdf")

pagina = doc[3]
img = pagina.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), alpha=False)
pil = Image.frombytes("RGB", [img.width, img.height], img.samples)
largura = pil.size[0]

col_dir = pil.crop((largura//2 - 10, 0, largura, pil.size[1]))
txt = pytesseract.image_to_string(col_dir, lang="por", config="--oem 1 --psm 6")

# Encontra Q012 e imprime linhas ao redor com repr
linhas = txt.splitlines()
em_q12 = False
for i, linha in enumerate(linhas):
    if re.search(r'Quest[aã]o\s+12', linha, re.IGNORECASE):
        em_q12 = True
    if em_q12:
        print(repr(linha))
