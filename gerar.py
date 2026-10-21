#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Gera folhas de desenho ABNT NBR 16752 (alinhada à ISO 5457 / ISO 7200)
para o TechDraw do FreeCAD, com legenda e quadro de revisões em português."""

import os
from xml.sax.saxutils import escape

FORMATOS = {
    "A0": (1189, 841),
    "A1": (841, 594),
    "A2": (594, 420),
    "A3": (420, 297),
    "A4": (210, 297),  # retrato
}

NS = 'https://www.freecad.org/wiki/index.php?title=Svg_Namespace'
FONT = "osifont"
LW_FRAME = 0.7
LW_THIN = 0.35
LBL = 2.2   # altura do texto dos rótulos
DAT = 3.5   # altura do texto dos dados

LEG_W = 180.0


def r(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


class Folha:
    def __init__(self, fmt, w, h):
        self.fmt, self.w, self.h = fmt, w, h
        self.out = []

    def add(self, s):
        self.out.append(s)

    def rect(self, x, y, w, h, lw=LW_THIN):
        self.add(f'<rect x="{r(x)}" y="{r(y)}" width="{r(w)}" height="{r(h)}" '
                 f'style="fill:none;stroke:#000000;stroke-width:{lw};stroke-linejoin:round"/>')

    def line(self, x1, y1, x2, y2, lw=LW_THIN):
        self.add(f'<path d="M {r(x1)},{r(y1)} L {r(x2)},{r(y2)}" '
                 f'style="fill:none;stroke:#000000;stroke-width:{lw};stroke-linecap:round"/>')

    def text(self, x, y, s, size=LBL, anchor="start", bold=False):
        fw = "bold" if bold else "normal"
        self.add(f'<text x="{r(x)}" y="{r(y)}" style="font-family:{FONT};font-size:{size}px;'
                 f'font-weight:{fw};text-anchor:{anchor};fill:#000000">{escape(s)}</text>')

    def field(self, x, y, name, value, size=DAT, anchor="start", autofill=None):
        af = f' freecad:autofill="{autofill}"' if autofill else ""
        self.add(f'<text x="{r(x)}" y="{r(y)}" freecad:editable="{name}"{af} '
                 f'style="font-family:{FONT};font-size:{size}px;text-anchor:{anchor};fill:#000000">'
                 f'<tspan>{escape(value)}</tspan></text>')

    def cell(self, x, y, w, h, label, name=None, value="", size=DAT, anchor="start", autofill=None):
        self.rect(x, y, w, h)
        if label:
            self.text(x + 0.8, y + LBL + 0.6, label)
        if name:
            if anchor == "middle":
                fx = x + w / 2
            else:
                fx = x + 1.2
            self.field(fx, y + h - 1.6, name, value, size, anchor, autofill)

    # ---------------------------------------------------------------
    def moldura(self):
        w, h = self.w, self.h
        # margens NBR 16752 / ISO 5457: 20 mm à esquerda, 10 mm nas demais
        self.fx0, self.fy0 = 20.0, 10.0
        self.fx1, self.fy1 = w - 10.0, h - 10.0
        self.rect(self.fx0, self.fy0, self.fx1 - self.fx0, self.fy1 - self.fy0, LW_FRAME)
        # marcas de centro
        cx, cy = w / 2, h / 2
        self.line(cx, 5, cx, self.fy0 + 5, LW_FRAME)
        # no A4 a legenda ocupa o centro inferior: a marca para na moldura
        self.line(cx, h - 5, cx, self.fy1 if self.fmt == "A4" else self.fy1 - 5, LW_FRAME)
        self.line(5, cy, self.fx0 + 5, cy, LW_FRAME)
        self.line(w - 5, cy, self.fx1 - 5, cy, LW_FRAME)
        if self.fmt != "A4":
            self.zonas()

    def zonas(self):
        """Sistema de referência por zonas (campos de 50 mm a partir do centro)."""
        w, h = self.w, self.h
        bx0, by0, bx1, by1 = 15.0, 5.0, w - 5.0, h - 5.0
        self.rect(bx0, by0, bx1 - bx0, by1 - by0, LW_THIN)

        def divisoes(a0, a1, c):
            pos = []
            k = 1
            while c - 50 * k > a0 + 10:
                pos.append(c - 50 * k)
                k += 1
            k = 1
            while c + 50 * k < a1 - 10:
                pos.append(c + 50 * k)
                k += 1
            pos.append(c)
            return sorted(pos)

        cx, cy = w / 2, h / 2
        xs = divisoes(self.fx0, self.fx1, cx)
        ys = divisoes(self.fy0, self.fy1, cy)
        # O centro também é divisa de zona; ali a marca de centragem faz o papel da linha.
        for x in xs:
            if abs(x - cx) > 1e-6:
                self.line(x, by0, x, self.fy0)
                self.line(x, by1, x, self.fy1)
        for y in ys:
            if abs(y - cy) > 1e-6:
                self.line(bx0, y, self.fx0, y)
                self.line(bx1, y, self.fx1, y)
        # rótulos
        bx = [self.fx0] + xs + [self.fx1]
        by = [self.fy0] + ys + [self.fy1]
        letras = "ABCDEFGHJKLMNPRSTUVWXYZ"  # sem I e O
        for i in range(len(bx) - 1):
            m = (bx[i] + bx[i + 1]) / 2
            self.text(m, 8.8, str(i + 1), 3.5, "middle")
            self.text(m, h - 6.2, str(i + 1), 3.5, "middle")
        for j in range(len(by) - 1):
            m = (by[j] + by[j + 1]) / 2 + 1.2
            self.text(17.5, m, letras[j], 3.5, "middle")
            self.text(w - 7.5, m, letras[j], 3.5, "middle")

    # ---------------------------------------------------------------
    def legenda(self):
        x0 = self.fx1 - LEG_W
        yb = self.fy1
        rows = [9.0, 12.0, 9.0, 16.0, 12.0]  # de baixo para cima
        ys = [yb]
        for hh in rows:
            ys.append(ys[-1] - hh)
        top = ys[-1]
        self.leg_top = top
        self.rect(x0, top, LEG_W, yb - top, LW_FRAME)

        # linha 1 (topo): empresa | cliente | projeto
        y = ys[5]; hh = rows[4]
        self.cell(x0, y, 60, hh, "EMPRESA / PROPRIETÁRIO", "empresa", "NOME DA EMPRESA", 3.5, autofill="organization")
        self.cell(x0 + 60, y, 60, hh, "CLIENTE", "cliente", "", 3.5)
        self.cell(x0 + 120, y, 60, hh, "PROJETO / CONTRATO / OM", "projeto", "", 3.5)

        # linha 2: título | material
        y = ys[4]; hh = rows[3]
        self.rect(x0, y, 125, hh)
        self.text(x0 + 0.8, y + LBL + 0.6, "TÍTULO")
        self.field(x0 + 1.2, y + 8.6, "titulo", "TÍTULO DO DESENHO", 5, autofill="title")
        self.field(x0 + 1.2, y + 14.2, "subtitulo", "Subtítulo", 3.5)
        self.rect(x0 + 125, y, 55, hh)
        self.text(x0 + 125.8, y + LBL + 0.6, "MATERIAL")
        self.field(x0 + 126.2, y + 8.6, "material", "", 3.5)
        self.field(x0 + 126.2, y + 14.2, "material_2", "", 3.5)

        # linha 3: responsáveis e escala
        y = ys[3]; hh = rows[2]
        xs = x0
        for lab, nm, af in (("DESENHO", "desenhado", "author"),
                            ("VERIFICADO", "verificado", None),
                            ("APROVADO", "aprovado", None)):
            self.cell(xs, y, 34, hh, lab, nm, "", 3.0, autofill=af)
            self.cell(xs + 34, y, 20, hh, "DATA", "data_" + nm, "", 3.0,
                      autofill=("date" if nm == "desenhado" else None))
            xs += 54
        self.cell(xs, y, 18, hh, "ESCALA", "escala", "1:1", 3.5, "middle", autofill="scale")

        # linha 4: número, revisão, folha, formato, unidade, diedro, ART
        y = ys[2]; hh = rows[1]
        self.cell(x0, y, 66, hh, "Nº DO DESENHO", "numero", "XX-XXX-000", 5)
        self.cell(x0 + 66, y, 14, hh, "REV.", "revisao", "0", 5, "middle")
        self.cell(x0 + 80, y, 18, hh, "FOLHA", "folha", "1/1", 3.5, "middle", autofill="sheet")
        self.rect(x0 + 98, y, 16, hh)
        self.text(x0 + 98.8, y + LBL + 0.6, "FORMATO")
        self.text(x0 + 106, y + hh - 1.6, self.fmt, 5, "middle")
        self.cell(x0 + 114, y, 14, hh, "UNIDADE", "unidade", "mm", 3.5, "middle")
        self.rect(x0 + 128, y, 22, hh)
        self.text(x0 + 128.8, y + LBL + 0.6, "1º DIEDRO")
        self.diedro(x0 + 139, y + 7.3)
        self.cell(x0 + 150, y, 30, hh, "ART / CREA", "art", "", 3.0)

        # linha 5 (base): tolerância geral | observação / situação
        y = ys[1]; hh = rows[0]
        self.cell(x0, y, 90, hh, "TOLERÂNCIA GERAL", "tolerancia", "ISO 2768-m", 3.0)
        self.cell(x0 + 90, y, 90, hh, "SITUAÇÃO", "situacao", "EM ELABORAÇÃO", 3.0)

    def diedro(self, cx, cy):
        """Símbolo do 1º diedro (ISO 128 / NBR 16752), altura total 6 mm."""
        lw = 0.35
        st = f'style="fill:none;stroke:#000000;stroke-width:{lw}"'
        # tronco de cone (vista de frente) à esquerda, círculos à direita
        self.add(f'<path d="M {r(cx-1.5)},{r(cy-2.25)} L {r(cx-7.5)},{r(cy-1.2)} L {r(cx-7.5)},{r(cy+1.2)} '
                 f'L {r(cx-1.5)},{r(cy+2.25)} Z" {st}/>')
        self.add(f'<circle cx="{r(cx+3.5)}" cy="{r(cy)}" r="2.25" {st}/>')
        self.add(f'<circle cx="{r(cx+3.5)}" cy="{r(cy)}" r="1.2" {st}/>')

    def revisoes(self, n=4):
        x0 = self.fx1 - LEG_W
        rh = 5.0
        cols = [("REV.", 12), ("DESCRIÇÃO", 110), ("POR", 30), ("DATA", 28)]
        y = self.leg_top
        # cabeçalho logo acima da legenda; linhas de revisão crescem para cima
        y -= rh
        xs = x0
        for lab, cw in cols:
            self.rect(xs, y, cw, rh)
            self.text(xs + cw / 2, y + 3.6, lab, LBL, "middle")
            xs += cw
        for i in range(1, n + 1):
            y -= rh
            xs = x0
            for k, (lab, cw) in enumerate(cols):
                self.rect(xs, y, cw, rh)
                nm = ["rev", "rev_descricao", "rev_por", "rev_data"][k] + f"_{i}"
                anchor = "middle" if k in (0, 3) else "start"
                fx = xs + cw / 2 if anchor == "middle" else xs + 1.2
                self.field(fx, y + 3.7, nm, "", 2.8, anchor)
                xs += cw
        self.rect(x0, y, LEG_W, self.leg_top - y, LW_FRAME)

    def svg(self):
        self.moldura()
        self.legenda()
        self.revisoes()
        orient = "Retrato" if self.h > self.w else "Paisagem"
        title = f"Folha ABNT NBR 16752 - {self.fmt} {orient}"
        head = (f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:freecad="{NS}" version="1.1" '
                f'width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}">\n'
                f'<title>{title}</title>\n'
                f'<!-- Gerado por gerar.py - FreeCAD Templates ABNT - licença CC0 1.0 -->\n')
        return head + "\n".join(self.out) + "\n</svg>\n"


def main():
    od = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Templates")
    os.makedirs(od, exist_ok=True)
    for fmt, (w, h) in FORMATOS.items():
        orient = "Retrato" if h > w else "Paisagem"
        fn = os.path.join(od, f"{fmt}_{orient}_ABNT_NBR16752.svg")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(Folha(fmt, w, h).svg())
        print(fn)


if __name__ == "__main__":
    main()
