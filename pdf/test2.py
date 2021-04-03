import os
from pprint import pprint
from typing import Dict

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox
from py_pdf_parser import tables
from py_pdf_parser.components import PDFDocument
from py_pdf_parser.loaders import load_file, Page

# path = os.path.join(os.path.dirname(__file__), 'simple_memo.pdf')
path = os.path.join(os.path.dirname(__file__), '2817_PART_B_DCHB_GUNTUR.pdf')
# document = load_file(path)

# Step 2 - Extract reference elements:
# to_element = document.elements.filter_by_text_equal('TO:').extract_single_element()
# from_element = document.elements.filter_by_text_equal('FROM:').extract_single_element()
# date_element = document.elements.filter_by_text_equal('DATE:').extract_single_element()
# subject_element = document.elements.filter_by_text_equal(
#     'SUBJECT:'
# ).extract_single_element()
#
# Step 3 - Extract the data
# to_text = document.elements.to_the_right_of(to_element).extract_single_element().text()
# from_text = (
#     document.elements.to_the_right_of(from_element).extract_single_element().text()
# )
# date_text = (
#     document.elements.to_the_right_of(date_element).extract_single_element().text()
# )
# subject_text_element = document.elements.to_the_right_of(
#     subject_element
# ).extract_single_element()
# subject_text = subject_text_element.text()
#
# content_elements = document.elements.after(subject_element)
# content_text = '\n'.join(element.text() for element in content_elements)
#
# output = {
#     'to': to_text,
#     'from': from_text,
#     'date': date_text,
#     'subject': subject_text,
#     'content': content_text,
# }

# pprint(output)

# pprint(dir(document))
# page = document.get_page(28)
# pprint(page.elements)

FONT_MAPPING = {
    'BookmanOldStyle-Bold,13.3': 'title',
    'BookmanOldStyle,7.6': 'sub_text',
    'BookmanOldStyle-Bold,10.5': 'table_header',
    'BookmanOldStyle,10.5': 'table_header',
    'Calibri,9.5': 'table_text',
    'Calibri,10.5': 'page_number',
}

def extract():
    pages: Dict[int, Page] = {}

    for page in extract_pages(path, page_numbers=[27]):
        elements = [element for element in page if isinstance(element, LTTextBox)]

        pages[page.pageid] = Page(width=page.width, height=page.height, elements=elements)

    return PDFDocument(pages=pages, pdf_file_path=path, font_mapping=FONT_MAPPING)

page = extract()

for element in page.elements:
    # pprint(element)
    # pprint(dir(element))
    pprint({
        'font': element.font,
        'text': element.text(),
    })

headers = page.elements.filter_by_font('table_header')

district_header = headers.filter_by_text_equal('District').extract_single_element()
towns_header = headers.filter_by_text_equal('Number of Towns').extract_single_element()

villages_table_elements = page.elements.between(district_header, towns_header)

table = tables.extract_table(villages_table_elements, as_text=True)

pprint(table)

data = []
for row in table:
    for col in row:
        data.append(list(filter(bool, [str.strip() for str in col.splitlines()])))

pprint(data)

stats = {
    'villages': {
        'total': int(data[3][0].replace(',', '')),
        'inhabited': int(data[3][1].replace(',', '')),
        'uninhabited': int(data[3][2].replace(',', '')),
    }
}

pprint(stats)
