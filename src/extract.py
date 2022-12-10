import logging
import re
from typing import List

import pandas as pd
from PyPDF2 import PdfReader, PdfFileReader



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract():
    file = 'src/data/raw/eresumen_visa_202211.pdf'

    # reader = PdfReader(file)
    # page = reader.pages[0]

    f = open(file, 'rb')
    reader = PdfFileReader(f)
    page = reader.getPage(0)
    text = page.extract_text().split('\n')

    # print(text)

    intervals = [0, 0]

    for line_nb, line in enumerate(text):
        if re.search('BONIFICACION ACUERDOS GLOBALES', line) != None:
            intervals[0] = line_nb

        if re.search('SALDO ACTUAL', line) != None:
            intervals[1] = line_nb

        # print(f'{line_nb} | {line}')
        # print(f'{line}')

    print()
    print(intervals)
    print()

    data_text: List[int] = text[intervals[0]:intervals[1]]

    date_column: List[str] = []

    # date_pattern = re.compile(r'(.[\d]..[\d]..[\d])')
    pattern = re.compile(r'(\d\d.\d\d.\d\d).*d\.*')

    for line_nb, line in enumerate(data_text):
        # print(f'{line_nb} | {line}')
        # print(f'{line}')
        data = re.match(pattern, line)
        print(data)
        
        if data:
            date_column.append(data.group(1).replace('.', '/'))

    print(date_column)


if __name__ == '__main__':
    extract()
