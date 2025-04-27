from django.conf import settings
from pdf2image import pdfinfo_from_path, convert_from_path

from systems.plugins.index import BaseProvider

import pdfplumber
import pytesseract
import re


class Provider(BaseProvider('file_parser', 'pdf')):

    def parse_file(self, file_path):
        text = self._parse_extract_file(file_path)
        if text:
            return text
        return self._parse_ocr_file(file_path)


    def _parse_extract_file(self, file_path):
        with pdfplumber.open(file_path) as pdf:
            text = []
            for page in pdf.pages:
                page_lines = page.extract_text_lines(x_tolerance = 0.5, y_tolerance = 0.5)
                if page_lines:
                    for line in page_lines:
                        line = re.sub(r'\s+', ' ', line.get('text', '') if isinstance(line, dict) else line)
                        add_line = True
                        # Number check
                        try:
                            int(re.sub(r'\s+', '', line))
                            add_line = False
                        except ValueError:
                            pass

                        # Page footer check
                        if re.search(r'^[Pp]age\s*\d+', line):
                            add_line = False

                        if add_line:
                            text.append(line)

                text.append("\n")

        return "\n".join(text).strip()

    def _parse_ocr_file(self, file_path):
        max_pages = pdfinfo_from_path(file_path)['Pages']
        batch_size = settings.PDF_OCR_BATCH_SIZE
        text = []

        for page in range(1, max_pages + 1, batch_size):
            doc = convert_from_path(file_path,
                dpi = settings.PDF_OCR_DPI,
                first_page = page,
                last_page = min(page + (batch_size - 1), max_pages)
            )
            for page_number, page_data in enumerate(doc):
                page_text = pytesseract.image_to_string(page_data).encode("utf-8").decode().strip()
                if page_text:
                    text.append(re.sub(r'\n+\s+\n+', '\n\n', page_text))

            text.append("\n")

        return "\n".join(text).strip()

