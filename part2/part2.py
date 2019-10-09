#!/usr/bin/env python

import argparse
import os
import time
import part1


import googleapiclient.discovery


def create_snapshot(compute, project, zone, disk):
    snapshot_body = {
        # TODO: Add desired entries to the request body.
        "name": "base-snapshot-" + disk,
        "sourceDisk": disk
    }

    request = compute.disks().createSnapshot(project=project, zone=zone, disk=disk, body=snapshot_body)
    response = request.execute()

    return response


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


def main(project, bucket, zone, instance_name, filename):
    compute = googleapiclient.discovery.build('compute', 'v1')

    response = create_snapshot(compute, project, zone, instance_name)

    instance_names = ["instance1", "instance2", "instance3"]
    times = []
    for instance_name in instance_names:
        print('Creating instance.')
        start_time = time.time()
        operation = part1.create_instance(compute, project, zone, instance_name, bucket)
        wait_for_operation(compute, project, zone, operation['name'])
        times.append(time.time() - start_time)

    with open(filename, 'w') as f:
        for i in range(len(instance_names)):
            f.write(instance_names[i]+'\t'+str(times[i])+' secs\n')

    instances = part1.list_instances(compute, project, zone)

    print('Instances in project %s and zone %s:' % (project, zone))
    for instance in instances:
        print(' - ' + instance['name'])


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

    filename = "TIMING.md"
    args = parser.parse_args()

    main(args.project_id, args.bucket_name, args.zone, args.name, filename)