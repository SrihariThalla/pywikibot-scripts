import pywikibot
import os
import overpy
from pywikibot import pagegenerators as pg


def print_log(item: pywikibot.ItemPage, message: str):
    print('%s - %s - %s' % (message, item.labels.get('en', 'No EN label'), item.getID()))


api = overpy.Overpass()
site = pywikibot.Site("wikidata", "wikidata")

script_dir = os.path.dirname(__file__)
with open(os.path.join(script_dir, 'ir_stations_wo_coord.rq'), 'r') as query_file:
    query = query_file.read()

generator = pg.WikidataSPARQLPageGenerator(query, site)

for item in generator:
    item.get()

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
