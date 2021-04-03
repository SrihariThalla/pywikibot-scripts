from enum import Enum

OSM_NODE = 'node'
OSM_WAY = 'way'
OSM_RELATION = 'relation'

OPTION_NONE = 'None'

SQS_OVERPASS = 'overpass'
SQS_WIKIDATA = 'wikidata'

QUEUE_WIKIDATA_CLAIMS = 'wikidata_claims'
QUEUE_OVERPASS_WORKLOAD = 'overpass_workload'

SQS_QUEUES = {
    QUEUE_WIKIDATA_CLAIMS: 'https://sqs.eu-central-1.amazonaws.com/238713673548/wikidata-claims',
    QUEUE_OVERPASS_WORKLOAD: 'https://sqs.eu-central-1.amazonaws.com/238713673548/overpass_workload',
}


class SqsDataType(Enum):
    STRING = 'String'
    NUMBER = 'Number'
