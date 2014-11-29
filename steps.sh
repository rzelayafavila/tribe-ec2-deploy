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
//  "vim";
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
//Unattended-Upgrade::Automatic-Reboot "false";' | sudo tee /etc/apt/apt.conf.d/50unattended-upgrades


#get python and mercurial installed
sudo apt-get update
sudo apt-get -y -q install mercurial build-essential python python-dev python-distribute python-pip nginx supervisor

sudo pip install uwsgi
sudo adduser tribe www-data --disabled-login --system
hg clone https://cgreene@bitbucket.org/greenelab/tribe-ec2-deploy
cd /home/tribe
sudo -u tribe hg clone https://bitbucket.org/greenelab/tribe
sudo pip install -r  /home/tribe/tribe/requirements.txt
cd ~
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s ~/tribe-ec2-deploy/configs/tribe_nginx.conf /etc/nginx/sites-enabled/
sudo mkdir /var/log/uwsgi
sudo chown tribe:www-data /var/log/uwsgi/
sudo /etc/init.d/nginx restart
