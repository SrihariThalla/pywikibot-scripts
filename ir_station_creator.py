#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import os

import overpy
import pywikibot
from PyInquirer import prompt
from colorama import init, deinit, Fore, Style
from progress.bar import Bar
from pywikibot import pagegenerators as pg

import firebase_init
import ir_station_creator_questions as questions

init(autoreset=True)

script_dir = os.path.dirname(__file__)

stations_ref = firebase_init.init()

site = pywikibot.Site("wikidata", "wikidata")

divisions_dict = dict()


def prepare_divisions_dict():
    divisions_query = f'''
                        SELECT ?item ?itemLabel WHERE {{
                            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
                            ?item wdt:P31 wd:Q63383616.
                        }}
                        '''

    divisions = list(pg.WikidataSPARQLPageGenerator(divisions_query, site))

    bar = Bar('Preparing Divisions data', max=len(divisions))

    for division in divisions:
        bar.next()
        division.get()

        division_name = division.labels.get('en', 'NO EN LABEL FOUND')

        if 'P1471' not in division.claims:
            print(f""" No reporting mark found for {division_name} - {division.getID()}""")

            continue

        if len(division.claims['P1471']) > 1:
            print(f""" Multiple reporting marks found for {division_name} - {division.getID()}""")

            continue

        divisions_dict[division.claims['P1471'][0].getTarget()] = division


def query_wikidata(code: str, name: str = None):
    query = f"""
            SELECT ?item WHERE {{
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
                ?item wdt:P5696 ?Indian_Railways_station_code.
                ?item wdt:P5696 "{code}".
            }}
            """

    items = list(pg.WikidataSPARQLPageGenerator(query, site))

    print()
    print(
        f'Searching {Fore.YELLOW}Wikidata{Style.RESET_ALL} for station '
        f'{Fore.CYAN}{name}{Style.RESET_ALL} - {Fore.CYAN}{code}'
    )
    print()

    if len(items) == 0:
        print(f'Wikidata item does {Fore.RED}not{Style.RESET_ALL} exist')

        return False

    for item in items:
        item.get()

        wiki = item.sitelinks.get('enwiki')
        wiki_title = '' if wiki is None else f' - {wiki.title}'

        for claim in item.claims['P5696']:
            if code.upper() == claim.getTarget().upper():
                color_code = Fore.GREEN
            else:
                color_code = Fore.RED

            if item.labels.get('en', 'Not found') == f'{name} railway station':
                color_name = Fore.GREEN
            else:
                color_name = Fore.RED

            print(
                f"Wikidata - {color_name}{item.labels.get('en', 'Not found')}{Style.RESET_ALL}"
                f" - {color_code}{claim.getTarget()}{Style.RESET_ALL} - {item.getID()} - "
                f"{item.full_url()}{wiki_title}"
            )

    return True


def query_firebase(code: str, name: str = None):
    print()
    print(
        f'Searching RBS {Fore.YELLOW}Firebase{Style.RESET_ALL} '
        f'for station {Fore.CYAN}{name}{Style.RESET_ALL} - {Fore.CYAN}{code}'
    )
    print()

    docs = stations_ref.where('code', '==', code).stream()
    results = []

    for doc in docs:
        data = doc.to_dict()

        if name is None:
            color_name = Fore.YELLOW
        elif name.lower() == data['name'].lower():
            color_name = Fore.GREEN
        else:
            color_name = Fore.RED

        if code == data['code']:
            color_code = Fore.GREEN
        else:
            color_code = Fore.RED

        print(
            f"{len(results)} . {color_name}{data['name']}{Style.RESET_ALL} - {color_code}{data['code']}{Style.RESET_ALL}"
            f" - {data['zone']} - {data['division_name']} - {data['valid_from']} - {data['valid_upto']}"
        )

        results.append(data)

    return results


def select_rbs_option(rbs_results: list):
    questions_rbs = [
        {
            'type': 'list',
            'name': 'option',
            'message': 'Choose option to create station Wiki Item from',
            'choices': [],
        },
    ]

    for i in range(0, len(rbs_results)):
        questions_rbs[0]['choices'].append(str(i))

    print()
    answers_rbs = prompt(questions_rbs)

    return rbs_results[int(answers_rbs['option'])]


def create_wikidata_item(name: str, code: str, lat: float, lon: float, division: pywikibot.ItemPage = None):
    site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()

    instance_of = pywikibot.Claim(repo, 'P31')
    instance_of.setTarget(pywikibot.ItemPage(repo, 'Q55488'))

    country = pywikibot.Claim(repo, 'P17')
    country.setTarget(pywikibot.ItemPage(repo, 'Q668'))

    owned_by = pywikibot.Claim(repo, 'P127')
    owned_by.setTarget(pywikibot.ItemPage(repo, 'Q819425'))

    station_code = pywikibot.Claim(repo, 'P5696')
    station_code.setTarget(code)

    coordinateclaim = pywikibot.Claim(site.data_repository(), 'P625')
    coordinate = pywikibot.Coordinate(lat, lon, precision=0.000001, site=site)
    coordinateclaim.setTarget(coordinate)

    data = {
        "labels": {"en": "%s railway station" % name, },
        "descriptions": {"en": "railway station in India", },
    }

    print()
    print(f'Station: "{name}" - Code: "{code}"')

    station = pywikibot.ItemPage(repo)
    station.editEntity(data, summary='Create entry for railway station')

    print(f'Station: "{name}" - Code: "{code}" - Wikidata: {Fore.GREEN}{station.getID()}')

    station.addClaim(instance_of, summary='Add instance_of claim')
    station.addClaim(country, summary='Add country claim')
    station.addClaim(owned_by, summary='Add owned_by claim')
    station.addClaim(station_code, summary='Add station code')
    station.addClaim(coordinateclaim, summary='Add coordinate claim from OSM')

    if division is not None:
        operator = pywikibot.Claim(repo, 'P137')
        operator.setTarget(division)

        station.addClaim(operator, summary='Add operator claim')

    # ToDo Add admin territory claim


def application():
    answers_osm = prompt(questions.questions_osm)
    osm_type = answers_osm['osm_type']
    osm_id = answers_osm['osm_id']

    if not osm_id.isdigit():
        print()
        print(f'{Fore.RED}{osm_id}{Style.RESET_ALL} is not a number')

        return

    overpass = overpy.Overpass()

    result = overpass.query("""
                            {0}({1});
                            (._;>;);
                            out body;
                            """.format(osm_type, osm_id))

    if 'node' == osm_type:
        node = result.nodes[0]

        print()
        print(node)
        print(node.tags)

        if 'ref' not in node.tags:
            print('Ref is not found. Manual intervention is necessary')

            return False

        if 'name' in node.tags:
            name = node.tags['name']
        else:
            name = None

        code = node.tags['ref']

        # Search Wikidata if the station is already existing
        query_has_results = query_wikidata(code, name)

        if query_has_results:
            # Confirm if item is found in Wikidata
            print()
            answers_wikidata = prompt(questions.questions_wikidata)

            if answers_wikidata['found']:
                return False

        # Query RBS Firebase for stations
        rbs_results = query_firebase(code, name)

        print()
        answers_wikidata_create = prompt(questions.questions_wikidata_create)

        if not answers_wikidata_create['create']:
            return False

        # RBS Firebase station doc dict to create Wikidata item
        dict_to_create = select_rbs_option(rbs_results)

        print()
        print(dict_to_create)

        # Set Division from RBS if exists
        if dict_to_create['division'] in divisions_dict:
            division = divisions_dict[dict_to_create['division']]
        else:
            division = None

        # Create Wikidata item
        create_wikidata_item(name=name, code=code, lat=float(node.lat), lon=float(node.lon), division=division)

    elif 'way' == osm_type:
        print(result.ways)

    else:
        print(result.relations)

    return True


prepare_divisions_dict()

while True:
    os.system('clear')
    application()

    print()
    answers_start = prompt(questions.questions_start)

    if not answers_start['start']:
        break

print()
deinit()
