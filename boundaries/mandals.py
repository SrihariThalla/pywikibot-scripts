import pywikibot
from PyInquirer import prompt
from progress.bar import Bar

from lib.constants import OSM_RELATION, SqsDataType, SQS_QUEUES, QUEUE_OVERPASS_WORKLOAD
from lib.functions import Functions
from lib.sqs import MessageAttribute

QUEUE_TYPE = 'mandal'

found = {
    'type': 'confirm',
    'name': 'found',
    'message': 'Is the Wikidata item found?',
    'default': False,
}
question = {
    'type': 'input',
    'name': 'wikidata',
    'message': 'Enter Wikidata item',
}

states_wiki_category = {
    'Andaman and Nicobar Islands': 'Category:Tehsils of the Andaman and Nicobar Islands',
    'Andhra Pradesh': 'Category:Mandals in Andhra Pradesh',
    'Chhattisgarh': 'Category:Tehsils of Chhattisgarh',
    'Goa': 'Category:Taluks of Goa',
    'Gujarat': 'Category:Talukas of Gujarat',
    'Haryana': 'Category:Tehsils in Haryana',
    'Himachal Pradesh': 'Category:Tehsils of Himachal Pradesh',
    'Jharkhand': 'Category:Sub-divisions in Jharkhand',
    'Karnataka': 'Category:Taluks of Karnataka',
    'Kerala': 'Category:Taluks of Kerala',
    'Madhya Pradesh': 'Category:Tehsils of Madhya Pradesh',
    'Maharashtra': 'Category:Talukas in Maharashtra',
    'Puducherry': 'Category:Taluks of Puducherry',
    'Rajasthan': 'Category:Tehsils of Rajasthan',
    'Tamil Nadu': 'Category:Taluks of Tamil Nadu',
    'Telangana': 'Category:Mandals in Telangana',
    'Uttar Pradesh': 'Category:Tehsils of Uttar Pradesh',
    'West Bengal': 'Category:Subdivisions of West Bengal',
}


class Mandals:
    def __init__(self):
        self.functions = Functions()

    def query_overpass(self):
        query = """
                [out:json][timeout:250];
                area(3600304716)->.searchArea;
                (
                  relation
                    ["admin_level"="6"]
                    ["boundary"="administrative"]
                    (area.searchArea);
                );
                out;
                >;
                out skel qt;
                """

        results = self.functions.overpassapi.query(query)

        bar = Bar('Pushing Relation to SQS', max=len(results.relations))

        for relation in results.relations:
            bar.next()

            self.functions.sqs_new.send_message(
                SQS_QUEUES[QUEUE_OVERPASS_WORKLOAD],
                [
                    MessageAttribute('osm_id', SqsDataType.NUMBER, relation.id),
                    MessageAttribute('osm_type', SqsDataType.STRING, OSM_RELATION),
                    MessageAttribute('type', SqsDataType.STRING, QUEUE_TYPE),
                ],
            )

        print()

    def process(self):
        response = self.functions.sqs_new.receive_message(SQS_QUEUES[QUEUE_OVERPASS_WORKLOAD])

        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        payload = message['MessageAttributes']

        if 'type' not in payload or QUEUE_TYPE != payload['type']['StringValue']:
            print('Message invalid')
            print(message)

            self.functions.sqs_new.delete_message(SQS_QUEUES[QUEUE_OVERPASS_WORKLOAD], receipt_handle)

            return

        relation = self.functions.osmapi.RelationGet(payload['osm_id']['StringValue'])

        print()
        print(relation['tag'])

        name = None if 'name' not in relation['tag'] else relation['tag']['name']
        wikidata = None if 'wikidata' not in relation['tag'] else relation['tag']['wikidata']
        wikipedia = None if 'wikipedia' not in relation['tag'] else relation['tag']['wikipedia']
        places = self.functions.geocode(f'{name}, India')

        print()
        print(f'Name - {name}')
        print(f'Wikidata - {wikidata}')
        print(f'Wikipedia - {wikipedia}')
        print('Geocoding -')

        if places is not None:
            process = self.process_state_category(places)

            if not process:
                self.functions.sqs_new.delete_message(SQS_QUEUES[QUEUE_OVERPASS_WORKLOAD], receipt_handle)
                return False

        print()
        print(f'https://www.openstreetmap.org/relation/{relation["id"]}')

        print()
        answer_found = prompt(found)

        if not answer_found['found']:

            wikidata = self.create_wikidata()

            print(wikidata)

            if wikidata is None:
                # self.functions.sqs_new.delete_message(SQS_QUEUES[QUEUE_OVERPASS_WORKLOAD], receipt_handle)
                return False

            # return False
        else:
            answer_wikidata = prompt(question)

            if len(answer_wikidata['wikidata']) == 0:
                wikidata = self.create_wikidata()

                print(wikidata)

                if wikidata is None:
                    self.functions.sqs_new.delete_message(SQS_QUEUES[QUEUE_OVERPASS_WORKLOAD], receipt_handle)
                    return False
            else:
                wikidata = pywikibot.ItemPage(answer_wikidata['wikidata'])

        # wikidata = self.create_wikidata()
        #
        # print(wikidata)
        #
        # if wikidata is None:
        #     self.functions.sqs_new.delete_message(SQS_QUEUES[QUEUE_OVERPASS_WORKLOAD], receipt_handle)
        #     return False
        #
        # else:
        # print()
        # answer_wikidata = prompt(question)
        #
        # if len(answer_wikidata['wikidata']) == 0:
        #     return False
        #
        # wikidata = pywikibot.ItemPage(answer_wikidata['wikidata'])
        #
        if wikidata is None:
            return False

        self.functions.osm.update_relation(relation, wikidata, 'Set Wiki tags for sub-districts in India')

    def process_state_category(self, places: list):
        q = {
            'type': 'list',
            'name': 'place',
            'message': 'Is the place found?',
            'choices': [
                '-1',
            ],
        }

        for i in range(0, len(places)):
            place = places[i]

            print(f'            {i}. {place.address}')

            if 'address' not in place.raw or 'state' not in place.raw['address']:
                print(place.raw)

                return True

            q['choices'].append(str(i))

        print()
        a = prompt(q)
        choice = int(a['place'])

        if -1 == choice:
            return False

        state = places[choice].raw['address']['state']

        if state not in states_wiki_category:
            print()
            print(f'{state} not set in Wiki categories list')

            return True

        wiki_category_pages = self.functions.wikidata.query_wikipedia_category_pages(states_wiki_category[state])

        for _, item in wiki_category_pages.items():
            wiki = item.sitelinks.get('enwiki')
            print(f'{item.full_url()} - {item.getID()} - {item.labels.get("en")} - {wiki.title}')

        return True

    def create_wikidata(self):
        q = {
            'type': 'input',
            'name': 'name',
            'message': 'Enter name of tehsil to create in Wikidata'
        }

        print()
        a = prompt(q)

        if len(a['name']) == 0:
            print()
            print('Input not entered')

            return None

        return self.functions.wikidata.create_tehsil(a['name'])
