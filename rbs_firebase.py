#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import os
import csv
from progress.bar import Bar
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

script_dir = os.path.dirname(__file__)
cred = credentials.Certificate(os.path.join(script_dir, 'rbs-stations-firebase.json'))

firebase_admin.initialize_app(cred, {
  'projectId': 'rbs-stations',
})

db = firestore.client()

with open(os.path.join(script_dir, 'rbs-stations.csv'), newline='') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=';')
    next(csv_reader)

    rows = list(csv_reader)

    bar = Bar('Importing RBS to Firebase', max=len(rows))

    for row in rows:
        doc_ref = db.collection('stations').document()
        insert = doc_ref.set({
            'code': row[1],
            'name': row[2],
            'numeric_code': row[3],
            'valid_from': row[4],
            'valid_upto': row[5],
            'guage': row[6],
            'traffic': row[7],
            'division': row[8],
            'division_name': row[9],
            'zone': row[10],
        })

        bar.next()

print()
