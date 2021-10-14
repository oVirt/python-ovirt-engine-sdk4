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
jobs helpers
"""

import logging
import time

import ovirtsdk4 as sdk
from ovirtsdk4 import types

POLL_INTERVAL = 1

log = logging.getLogger("helpers")


class JobFailed(Exception):
    pass


class Timeout(Exception):
    pass


def wait_for_jobs(connection, correlation_id, deadline):
    """
    Wait for job started with a correlation_id header.

    Typical usage:

        correlation_id = str(uuid.uuid4())
        deadline = time.monotonic() + timeout

        some_service.operation(
            ...
            query={"correlation_id": correlation_id},
        )

        jobs.wait_for_jobs(connection, correlation_id, deadline)

    Raises JobFailed if one of the underlying jobs has failed or Timeout if the
    deadline is reached.
    """
    log.info("Waiting for jobs with correlation id %s",
             correlation_id)

    while not jobs_completed(connection, correlation_id):
        time.sleep(POLL_INTERVAL)
        if time.monotonic() > deadline:
            raise Timeout(
                f"Timeout waiting for jobs with correlation id "
                f"{correlation_id}")

    log.info("Jobs with correlation id %s finished",
             correlation_id)


def jobs_completed(connection, correlation_id):
    """
    Return True if all jobs with specified correlation id have completed,
    False otherwise.

    Raise JobFailed if some jobs have failed or aborted.
    """
    jobs_service = connection.system_service().jobs_service()

    try:
        jobs = jobs_service.list(search=f"correlation_id={correlation_id}")
    except sdk.Error as e:
        log.warning(
            "Error searching for jobs with correlation id %s: %s",
            correlation_id, e)
        # We don't know, assume that jobs did not complete yet.
        return False

    if all(job.status != types.JobStatus.STARTED for job in jobs):
        failed_jobs = [(job.description, str(job.status))
                       for job in jobs
                       if job.status != types.JobStatus.FINISHED]
        if failed_jobs:
            raise JobFailed(
                f"Some jobs for with correlation id {correlation_id} have "
                f"failed: {failed_jobs}")

        return True
    else:
        jobs_status = [(job.description, str(job.status)) for job in jobs]
        log.debug("Some jobs with correlation id %s are running: %s",
                  correlation_id, jobs_status)
        return False
