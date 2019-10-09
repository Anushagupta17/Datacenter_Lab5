#!/usr/bin/env python

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example of using the Compute Engine API to create and delete instances.

Creates a new compute engine instance and uses it to apply a caption to
an image.

    https://cloud.google.com/compute/docs/tutorials/python-guide

For more information, see the README.md under /compute.
"""

import argparse
import os
import time

import googleapiclient.discovery
import google.oauth2.service_account as service_account


def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None


def create_instance(compute, project, zone, name, bucket, creds_content, create_instance_file, startup_script_file):
    # Get the latest Debian Jessie image.
    image_response = compute.images().getFromFamily(
        project='ubuntu-os-cloud', family='ubuntu-1804-lts').execute()
    source_disk_image = image_response['selfLink']

    # Configure the machine
    machine_type = "zones/%s/machineTypes/n1-standard-1" % zone
    startup_script = open(
        os.path.join(
            os.path.dirname(__file__), 'startup-script-VM1.sh'), 'r').read()
    image_url = "http://storage.googleapis.com/gce-demo-input/photo.jpg"
    image_caption = "Ready for dessert?"

    config = {
        'name': name,
        'machineType': machine_type,

        # Specify the boot disk and the image to use as a source.
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],

        # Specify a network interface with NAT to access the public
        # internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write'
            ]
        }],

        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        'metadata': {
            'items': [{
                # Startup script is automatically executed by the
                # instance upon startup.
                'key': 'startup-script',
                'value': startup_script
            }, {
                'key': 'url',
                'value': image_url
            }, {
                'key': 'text',
                'value': image_caption
            }, {
                'key': 'bucket',
                'value': bucket
            },
               {
                'key': 'creds-content',
                'value': creds_content
            },
               {
                'key': 'create-instance',
                'value': create_instance_file
            },
               {
                'key': 'startup-script-VM2',
                'value': startup_script_file
            },
               {
                'key': 'project_id',
                'value': project
            },
               {
                'key': 'zone',
                'value': zone
            },
            ]
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()


def wait_for_operation(compute, project, zone, operation):
    print('Waiting for operation to finish...')
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(1)
# [END wait_for_operation]


def exists_firewall(compute, project):
    request = compute.firewalls().list(project=project)
    while request is not None:
        response = request.execute()
        for firewall in response['items']:
            # TODO: Change code below to process each `firewall` resource:
            if firewall["name"] == "allow-5000":
                return 1
        request = compute.firewalls().list_next(previous_request=request, previous_response=response)
    return 0


def create_firewall(compute, project):
    firewall_body = {
        "name": "allow-5000",
        "allowed": [{
            "IPProtocol": "tcp",
            "ports": [5000]
        }],
        "sourceRanges": [
            "0.0.0.0/0"
        ],
        "targetTags": [
            "allow-5000"
        ]
    }

    request = compute.firewalls().insert(project=project, body=firewall_body)
    response = request.execute()

    # TODO: Change code below to process the `response` dict:
    return response


def set_tags(compute, project, zone, instance_name):
    request = compute.instances().get(project=project, zone=zone, instance=instance_name)
    response = request.execute()
    # print(response)
    tags_body = {
        "items": [
            "allow-5000"
        ],
        "fingerprint": response["tags"]["fingerprint"]
    }

    request = compute.instances().setTags(project=project, zone=zone, instance=instance_name, body=tags_body)
    response = request.execute()

    # TODO: Change code below to process the `response` dict:
    return response


def main(project, bucket, zone, instance_name, filename, create_instance_filename, startup_filename):
    credentials = service_account.Credentials.from_service_account_file(filename=filename)
    compute = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

    print('Creating instance.')

    with open(filename, 'r') as f:
        creds_content = f.read()

    with open(create_instance_filename, 'r') as f:
        create_instance_file = f.read()

    with open(startup_filename, 'r') as f:
        startup_script_file = f.read()

    operation = create_instance(compute, project, zone, instance_name, bucket, creds_content, create_instance_file,
                                startup_script_file)
    wait_for_operation(compute, project, zone, operation['name'])

    instances = list_instances(compute, project, zone)

    print('Instances in project %s and zone %s:' % (project, zone))
    for instance in instances:
        print(' - ' + instance['name'])

    """if not(exists_firewall(compute, project)):
        response1 = create_firewall(compute, project)
    response2 = set_tags(compute, project, zone, instance_name)"""


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('project_id', help='Your Google Cloud project ID.')
    parser.add_argument(
        'bucket_name', help='Your Google Cloud Storage bucket name.')
    parser.add_argument(
        '--zone',
        default='us-central1-f',
        help='Compute Engine zone to deploy to.')
    parser.add_argument(
        '--name', default='demo-instance', help='New instance name.')

    args = parser.parse_args()
    filename = "service-credentials.json"
    create_instance_filename = "create_instance_VM2.py"
    startup_filename = "startup-script-VM2.sh"
    main(args.project_id, args.bucket_name, args.zone, args.name, filename, create_instance_filename, startup_filename)
