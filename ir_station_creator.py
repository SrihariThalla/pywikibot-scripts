#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import pywikibot
import sys

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

name = sys.argv[1]
code = sys.argv[2]

print('Station: "%s" - Code: "%s"' % (name, code))

instance_of = pywikibot.Claim(repo, 'P31')
instance_of.setTarget(pywikibot.ItemPage(repo, 'Q55488'))

country = pywikibot.Claim(repo, 'P17')
country.setTarget(pywikibot.ItemPage(repo, 'Q668'))

owned_by = pywikibot.Claim(repo, 'P127')
owned_by.setTarget(pywikibot.ItemPage(repo, 'Q819425'))

station_code = pywikibot.Claim(repo, 'P5696')
station_code.setTarget(code)

data = {
    "labels": {"en": "%s railway station" % name, },
    "descriptions": {"en": "railway station in India", },
}

station = pywikibot.ItemPage(repo)
station.editEntity(data)

print('Station: "%s" - Code: "%s" - Wikidata: %s' % (name, code, station.getID()))

station.addClaim(instance_of)
station.addClaim(country)
station.addClaim(owned_by)
station.addClaim(station_code)
