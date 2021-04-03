questions_start = [
    {
        'type': 'confirm',
        'name': 'start',
        'message': 'Start a new work?',
    },
]

questions_generate_workload_confirm = [
    {
        'type': 'confirm',
        'name': 'workload',
        'message': 'Generate new Overpass workload?',
        'default': False,
    },
]

WORKLOAD_WIKIDATA_IR = 'Add Wiki to IR railway stations'
WORKLOAD_WIKIDATA_DMRC = 'Add Wiki to DMRC railway stations'

questions_generate_workload_list = [
    {
        'type': 'list',
        'name': 'overpass_list',
        'message': 'Which workload to generate?',
        'choices': [
            WORKLOAD_WIKIDATA_IR,
            WORKLOAD_WIKIDATA_DMRC,
        ],
        # 'filter': lambda val: val.lower().replace(' ', '_'),
    },
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

questions_osm_update = [
    {
        'type': 'confirm',
        'name': 'confirm',
        'message': 'Confirm updating OSM?',
        'default': False,
    }
]
