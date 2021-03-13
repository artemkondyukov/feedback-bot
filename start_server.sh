cd /opt/feedback-bot
docker run -v /data:/data --name feedback-bot feedback-bot-image > run.out 2>run.err &