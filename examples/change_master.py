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
Show how to change master storage domain.

Example usage:

    $ ./change_master.py -c engine-dev 46 sparse-nfs-00
    Found data center name=46 id=3f8e08e6-5485-429e-a686-63754906b27b
    Found storage domain name=sparse-nfs-00 id=60edfd87-a97c-497c-85a2-2f044993bc2e
    Setting storage domain sparse-nfs-00 as master
    Operation failed: [Cannot switch master storage domain. The storage pool has running tasks.]
    Trying again in 10 seconds...
    Setting storage domain sparse-nfs-00 as master
    Operation failed: [Cannot switch master storage domain. The storage pool has running tasks.]
    Trying again in 10 seconds...
    Setting storage domain sparse-nfs-00 as master
    Waiting for job with correlation id 057f7087-569a-4a99-8092-0cc3f66cce04
    Operation completed in 10.24 seconds

"""

import time
import uuid
from contextlib import closing

import ovirtsdk4 as sdk
from ovirtsdk4 import types

from helpers import common
from helpers import jobs

parser = common.ArgumentParser(description="Change master storage domain")

parser.add_argument(
    "data_center",
    help="Data center name to modify.")

parser.add_argument(
    "storage_domain",
    help="Storage domain name to use as new master storage domain.")

args = parser.parse_args()
common.configure_logging(args)

connection = common.create_connection(args)
with closing(connection):
    system_service = connection.system_service()

    # First, find the data center by searching the specified data center name.

    dcs_service = system_service.data_centers_service()
    dcs = dcs_service.list(search=f"name={args.data_center}")
    if not dcs:
        raise RuntimeError(f"No such data center: {args.data_center}")

    dc = dcs[0]
    print(f"Found data center name={dc.name} id={dc.id}")

    # Now find the storage domain using the specified storage domain name.

    sds_service = system_service.storage_domains_service()
    sds = sds_service.list(search=f"name={args.storage_domain}")
    if not sds:
        raise RuntimeError(f"No such storage domain: {args.storage_domain}")

    sd = sds[0]
    print(f"Found storage domain name={sd.name} id={sd.id}")

    if sd.master:
        raise RuntimeError(f"Storage domain {sd.name} is already master")

    # Try to select storage domain as master. This may take some time if
    # related tasks are running, so we want to wait for the job. To wait for
    # the job we need to create a unique correlation id, and set a deadline.

    dc_service = dcs_service.data_center_service(id=dc.id)

    while True:
        print(f"Setting storage domain {sd.name} as master")

        correlation_id = str(uuid.uuid4())
        start = time.monotonic()
        deadline = start + 180
        try:
            dc_service.set_master(
                storage_domain=sd,
                query={"correlation_id": correlation_id},
            )
            break
        except sdk.Error as e:
            if e.code != 409:
                raise

            print(f"Operation failed: {e.fault.detail}")

            # Switching storage domain is not possible when SPM tasks are
            # running. Since these tasks are usually fast, trying again after
            # few seconds typically succeeds.

            print("Trying again in 10 seconds...")
            time.sleep(10)

    print(f"Waiting for job with correlation id {correlation_id}")

    jobs.wait_for_jobs(connection, correlation_id, deadline)

    elapsed = time.monotonic() - start
    print(f"Operation completed in {elapsed:.2f} seconds")
