#setup unattended updates

echo 'APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";' | sudo tee /etc/apt/apt.conf.d/20auto-upgrades

echo '// Automatically upgrade packages from these (origin, archive) pairs
Unattended-Upgrade::Allowed-Origins {    
    // ${distro_id} and ${distro_codename} will be automatically expanded
    "${distro_id} stable";
    "${distro_id} ${distro_codename}-security";
    "${distro_id} ${distro_codename}-updates";
//  "${distro_id} ${distro_codename}-proposed-updates";
};

// List of packages to not update
Unattended-Upgrade::Package-Blacklist {
//  "libc6";
//  "libc6-dev";
//  "libc6-i686";
};

// Send email to this address for problems or packages upgrades
// If empty or unset then no email is sent, make sure that you 
// have a working mail setup on your system. The package 'mailx'
// must be installed or anything that provides /usr/bin/mail.
//Unattended-Upgrade::Mail "root@localhost";

// Do automatic removal of new unused dependencies after the upgrade
// (equivalent to apt-get autoremove)
//Unattended-Upgrade::Remove-Unused-Dependencies "false";

// Automatically reboot *WITHOUT CONFIRMATION* if a 
// the file /var/run/reboot-required is found after the upgrade 
Unattended-Upgrade::Automatic-Reboot "true";' | sudo tee /etc/apt/apt.conf.d/50unattended-upgrades

#install elasticsearch repository
wget -qO - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -
echo 'deb http://packages.elasticsearch.org/elasticsearch/1.4/debian stable main
' | sudo tee -a /etc/apt/sources.list

#get python and mercurial installed
sudo apt-get update
sudo apt-get -y -q install nodejs-legacy mercurial build-essential python python-dev python-distribute python-pip nginx supervisor postgresql-common libpq-dev postgresql-client npm elasticsearch openjdk-7-jre rabbitmq-server supervisor

#have elasticsearch only look locally
echo 'network.bind_host: 127.0.0.1
script.disable_dynamic: true
bootstrap.mlockall: true
path.data: /elastic
path.logs: /var/log/elasticsearch
cluster.name: tribesearch
' | sudo tee -a /etc/elasticsearch/elasticsearch.yml

#add the elastic search partition to the fstab
echo '/dev/xvdf	/elastic	 ext4	defaults,nofail,nobootwait	0 2
' | sudo tee -a /etc/fstab


#elastic search likes this http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/setup-configuration.html#vm-max-map-count
sudo sysctl -w vm.max_map_count=262144
#set heap size for elastic http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/setup-configuration.html#_environment_variables
echo 'ES_HEAP_SIZE=512m' | sudo tee -a /etc/environment
#make elasticsearch start on boot
sudo update-rc.d elasticsearch defaults 95 10
sudo pip install pyelasticsearch

#make the rabbitmq user
sudo rabbitmqctl add_user tribe 4HU7c36GygdVqCIOLCBH
#make the vhost for tribe
sudo rabbitmqctl add_vhost tribe
#give the tribe user access to the tribe vhost
sudo rabbitmqctl set_permissions -p tribe tribe ".*" ".*" ".*"

#run celery through supervisor
echo '[program:tribe-celery]
command=celery -A tribe worker -c 3 --loglevel=INFO
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


#install uwsgi, get config files
sudo pip install uwsgi
sudo adduser tribe www-data --disabled-login --system
hg clone https://cgreene@bitbucket.org/greenelab/tribe-ec2-deploy
cd /home/tribe

#need to add ssh deploy key for tribe before this
sudo -u tribe hg clone ssh+hg://hg@bitbucket.org/greenelab/tribe

#need to add ssh deploy key for cgreene/go before this
sudo pip install -r  /home/tribe/tribe/requirements.txt

#start to get the npm stuff in place
sudo npm -g install grunt-cli karma bower
cd /home/tribe/tribe/interface
sudo -u tribe npm install
sudo -u tribe bower install
sudo -u tribe grunt --compile

#point to interface/bin
cd /home/tribe/tribe/
sudo -u tribe ln -s ../interface/bin static


cd ~
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s ~/tribe-ec2-deploy/configs/tribe_nginx.conf /etc/nginx/sites-enabled/

#setup uwsgi
sudo mkdir /var/log/uwsgi
sudo chown -R www-data:www-data /var/log/uwsgi/
sudo mkdir /etc/uwsgi
sudo mkdir /etc/uwsgi/vassals
sudo ln -s /home/ubuntu/tribe-ec2-deploy/configs/tribe_uwsgi.ini /etc/uwsgi/vassals/
sudo ln -s /home/ubuntu/tribe-ec2-deploy/configs/uwsgi.conf /etc/init/

#restart required services
sudo service uwsgi restart
sudo /etc/init.d/nginx restart
sudo /etc/init.d/elasticsearch restart

#rebuild search index if needed
sudo -u tribe /home/tribe/manage.py rebuild_index 
