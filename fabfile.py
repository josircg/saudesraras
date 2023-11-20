import os
import fabric.main

from fabric import task, Connection
from io import BytesIO
from datetime import datetime

from invoke import UnexpectedExit


def deploy(connection, path):
    with connection.cd(path):
        connection.run('git pull')
        connection.run('../../bin/python3 manage.py migrate')
        connection.run('../../bin/python3 manage.py compilemessages')
        connection.run('../../bin/python3 manage.py collectstatic --noinput')
        connection.run('supervisorctl restart civis')
        print('Atualização efetuada com sucesso!')
        print('Executando flake8...')
        connection.run('../../bin/python3 -m flake8')
        print('Fim do processo...')


@task
def deploy_hml_old(context):
    deploy(Connection('webapp@172.16.17.126', port=25000), '/var/webapp/civis/civis/src/')


@task
def deploy_hml(context):
    deploy(Connection('webapp@172.16.17.126', port=25000), '/var/webapp/civis-django-3.2/civis/src')


@task
def deploy_producao(context):
    connection = Connection('webapp@172.16.16.126', port=25000)
    with connection.cd('/var/webapp/civis/civis/src/'):
        connection.run('git pull')
        connection.run('./deploy.sh')
        connection.run('supervisorctl restart civis')
        print('Atualização efetuada com sucesso!')


@task
def upgrade_requirements_hml(context):
    connection = Connection('webapp@172.16.17.126', port=25000)
    with connection.cd('/var/webapp/civis/civis/src'):
        connection.run('git pull')
        connection.run('../../bin/pip install django_select2 --upgrade')
        connection.run('../../bin/pip install -r ../requirements.txt')
        print('Atualização efetuada')


@task
def connect_hml(context):
    connection = Connection('webapp@172.16.17.126', port=25000)
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
        connection.run(f'zip -r {filename} civis/src/media')
        connection.get(filename)


@task
def backup_local(context):
    get_database(Connection('supervisor@192.168.0.24'), 'civis_hml', '')


@task
def teste(context):
    # with Connection('webapp@172.16.17.126', port=25000, connect_timeout=10) as conn:
    #    result = file_exists(conn, '/home/webapp/.bashrc')
    #    print(result)

    with Connection('supervisor@192.168.0.6', connect_timeout=5) as conn:
        home_dir = conn.run('echo $HOME', hide=True).stdout.strip()
        print(home_dir)
        if file_exists(conn, 'lacie2.key'):
            print('ok')
        else:
            print('nok')


@task
def backup_hml(context):
    connection = Connection('webapp@172.16.17.126', port=25000)
    get_database(connection, banco='localhost/civis', path='/var/webapp/backup')
    get_mediafiles(connection, '/var/webapp/civis')


@task
def backup_producao(context):
    # get_database(Connection('webapp@172.16.16.126', port=25000),
    #       banco='eucitizenscience_usr@localhost:5432/eucitizenscience_db',
    #       path='/var/webapp/backup')
    get_mediafiles(Connection('webapp@172.16.16.126', port=25000), '/var/webapp/civis')


if __name__ == '__main__':
    fabric.main.program.run()
