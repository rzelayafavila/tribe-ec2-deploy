"""
Fab tasks to provision a Tribe server.

Use these only once to setup an ubuntu server. For day to day usage and
development you should use the tribe fabfile.
"""

from fabric.api import put, get, run, sudo, execute


def enable_unattended_updates():
    """
    Tell ubuntu to install upgrades automatically.

    This enables automatic and unattended upgrades. This also allows automatic
    reboots if required.
    """
    put('files/upgrade/20auto-upgrades', '/etc/apt/apt.conf.d/20auto-upgrades', use_sudo=True)
    put('files/upgrade/50unattended-upgrades', '/etc/apt/apt.conf.d/50unattended-upgrades', use_sudo=True)


def _install_elasticsearch():
    """
    Install ElasticSearch packages + JRE.

    Add the elastic search repo and key, and the install the ElasticSearch
    package and dependencies.
    """
    run('wget -qO - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -')
    run("""echo 'deb http://packages.elasticsearch.org/elasticsearch/1.4/debian stable main
' | sudo tee -a /etc/apt/sources.list""")
    sudo('apt-get update')
    sudo('apt-get -y -q install elasticsearch openjdk-7-jre')


def _install_python_deps():
    """
    Install python and the packages required for development.

    Install mercurial, pip, distribute, and packages needed to build python
    libraries by pip.
    """
    sudo('apt-get -y -q install python python-dev mercurial python-distribute python-pip python-virtualenv')


def _install_postgres():
    """
    Install postgres client packages.

    Install the packages needed to build postgres client utilities via pip.
    """
    sudo('apt-get -y -q install postgresql-common libpq-dev postgresql-client ')


def install_system_packages():
    """
    Install all packages required for Tribe.

    Install all python, postgres, elasticsearch, and other packages required to deploy and manage
    a Tribe instance.
    """
    sudo('apt-get update')
    execute(_install_elasticsearch)
    execute(_install_python_deps)
    execute(_install_postgres)
    sudo('apt-get -y -q install nodejs-legacy build-essential nginx npm supervisor')


def setup_elasticsearch():
    """
    Configure ElasticSearch.

    Make a location for the search index, and configure the server to allow connections from
    localhost.
    """
    sudo('mkdir /var/elastic')
    sudo('chown -R elasticsearch:elasticsearch /var/elastic')
    sudo('sysctl -w vm.max_map_count=262144')
    run("echo 'ES_HEAP_SIZE=512m' | sudo tee -a /etc/environment")
    sudo('update-rc.d elasticsearch defaults 95 10')

    # elasticsearch should only look at this host. Create config files.
    run("""echo 'network.bind_host: 127.0.0.1
script.disable_dynamic: true
bootstrap.mlockall: true
path.data: /var/elastic
path.logs: /var/log/elasticsearch
cluster.name: tribesearch
' | sudo tee -a /etc/elasticsearch/elasticsearch.yml""")


def create_tribe_user():
    """
    Create a tribe user.

    Before running this command, make sure that you have created a file named authorized_keys in
    this directory that contains the public keys for people that will need to be able to access this
    instance of Tribe as a user "tribe".
    """
    sudo('adduser tribe --disabled-password')
    sudo('mkdir /home/tribe/.ssh', user="tribe")
    put('authorized_keys', '/home/tribe/.ssh/', use_sudo=True)
    sudo('chown tribe:tribe /home/tribe/.ssh/authorized_keys')


def create_deploy_keys():
    """
    Create deployment keys.

    This command will create deployment keys on the remote server and download the
    public key as deploy_rsa.pub. Add this deployment key to bitbucket to be able
    to clone the mercurial repository.
    """
    sudo("ssh-keygen -t rsa", user="tribe")
    get('/home/tribe/.ssh/id_rsa.pub', 'deploy_rsa.pub')


def clone_tribe_repo():
    """
    Clone the Tribe repository.

    This command clones the tribe repository from bitbucket into /home/tribe/tribe. This will be
    the location where the python code for the server is stored.
    """
    sudo('hg clone ssh://hg@bitbucket.org/greenelab/tribe /home/tribe/tribe', user="tribe")


def setup_nginx():
    """
    Setup nginx.

    This command will remove the default nginx site, and put a configuration file for tribe into
    the sites-enabled folder.
    """
    sudo('rm -f /etc/nginx/sites-enabled/default')
    put('files/nginx/tribe-nginx.conf', '/etc/nginx/sites-enabled/', use_sudo=True)
    sudo('/etc/init.d/nginx restart')


def setup_virtualenv():
    """
    Setup Python Virtual Envrionment.

    This command will create a virtual environment for Tribe in /home/tribe/.virtualenvs. This is
    the virtualenv that will contain the python packages that are pip installed from Tribe's
    requirements.txt
    """
    sudo('mkdir -p /home/tribe/.virtualenvs', user='tribe')
    sudo('virtualenv /home/tribe/.virtualenvs/tribe', user='tribe')


def setup_supervisor():
    """
    Setup supervisor.

    Supervisor allows us to control gunicorn instances of Tribe. gunicorn can be installed in the
    virtualenv, and the "tribe" user can restart the server without requiring unrestricted sudo.
    """
    put('files/supervisord/tribe_super.conf', '/etc/supervisor/conf.d/tribe_super.conf', use_sudo=True)
    sudo('sudo /etc/init.d/supervisor restart')


def setup_sudo_restart_super():
    """
    Allow the tribe user to restart Supervisor.

    Create a supervisor group, add tribe to it, upload a sudo configuration that allows
    the tribe user to perform the restart procedure for the tribe server.
    """
    put('files/supervisord/super_sudo', '/etc/sudoers.d/super_sudo', use_sudo=True, mode=0440)
    sudo('chown root:root /etc/sudoers.d/super_sudo')
    sudo('sudo /etc/init.d/supervisor restart')


def setup_yuglify():
    """
    Install yuglify.

    Install a minification package. Here yuglfiy, that can be used to combine and shrink javascript
    source.
    """
    sudo('npm -g install yuglify')
