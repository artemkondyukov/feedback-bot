#!/bin/bash
yum -y update

sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user

cd /opt/feedback-bot
docker image build . -t feedback-bot-image
