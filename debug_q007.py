import sys, fitz, pytesseract, re
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

ZOOM = 300/72
doc = fitz.open(r"C:\Projetos\henryjr\dados\provas\2010\dia1.pdf")

# Q007 está nas primeiras páginas do dia1
for pg_num in range(2, 6):
    pagina = doc[pg_num]
    img = pagina.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), alpha=False)
    pil = Image.frombytes("RGB", [img.width, img.height], img.samples)
    largura = pil.size[0]

    for col_name, col_img in [
        ("ESQ", pil.crop((0, 0, largura//2+10, pil.size[1]))),
        ("DIR", pil.crop((largura//2-10, 0, largura, pil.size[1]))),
    ]:
        txt = pytesseract.image_to_string(col_img, lang="por", config="--oem 1 --psm 6")
        em_q7 = False
        for linha in txt.splitlines():
            if re.search(r'Quest[aã]o\s+7\b', linha, re.IGNORECASE):
                em_q7 = True
            if em_q7:
                print(repr(linha))
                if re.search(r'Quest[aã]o\s+8\b', linha, re.IGNORECASE):
                    em_q7 = False
                    break

doc.close()
