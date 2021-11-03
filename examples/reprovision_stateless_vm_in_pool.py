#!/usr/bin/env python
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
Show how to re-provision stateless VM in VM pool while maintaining VM permissions

vm_name - VM to recreate
"""

import logging
import sys
import time
import uuid

import ovirtsdk4 as sdk
import ovirtsdk4.types as types

from helpers import jobs

vm_name = 'vm'
TIMEOUT = 100

# Create the connection to the server:
connection = sdk.Connection(
    url='https://engine40.example.com/ovirt-engine/api',
    username='admin@internal',
    password='redhat123',
    ca_file='ca.pem',
    debug=True,
    log=logging.getLogger(),
)

system_service = connection.system_service()

vms_service = system_service.vms_service()

vms = vms_service.list(search=f"name={vm_name}")
if not vms:
    print("VM doesn't exist")
    sys.exit(0)

vm = vms[0]
vm_template = connection.follow_link(vm.template)
template_id = vm_template.id
template_name = vm_template.name
template_base_template = vm_template.version.base_template

if vm.use_latest_template_version:
    print('VM should not use latest template version')
    sys.exit(0)

# Stop the VM in case it is running

vm_service = vms_service.vm_service(vm.id)
if vm.status != types.VmStatus.DOWN:
    # Call the "stop" method of the service to stop it:
    vm_service.stop()
    # Wait till the virtual machine is down:
    while True:
        time.sleep(5)
        vm = vm_service.get()
        if vm.status == types.VmStatus.DOWN:
            break

# Remove the disks from the VM

disk_attachments_service = vm_service.disk_attachments_service()
disks_service = system_service.disks_service()

correlation_id = str(uuid.uuid4())
start = time.monotonic()
deadline = start + TIMEOUT

for disk_attachment in disk_attachments_service.list():
    disk_attachment_service = disk_attachments_service.attachment_service(disk_attachment.id)
    disk_service = disks_service.disk_service(disk_attachment.disk.id)
    disk_service.remove(query={'correlation_id': correlation_id})
    print(f"Removing disk - Waiting for job with correlation id {correlation_id}")
    jobs.wait_for_jobs(connection, correlation_id, deadline)
    elapsed = time.monotonic() - start
    print(f"Removing disk - Operation completed in {elapsed:.2f} seconds")


# Create new template from the VM

templates_service = system_service.templates_service()

new_template = templates_service.add(
    template=types.Template(
        version=types.TemplateVersion(
            base_template=template_base_template
        ),
        name=template_name,
        vm=types.Vm(
            id=vm.id
        )
    )
)
new_template_service = templates_service.template_service(new_template.id)

# Wait till the status of the template is OK, as that means that it is
# completely created and ready to use

while True:
    time.sleep(5)
    new_template = new_template_service.get()
    if new_template.status == types.TemplateStatus.OK:
        break

# Change the VM template to the new version
correlation_id = str(uuid.uuid4())
start = time.monotonic()
deadline = start + TIMEOUT

try:
    vm_service.update(
        types.Vm(
            template=types.Template(
                id=new_template.id
            )
        ),
        query={'correlation_id': correlation_id}
    )
except:
    # ignore exception, call fails as the VM can't be returned because the VM is already deleted and recreated
    pass


print(f"Updating VM to temporary template - Waiting for job with correlation id {correlation_id}")

jobs.wait_for_jobs(connection, correlation_id, deadline)

elapsed = time.monotonic() - start
print(f"Updating VM to temporary template - Operation completed in {elapsed:.2f} seconds")

vm = vms_service.list(search=f"name={vm_name}")
vm_service = vms_service.vm_service(vm[0].id)

# restore the VM template to the old version

correlation_id = str(uuid.uuid4())
start = time.monotonic()
deadline = start + TIMEOUT


try:
    vm_service.update(
        types.Vm(
            template=types.Template(
                id=template_id
            )
        ),
        query={'correlation_id': correlation_id}
    )
except:
    # ignore exception, call fails as the VM can't be returned because the VM is already deleted and recreated
    pass

print(f"Updating VM to the original template - Waiting for job with correlation id {correlation_id}")

jobs.wait_for_jobs(connection, correlation_id, deadline)

elapsed = time.monotonic() - start
print(f"Updating VM to the original template - Operation completed in {elapsed:.2f} seconds")

# Remove newly created template

new_template_service.remove(
    template=types.Template(
        id=new_template.id
    )
)

connection.close()
