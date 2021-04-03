import pywikibot
from PyInquirer import prompt
from colorama import Fore, Style

from pywikibot import pagegenerators as pg


def query_wikidata(site):
    query = f"""
            SELECT ?item ?itemLabel WHERE {{
                SERVICE wikibase:mwapi {{
                    bd:serviceParam wikibase:endpoint "en.wikipedia.org";     
                    wikibase:api "Generator";
                    mwapi:generator "categorymembers";        
                    mwapi:gcmtitle "Category:Delhi Metro stations";.
                    ?item wikibase:apiOutputItem mwapi:item.
                }}
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}    
            }}
            """

    items = list(pg.WikidataSPARQLPageGenerator(query, site))

    return items


should_edit = [
    {
        'type': 'confirm',
        'name': 'confirm',
        'message': 'Should update the EN label?',
        'default': False,
    },
]
site = pywikibot.Site('wikidata', 'wikidata')

items = query_wikidata(site)

for item in items:
    item.get()
    en_label = item.labels.get('en', 'Not found')

    wiki = item.sitelinks.get('enwiki')
    wiki_title = '' if wiki is None else wiki.title

    if wiki_title == en_label:
        print(f'{item.getID()} - {item.full_url()} - "{Fore.GREEN}{en_label}{Style.RESET_ALL}"'
              f'- en:"{Fore.GREEN}{wiki_title}{Style.RESET_ALL}" - matches')

        continue

    new_label = f'{en_label.strip()} metro station'
    new_label_color = Fore.GREEN if wiki_title == new_label else Fore.RED

    print(f'{item.getID()} - {item.full_url()} - "{new_label_color}{en_label}{Style.RESET_ALL}"',
          f'- en:"{new_label_color}{wiki_title}{Style.RESET_ALL}"')

    answer = prompt(should_edit)

    if not answer['confirm']:
        continue

    data = {
        'labels': {'en': f'{en_label.strip()} metro station', },
    }

    item.editEntity(data, summary='Update EN label')
