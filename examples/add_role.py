#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2016 Red Hat, Inc.
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

# This example will connect to the server and create new role:
# Create the connection to the server:
connection = sdk.Connection(
    url='https://engine40.example.com/ovirt-engine/api',
    username='admin@internal',
    password='redhat123',
    ca_file='ca.pem',
    debug=True,
    log=logging.getLogger(),
)

# Get the reference to the roles service:
roles_service = connection.system_service().roles_service()

# Use the "add" method to create new role (note that you need to pass
# permit id not the name, when creating new role):
role = roles_service.add(
    types.Role(
        name='myrole',
        administrative=False,
        description='My custom role to create virtual machines',
        permits=[
            # create_vm permit
            types.Permit(id='1'),
            # login permit
            types.Permit(id='1300'),
        ],
    ),
)

# Close the connection to the server:
connection.close()
