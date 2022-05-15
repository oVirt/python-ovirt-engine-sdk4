#!/usr/bin/env python3
#
# Copyright (c) 2022 Red Hat, Inc.
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
Show how to delete many disks created by the 'add_disks.py' example easily,
based on their description.
"""

import sys
from contextlib import closing

from helpers import common
from helpers.common import progress

parser = common.ArgumentParser(description="Delete disks by a given description")

parser.add_argument(
    "--sd-name",
    required=True,
    help="Name of the storage domain.")

parser.add_argument(
    "--description",
    default="Created by add_disks.py",
    help="The description of the disks to be deleted.")

args = parser.parse_args()

progress("Connecting...")
connection = common.create_connection(args)
with closing(connection):
    storage_domains_service = connection.system_service().storage_domains_service()
    found_sd = storage_domains_service.list(search=f'name={args.sd_name}')
    if not found_sd:
        raise RuntimeError(f"Couldn't find storage domain {args.sd_name}")

    sd = found_sd[0]
    sd_service = storage_domains_service.storage_domain_service(sd.id)
    sd_disks_service = sd_service.disks_service()

    # StorageDomainDisksService.list has no 'search' parameter and ignores
    # query={'name': 'spam'} so we have to do the filtering ourselves
    disks = [disk for disk in sd_disks_service.list()
             if disk.description == args.description]

    if not disks:
        progress("No disks were found")
        sys.exit(1)

    for i, disk in enumerate(disks, start=1):
        progress(f"Removing disk {disk.id} ({i}/{len(disks)})")
        sd_disks_service.disk_service(disk.id).remove()

progress("All disks were removed")
