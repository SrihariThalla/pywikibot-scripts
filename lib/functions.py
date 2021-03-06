import os
from os.path import expanduser

import boto3
# import firebase_admin
import osmapi
import overpy
import pywikibot
from PyInquirer import prompt
from colorama import Fore, Style
# from firebase_admin import firestore, credentials
from geopy import Nominatim
from pywikibot import pagegenerators as pg

from lib import questions_overpass
from lib.osm import Osm
from lib.sqs import Sqs
from lib.wikidata import Wikidata

OSM_NODE = 'node'
OSM_WAY = 'way'
OSM_RELATION = 'relation'
OPTION_NONE = 'None'
SQS_OVERPASS = 'overpass'
SQS_WIKIDATA = 'wikidata'

queues = {
    'wikidata_claims': 'https://sqs.eu-central-1.amazonaws.com/238713673548/wikidata-claims',
    'overpass_workload': 'https://sqs.eu-central-1.amazonaws.com/238713673548/overpass_workload',
}


# def firebase_init():
#     cred = credentials.Certificate(os.path.join(expanduser('~'), 'rbs-stations-firebase.json'))
#
#     firebase_admin.initialize_app(cred, {
#         'projectId': 'rbs-stations',
#     })
#
#     db = firestore.client()
#     stations_ref = db.collection('stations')
#
#     return stations_ref


def prepare_changeset_option(changesets: list):
    questions = [
        {
            'type': 'list',
            'name': 'option',
            'message': 'Choose option to create station Wiki Item from',
            'choices': [],
        },
    ]

    for index in changesets:
        questions[0]['choices'].append(str(index))

    questions[0]['choices'].append(OPTION_NONE)

    return questions


def prepare_rbs_option(rbs_results: list):
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

    return questions_rbs


class Functions:
    def __init__(self):
        # self.firebase = firebase_init()
        self.wikidata_site = pywikibot.Site("wikidata", "wikidata")
        self.overpassapi = overpy.Overpass()
        self.osmapi = osmapi.OsmApi(
            # api='https://api06.dev.openstreetmap.org',
            username='',
            password='',
        )
        self.sqs = boto3.client('sqs')
        self.sqs_new = Sqs()
        self.zones = dict()
        self.divisions = dict()
        self.dmrc = dict()
        self.wikidata = Wikidata()
        self.osm = Osm()

    def sqs_send_message(self, id: str, type: str, key: str, summary: str = '-', value: str = '-', lat: float = 0,
                         lon: float = 0, queue: str = 'wikidata'):
        if SQS_WIKIDATA == queue:
            self.sqs.send_message(
                QueueUrl=queues['wikidata_claims'],
                MessageAttributes={
                    'id': {
                        'DataType': 'String',
                        'StringValue': id,
                    },
                    'summary': {
                        'DataType': 'String',
                        'StringValue': summary,
                    },
                    'type': {
                        'DataType': 'String',
                        'StringValue': type,
                    },
                    'key': {
                        'DataType': 'String',
                        'StringValue': key,
                    },
                    'value': {
                        'DataType': 'String',
                        'StringValue': value,
                    },
                    'lat': {
                        'DataType': 'Number',
                        'StringValue': str(lat),
                    },
                    'lon': {
                        'DataType': 'Number',
                        'StringValue': str(lon),
                    },
                },
                MessageBody='Data'
            )

        if SQS_OVERPASS == queue:
            self.sqs.send_message(
                QueueUrl=queues['overpass_workload'],
                MessageAttributes={
                    'osm_id': {
                        'DataType': 'String',
                        'StringValue': id,
                    },
                    'osm_type': {
                        'DataType': 'String',
                        'StringValue': type,
                    },
                    'type': {
                        'DataType': 'String',
                        'StringValue': key,
                    },
                },
                MessageBody='Data'
            )

    def sqs_process_wikidata(self):
        response = self.sqs.receive_message(
            QueueUrl=queues['wikidata_claims'],
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
        )

        message = response['Messages'][0]
        payload = message['MessageAttributes']

        site = pywikibot.Site('wikidata', 'wikidata')
        repo = site.data_repository()

        print(payload['type']['StringValue'], payload['key']['StringValue'], payload['summary']['StringValue'])

        claim = pywikibot.Claim(repo, payload['key']['StringValue'])
        type = payload['type']['StringValue']

        if 'item' == type:
            claim.setTarget(pywikibot.ItemPage(repo, payload['value']['StringValue']))

        if 'identifier' == type:
            claim.setTarget(payload['value']['StringValue'])

        if 'coordinate' == type:
            coordinate = pywikibot.Coordinate(
                lat=float(payload['lat']['StringValue']),
                lon=float(payload['lon']['StringValue']),
                precision=0.000001,
                site=site
            )
            claim.setTarget(coordinate)

        item = pywikibot.ItemPage(repo, payload['id']['StringValue'])
        item.get()

        item.addClaim(claim, summary=payload['summary']['StringValue'])

        print(f'Added {Fore.YELLOW}{payload["key"]["StringValue"]}{Style.RESET_ALL}'
              f' claim to {Fore.YELLOW}{item.getID()}{Style.RESET_ALL} {Fore.GREEN}'
              f'{item.labels.get("en", "Not found")}{Style.RESET_ALL}'
              )

        self.sqs_delete_message(SQS_WIKIDATA, message['ReceiptHandle'])

    def sqs_process_overpass(self):
        return self.sqs.receive_message(
            QueueUrl=queues['overpass_workload'],
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
        )

    def sqs_receive_message(self, queue: str = 'wikidata'):
        if SQS_WIKIDATA == queue:
            self.sqs_process_wikidata()

        if SQS_OVERPASS == queue:
            return self.sqs_process_overpass()

    def sqs_delete_message(self, queue: str, receipt_handle: str):
        if SQS_WIKIDATA == queue:
            self.sqs.delete_message(
                QueueUrl=queues['wikidata_claims'],
                ReceiptHandle=receipt_handle
            )

        if SQS_OVERPASS == queue:
            self.sqs.delete_message(
                QueueUrl=queues['overpass_workload'],
                ReceiptHandle=receipt_handle
            )

    def prepare_zones_dict(self):
        if bool(self.zones):
            return self.zones

        query = """
                SELECT ?item WHERE {
                    ?item wdt:P31 wd:Q63383608.
                }
                """

        print('Preparing IR Zones data')

        items = pg.PreloadingEntityGenerator(pg.WikidataSPARQLPageGenerator(query, self.wikidata_site))

        for item in items:
            name = item.labels.get('en')

            if 'P1471' not in item.claims:
                print(f'No reporting mark found for {name} - {item.getID()}')

                continue

            if len(item.claims['P1471']) > 1:
                print(f'Multiple reporting marks found for {name} - {item.getID()}')

                continue

            self.zones[item.claims['P1471'][0].getTarget()] = item

        return self.zones

    def prepare_divisions_dict(self):
        if bool(self.divisions):
            return self.divisions

        query = """
                SELECT ?item WHERE {
                    ?item wdt:P31 wd:Q63383616.
                }
                """

        print('Preparing IR Divisions data')

        items = pg.PreloadingEntityGenerator(pg.WikidataSPARQLPageGenerator(query, self.wikidata_site))

        for item in items:
            name = item.labels.get('en', None)

            if 'P1471' not in item.claims:
                print(f'No reporting mark found for {name} - {item.getID()}')

                continue

            if len(item.claims['P1471']) > 1:
                print(f'Multiple reporting marks found for {name} - {item.getID()}')

                continue

            self.divisions[item.claims['P1471'][0].getTarget()] = item

        return self.divisions

    def prepare_dmrc_wikidata(self):
        if bool(self.dmrc):
            return

        query = """
                SELECT ?item WHERE {
                  ?item wdt:P31 wd:Q928830;
                        wdt:P81 [ wdt:P361 wd:Q271195 ].
                }
                """

        print('Preparing DMRC stations data')

        items = pg.PreloadingEntityGenerator(pg.WikidataSPARQLPageGenerator(query, self.wikidata_site))

        for item in items:
            item.get()
            self.dmrc[item.getID()] = item

        return self.dmrc

    def query_wikidata(self, code: str):
        query = f"""
                SELECT ?item WHERE {{
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
                    ?item wdt:P5696 ?Indian_Railways_station_code.
                    ?item wdt:P5696 "{code}".
                }}
                """

        items = list(pg.WikidataSPARQLPageGenerator(query, self.wikidata_site))

        return items

    def query_firebase(self, code: str, printItems: bool = False, label: str = ''):
        docs = self.firebase.where('code', '==', code).stream()
        results = []

        for doc in docs:
            data = doc.to_dict()

            results.append(data)

        questions_rbs = [
            {
                'type': 'list',
                'name': 'option',
                'message': 'Choose option to create station Wiki Item from',
                'choices': [],
            },
        ]

        for i in range(0, len(results)):
            questions_rbs[0]['choices'].append(str(i))

        if not printItems:
            return {
                'data': results,
                'prompt': questions_rbs,
            }

        print()
        i = 1
        for item in results:
            if 'code' not in item:
                print(f'RBS code is not set')

                continue

            if label is None:
                rbs_name_color = Fore.YELLOW
            elif label.lower() == f'{item["name"]} railway station':
                rbs_name_color = Fore.GREEN
            else:
                rbs_name_color = Fore.RED

            rbs_code_color = Fore.RED if item['code'] != code else Fore.GREEN

            print(
                f"{i} . {rbs_name_color}{item['name']}{Style.RESET_ALL} - "
                f"{rbs_code_color}{item['code']}{Style.RESET_ALL} - {item['zone']} - "
                f"{item['division_name']} - {item['valid_from']} - {item['valid_upto']}"
            )

            i += 1

        return {
            'data': results,
            'prompt': questions_rbs,
        }

    def create_wikidata_item(self, name: str, code: str, lat: float, lon: float, division: pywikibot.ItemPage = None):
        repo = self.wikidata_site.data_repository()

        instance_of = pywikibot.Claim(repo, 'P31')
        instance_of.setTarget(pywikibot.ItemPage(repo, 'Q55488'))

        country = pywikibot.Claim(repo, 'P17')
        country.setTarget(pywikibot.ItemPage(repo, 'Q668'))

        owned_by = pywikibot.Claim(repo, 'P127')
        owned_by.setTarget(pywikibot.ItemPage(repo, 'Q819425'))

        station_code = pywikibot.Claim(repo, 'P5696')
        station_code.setTarget(code)

        coordinateclaim = pywikibot.Claim(self.wikidata_site.data_repository(), 'P625')
        coordinate = pywikibot.Coordinate(lat, lon, precision=0.000001, site=self.wikidata_site)
        coordinateclaim.setTarget(coordinate)

        data = {
            'labels': {'en': f'{name} railway station', },
            'descriptions': {'en': 'railway station in India', },
        }

        station = pywikibot.ItemPage(repo)
        station.editEntity(data, summary='Create entry for railway station')

        print()
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

        return station

    def update_osm_node(self, element: dict, station: pywikibot.ItemPage):
        element['tag']['wikidata'] = station.getID()

        print()
        print(f'Wikidata - {element["tag"]["wikidata"]}')

        wiki = station.sitelinks.get('enwiki')

        if wiki is not None:
            element['tag']['wikipedia'] = f'en:{wiki.title}'
            print(f'Wikipedia - "{element["tag"]["wikipedia"]}"')

        update_dict = {
            'id': element['id'],
            'lat': element['lat'],
            'lon': element['lon'],
            'tag': element['tag'],
            'version': element['version'],
        }

        print()
        answer_confirm = prompt(questions_overpass.questions_osm_update)

        if not answer_confirm['confirm']:
            print(f'{Fore.RED}NOT{Style.RESET_ALL} updating OSM')
            print()

            return False

        try:
            self.osmapi.NodeUpdate(update_dict)
        except osmapi.NoChangesetOpenError:
            self.osmapi.ChangesetCreate({"comment": "Set wiki tags for railway stations in India"})
            self.osmapi.NodeUpdate(update_dict)

        return True

    def geocode(self, address: str):
        return Nominatim(user_agent='geopy').geocode(address, exactly_one=False, addressdetails=True)
        # return Nominatim(domain='nominatim.geocoding.ai').geocode(address, exactly_one=False, addressdetails=True)
