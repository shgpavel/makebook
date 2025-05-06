#!/usr/bin/env python3

from pypdf import PdfReader, PdfWriter, Transformation
import os
import sys
import math
from pypdf._page import PageObject


def best_quire_size(total_pages, min_quire=4, max_quire=20):
    best_n = None
    best_remainder = total_pages
    for n in range(min_quire, max_quire + 1):
        quire_pages = 4 * n
        remainder = (quire_pages - (total_pages % quire_pages)) % quire_pages
        if remainder < best_remainder:
            best_n = n
            best_remainder = remainder
    return best_n, best_remainder


def paginate_quire(pages):
    sheets = []
    n = len(pages)
    left = 0
    right = n - 1
    while left < right:
        sheets.append((pages[right], pages[left]))
        left += 1
        right -= 1
    if left == right:
        sheets.append((None, pages[left]))
    return sheets


def build_booklet_order(total_pages, quire_size):
    quire_pages = 4 * quire_size
    all_pages = list(range(1, total_pages + 1))
    while len(all_pages) % quire_pages != 0:
        all_pages.append(None)

    front_order = []
    back_order = []

    for q in range(0, len(all_pages), quire_pages):
        q_pages = all_pages[q : q + quire_pages]
        sheet_order = []
        while q_pages:
            sheet = [q_pages.pop(-1), q_pages.pop(0), q_pages.pop(0), q_pages.pop(-1)]
            sheet_order.append(sheet)
        for sheet in sheet_order:
            front_order.extend([sheet[0], sheet[1]])
            back_order.extend([sheet[2], sheet[3]])

    return front_order, back_order


def save_pdf_2up(input_pdf, output_pdf, page_order, page_size=(842.0, 595.0)):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for i in range(0, len(page_order), 2):
        writer.add_blank_page(width=page_size[0], height=page_size[1])
        new_page = writer.pages[-1]

        for j, offset_x in enumerate([0, page_size[0] / 2]):
            index = i + j
            if index >= len(page_order):
                continue

            p = page_order[index]
            if p is None:
                continue

            src = reader.pages[p - 1]
            src_width = float(src.mediabox.width)
            src_height = float(src.mediabox.height)

            target_width = page_size[0] / 2
            target_height = page_size[1]

            scale = target_height / src_height
            scaled_width = src_width * scale

            translate_x = offset_x + (target_width - scaled_width) / 2
            translate_y = 0

            t = Transformation().scale(scale).translate(tx=translate_x, ty=translate_y)
            new_page.merge_transformed_page(src, t)

    with open(output_pdf, "wb") as f:
        writer.write(f)


def main():
    if len(sys.argv) != 2:
        print("Usage: ./main.py <input.pdf>")
        sys.exit(1)

    input_pdf = sys.argv[1]

    if not os.path.isfile(input_pdf):
        print(f"Error: File '{input_pdf}' does not exist")
        sys.exit(1)

    if not input_pdf.lower().endswith(".pdf"):
        print("Error: Input file must be a PDF")
        sys.exit(1)

    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)

    if total_pages < 9:
        print("Error: Input pdf is small (less than 4 pages)")
        sys.exit(1)

    quire_size, blanks = best_quire_size(total_pages)
    print(f"Optimal quire size: {quire_size} sheets ({4 * quire_size} pages)")
    print(f"Blanks: {blanks}")

    front_order, back_order = build_booklet_order(total_pages, quire_size)

    save_pdf_2up(input_pdf, "booklet-front.pdf", front_order)
    save_pdf_2up(input_pdf, "booklet-back.pdf", back_order)
    print("Created booklet-front.pdf and booklet-back.pdf")


if __name__ == "__main__":
    main()
