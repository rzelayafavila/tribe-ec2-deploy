sudo apt-get update
sudo apt-get -y -q install mercurial build-essential python python-dev python-distribute python-pip nginx supervisor
sudo pip install uwsgi
sudo adduser tribe www-data --disabled-login --system
hg clone https://cgreene@bitbucket.org/greenelab/tribe-ec2-deploy
cd /home/tribe
sudo -u tribe hg clone https://bitbucket.org/greenelab/tribe
cd ~

