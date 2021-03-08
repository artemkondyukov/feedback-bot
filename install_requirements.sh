#!/bin/bash
yum -y update
yum -y install python36 python36-pip
pip-3.6 install -r /opt/feedback-bot/requirements.txt