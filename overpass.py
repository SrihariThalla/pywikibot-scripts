import os

import overpy
from PyInquirer import prompt
from colorama import init, deinit, Fore, Style

import functions
import queries
import questions_overpass as questions
import sqs

init(autoreset=True)
func = functions.Functions()


def add_wikidata():
    query = """
    [out:json]
    [timeout:250]
    ;
    area(3600304716)->.searchArea;
    (
      node
        ["railway"="station"]
        ["ref"]
        ["wikidata"!~".*"]
        (area.searchArea);
    );
    out;
    >;
    out skel qt;
    """

    results = overpy.Overpass().query(query)

    for node in results.nodes:
        print(node)
        sqs.send_message(
            id=str(node.id),
            type='node',
            key='add-wiki',
            queue='overpass',
        )

    for way in results.ways:
        print(way)
        sqs.send_message(
            id=str(way.id),
            type='way',
            key='add-wiki',
            queue='overpass',
        )

    for relation in results.relations:
        print(relation)
        sqs.send_message(
            id=str(relation.id),
            type='relation',
            key='add-wiki',
            queue='overpass',
        )

    print(f'Added Nodes={len(results.nodes)} Ways={len(results.ways)} Relations={len(results.relations)}')


def start_dmrc_work(payload: dict):
    # func.prepare_dmrc_wikidata()

    osm_type = payload['osm_type']['StringValue']
    osm_id = payload['osm_id']['StringValue']

    if functions.OSM_WAY == osm_type or functions.OSM_RELATION == osm_type:
        print('Way and Relation is not implemented')
        print(payload)
        print()

        return False

    element = func.osmapi.NodeGet(osm_id)

    name = None if 'name' not in element['tag'] else element['tag']['name']
    tag_wikidata = None if 'wikidata' not in element['tag'] else element['tag']['wikidata']
    tag_wikipedia = None if 'wikipedia' not in element['tag'] else element['tag']['wikipedia']

    print()
    print(f'OSM - https://www.openstreetmap.org/node/{osm_id}')
    print(f'Name - {name}')
    print(f'Wikidata - {tag_wikidata}')
    print(f'Wikipedia - {tag_wikipedia}')


def should_start_workload():
    response = sqs.receive_message('overpass')

    if 'Messages' not in response:
        print(f'{Fore.YELLOW}SQS Queue is probably empty{Style.RESET_ALL}')
        print()

        return

    message = response['Messages'][0]
    payload = message['MessageAttributes']

    if questions.WORKLOAD_WIKIDATA_DMRC == payload['type']['StringValue']:
        start_dmrc_work(payload)

        return

    osm_type = payload['osm_type']['StringValue']
    osm_id = payload['osm_id']['StringValue']

    if functions.OSM_WAY == osm_type or functions.OSM_RELATION == osm_type:
        print('Way and Relation is not implemented')
        print(payload)
        print()

        return

    element = func.osmapi.NodeGet(osm_id)

    if 'ref' not in element['tag']:
        print('Ref is not set')
        print(element)
        print()

        return

    ref = element['tag']['ref']

    if 'name' in element['tag']:
        name = element['tag']['name']
    else:
        name = 'No "name" tagged'

    if 'wikidata' in element['tag']:
        tag_wikidata = element['tag']['wikidata']
    else:
        tag_wikidata = None

    if 'wikipedia' in element['tag']:
        tag_wikipedia = element['tag']['wikipedia']
    else:
        tag_wikipedia = None

    print()
    print(f'OSM - https://www.openstreetmap.org/{osm_type}/{osm_id}')
    print(f'Deep History - https://osmlab.github.io/osm-deep-history/#/{osm_type}/{osm_id}')
    print(f'Type - {osm_type}')
    print(f'ID - {osm_id}')
    print(f'Ref - {ref}')
    print(f'Name - {name}')
    print(f'Wikidata - {tag_wikidata}')
    print(f'Wikipedia - {tag_wikipedia}')
    print()

    # Check if Wikidata and Wikipedia are already set
    if tag_wikidata is not None and tag_wikipedia is not None:
        print(f'{Fore.GREEN}Wikidata and Wikipedia are already set{Style.RESET_ALL}')
        print()

        sqs.delete_message('overpass', message['ReceiptHandle'])

        return

    items = func.query_wikidata(ref)

    print(
        f'Searching {Fore.YELLOW}Wikidata{Style.RESET_ALL} for station '
        f'{Fore.CYAN}{name}{Style.RESET_ALL} - {Fore.CYAN}{ref}'
    )
    print()

    if len(items) > 1:
        print(f'{Fore.RED}Multiple{Style.RESET_ALL} Wikidata items exist')
        print()

        return

    if len(items) == 1:
        wikidata_item = dict()

        for item in items:
            item.get()

            wiki = item.sitelinks.get('enwiki')
            wiki_title = '' if wiki is None else f' - {wiki.title}'

            for claim in item.claims['P5696']:
                if ref.upper() == claim.getTarget().upper():
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

            wikidata_item['id'] = item.getID()
            wikidata_item['wiki'] = None if wiki is None else f'en:{wiki.title}'

        # Confirm if item is found in Wikidata
        print()
        answers_wikidata = prompt(questions.questions_wikidata)
        print()

        if answers_wikidata['found']:
            print(wikidata_item)
            print()

            if func.update_osm_node(element, items[0]):
                sqs.delete_message('overpass', message['ReceiptHandle'])

            return

    print(f'Wikidata item does {Fore.RED}not{Style.RESET_ALL} exist')
    print()

    print(
        f'Searching RBS {Fore.YELLOW}Firebase{Style.RESET_ALL} '
        f'for station {Fore.CYAN}{name}{Style.RESET_ALL} - {Fore.CYAN}{ref}'
    )
    print()

    firebase_items = func.query_firebase(ref)

    if len(firebase_items) == 0:
        print(f'RBS item does {Fore.RED}not{Style.RESET_ALL} exist')
        print()

        sqs.delete_message('overpass', message['ReceiptHandle'])

        return

    for item in firebase_items:
        if name is None:
            color_name = Fore.YELLOW
        elif name.lower() == item['name'].lower():
            color_name = Fore.GREEN
        else:
            color_name = Fore.RED

        if ref == item['code']:
            color_code = Fore.GREEN
        else:
            color_code = Fore.RED

        print(
            f"{len(firebase_items)} . {color_name}{item['name']}{Style.RESET_ALL} - {color_code}{item['code']}{Style.RESET_ALL}"
            f" - {item['zone']} - {item['division_name']} - {item['valid_from']} - {item['valid_upto']}"
        )

    print()
    answers_wikidata_create = prompt(questions.questions_wikidata_create)

    if not answers_wikidata_create['create']:
        print(f'Wikidata item is {Fore.RED}not{Style.RESET_ALL} created')
        print()

        sqs.delete_message('overpass', message['ReceiptHandle'])

        return False

    questions_rbs = functions.prepare_rbs_option(firebase_items)

    print()
    answers_rbs = prompt(questions_rbs)

    dict_to_create = firebase_items[int(answers_rbs['option'])]

    divisions_dict = []

    # Set Division from RBS if exists
    if dict_to_create['division'] in divisions_dict:
        division = divisions_dict[dict_to_create['division']]
    else:
        division = None

    # Create Wikidata item
    station = func.create_wikidata_item(name=name, code=ref, lat=float(element['lat']), lon=float(element['lon']),
                                        division=division)

    if func.update_osm_node(element, station):
        sqs.delete_message('overpass', message['ReceiptHandle'])


def should_generate_workload():
    """
    Generate workload and upload to SQS
    """
    answers_overpass = prompt(questions.questions_generate_workload_confirm)

    if not answers_overpass['workload']:
        return False

    answers_overpass_list = prompt(questions.questions_generate_workload_list)
    overpass_list = answers_overpass_list['overpass_list']

    if questions.WORKLOAD_WIKIDATA_IR == overpass_list:
        print(f'Generating Overpass workload for: {questions.WORKLOAD_WIKIDATA_IR}')

        add_wikidata()

    if questions.WORKLOAD_WIKIDATA_DMRC == overpass_list:
        print(f'Generating Overpass workload for: {questions.WORKLOAD_WIKIDATA_DMRC}')

        queries.add_dmrc_stations(func)

    return True


os.system('clear')

while True:
    answers_start = prompt(questions.questions_start)

    if answers_start['start']:
        os.system('clear')
        should_start_workload()

        continue

    result = should_generate_workload()

    if not result:
        break

print()
deinit()
