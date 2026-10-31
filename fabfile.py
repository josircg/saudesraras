import os
import fabric.main

from fabric import task, Connection
from io import BytesIO
from datetime import datetime

from invoke import UnexpectedExit

AWS_SERVER = 'webapp@54.234.183.153'
MG1_SERVER = 'webapp@201.23.84.25'


def deploy(connection, path):
    # O `uv` fica em ~/.local/bin, que NAO entra no PATH de uma shell
    # nao-interativa/nao-login (como a do connection.run). Sem isso, os
    # comandos `uv ...` falham com "command not found". O prefix abaixo
    # garante o PATH para todos os comandos do bloco (usa $HOME, sem hardcode).
    with connection.prefix('export PATH="$HOME/.local/bin:$PATH"'):
        with connection.cd(path):
            connection.run('git pull')
            connection.run('uv sync --group=prod')
            connection.run('uv run manage.py migrate')
            connection.run('uv run manage.py compilemessages')
            connection.run('uv run manage.py collectstatic --noinput')
            connection.run('sudo systemctl restart saudesraras')
            print('Atualização efetuada com sucesso!')


@task
def deploy_producao(context):
    deploy(Connection(MG1_SERVER), '/var/webapp/saudesraras/src')


@task
def connect(context):
    connection = Connection(MG1_SERVER)
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
        home_path = connection.run('echo $HOME', hide=True).stdout.strip()
        filename = f'{home_path}/.pgpass'
        if not file_exists(connection, filename):
            print(f'Arquivo de senha não encontrado: {filename}')
            return
        filename = path + '/backup%s.gz' % datetime.strftime(datetime.now(), '%Y%m%d')
        connection.run(f'pg_dump postgresql://{banco} | gzip > {filename}')
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
def get_file(connection):
    connection = Connection(MG1_SERVER)
    connection.get('/var/webapp/raras/db.sql')
    print('Arquivo copiado na pasta local')


@task
def backup_local(context):
    get_database(Connection('supervisor@192.168.0.24'), 'raras_usr@localhost:5432/raras', '.')


@task
def backup(context):
    connection = Connection(MG1_SERVER)
    get_database(connection, banco='raras@localhost/saudesraras', path='/var/webapp/raras')
    get_mediafiles(connection,path='/var/webapp/raras')


if __name__ == '__main__':
    fabric.main.program.run()
