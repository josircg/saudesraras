Tutorial de Instalação de um servidor do CIVIS para ambiente de produção:

1) Instalação do NGINX e Supervisor (logado como root) e configuração do timezone:

````
apt-get install -y nginx build-essential libssl-dev python3-dev python-setuptools libxml2-dev supervisor git libfreetype6 libfreetype6-dev python3-virtualenv libpq-dev
dpkg-reconfigure tzdata
````

2) Criação do usuário webapp e permissões de uso (logado como root)

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

3) Criação da chave pública para enviar para o gitlab

````
su - webapp
ssh-keygen -N ''
cd .ssh
cat id_rsa.pub
````

4) Ainda logado como webapp, instalar o ambiente:

> cd /var/webapp
> virtualenv civis

Outra opção é utilizar: mkvirtualenv civis -p python3

5)Ativar virtualenv
```
cd civis
source bin/activate
mkdir logs
```

6) Clonar o repositório (Não é necessário nenhuma senha pois a chave já foi incluida gitlab)
> git clone  git@git.ibict.br:cgti/civis.git

7) Entrar no repositório e instalar as bibliotecas do python

```
cd civis
pip install -r requirements/production.txt
```

8) Altere o arquivo manage.py para apontar para o eucs_platform/settings/production.py

9) Novamente logado como root/sudo, configurar o NGINX

* copiar o arquivo nginx.conf alterando os parâmetros necessários

```
cp docs/nginx.conf /etc/nginx/sites-enabled/civis.conf
```

* para testar se a configuração foi bem sucedida, executar: nginx -t 
* para aplicar os ajustes: sudo systemctl restart nginx

10) Configurar o supervisor

* Copiar o arquivo supervisor.conf para /etc/supervisor/conf.d/ e alterar os parâmetros necessários

```
cp docs/supervisor.conf /etc/supervisor/conf.d/civis.conf
supervisor reload  
```

11) PostgreSQL (Logado como superuser)
 
O Banco de Dados utiliza PostGIS [*], assim algumas instruções extras devem ser executadas: 

```
sudo apt install postgis postgresql-12-postgis-3 postgresql-12-postgis-3-scripts
```
[*] https://www.vultr.com/docs/install-the-postgis-extension-for-postgresql-on-ubuntu-linux/

```
su - postgres psql ou sudo -u postgres psql
create user eucitizenscience_usr with encrypted password 'mypass';
create database civis with owner=eucitizenscience_usr;
\connect civis;
create extension postgis;
GRANT ALL on public.spatial_ref_sys TO eucitizenscience_usr;
```

Teste de Conexão no postgres (já logado como webapp):

```
psql -h localhost -U eucitizenscience_usr civis
```

