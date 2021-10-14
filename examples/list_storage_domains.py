#!/usr/bin/python3
#
# Copyright (c) 2021 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Show how to list storage domains and limit the results with a search pattern.

Examples
--------

List all storage domains:

    $ ./list_storage_domains.py -c engine-dev
    [
      {
        "name": "iscsi-00",
        "id": "feab3738-c158-4d48-8a41-b5a95c057a50",
        "type": "data"
      },
      {
        "name": "iscsi-01",
        "id": "313e6d78-80f7-41ab-883b-d1bddf77a5da",
        "type": "data"
      },
      ...
    ]

List all storage domains where name starts with "nfs":


    $ ./list_storage_domains.py -c engine-dev --search 'name=nfs*'
    [
      {
        "name": "nfs-00",
        "id": "8ece2aae-5c72-4a5c-b23b-74bae65c88e1",
        "type": "data"
      },
      {
        "name": "nfs-01",
        "id": "f07583a1-03d5-4716-9fb0-7dc5c347371a",
        "type": "data"
      },
      {
        "name": "nfs-03",
        "id": "a600ba04-34f9-4793-a5dc-6d4150716d14",
        "type": "data"
      }
    ]

Find storage domain where named "nfs-01":

    $ ./list_storage_domains.py -c engine-dev -s name=nfs-01
    [
      {
        "name": "nfs-01",
        "id": "f07583a1-03d5-4716-9fb0-7dc5c347371a",
        "type": "data"
      }
    ]

"""

import json
from contextlib import closing

import ovirtsdk4 as sdk
from helpers import common


parser = common.ArgumentParser(description="List storage domains")

parser.add_argument(
    "-s", "--search",
    help="If specified, limit the result using the search pattern.")

args = parser.parse_args()

connection = common.create_connection(args)
with closing(connection):
    sds_service = connection.system_service().storage_domains_service()
    storage_domains = sds_service.list(search=args.search)

    results = [{"name": sd.name, "id": sd.id, "type": str(sd.type)}
               for sd in storage_domains]
    print(json.dumps(results, indent=2))
