#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import boto3
import pywikibot

from colorama import init, deinit, Fore, Style

sqs = boto3.client('sqs')

queue_url = 'https://sqs.eu-central-1.amazonaws.com/238713673548/wikidata-claims'


def send_message(id: str, summary: str, type: str, key: str, value: str = '-', lat: float = 0, lon: float = 0):
    response = sqs.send_message(
        QueueUrl=queue_url,
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

    return response


def receive_message():
    response = sqs.receive_message(
        QueueUrl=queue_url,
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

    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=message['ReceiptHandle']
    )
