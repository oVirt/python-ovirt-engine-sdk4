#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2020 Red Hat, Inc.
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
This example will connect to the server and perform the selected full
backup operation (start backup, finalize backup or download backup disks)
for an existing running VM with the given disks.

Note that this feature API is supported from version 4.3
but the feature is currently in tech-preview until libvirt will
release official release that contains the support for incremental
backup.
Using this example requires a special libvirt version supporting
incremental backup.

Requires the ovirt-imageio-client package.
"""

import glob
import inspect
import os
import sys
import time

from contextlib import closing

from ovirt_imageio import client

import ovirtsdk4 as sdk
import ovirtsdk4.types as types

from helpers import common
from helpers import imagetransfer
from helpers import units
from helpers.common import progress


def main():
    parser = common.ArgumentParser(description="Backup VM disks")
    subparsers = parser.add_subparsers(title="commands")

    # Full backup flow parser
    full_parser = subparsers.add_parser(
        "full",
        help="Run full backup.")

    full_parser.set_defaults(command=cmd_full)

    add_download_args(full_parser)
    add_start_backup_args(full_parser)
    add_testing_args(full_parser)

    # Incremental backup flow parser
    incremental_parser = subparsers.add_parser(
        "incremental",
        help="Run incremental backup.")

    incremental_parser.set_defaults(command=cmd_incremental)

    add_download_args(incremental_parser)
    add_start_backup_args(incremental_parser)

    incremental_parser.add_argument(
        "--from-checkpoint-uuid",
        required=True,
        help="Perform incremental backup since the specified checkpoint "
             "UUID.")

    add_testing_args(incremental_parser)

    # Start backup flow parser
    start_parser = subparsers.add_parser(
        "start",
        help="Start VM backup.")

    start_parser.set_defaults(command=cmd_start)

    add_start_backup_args(start_parser)

    start_parser.add_argument(
        "--from-checkpoint-uuid",
        help="Perform incremental backup since the specified checkpoint "
             "UUID.")

    # Download flow parser
    download_parser = subparsers.add_parser(
        "download",
        help="Download VM backup disk.")

    download_parser.set_defaults(command=cmd_download)

    add_download_args(download_parser)

    download_parser.add_argument(
        "vm_uuid",
        help="UUID of the VM for the backup.")

    download_parser.add_argument(
        "--backup-uuid",
        required=True,
        help="UUID of the backup to finalize.")

    download_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Download incremental backup data in qcow2 format. The "
             "downloaded disk should be rebased on the previous backup "
             "to restore the disk contents. Can be used only if the "
             "backup was started with --from-checkpoint-uuid.")

    # Stop backup flow parser
    stop_parser = subparsers.add_parser(
        "stop",
        help="Stop VM backup.")

    stop_parser.set_defaults(command=cmd_stop)

    stop_parser.add_argument(
        "vm_uuid",
        help="UUID of the VM for the backup.")

    stop_parser.add_argument(
        "backup_uuid",
        help="UUID of the backup to finalize.")

    args = parser.parse_args()

    common.configure_logging(args)
    args.command(args)


# Commands

def cmd_full(args):
    """
    Run full backup flow - start, download and stop backup.
    """
    progress("Starting full backup for VM %r" % args.vm_uuid)

    connection = common.create_connection(args)
    with closing(connection):
        args.from_checkpoint_uuid = None
        backup = start_backup(connection, args)
        try:
            download_backup(connection, backup, args)
        finally:
            progress("Finalizing backup")
            stop_backup(connection, backup, args)

    progress("Full backup %r completed successfully" % backup.id)


def cmd_incremental(args):
    """
    Run incremental backup flow - start_incremental, download and stop backup.
    """
    progress("Starting incremental backup for VM %r" % args.vm_uuid)

    connection = common.create_connection(args)
    with closing(connection):
        backup = start_backup(connection, args)
        try:
            download_backup(connection, backup, args, incremental=True)
        finally:
            progress("Finalizing backup")
            stop_backup(connection, backup, args)

    progress("Incremental backup %r completed successfully" % backup.id)


def cmd_start(args):
    """
    Start backup, printing backup UUID.

    To download the backup run download command.
    To stop the backup run the stop command.
    """
    if args.from_checkpoint_uuid:
        progress(
            "Starting incremental backup since checkpoint %r for VM %r" % (
                args.from_checkpoint_uuid, args.vm_uuid))
    else:
        progress("Starting full backup for VM %r" % args.vm_uuid)

    connection = common.create_connection(args)

    with closing(connection):
        backup = start_backup(connection, args)

    progress("Backup %r is ready" % backup.id)


def cmd_download(args):
    """
    Download backup using the backup UUID printed by the start command.
    """
    progress("Downloading VM %r disks" % args.vm_uuid)
    args.download_backup = True

    connection = common.create_connection(args)
    with closing(connection):
        verify_vm_exists(connection, args.vm_uuid)
        backup_service = get_backup_service(
            connection, args.vm_uuid, args.backup_uuid)

        backup = get_backup(connection, backup_service, args.backup_uuid)
        if backup.phase != types.BackupPhase.READY:
            raise RuntimeError("Backup {} is not ready".format(backup_uuid))

        download_backup(connection, backup, args, incremental=args.incremental)

    progress("Finished downloading disks")


def cmd_stop(args):
    """
    Stop backup using the backup UUID printed by the start command.
    """
    progress("Finalizing backup %r" % args.backup_uuid)

    connection = common.create_connection(args)
    with closing(connection):
        verify_vm_exists(connection, args.vm_uuid)
        backup_service = get_backup_service(
            connection, args.vm_uuid, args.backup_uuid)

        # In a real application it will be a good idea to check if the backup
        # has succeeded, but it is useful to be able to stop more than once
        # for testing purposes.
        backup = get_backup(connection, backup_service, args.backup_uuid)
        stop_backup(connection, backup, args)

    progress("Backup %r completed successfully" % args.backup_uuid)


# Argument parsing

def add_download_args(parser):
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="maximum number of workers to use for backup. The default "
             "(4) improves performance when backing up a single disk. "
             "You may want to use lower number if you back up many disks "
             "in the same time.")

    parser.add_argument(
        "--buffer-size",
        type=units.humansize,
        default=client.BUFFER_SIZE,
        help="Buffer size per worker. The default ({}) gives good "
             "performance with the default number of workers. If you use "
             "smaller number of workers you may want use larger value."
             .format(client.BUFFER_SIZE))

    parser.add_argument(
        "--backup-dir",
        default="./",
        help="Path to a directory to download backup disks "
             "to (The default is the current directory).")

    parser.add_argument(
        "--timeout-policy",
        choices=('legacy', 'pause', 'cancel'),
        default='cancel',
        help="The action to be made for a timed out transfer.")


def add_start_backup_args(parser):
    parser.add_argument(
        "vm_uuid",
        help="UUID of the VM to backup.")

    parser.add_argument(
        "--backup-uuid",
        help="UUID of the created VM backup.")

    parser.add_argument(
        "--disk-uuid",
        action="append",
        help="Disk UUID to backup. May be used multiple times to backup "
             "multiple disks. If not specified, backup all VM disks.")

    parser.add_argument(
        "--description",
        dest="description",
        help="A description for the created backup/checkpoint to persist in the Engine DB.")


def add_testing_args(parser):
    """
    Testing options for full and incremental backup.
    """
    parser.add_argument(
        "--skip-download",
        dest="download_backup",
        action="store_false",
        help="If specified, start and stop a backup without downloading "
             "the disks.")


# Backup helpers

def start_backup(connection, args):
    verify_vm_exists(connection, args.vm_uuid)

    system_service = connection.system_service()
    vm_service = system_service.vms_service().vm_service(id=args.vm_uuid)

    backups_service = vm_service.backups_service()

    if args.disk_uuid:
        disks = [types.Disk(id=disk_id) for disk_id in args.disk_uuid]
    else:
        disks = get_vm_disks(connection, args.vm_uuid)

    if not disks:
        raise RuntimeError("Cannot start a backup without disks")

    backup = backups_service.add(
        types.Backup(
            id=args.backup_uuid,
            disks=disks,
            from_checkpoint_id=args.from_checkpoint_uuid,
            description=args.description
        )
    )

    progress("Waiting until backup %r is ready" % backup.id)

    # "get_backup()" invocation will raise if the backup failed.
    # So we just need to wait until the backup phase is READY.
    backup_service = backups_service.backup_service(backup.id)
    while backup.phase != types.BackupPhase.READY:
        time.sleep(1)
        backup = get_backup(connection, backup_service, backup.id)

    if backup.to_checkpoint_id is not None:
        progress("Created checkpoint %r" % backup.to_checkpoint_id)

    return backup


def stop_backup(connection, backup, args):
    backup_service = get_backup_service(connection, backup.vm.id, backup.id)

    backup_service.finalize()

    # "get_backup()" invocation will raise if the backup failed.
    # So we just need to wait until the backup phase is SUCCEEDED.
    while backup.phase != types.BackupPhase.SUCCEEDED:
        time.sleep(1)
        backup = get_backup(connection, backup_service, backup.id)


def download_backup(connection, backup, args, incremental=False):
    if not args.download_backup:
        progress("Skipping download")
        return

    backup_service = get_backup_service(connection, backup.vm.id, backup.id)
    backup_disks = backup_service.disks_service().list()

    timestamp = time.strftime("%Y%m%d%H%M%S")
    for disk in backup_disks:
        # During incremental backup, incremental backup may not be available
        # for some of the disks. We need to check the backup mode of the disk.
        has_incremental = disk.backup_mode == types.DiskBackupMode.INCREMENTAL

        # If incremental backup is not available, warn about it, since full
        # backup is much slower and takes much more storage.
        if incremental and not has_incremental:
            progress("Incremental backup not available for disk %r" % disk.id)

        file_name = "{}.{}.{}.{}.qcow2".format(
            timestamp, backup.to_checkpoint_id, disk.id, disk.backup_mode)
        disk_path = os.path.join(args.backup_dir, file_name)

        # When downloading incremental backup, try to use the previous backup
        # file as a backing file. This creates a chain that can be used later
        # to restore the disk.
        if has_incremental:
            backing_file = find_backing_file(
                args.backup_dir, backup.from_checkpoint_id, disk.id)
        else:
            backing_file = None

        download_disk(
            connection, backup.id, disk, disk_path, args,
            incremental=has_incremental,
            backing_file=backing_file)


def get_backup_service(connection, vm_uuid, backup_uuid):
    system_service = connection.system_service()
    vms_service = system_service.vms_service()
    backups_service = vms_service.vm_service(id=vm_uuid).backups_service()
    return backups_service.backup_service(id=backup_uuid)


def download_disk(connection, backup_uuid, disk, disk_path, args,
                  incremental=False, backing_file=None):
    progress("Downloading %s backup for disk %r" %
             ("incremental" if incremental else "full", disk.id))
    progress("Creating backup file %r" % disk_path)
    if backing_file:
        progress("Using backing file %r" % backing_file)

    transfer = imagetransfer.create_transfer(
        connection,
        disk,
        types.ImageTransferDirection.DOWNLOAD,
        backup=types.Backup(id=backup_uuid),
        timeout_policy=types.ImageTransferTimeoutPolicy(args.timeout_policy))
    try:
        progress("Image transfer %r is ready" % transfer.id)
        download_url = transfer.transfer_url

        extra_args = {}

        parameters = inspect.signature(client.download).parameters

        # Use multiple workers to speed up the download.
        if "max_workers" in parameters:
            extra_args["max_workers"] = args.max_workers

        # Use proxy_url if available. Download will use proxy_url if
        # transfer_url is not available.
        if "proxy_url" in parameters:
            extra_args["proxy_url"] = transfer.proxy_url

        with client.ProgressBar() as pb:
            client.download(
                download_url,
                disk_path,
                args.cafile,
                incremental=incremental,
                secure=args.secure,
                buffer_size=args.buffer_size,
                progress=pb,
                backing_file=backing_file,
                backing_format="qcow2",
                **extra_args)
    finally:
        progress("Finalizing image transfer")
        imagetransfer.finalize_transfer(connection, transfer, disk)

    progress("Download completed successfully")


# General helpers

def get_vm_disks(connection, vm_id):
    system_service = connection.system_service()
    vm_service = system_service.vms_service().vm_service(id=vm_id)
    disk_attachments = vm_service.disk_attachments_service().list()

    disks = []
    for disk_attachment in disk_attachments:
        disk_id = disk_attachment.disk.id
        disk = system_service.disks_service().disk_service(disk_id).get()
        disks.append(disk)

    return disks


def get_last_backup_event(connection, search_id):
    events_service = connection.system_service().events_service()
    backup_events = events_service.list(search=str(search_id))
    if not backup_events:
        return None

    # The first item is the most recent event.
    last_event = backup_events[0]
    return dict(code=event.code, description=event.description)


def verify_vm_exists(connection, vm_uuid):
    system_service = connection.system_service()
    vm_service = system_service.vms_service().vm_service(id=vm_uuid)
    try:
        vm_service.get()
    except sdk.NotFoundError:
        progress("VM %r does not exist" % vm_uuid)
        sys.exit(1)


def get_backup(connection, backup_service, backup_uuid):
    try:
        backup = backup_service.get()
    except sdk.NotFoundError:
        last_event = get_last_backup_event(connection, backup_uuid)
        raise RuntimeError("Backup {} does not exist, last reported event: {}"
                           .format(backup_uuid, last_event))

    if backup.phase == types.BackupPhase.FAILED:
        last_event = get_last_backup_event(connection, backup_uuid)
        raise RuntimeError("Backup {} has failed, last reported event: {}"
                           .format(backup_uuid, last_event))

    return backup


def find_backing_file(backup_dir, checkpoint_uuid, disk_uuid):
    """
    Return the name of the backing file for checkpoint, or None if the file was
    not found.

    Assumes backup filename:

        {timestamp}.{checkpoint-uuid}.{disk-uuid}.{backup-mode}.qcow2
    """
    pattern = os.path.join(backup_dir, f"*.{checkpoint_uuid}.{disk_uuid}.*")
    matches = glob.glob(pattern)
    if not matches:
        return None

    # The backing file can be an absolute path or a relative path from the
    # image directory. Using a relative path make is easier to manage.
    return os.path.relpath(matches[0], backup_dir)


if __name__ == "__main__":
    main()
