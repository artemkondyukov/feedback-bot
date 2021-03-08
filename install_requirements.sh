#!/bin/bash
yum -y update
yum -y install python3 python3-pip
pip-3 install -r /opt/feedback-bot/requirements.txt