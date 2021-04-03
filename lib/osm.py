import osmapi
from PyInquirer import prompt
from colorama import Fore, Style
from pywikibot import ItemPage

questions_osm_update = [
    {
        'type': 'confirm',
        'name': 'confirm',
        'message': 'Confirm updating OSM?',
        'default': False,
    }
]


class Osm:
    def __init__(self):
        self.osmapi = osmapi.OsmApi(
            api='https://api06.dev.openstreetmap.org',
            username='',
            password='',
        )

    def update_relation(self, relation, wikidata: ItemPage, comment: str):
        relation['tag']['wikidata'] = wikidata.getID()

        print()
        print(f'Wikidata - {relation["tag"]["wikidata"]}')

        wiki = wikidata.sitelinks.get('enwiki')

        if wiki is not None:
            relation['tag']['wikipedia'] = f'en:{wiki.title}'
            print(f'Wikipedia - "{relation["tag"]["wikipedia"]}"')

        update_dict = {
            # 'id': relation['id'],
            'id': 11,
            'member': relation['member'],
            'tag': relation['tag'],
            'version': relation['version'],
        }

        print()
        answer_confirm = prompt(questions_osm_update)

        if not answer_confirm['confirm']:
            print(f'{Fore.RED}NOT{Style.RESET_ALL} updating OSM')
            print()

            return False

        try:
            self.osmapi.RelationUpdate(update_dict)
        except osmapi.NoChangesetOpenError:
            self.osmapi.ChangesetCreate({'comment': comment})
            self.osmapi.RelationUpdate(update_dict)

        return True
