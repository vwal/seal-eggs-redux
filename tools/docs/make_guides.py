"""Build printable release documents using Python 3, ReportLab and pypdf.

From any directory, run python3 path/to/make_guides.py. The default destination
is the repository's docs directory. Use --output DIR for a local proof.
"""

import argparse
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from guide_content import DOCUMENTS, LED_COLORS

INK = "#182D2C"
TEXT = "#233534"
MUTED = "#425E5A"
TEAL = "#165F56"
LINE = "#BBCFCB"
TINT = "#EDF5F2"
PALE = "#F5F8F7"
WHITE = "#FFFFFF"
SITE = "https://vwal.github.io/seal-eggs-redux/"
LICENSE_URL = SITE + "LICENSE.txt"
SEAL_EGGS_NOTICE_PATH = "notices/Seal-Eggs-LICENSE.md"
SEAL_EGGS_LICENSE_URL = SITE + SEAL_EGGS_NOTICE_PATH
REPOSITORY = Path(__file__).resolve().parents[2]
NOTICES = ("LICENSE.txt", "THIRD-PARTY.md", SEAL_EGGS_NOTICE_PATH,
           "notices/Beads-MIT.txt", "notices/LICENSE-beads.txt",
           "vendor/INTELLIJEL-LICENSE.txt", "vendor/WEBDFU-LICENSE.txt")


def color(s):
    return HexColor(s)


def paragraph(value, size=10.25, leading=None, bold=False, tint=TEXT):
    # Content uses only the short ReportLab markup produced by guide_content.
    for label, shade in LED_COLORS.items():
        value = value.replace("{" + label + "}", '<font color="' + shade + '">●</font> ' + label)
    style = ParagraphStyle("text", fontName="Helvetica-Bold" if bold else "Helvetica",
                           fontSize=size, leading=leading or size * 1.27, textColor=color(tint),
                           alignment=TA_LEFT, spaceAfter=0, spaceBefore=0, splitLongWords=False)
    return Paragraph(value, style)


def line(canvas, x, y, right, tint=LINE, weight=.55):
    canvas.setStrokeColor(color(tint))
    canvas.setLineWidth(weight)
    canvas.line(x, y, right, y)


def wrap(value, width, **style):
    item = paragraph(value, **style)
    _, height = item.wrap(width, 2000)
    return item, height


@dataclass
class Block:
    height: float
    draw: object


def section(title, width):
    return Block(23, lambda c, x, y: draw_section(c, x, y, title, width))


def draw_section(c, x, y, title, width):
    c.setFont("Helvetica-Bold", 13.4)
    c.setFillColor(color(TEAL))
    c.drawString(x, y - 14, title)


def textblock(content, width):
    item, height = wrap(content, width)
    return Block(height + 2, lambda c, x, y: item.drawOn(c, x, y - height))


def callout(title, content, width):
    item, h = wrap(content, width - 26, size=10.2)
    total = h + 33

    def draw(c, x, y):
        c.setFillColor(color(TINT))
        c.roundRect(x, y - total, width, total, 4, stroke=0, fill=1)
        c.setFillColor(color(TEAL))
        c.rect(x, y - total, 3.5, total, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 10.6)
        c.drawString(x + 13, y - 14, title)
        item.drawOn(c, x + 13, y - 21 - h)

    return Block(total, draw)


def table(headers, proportions, rows, width, small=False):
    columns = [width * p for p in proportions]
    assert abs(sum(columns) - width) < .02
    prepared = []
    for ri, row in enumerate([headers, *rows]):
        assert len(row) == len(columns)
        is_header = ri == 0
        if is_header:
            top, bottom = 6, 5
        elif small:
            top, bottom = 4.6, 4.6
        else:
            top, bottom = 5.5, 5.5
        cells = [wrap(cell, col - 14, size=8.35 if is_header else (9.45 if small else 10.05),
                      tint=WHITE if is_header else (INK if i == 0 else TEXT),
                      bold=is_header or i == 0) for i, (cell, col) in enumerate(zip(row, columns))]
        prepared.append((is_header, top, max(h for _, h in cells) + top + bottom, cells))
    height = sum(row[2] for row in prepared)

    def draw(c, x, y):
        for ri, (is_header, top, rh, cells) in enumerate(prepared):
            if is_header or ri % 2 == 0:
                c.setFillColor(color(TEAL if is_header else PALE))
                c.rect(x, y-rh, width, rh, stroke=0, fill=1)
            xx = x
            for col, (item, h) in zip(columns, cells):
                item.drawOn(c, xx + 7, y - top - h)
                xx += col
            y -= rh
            if not is_header:
                line(c, x, y, x + width)

    return Block(height, draw)


def draw_pdf(filename, title, pages, size):
    rendered = BytesIO()
    c = Canvas(rendered, pagesize=size, invariant=1, pageCompression=1)
    c.setTitle(f"Seal Eggs Redux 1.3.5.0+c | {title}")
    c.setAuthor("Seal Eggs Redux project")
    c.setSubject("Operating reference for the Intellijel Sealegs community firmware")
    c.setCreator("Seal Eggs Redux documentation")
    w, h = size
    m = 38
    area = w - 2 * m
    for index, (heading, summary, contents) in enumerate(pages, 1):
        c.bookmarkPage(f"p{index}")
        c.addOutlineEntry(heading, f"p{index}")
        c.setFillColor(color(TEAL))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(m, h - 38, "SEAL EGGS REDUX")
        c.setFont("Helvetica", 10)
        c.drawString(m + 101, h - 38, " /  " + title)
        c.setFont("Courier-Bold", 10)
        c.drawRightString(w - m, h - 38, "1.3.5.0+c")
        line(c, m, h - 47, w - m, TEAL, 1)
        c.setFont("Helvetica-Bold", 27)
        c.setFillColor(color(INK))
        if c.stringWidth(heading, "Helvetica-Bold", 27) > area:
            raise ValueError(f"Overlong heading {heading}")
        c.drawString(m, h - 80, heading)
        subtitle, sh = wrap(summary, area, size=11.0, tint=MUTED)
        subtitle.drawOn(c, m, h - 90 - sh)
        y = h - 100 - sh
        blocks = []
        for kind, args in contents:
            if kind == "heading":
                b = section(args, area)
            elif kind == "p":
                b = textblock(args, area)
            elif kind == "note":
                b = callout(*args, area)
            else:
                headers, ratios, rows = args
                b = table(headers, ratios, rows, area, small=kind == "compact")
            blocks.append((kind, b))
        # Sections breathe more on the taller sheet. Table text remains at the
        # same physical size in both formats.
        fixed = sum(b.height for _, b in blocks)
        room = y - 55 - fixed
        units = sum((1 if k == "heading" else .38) for k, _ in blocks[1:])
        gap = min(11.5, room / max(1, units))
        if gap < -0.01:
            raise ValueError(f"{filename.name} p{index} overflows by {-room:.1f}pt")
        for i, (kind, b) in enumerate(blocks):
            if i:
                y -= gap * (1 if kind == "heading" else .38)
            b.draw(c, m, y)
            y -= b.height
        line(c, m, 42, w - m, LINE)
        c.setFont("Helvetica", 8.2)
        c.setFillColor(color(MUTED))
        attribution = "© 2026 vwal  ·  Attribution / No Sale  ·  "
        c.drawString(m, 31, attribution)
        link_x = m + c.stringWidth(attribution, "Helvetica", 8.2)
        license_label = LICENSE_URL.removeprefix("https://")
        c.setFillColor(color(TEAL))
        c.drawString(link_x, 31, license_label)
        c.linkURL(LICENSE_URL, (link_x, 29, link_x + c.stringWidth(license_label, "Helvetica", 8.2), 39),
                  relative=0, thickness=0)
        c.setFillColor(color(MUTED))
        c.drawRightString(w - m, 31, f"{title}   /   {index} of {len(pages)}")
        notice = "Required Notice: Copyright 2026 Bribery (https://thisisbribery.com)"
        c.drawString(m, 20, notice)
        notice_x = m + c.stringWidth(notice + "   ·   ", "Helvetica", 8.2)
        notice_label = SEAL_EGGS_LICENSE_URL.removeprefix("https://")
        c.setFillColor(color(TEAL))
        c.drawString(notice_x, 20, notice_label)
        c.linkURL(SEAL_EGGS_LICENSE_URL,
                  (notice_x, 18, notice_x + c.stringWidth(notice_label, "Helvetica", 8.2), 28),
                  relative=0, thickness=0)
        c.showPage()
    c.save()
    # Printed copies carry the legible URL. Digital copies also contain the
    # unabridged release terms and the original third-party notices as text.
    rendered.seek(0)
    writer = PdfWriter(clone_from=rendered)
    for notice in NOTICES:
        path = REPOSITORY / notice
        writer.add_attachment(path.name, path.read_bytes())
    with filename.open("wb") as output:
        writer.write(output)
    writer.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[2] / "docs")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for slug, title, pages in DOCUMENTS:
        for paper, size in (("letter", letter), ("a4", A4)):
            draw_pdf(args.output / f"sealegs-redux-{slug}-{paper}.pdf", title, pages, size)


if __name__ == "__main__":
    main()
