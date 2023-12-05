# Installation for developers

## Package Requirements (Debian 10 or Ubuntu 20.04 or superior)

    sudo apt install python3-venv python3-pip libpq-dev gettext python-is-python3 libjpeg-dev zlib1g-dev gdal-bin

## Configure postgres

1) To use postgresql

In the app server:

   ```
   sudo apt install postgresql postgis postgresql-12-postgis-3
   ```

For postgresql 14 or superior:

   ```
   sudo apt install postgresql postgis
   ```

On a external postgres Server:

   ```
   sudo apt install postgresql-client-14
   ```


2) Open psql console:
```
create database eucitizenscience;
create user eucitizenscience_usr with password 'XXX';
grant all on database eucitizenscience to eucitizenscience_usr;
\connect eucitizenscience;
create extension postgis;
```
## Python Installation

1) In source directory:

```
python3 -m venv venv
source venv/bin/activate
git clone git@git.ibict.br:cgti/civis.git
cd civis
pip install -r requirements.txt
cd src
cp eucs_platform/settings/local.sample.reference.env eucs_platform/settings/local.env
```

2) Edit local.env with database and email configuration and test your configuration

```
python manage.py check
python manage.py collectstatic
```

3) Install flake8 pre-commit hook (optional) to check PEP8 before commit. 
Run `pre-commit install` to set up the git hook scripts (see .pre-commit-config.yaml):

```
pre-commit install
```

To commit without flake8 verification just run `commit` with `--no-verify` flag:

```
git commit -m "feat: pre-commit hooks" --no-verify
```

4) To install a empty database, run: 

```
python manage.py migrate
python manage.py loaddata projects/fixtures/topics.json
python manage.py loaddata projects/fixtures/status.json
python manage.py loaddata projects/fixtures/participationtasks.json
python manage.py loaddata resources/fixtures/categories.json
python manage.py loaddata resources/fixtures/themes.json
python manage.py loaddata organisations/fixtures/organisation_types.json
```

5) To restore a existing database:

```
psql < base.sql
python manage.py migrate
```

## Launch
```
python manage.py runserver
```

## Cron jobs commands [4]
```
python manage.py runcrons
python manage.py runcrons --force
```

And to do this automatically:
```
python manage.py crontab add
```

[1]: https://eu-citizen.science/
[2]: https://www.python.org/
[3]: https://www.djangoproject.com/
[4]: https://pypi.org/project/django-crontab/ 
[5]: https://flake8.pycqa.org/en/latest/user/using-hooks.html
[6]: https://pre-commit.com/#pre-commit-configyaml---hooks
