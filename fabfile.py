import os
import time
# noinspection PyUnresolvedReferences,PyPackageRequirements
from fabric.api import local
# from fabric.context_managers import cd
# pip install -U python-dotenv
# noinspection PyUnresolvedReferences,PyPackageRequirements
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
api_container = 'sdr_service'
db_container = os.environ.get('DB_HOST')
db_name = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
admin_user = 'admin'
admin_email = os.environ.get('ADMINS').split(',')[0].strip()
admin_pass = os.environ.get('SU_PASS')


def _dcmd(cmd):
    """Prefix the container command with the docker cmd"""
    return "docker exec -it %s %s" % (api_container, cmd)


def build():
    """Run to build a new image prior to fab up"""
    local("docker-compose build")
    # local("docker-compose build --no-cache")
    # local("docker-compose build --no-cache --pull")


def up():
    """Create and start the docker services"""
    local("docker-compose up -d")


def down():
    """Stop and remove the docker services"""
    local("docker-compose down")


def runserver():
    """Enter Django's runserver on 0.0.0.0:8080"""
    local(_dcmd("python3 manage.py runserver 0.0.0.0:8080"))


def collectstatic():
    """Run Django's collectstatic"""
    local(_dcmd("python3 manage.py collectstatic -c --noinput"))


def clearstatic():
    # with cd('src/media/'):
        # local("ls | grep -v .gitignore | xargs rm")
    local("find src/media/ ! -name '.gitignore' | xargs ls")


def makemigrations():
    """Run Django's makemigrations"""
    local(_dcmd("python3 manage.py makemigrations"))


def migrate():
    """Run Django's migrate"""
    local(_dcmd("python3 manage.py migrate"))


def shell_plus():
    """Run Django extensions's shell_plus"""
    local(_dcmd("python3 manage.py shell_plus"))


def shell():
    """ssh into the running container"""
    local("docker exec -it %s /bin/bash" % api_container)


def db_init():
    query = "CREATE DATABASE %s WITH OWNER = %s ENCODING = 'UTF8' LC_COLLATE = 'en_US.utf8' LC_CTYPE = " \
            "'en_US.utf8' CONNECTION LIMIT = -1;" % (db_name, db_user)
    command = "psql -h %s -U %s -c \"%s\"" % (db_container, db_user, query)
    local(_dcmd(command))


def createsuperuser():
    createsu = "from django.contrib.auth.models import User; User.objects.create_superuser('%s', '%s', '%s')" \
               % (admin_user, admin_email, admin_pass)
    local(_dcmd("python3 manage.py shell -c \"%s\"" % createsu))


def dbrestore(key_name):
    """Restore the database from a named s3 key
        ie - fab db_restore:dev
    """
    local(_dcmd("python3 manage.py dbrestore {}".format(key_name)))


def dbbackup(key_name):
    """Backup the database from a named s3 key
        ie - fab db_backup:dev
    """
    local(_dcmd("python3 manage.py dbbackup {}".format(key_name)))


def fresh_install(key_name=None):
    key_name = key_name or 'local'

    down()
    build()
    up()
    time.sleep(20)

    collectstatic()

    # db_init()
    dbrestore(key_name)
    migrate()
    # createsuperuser()
