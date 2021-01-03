#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

questions_start = [
    {
        'type': 'confirm',
        'name': 'start',
        'message': 'Start a new lookup?',
    },
]

questions_osm = [
    {
        'type': 'list',
        'name': 'osm_type',
        'message': 'What\'s the OSM type?',
        'choices': [
            'Node',
            'Way',
            'Relation',
        ],
        'filter': lambda val: val.lower(),
    },
    {
        'type': 'input',
        'name': 'osm_id',
        'message': 'What\'s the OSM ID?',
    }
]

questions_wikidata = [
    {
        'type': 'confirm',
        'name': 'found',
        'message': 'Is this what you are looking for?',
    }
]

questions_wikidata_create = [
    {
        'type': 'confirm',
        'name': 'create',
        'message': 'Confirm creating new Item?',
        'default': False,
    }
]
