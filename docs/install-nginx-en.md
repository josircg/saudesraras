Tutorial for install CIVIS on a production server:

1) Install NGINX and Supervisor (logged as root):

````
apt-get install -y nginx build-essential libssl-dev python3-dev python-setuptools libxml2-dev supervisor git libfreetype6 libfreetype6-dev python3-virtualenv libpq-dev
dpkg-reconfigure tzdata gdal-bin gettext
````

2) Create webapp user and permissions (logged as root)

````
adduser  --gecos "" webapp
usermod -a -G www-data webapp
cd /var
mkdir webapp
chown root:www-data webapp
chmod g+ws webapp
cd /etc/nginx/
sudo chown root:www-data sites-enabled
sudo chown root:www-data sites-available
sudo chmod 775 sites-*
sudo chown root:www-data /var/log/nginx
sudo chmod 775 /var/log/nginx
sudo chown webapp:www-data /etc/supervisor/conf.d
sudo chmod 775 /etc/supervisor/conf.d
````

3) Log in as webapp and create a public key. Add it to gitlab/github deploy keys:

````
su - webapp
ssh-keygen -N ''
cd .ssh
cat id_rsa.pub
````

4) Logged as webapp, install the python environment:

````
cd /var/webapp
virtualenv raras
````

Another option is: mkvirtualenv civis -p python3

5) Activate Python environment
```
cd raras
source bin/activate
mkdir logs
```

6) Clone CIVIS repository (If git asks for a password, then step (3) didn't work well)
> git clone git@github.com:josircg/saudesraras.git 

7) Access project folder and install libraries

```
cd raras
pip install -r requirements/production.txt
```

8) Change manage.py to point to eucs_platform/settings/production.py

9) Start NGINX configuration

* copy template nginx.conf and change the site parameters (domain, port, path, etc)

```
cp docs/nginx.conf /etc/nginx/sites-enabled/raras.conf
```

* to test if your new config is ok, run '''nginx -t''' 
* to apply the new config: '''sudo systemctl restart nginx'''
 
10) PostgreSQL (Logged as root)
 
O Banco de Dados utiliza PostGIS [*], assim algumas instruções extras devem ser executadas: 

```
sudo apt install postgis postgresql-12-postgis-3 postgresql-12-postgis-3-scripts
```
[*] https://www.vultr.com/docs/install-the-postgis-extension-for-postgresql-on-ubuntu-linux/

```
su - postgres psql ou sudo -u postgres psql
create user raras_usr with encrypted password 'mypass';
create database saudesraras with owner=raras_usr;
\connect saudesraras;
create extension postgis;
GRANT ALL on public.spatial_ref_sys TO raras_usr;
```

Log in as webapp and test postgres connection:

```
psql -h localhost -U raras_usr saudesraras
```

11) Change local.env to apply your new PostgreSQL database and test the connection:

```
cd /var/webapp/raras/saudesraras
source ../bin/activate
cd src
python manage.py dbshell
```

12) Test also the django configuration:

```
python manage.py check
```

13) Import your database or create an empty instance and the apply the model update:

```
python manage.py migrate
python manage.py collectstatic
```

14) Configure supervisor

```
cp /var/webapp/civis/civis/docs/supervisor.conf /etc/supervisor/conf.d/civis.conf 
* Change your path/port
supervisor reload
```

15) Finally, test your site on browser and be happy!


