#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import pywikibot
import csv
import os


def item_name(item):
    return item.labels.get('en', 'Not found')


def wikiparser(station):
    site = pywikibot.Site('wikidata', 'wikidata')
    repo = site.data_repository()
    station = pywikibot.ItemPage(repo, station)
    station.get()

    if not station.botMayEdit():
        print('%s - Bot may not edit' % (item_name(station)))

        return

    if 'P137' not in station.claims:
        print('%s - No operator found' % (item_name(station)))

        return

    if 1 == len(station.claims['P137']):
        print('%s - Has only one Operator' % (item_name(station)))

        return

    claims = dict()
    claims_to_remove = []

    for operator in station.claims['P137']:
        target = operator.getTarget()

        if 'wikibase-item' != operator.type:
            print('%s - %s - Type is not wikibase-item. But: %s' % (item_name(station), operator.snak, operator.type))

            return

        division = operator.getTarget()
        division.get()

        if target.getID() in claims:
            print('%s - %s - %s - Found' % (item_name(station), operator.snak, item_name(division)))

            claims_to_remove.append(operator)

            continue

        print("%s - %s - %s - Not found" % (item_name(station), operator.snak, item_name(division)))

        claims[target.getID()] = True

    if len(claims_to_remove) == 0:
        print('%s - No claims to remove' % (item_name(station)))

        return

    station.removeClaims(claims_to_remove)

    print('Removed = %d' % (len(claims_to_remove)))


script_dir = os.path.dirname(__file__)
with open(os.path.join(script_dir, 'data.csv'), newline='') as csvfile:
    data = csv.reader(csvfile, delimiter=',')
    for row in data:
        wikiparser(row[0])
