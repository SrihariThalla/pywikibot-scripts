import os

from PyInquirer import prompt

from wiki_citations_archival.citations import Citations

q = {
    'type': 'confirm',
    'name': 'start',
    'message': 'Start new work?',
}

citations = Citations()

while True:
    a = prompt(q)

    if not a['start']:
        break

    os.system('clear')

    citations.process()
