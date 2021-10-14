#!/usr/bin/env python
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

import logging

import ovirtsdk4 as sdk
import ovirtsdk4.types as types

logging.basicConfig(level=logging.DEBUG, filename='example.log')

# This example shows how to import an external template from an
# OVA file.

# Create a connection to the server:
connection = sdk.Connection(
    url='https://engine40.example.com/ovirt-engine/api',
    username='admin@internal',
    password='redhat123',
    ca_file='ca.pem',
    debug=True,
    log=logging.getLogger(),
)

# Get the reference to the service that manages import of external
# templates:
system_service = connection.system_service()
imports_service = system_service.external_template_imports_service()

# Initiate the import of template 'mytemplate' from the OVA file. Note
# that the .ova file needs to be previously copied to a place where the
# selected host (the 'myhost' host in this case) can read it. Make also
# sure that the 'vdsm' user can read it. To do so the easier way is to
# change the ownership of the directory:
#
#  chown --recursive 36:36 /mytemplates
#
# The 'clone' parameter determines whether the new template is imported
# as a new entity or not. Default value is 'False', setting it to 'True'
# allows for importing the same template multiple times.
#
# If something fails during the import there will be useful information
# in the '/var/log/vdsm/import' directory of the selected host.
imports_service.add(
    types.ExternalTemplateImport(
        template=types.Template(
            name='mytemplate'
        ),
        url='ova:///mytemplates/my.ova',
        cluster=types.Cluster(
            name='mycluster'
        ),
        storage_domain=types.StorageDomain(
            name='mydata'
        ),
        host=types.Host(
            name='myhost'
        ),
        clone=True
    )
)

# Close the connection:
connection.close()
