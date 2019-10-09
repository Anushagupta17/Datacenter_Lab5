#!/bin/bash

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

apt-get update

PROJECT_ID=$(curl http://metadata/computeMetadata/v1/instance/attributes/project_id -H "Metadata-Flavor: Google")
ZONE=$(curl http://metadata/computeMetadata/v1/instance/attributes/zone -H "Metadata-Flavor: Google")
BUCKET=$(curl http://metadata/computeMetadata/v1/instance/attributes/bucket -H "Metadata-Flavor: Google")
CREDS_FILE="server-credentials.json"
CREATE_INSTANCE_FILE="create_instance_VM2.py"
STARTUP_SCRIPT_FILE="startup-script-VM2.sh"

curl http://metadata/computeMetadata/v1/instance/attributes/create-instance -H "Metadata-Flavor: Google" > $CREATE_INSTANCE_FILE
curl http://metadata/computeMetadata/v1/instance/attributes/startup-script-VM2 -H "Metadata-Flavor: Google" > $STARTUP_SCRIPT_FILE
curl http://metadata/computeMetadata/v1/instance/attributes/creds-content -H "Metadata-Flavor: Google" > $CREDS_FILE

sudo apt-get install -y python3 python3-pip git
sudo python3 setup.py install
sudo pip3 install -e .
sudo pip3 install --upgrade google-api-python-client
cd /
python3 create_instance_VM2.py --name instance2 --zone $ZONE $PROJECT_ID $BUCKET