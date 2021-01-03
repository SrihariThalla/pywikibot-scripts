#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import os
from os.path import expanduser

import firebase_admin
from firebase_admin import credentials, firestore


def init():
    cred = credentials.Certificate(os.path.join(expanduser('~'), 'rbs-stations-firebase.json'))

    firebase_admin.initialize_app(cred, {
        'projectId': 'rbs-stations',
    })

    db = firestore.client()
    stations_ref = db.collection('stations')

    return stations_ref
