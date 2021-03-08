#!/bin/bash
yum -y update
yum -y install docker-ce docker-ce-cli containerd.io
#yum -y install python3 python3-pip
#pip-3 install -r /opt/feedback-bot/requirements.txt
cd /opt/feedback-bot
docker image build . -t feedback-bot-image
docker run feedback-bot-image