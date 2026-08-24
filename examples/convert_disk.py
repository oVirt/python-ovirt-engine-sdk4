#!/usr/bin/env python
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
Show how to download disk snapshots using imageio client.
Requires the ovirt-imageio-client package.
"""

import time

from contextlib import closing

import ovirtsdk4.types as types

from helpers import common


def parse_args():
    parser = common.ArgumentParser(description="Download disk snapshot")

    parser.add_argument("disk_id", help="The disk's id")

    parser.add_argument(
        "-f", "--format",
        choices=("raw", "qcow2"),
        help=("The format the disk will converted to (qcow2, raw"))

    parser.add_argument(
        "--sparse",
        type=bool,
        help=("If true, the disk will be converted to a sparse disk, "
              "Otherwise to a preallocated disk")
        )

    return parser.parse_args()


args = parse_args()
common.configure_logging(args)

connection = common.create_connection(args)
with closing(connection):
    # Get the reference to the disks service:
    disks_service = connection.system_service().disks_service()

    # Find the disk we want to convert by id
    disk_service = disks_service.disk_service(args.disk_id)

    # Start the conversion to raw/preallocated
    if args.format == 'raw':
        disk_format = types.DiskFormat.RAW
    elif args.format == 'cow':
        disk_format = types.DiskFormat.COW
    disk_service.convert(
            disk=types.Disk(
                format=disk_format,
                sparse=args.sparse)
    )

    disk_service = disks_service.disk_service(args.disk_id)

    while True:
        time.sleep(1)
        disk = disk_service.get()
        if disk.status == types.DiskStatus.OK:
            break
