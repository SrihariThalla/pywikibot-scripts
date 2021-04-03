
def start_dmrc_work(payload: dict):
    osm_type = payload['osm_type']['StringValue']
    osm_id = payload['osm_id']['StringValue']

    if functions.OSM_WAY == osm_type or functions.OSM_RELATION == osm_type:
        print('Way and Relation is not implemented')
        print(payload)
        print()

        return False

    element = func.osmapi.NodeGet(osm_id)

    print(element)
