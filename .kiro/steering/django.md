# Contexto do Projeto — Saudes Raras

Sistema de Informações sobre Doenças Raras que lista organizações, projetos, eventos e notícias sobre o tema. É um software livre e tem repositório público.

## Stack confirmada

- **Python**: 3.10.19 (virtualenv via uv)
- **Django**: 3.2.25 — o pin fica em `requirements/base.txt` (`django<4.0`).
  NÃO subir para 4.x sem uma migração planejada (ver spec de migração Django 4.x).
- **Banco**: PostgreSQL (via `psycopg2`), com extensões GIS (`django.contrib.gis`,
  `django-leaflet`).
- **Interpretador do venv**: uv
- **Localização/Tradução**: translate.sh

## Módulos de settings

Os settings ficam em `src/eucs_platform/settings/`:

- `base.py` — configuração comum a todos os ambientes; lê o `local.env`.
- `development.py` — herda de `base`, adiciona debug toolbar, logging, etc.
- `production.py` — herda de `base`, template cacheado, logging de produção.
- `local.env` — variáveis de ambiente (SECRET_KEY, banco, SMTP, chaves de API).
  **NÃO é versionado** (git-ignored). Há um `local.sample.reference.env` de
  referência.

**IMPORTANTE — settings padrão:** o `manage.py` usa
`eucs_platform.settings.production` como default. Ou seja, rodar
`python manage.py runserver` sem exportar `DJANGO_SETTINGS_MODULE` carrega
**production**, não development. Ao reproduzir o comportamento do servidor em
scripts de verificação, use:

```
DJANGO_SETTINGS_MODULE=eucs_platform.settings.production uv run manage.py <cmd>
```

## Como rodar comandos

Todo o código fica em `src/`. Comandos de manage.py rodam a partir de `src/`.

```
cd src
uv run manage.py check
```

(ou `workon saudesraras && cd src && python manage.py check` se o virtualenvwrapper
estiver configurado na máquina.)

### Comandos de verificação (sempre nesta ordem após mudanças)

1. `python manage.py check` — valida configuração e apps.
2. `python manage.py makemigrations --check --dry-run` — garante que o modelo em
   código bate com as migrations. Se acusar mudanças, há drift (ver abaixo).
3. Testes do app afetado (quando existirem).

### Testes

A suíte de testes ainda é mínima. Ao criar testes, use o runner padrão do Django
(`python manage.py test <app>`).
## Apps locais

São **15 apps**, todos em `src/`: `accounts`, `authors`, `blog`, `contact`,
`digest`, `diseases`, `events`, `organisations`, `pages`, `platforms`,
`profiles`, `projects`, `resources`, `utilities`. Além desses, `eucs_platform`
é o projeto (settings, urls, views raiz, dashboard do admin).

Para o mapa detalhado de cada app (responsabilidade, models, rotas,
dependências), ver `#structure` (em `.kiro/steering/structure.md`). desses, `eucs_platform` é o projeto (settings, urls, views
raiz, `maps.py`).

## Bibliotecas e integrações relevantes

- **Autenticação**: modelo de usuário customizado via `django-authtools`
  (`AUTH_USER_MODEL = "authtools.User"`). Forms em `accounts/forms.py` usam
  `authtools.forms`. Admin do usuário via `authtools.admin.NamedUserAdmin`.
- **Admin**: `django-admin-tools` (com dashboard customizado em
  `eucs_platform/dashboard.py`). `poweradmin` também está em `INSTALLED_APPS`.
- **API/REST**: `djangorestframework`, `rest_framework_swagger`
  (django-rest-swagger, pacote morto), `drf-yasg`. OAuth/OIDC via
  `django-oauth-toolkit` e `django-oidc-provider`.
- **Mapas**: hoje o sistema usa **apenas django-leaflet** (client-side):
  `LEAFLET_CONFIG` em `base.py`, usado nas páginas de organização/projeto via
  `{% leaflet_map %}`. O mapa server-side com **folium** descrito na seção
  "Mapas e a chave CARTO" é uma **feature planejada**, ainda **não
  implementada** neste repositório (ver aviso naquela seção).
- **Editores de texto**: `django-ckeditor` e `django-summernote`.
- **Outros**: `django-countries` (campo `CountryField`), `django-crispy-forms`
  + `crispy-bootstrap3`, `django-simple-captcha`.

## Mapas e a chave CARTO (feature PLANEJADA — ainda não implementada)

> **Atenção:** esta seção descreve uma feature **planejada para o futuro**, não
> o estado atual do código. Hoje **não existe** `eucs_platform/maps.py`,
> `generate_map`, `map_view` nem rota `/map/` neste repositório, e
> `LEAFLET_CONFIG['TILES']` usa CartoDB Light **sem** `?key=` (não lê
> `CARTODB_API`). O conteúdo abaixo é a referência de design para quando o mapa
> server-side com folium for implementado.

Os basemaps da CARTO (CartoDB) passaram a **exigir uma API key** desde ~2026,
passada como `?key=<KEY>` na URL do tile. Sem a chave, os tiles vêm com a marca
d'água "API KEY REQUIRED".

- A chave deverá ficar em `CARTODB_API` (lida do `local.env` em `base.py`).
- **folium** (`maps.py`, a criar): `generate_map` usaria, por padrão, a URL
  CARTO
  `https://basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}.png?key=<KEY>`
  com `attr` obrigatório. Passar `tiles` explícito manteria compatibilidade.
- **leaflet** (`LEAFLET_CONFIG['TILES']`): deverá passar a usar a tupla CARTO
  Positron com a mesma chave.
- **folium ≥ 0.18 rejeita coordenadas `None`** com `ValueError` — um único
  marcador inválido derrubaria o mapa inteiro (HTTP 500). `generate_map` deverá
  filtrar via `has_valid_location`. As coordenadas vêm como `Decimal`
  (DecimalField), então a validação deve usar conversão `float()`, não
  `isinstance(int, float)`.

## Dívida técnica conhecida

- **Pin `setuptools<81`** (`requirements/base.txt`): necessário porque
  `drf-yasg 1.21.7` e `django-countries 7.5.1` ainda importam `pkg_resources`
  (removido do setuptools 81+) de forma incondicional no startup. As versões que
  largam `pkg_resources` (`drf-yasg 1.21.11+`) exigem **Django ≥ 4.0**. Portanto
  remover o pin está acoplado à migração Django 4.x. (`django-authtools` já foi
  para 2.0.2 e não depende mais de `pkg_resources`.)
- **`django-rest-swagger` (2.2.0)**: pacote morto, provavelmente incompatível
  com Django 4. Candidato a remoção/substituição por `drf-yasg` na migração.

## Armadilhas de ambiente

- Todo o projeto está em `src/`. Comandos de manage.py rodam a partir dali.
- O `runserver` default carrega **production** settings (ver acima).
- O `local.env` não é lido a quente: alterações nele exigem **reiniciar** o
  `runserver` (o autoreload do Django reage a `.py`, não a `.env`).
- **Drift de migrations**: edições em models sem rodar `makemigrations` deixam o
  schema em código divergente das migrations. Sempre rode
  `makemigrations --check --dry-run`. Migrations que só mudam metadados
  (verbose_name, defaults) geram SQL vazio em `sqlmigrate` — seguras de aplicar.

## Remote git


## Fluxo de trabalho com specs

Para features não-triviais, use o template de spec deste projeto:
`#django-spec-template` (em `.kiro/steering/django-spec-template.md`).

Nunca aplique `migrate` em banco de produção sem o usuário confirmar.
