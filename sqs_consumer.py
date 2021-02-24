#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
from colorama import init, deinit

import sqs

init(autoreset=True)

while True:
    try:
        sqs.receive_message()
    except Exception as exception:

        if KeyError == type(exception):
            continue

        print(format(exception))

        deinit()
        exit(1)
