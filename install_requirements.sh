#!/bin/bash
yum -y update
#yum install -y yum-utils device-mapper-persistent-data lvm2
#yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

#yum install -y docker-ce docker-ce-cli containerd.io
#yum -y install python3 python3-pip
#pip-3 install -r /opt/feedback-bot/requirements.txt

#sudo systemctl start docker
#sudo systemctl enable docker

sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user

cd /opt/feedback-bot
docker image build . -t feedback-bot-image
