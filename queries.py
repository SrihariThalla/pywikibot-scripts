import overpy

import functions
import questions_overpass as questions


def add_dmrc_stations(func: functions.Functions):
    query = """
            [out:xml]
            [timeout:25]
            ;
            (
              node
                ["railway"="station"]
                ["network"="Delhi Metro"]
                ["wikidata"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              way
                ["railway"="station"]
                ["network"="Delhi Metro"]
                ["wikidata"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              relation
                ["railway"="station"]
                ["network"="Delhi Metro"]
                ["wikidata"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              node
                ["railway"="station"]
                ["network"="Delhi Metro"]
                ["wikipedia"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              way
                ["railway"="station"]
                ["network"="Delhi Metro"]
                ["wikipedia"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              relation
                ["railway"="station"]
                ["network"="Delhi Metro"]
                ["wikipedia"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              node
                ["railway"="station"]
                ["network"="DMRC"]
                ["wikidata"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              way
                ["railway"="station"]
                ["network"="DMRC"]
                ["wikidata"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              relation
                ["railway"="station"]
                ["network"="DMRC"]
                ["wikidata"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              node
                ["railway"="station"]
                ["network"="DMRC"]
                ["wikipedia"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              way
                ["railway"="station"]
                ["network"="DMRC"]
                ["wikipedia"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
              relation
                ["railway"="station"]
                ["network"="DMRC"]
                ["wikipedia"!~".*"]
                (28.456316470125,76.983947753906,28.708355253824,77.300834655762);
            );
            out meta;
            >;
            out meta qt;
            """

    results = overpy.Overpass().query(query)

    for node in results.nodes:
        print(node)
        func.sqs_send_message(
            id=str(node.id),
            type=functions.OSM_NODE,
            key=questions.WORKLOAD_WIKIDATA_DMRC,
            queue=functions.SQS_OVERPASS,
        )

    for way in results.ways:
        print(way)
        func.sqs_send_message(
            id=str(way.id),
            type=functions.OSM_WAY,
            key=questions.WORKLOAD_WIKIDATA_DMRC,
            queue=functions.SQS_OVERPASS,
        )

    for relation in results.relations:
        print(relation)
        func.sqs_send_message(
            id=str(relation.id),
            type=functions.OSM_RELATION,
            key=questions.WORKLOAD_WIKIDATA_DMRC,
            queue=functions.SQS_OVERPASS,
        )

    print(f'Added Nodes={len(results.nodes)} Ways={len(results.ways)} Relations={len(results.relations)}')
