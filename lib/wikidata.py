import pywikibot
from colorama import Fore, Style
from pywikibot import pagegenerators


class Wikidata:
    # category_pages: dict[str, pywikibot.ItemPage]

    def __init__(self):
        self.wikidata_site = pywikibot.Site("wikidata", "wikidata")
        self.category_pages = dict()

    def query_ir_station(self, code: str, prefetch: bool = False):
        query = f"""
                SELECT ?item WHERE {{
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
                    ?item wdt:P5696 ?Indian_Railways_station_code.
                    ?item wdt:P5696 "{code}".
                }}
                """

        items = pagegenerators.WikidataSPARQLPageGenerator(query, self.wikidata_site)

        if prefetch:
            items = pagegenerators.PreloadingEntityGenerator(items)

        return items

    def query_wikipedia_category_pages(self, category: str):
        if category in self.category_pages:
            return self.category_pages[category]

        query = f"""
                SELECT ?item WHERE {{
                    SERVICE wikibase:mwapi {{
                        bd:serviceParam wikibase:endpoint "en.wikipedia.org";
                                        wikibase:api "Generator";
                                        mwapi:generator "categorymembers";
                                        mwapi:gcmtitle "{category}";.
                        ?item wikibase:apiOutputItem mwapi:item.
                    }}
                }}
                """

        items = pagegenerators.PreloadingEntityGenerator(
            pagegenerators.WikidataSPARQLPageGenerator(query, self.wikidata_site)
        )

        self.category_pages[category] = dict()
        category_pages = dict()

        for item in items:
            if item.labels.get('en') is None:
                print(item)
                print('NO ENGLISH LABEL')

            category_pages[item.labels.get('en').lower()] = item

        for key in sorted(category_pages):
            self.category_pages[category][key] = category_pages[key]

        return self.category_pages[category]

    def create_tehsil(self, name: str):
        repo = self.wikidata_site.data_repository()

        instance_of = pywikibot.Claim(repo, 'P31')
        instance_of.setTarget(pywikibot.ItemPage(repo, 'Q7694920'))

        country = pywikibot.Claim(repo, 'P17')
        country.setTarget(pywikibot.ItemPage(repo, 'Q668'))

        owned_by = pywikibot.Claim(repo, 'P127')
        owned_by.setTarget(pywikibot.ItemPage(repo, 'Q819425'))

        data = {
            'labels': {'en': name, },
            'descriptions': {'en': 'tehsil in India', },
        }

        tehsil = pywikibot.ItemPage(repo)
        tehsil.editEntity(data, summary='Create entry for tehsil')

        print()
        print(f'Tehsil: "{name}" - Wikidata: {Fore.GREEN}{tehsil.getID()}{Style.RESET_ALL}')

        tehsil.addClaim(instance_of, summary='Add instance_of claim')
        tehsil.addClaim(country, summary='Add country claim')

        return tehsil
