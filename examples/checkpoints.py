#!/usr/bin/python3
# -*- coding: utf-8 -*-

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
This example shows how to manage VM checkpoints.

To remove a single checkpoint, use:

    ./checkpoints.py -c myengine remove vm-id checkpoint-id

To remove checkpoints older than 7 days:

    ./checkpoints.py -c myengine purge vm-id

To remove checkpoints older than 1 day:

    ./checkpoints.py -c myengine purge --days 1 vm-id

"""
import time
import datetime

from contextlib import closing

import ovirtsdk4 as sdk
from helpers import common
from helpers.common import progress

def main():
    parser = common.ArgumentParser(description="Manage checkpoints")
    subparsers = parser.add_subparsers(title="commands")

    remove = subparsers.add_parser(
        "remove",
        help="Remove a VM checkpoint.")
    remove.set_defaults(command=cmd_remove)
    remove.add_argument(
        "vm_uuid",
        help="VM UUID for removing checkpoint.")
    remove.add_argument(
        "checkpoint_uuid",
        help="The removed checkpoint UUID.")

    purge = subparsers.add_parser(
        "purge",
        help="Remove old VM checkpoint.")
    purge.set_defaults(command=cmd_purge)
    purge.add_argument(
        "--days",
        type=int,
        default=7,
        help="Remove checkpoints older than specified days. If not "
             "specified, remove checkpoints older than 7 days.")
    purge.add_argument(
        "vm_uuid",
        help="VM UUID for removing checkpoint.")

    args = parser.parse_args()

    common.configure_logging(args)
    args.command(args)


def cmd_remove(args):
    progress(f"Removing VM {args.vm_uuid} checkpoint {args.checkpoint_uuid}")

    # Create a connection to the server
    connection = common.create_connection(args)
    with closing(connection):
        system_service = connection.system_service()
        vm_service = system_service.vms_service().vm_service(id=args.vm_uuid)
        checkpoints_service = vm_service.checkpoints_service()
        checkpoint_service = checkpoints_service.checkpoint_service(id=args.checkpoint_uuid)

        # Validate that the VM has the requested checkpoint
        try:
            checkpoint_service.get()
        except sdk.NotFoundError:
            raise RuntimeError(f"VM {args.vm_uuid} has no checkpoint {args.checkpoint_uuid}")

        remove_checkpoint(checkpoint_service)
        progress(f"Checkpoint {args.checkpoint_uuid} removed successfully")


def cmd_purge(args):
    progress(f"Removing VM {args.vm_uuid} checkpoints older than {args.days} days")

    # Create a connection to the server
    connection = common.create_connection(args)
    with closing(connection):
        system_service = connection.system_service()
        vm_service = system_service.vms_service().vm_service(id=args.vm_uuid)
        checkpoints_service = vm_service.checkpoints_service()

        now = datetime.datetime.now(datetime.timezone.utc)

        for checkpoint in checkpoints_service.list():
            checkpoint_age = now - checkpoint.creation_date

            if checkpoint_age.days > args.days:
                progress(f"Removing checkpoint {checkpoint.id}, created {checkpoint_age.days} days ago")
                checkpoint_service = checkpoints_service.checkpoint_service(checkpoint.id)
                remove_checkpoint(checkpoint_service)
                progress(f"Checkpoint {checkpoint.id} removed successfully")


def remove_checkpoint(checkpoint_service, timeout=60):
    checkpoint_service.remove()

    dedaline = time.monotonic() + timeout
    while True:
        try:
            checkpoint_service.get()
        except sdk.NotFoundError:
            break

        if time.monotonic() > deadline:
            raise RuntimeError("Timeout waiting for checkpoint removal")

        time.sleep(1)


if __name__ == "__main__":
    main()
