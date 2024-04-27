import os
import fabric.main

from fabric import task, Connection
from io import BytesIO
from datetime import datetime

from invoke import UnexpectedExit

HML_SERVER = 'webapp@3.89.127.179'

def deploy(connection, path):
    with connection.cd(path):
        connection.run('git pull')
        connection.run('../../bin/python3 manage.py migrate')
        connection.run('../../bin/python3 manage.py compilemessages')
        connection.run('../../bin/python3 manage.py collectstatic --noinput')
        connection.run('supervisorctl restart raras')
        print('Atualização efetuada com sucesso!')
        print('Fim do processo...')


def deploy(connection, path):
    with connection.cd(path):
        connection.run('git pull')
        connection.run('../../bin/python3 manage.py migrate')
        connection.run('../../bin/python3 manage.py compilemessages')
        connection.run('../../bin/python3 manage.py collectstatic --noinput')
        connection.run('supervisorctl restart raras')
        print('Atualização efetuada com sucesso!')


@task
def deploy_hml(context):
    deploy(Connection(HML_SERVER), '/var/webapp/raras/saudesraras/src')


@task
def upgrade_requirements_hml(context):
    connection = Connection(HML_SERVER)
    with connection.cd('/var/webapp/raras/saudesraras/src'):
        connection.run('git pull')
        connection.run('../../bin/pip install django_select2 --upgrade')
        connection.run('../../bin/pip install -r ../requirements.txt')
        print('Atualização efetuada')


@task
def connect_hml(context):
    connection = Connection(HML_SERVER)
    with connection.cd('/var/webapp/'):
        result = connection.run('ls', hide=True)
    msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
    print(msg.format(result))


def read_var(connection, file_path, encoding='utf-8'):
    io_obj = BytesIO()
    connection.get(file_path, io_obj)
    return io_obj.getvalue().decode(encoding)


def home_dir(conn):
    return conn.run('echo $HOME', hide=True).stdout.strip()


def file_exists(connection, full_path):
    try:
        connection.run(f'ls -ls {full_path}', hide=True)
        return True
    except UnexpectedExit:
        return False


def get_database(connection, banco, path):
    with connection.cd(path):
        print('Conectado')
        # Verifica se o arquivo pgpass existe
        home_dir = connection.run('echo $HOME', hide=True).stdout
        filename = f'{home_dir}/.pgpass'
        if not file_exists(connection, filename):
            print('Senha não encontrada: %s' % filename)
            return
        filename = path + '/backup%s.gz' % datetime.strftime(datetime.now(), '%Y%m%d')
        connection.run('pg_dump postgresql://%s | gzip > %s' %
                       (banco, filename))
        print(f'Backup PostgreSQL gerado em {filename}')
        connection.get(filename)
        print('Backup copiado na pasta local')
        connection.run(f'rm {filename}')


def get_mediafiles(connection, path):
    with connection.cd(path):
        filename = os.path.join(path, 'media%s.zip' % datetime.strftime(datetime.now(), '%Y%m%d'))
        print(filename)
        connection.run(f'zip -r {filename} saudesraras/src/media')
        connection.get(filename)


@task
def backup_local(context):
    get_database(Connection('supervisor@192.168.0.24'), 'civis_hml', '')


@task
def backup_hml(context):
    connection = Connection('webapp@3.89.127.179')
    get_database(connection, banco='localhost/raras', path='/var/webapp/raras')


if __name__ == '__main__':
    fabric.main.program.run()
