import os
from pprint import pprint

import mwparserfromhell
import pywikibot
from PyInquirer import prompt
from colorama import Fore, Style
from pywikibot import pagegenerators


def prompt_bool_question(question: str):
    return {
        'type': 'confirm',
        'name': 'confirm',
        'message': question,
        'default': False,
    }


def prompt_list_question(question: str):
    return {
        'type': 'list',
        'name': 'confirm',
        'message': question,
        'choices': [
            'noinclude',
            'examples',
        ],
    }


class PartyColors:
    def __init__(self):
        self.wikipedia_en = pywikibot.Site('en', 'wikipedia')

    def process(self):
        query = f'''
                SELECT ?item ?itemLabel WHERE {{
                    SERVICE wikibase:mwapi {{
                        bd:serviceParam wikibase:endpoint "en.wikipedia.org";     
                                        wikibase:api "Generator";
                                        mwapi:generator "categorymembers";        
                                        mwapi:gcmtitle "Category:India political party colour templates";.
                        ?item wikibase:apiOutputItem mwapi:item.
                    }}
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
                }}
                '''
        wikidata_site = pywikibot.Site("wikidata", "wikidata")
        generator = pagegenerators.WikidataSPARQLPageGenerator(query, site=wikidata_site)

        for item in generator:
            print()
            if not prompt(prompt_bool_question('Start new work?'))['confirm']:
                break

            os.system('clear')
            item.get()

            wiki = item.sitelinks.get('enwiki')

            if wiki is None:
                print()
                pprint(f'EN Wiki is not set for {item.pageid}')
                print()

                continue

            self.process_item(wiki.namespace.id, wiki.title)

    def process_item(self, namespace: int, title: str):
        name = f'{self.wikipedia_en.namespace(namespace)}:{title}'
        article = pywikibot.Page(self.wikipedia_en, name)

        if not article.has_permission('edit'):
            print()
            print(article.title())
            print(article.full_url())
            print()
            print(f'Not {Fore.RED}permitted{Style.RESET_ALL} to edit')

            return

        wikicode = mwparserfromhell.parse(article.text)

        counters = {
            'noinclude': 0,
            'examples': 0,
        }
        examples_set = False

        print('------------------------')
        for tag in wikicode.filter_tags():
            if 'nowiki' == tag.tag:
                print(f'{Fore.RED}{tag}{Style.RESET_ALL}')
                print('------------------------')

            if 'noinclude' == tag.tag:
                counters['noinclude'] += 1

                print(str(tag))
                print('------------------------')

            if 'table' == tag.tag:
                counters['examples'] += 1

                if (tag.contents.contains("'''This color'''")
                        and tag.contents.contains("'''White on this color'''")
                        and tag.contents.contains("'''Black on this color'''")
                        and tag.contents.contains("'''Grey on this color'''")
                ):
                    examples_set = True

                print(str(tag))
                print('------------------------')

        print()
        print(article.title())
        print(article.full_url())

        if counters['noinclude'] > 1 or counters['examples'] > 1:
            print()
            print(f'{Fore.RED}Invalid{Style.RESET_ALL} counters')
        elif examples_set:
            print()
            print(f'{Fore.GREEN}Already set{Style.RESET_ALL}')

            return

        print()
        if not prompt(prompt_bool_question('Should update the template?'))['confirm']:
            return

        tag_to_replace = None

        print()
        answer = prompt(prompt_list_question('Which section to update?'))['confirm']

        for tag in wikicode.filter_tags():
            if 'noinclude' == answer and 'noinclude' == tag.tag:
                tag_to_replace = str(tag)

                break

            if 'examples' == answer and 'table' == tag.tag:
                tag_to_replace = str(tag)

                break

        if tag_to_replace is None:
            return

        new_noinclude = '<noinclude>\n\n== Examples ==\n{|\n|- style="color:{{ {{PAGENAME}} }}"\n| \'\'\'This color\'\'\'\n|- style="background:{{ {{PAGENAME}} }}; color:white"\n| \'\'\'White on this color\'\'\'\n|- style="background:{{ {{PAGENAME}} }}; color:black"\n| \'\'\'Black on this color\'\'\'\n|- style="background:{{ {{PAGENAME}} }}; color:grey"\n| \'\'\'Grey on this color\'\'\'\n|}\n\n[[Category:India political party colour templates|{{PAGENAME}}]]\n</noinclude>'

        new_examples = '{|\n|- style="color:{{ {{PAGENAME}} }}"\n| \'\'\'This color\'\'\'\n|- style="background:{{ {{PAGENAME}} }}; color:white"\n| \'\'\'White on this color\'\'\'\n|- style="background:{{ {{PAGENAME}} }}; color:black"\n| \'\'\'Black on this color\'\'\'\n|- style="background:{{ {{PAGENAME}} }}; color:grey"\n| \'\'\'Grey on this color\'\'\'\n|}'

        if 'noinclude' == answer:
            wikicode.replace(tag_to_replace, new_noinclude)
        else:
            wikicode.replace(tag_to_replace, new_examples)

        print()
        print('------------------------')
        print(str(wikicode))
        print('------------------------')
        print()

        article.text = str(wikicode)
        article.save(summary='Update template with examples')
