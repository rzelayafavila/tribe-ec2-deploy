#no longer using celery -- using realtime signal processor instead
sudo apt-get -y -q install supervisor rabbitmq-server


#make the rabbitmq user
sudo rabbitmqctl add_user tribe 4HU7c36GygdVqCIOLCBH
#make the vhost for tribe
sudo rabbitmqctl add_vhost tribe
#give the tribe user access to the tribe vhost
sudo rabbitmqctl set_permissions -p tribe tribe ".*" ".*" ".*"

#run celery through supervisor
echo '[program:tribe-celery]
command=celery -A tribe worker --autoscale=5,1 --loglevel=INFO
directory=/home/tribe/tribe
user=nobody
numprocs=1
autostart=true
autorestart=true
startsecs=10

; Need to wait for currently executing tasks to finish at shutdown.
; Increase this if you have very long running tasks.
stopwaitsecs = 600

; When resorting to send SIGKILL to the program to terminate it
; send SIGKILL to its whole process group instead,
; taking care of its children as well.
killasgroup=true

; if rabbitmq is supervised, set its priority higher
; so it starts first
priority=998' | sudo tee /etc/supervisor/conf.d/tribe-celery.conf
sudo supervisorctl reread



