import os

from PyInquirer import prompt

from boundaries.mandals import Mandals
from boundaries.wiki_mandals import WikiMandals

q = {
    'type': 'confirm',
    'name': 'start',
    'message': 'Start new work?',
}

# mandals = Mandals()
mandals = WikiMandals()
mandals.process()

# while True:
    # os.system('clear')
    #
    # a = prompt(q)
    #
    # if not a['start']:
    #     break
    #
    # mandals.process()
