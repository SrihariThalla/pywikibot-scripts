#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import pywikibot
import os
import overpy
from pywikibot import pagegenerators as pg


def print_log(item: pywikibot.ItemPage, message: str):
    print('%s - %s - %s' % (message, item.labels.get('en', 'No EN label'), item.getID()))


def get_location(item_id):
    # result = api.query("""
    #         node["wikidata"="{0}"];
    #         (._;>;);
    #         out body;
    #         """.format(item_id))
    #
    # if len(result.nodes) == 1:
    #     return result.nodes[0]
    #
    # if len(result.nodes) > 1:
    #     print_log(item, 'Too many nodes found for')
    #     print()
    #
    #     return False

    result = api.query("""
                way["wikidata"="{0}"];
                (._;>;);
                out body;
                """.format(item_id))

    # if len(result.ways) == 1:
    #     return result.ways[0]

    if len(result.ways) > 1:
        print_log(item, 'Too many ways found for')
        print()

        return False

    print(result.ways)

    result = api.query("""
                    relation["wikidata"="{0}"];
                    (._;>;);
                    out body;
                    """.format(item_id))

    print(result.relations)

    if len(result.relations) == 1:
        return result.relations

    return False


api = overpy.Overpass()
site = pywikibot.Site("wikidata", "wikidata")

script_dir = os.path.dirname(__file__)
with open(os.path.join(script_dir, 'ir_stations_wo_coord.rq'), 'r') as query_file:
    query = query_file.read()

generator = pg.WikidataSPARQLPageGenerator(query, site)

for item in generator:
    item.get()

    # location = get_location(item.getID())
    #
    # print(location)
    #
    # if not location:
    #     print_log(item, 'No location found for')
    #
    # continue

    result = api.query("""
        node["wikidata"="{0}"];
        (._;>;);
        out body;
        """.format(item.getID()))

    if len(result.nodes) == 0:
        print_log(item, 'No nodes are found for')
        print()

        continue

    if len(result.nodes) > 1:
        print_log(item, 'Too many nodes found for')
        print()

        continue

    node = result.nodes[0]

    print_log(item, '%d %f %f' % (node.id, node.lat, node.lon))

    coordinateclaim = pywikibot.Claim(site.data_repository(), 'P625')
    coordinate = pywikibot.Coordinate(lat=float(node.lat), lon=float(node.lon), precision=0.000001, site=site)
    coordinateclaim.setTarget(coordinate)
    item.addClaim(coordinateclaim, summary='Adding coordinate claim from OSM')

    print_log(item, 'Coordinates added to')
    print()
