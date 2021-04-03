import pywikibot
from colorama import Fore, Style
from pywikibot import pagegenerators

from lib.functions import Functions


def query_wikidata():
    query = """
            SELECT ?item WHERE {
                ?item wdt:P31 wd:Q55488;
                      wdt:P127 wd:Q819425;
                      wdt:P5696 [];
                      wdt:P137 [ wdt:P31 wd:Q63383608 ].
            }
            """

    print('Loading Wikidata items')

    gen = pagegenerators.PreloadingEntityGenerator(pagegenerators.WikidataSPARQLPageGenerator(query))

    items = []
    for item in gen:
        items.append(item)

    return items


class WikidataOperator:
    def __init__(self):
        self.functions = Functions()
        self.functions.prepare_zones_dict()

    def process_wikidata_items(self):
        for item in query_wikidata():
            if 'P5696' not in item.claims or len(item.claims['P5696']) != 1:
                print()
                print('P5696 code is not valid')
                print(item)

                continue

            label = item.labels.get('en', None)
            p5696 = item.claims['P5696'][0].getTarget()
            rbs_data = self.functions.query_firebase(p5696, True, label)

            if len(rbs_data['data']) == 0:
                # print()
                # print(f'{item.getID()} - {item.full_url()} - {p5696} - {label} - {Fore.RED}No RBS data{Style.RESET_ALL}')

                continue

            if 'P137' in item.claims:

                for operator in item.claims['P137']:
                    print()
                    print(f'Operator already tagged {item.getID()} - {item.full_url()} - {label} - {operator.getTarget()}')

                continue

            print()
            print(f'{item.getID()} - {item.full_url()} - {p5696} {label}')
