"""
Fab tasks to provision a Tribe server.

Use these only once to setup an ubuntu server. For day to day usage and
development you should use the tribe fabfile.
"""

from fabric.api import put, run, sudo, execute


def enable_unattended_updates():
    """
    Tell ubuntu to install upgrades automatically.

    This enables automatic and unattended upgrades. This also allows automatic
    reboots if required.
    """
    put('files/upgrade/20auto-upgrades', '/etc/apt/apt.conf.d/20auto-upgrades', use_sudo=True)
    put('files/upgrade/50unattended-upgrades', '/etc/apt/apt.conf.d/50unattended-upgrades', use_sudo=True)

def _add_elasticsearch_repo():
    run('wget -qO - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -')
    run("""echo 'deb http://packages.elasticsearch.org/elasticsearch/1.4/debian stable main
' | sudo tee -a /etc/apt/sources.list""")

def install_system_packages():
    execute(_add_elasticsearch_repo)
    sudo('apt-get update')
    sudo('apt-get -y -q install nodejs-legacy mercurial build-essential python python-dev python-distribute python-pip nginx postgresql-common libpq-dev postgresql-client npm elasticsearch openjdk-7-jre python-virtualenv supervisor')


def setup_elasticsearch():
    sudo('mkdir /var/elastic')
    sudo('chown -R elasticsearch:elasticsearch /var/elastic')
    sudo('sysctl -w vm.max_map_count=262144')
    run("echo 'ES_HEAP_SIZE=512m' | sudo tee -a /etc/environment")
    sudo('update-rc.d elasticsearch defaults 95 10')
    #elasticsearch should only look at this host. Create config files.
    run("""echo 'network.bind_host: 127.0.0.1
script.disable_dynamic: true
bootstrap.mlockall: true
path.data: /var/elastic
path.logs: /var/log/elasticsearch
cluster.name: tribesearch
' | sudo tee -a /etc/elasticsearch/elasticsearch.yml""")

# Make an authorized keys file before running this. Put together the public keys from people that you'd like to be able to access the tribe user.
def create_tribe_user():
    sudo('adduser tribe --disabled-password')
    sudo('mkdir /home/tribe/.ssh', user="tribe")
    put('authorized_keys', '/home/tribe/.ssh/', use_sudo=True, mode=0600)
    sudo('chown tribe:tribe /home/tribe/.ssh/authorized_keys')

# Make deployment keys before running this.
def upload_deploy_keys():
    put('bb-deploy-tribe_rsa', '/home/tribe/.ssh/id_rsa', use_sudo=True, mode=0600)
    put('bb-deploy-tribe_rsa.pub', '/home/tribe/.ssh/id_rsa.pub', use_sudo=True, mode=0644)
    sudo('chown tribe:tribe /home/tribe/.ssh/id_rsa*')

def clone_imp_repo():
    sudo('hg clone ssh://hg@bitbucket.org/greenelab/tribe /home/tribe/tribe', user="tribe")

def setup_nginx():
    sudo('rm -f /etc/nginx/sites-enabled/default')
    put('files/nginx/tribe-nginx.conf', '/etc/nginx/sites-enabled/', use_sudo=True)
    sudo('/etc/init.d/nginx restart')

def setup_virtualenv():
    sudo('mkdir -p /home/tribe/.virtualenvs', user='tribe')
    sudo('virtualenv /home/tribe/.virtualenvs/tribe', user='tribe')

def setup_supervisor():
    put('files/supervisord/tribe_super.conf', '/etc/supervisor/conf.d/tribe_super.conf', use_sudo=True)
    sudo('sudo /etc/init.d/supervisor restart')

def setup_sudo_restart_super():
    sudo('groupadd -f supervisor')
    sudo('usermod -a -G supervisor tribe')
    put('files/supervisord/super_sudo', '/etc/sudoers.d/super_sudo', use_sudo=True, mode=0440)
    put('files/supervisord/supervisord.conf', '/etc/supervisor/supervisord.conf', use_sudo=True, mode=0644)
    sudo('chown root:root /etc/sudoers.d/super_sudo')
    sudo('sudo /etc/init.d/supervisor restart')

def setup_yuglify():
    sudo('npm -g install yuglify')
