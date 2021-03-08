cd /opt/feedback-bot
#python3 src/main.py > run.out 2>run.err &
docker run feedback-bot-image > run.out 2>run.err &