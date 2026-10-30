# Estrutura da Aplicação — Saúdes Raras

Mapa dos apps e do projeto `eucs_platform`. Reflete o código real em `src/`
(investigado em 2026-10-17). Use como referência de "onde as coisas estão"
antes de ler o código em detalhe.

> Stack, comandos e armadilhas de ambiente ficam em `django.md`. Este arquivo
> cobre **estrutura**: apps, responsabilidades, models, rotas e dependências.

## Projeto `eucs_platform`

O projeto Django fica em `src/eucs_platform/`. Não é um app de domínio — é a
"cola": settings, urls raiz, views da home, dashboard do admin e utilitários.

- `settings/` — `base.py` (comum, lê `local.env`), `development.py`,
  `production.py`. `manage.py` usa **production** como default (apesar do
  comentário no arquivo dizer development).
- `urls.py` — urls raiz (ver seção "Roteamento" abaixo).
- `views.py` — views da home e páginas institucionais (function-based). A
  `home` agrega conteúdo de quase todos os apps.
- `dashboard.py` — dashboards customizados do `django-admin-tools`.
- `cron.py` — cron jobs (`django_cron`): expiração de usuários, limpeza de
  captcha.
- `context_processors.py`, `logger.py`, `oidc_provider_settings.py`,
  `sitemaps.py`, `utils.py`, `visao.py` (integração "Visão"/geoserver usada
  por `projects`), `wsgi.py`.

## Apps locais (15)

Todos em `src/`. Ordem de dependência (folha → raiz):
`utilities`, `authors`, `diseases` → `organisations` → `platforms`/`projects`
→ `resources` → `blog`/`events`/`digest`/`contact`/`pages`/`profiles`.

### Núcleo de domínio

- **diseases** — catálogo de **doenças raras** e **sintomas**; busca por
  sintoma. Models: `Disease` (name, ICD, M2M `symptoms`), `Symptom`. Views FBV.
  Rotas: `diseases/`+`doencas/`, `disease/<pk>/`, `symptoms/`+`sintomas/`.
  Referenciado por `organisations` (M2M `Organisation.diseases`).

- **organisations** — organizações atuantes em doenças raras (cadastro,
  moderação, permissões de edição, mapa leaflet). Models: `Organisation`
  (PointField GIS + lat/long Decimal, M2M `diseases`, FK `orgType`, `creator`,
  `approved`), `OrganisationType` (traduzível), `OrganisationPermission`.
  Views FBV + DRF em `api/`. Depende de `diseases`. Consumido por
  `platforms`, `projects`, `resources`, `profiles`.

- **projects** — projetos de ciência cidadã / iniciativas. **App mais
  complexo**: cadastro, moderação, destaque, tradução de conteúdo, permissões/
  convites de editores, estatísticas, download. Models principais: `Project`
  (MultiPolygonField GIS, M2M `organisation`/`keywords`/`editors`/..., FK
  `mainOrganisation`, `status`), além de `Status`/`Topic`/`ParticipationTask`
  (traduzíveis), `Keyword`, `FundingBody`, `ProjectPermission`,
  `FollowedProjects`. Views FBV + DRF em `api/` (ViewSets via `DefaultRouter`).
  Depende de `organisations`, `utilities`. Management command:
  `populate_visao`. Mapa leaflet em `project.html`/`project_form.html`.

- **platforms** — plataformas de iniciativas, com palavras-chave e extensão
  geográfica, vinculadas a organizações. Models: `Platform` (M2M
  `organisation`/`keywords`, FK `geoExtend`), `Keyword`, `GeographicExtend`
  (traduzível). Views FBV + DRF em `api/`. Depende de `organisations`.

- **resources** — recursos e **recursos de treinamento** (publicações,
  materiais) com categorias/temas/audiência, bookmarks, agrupamentos curados,
  moderação e download. Models: `Resource` (M2M `authors`/`organisation`/
  `project`/`keywords`/`theme`, FK `category`, flag `isTrainingResource`),
  `TrainingResource` (herança), `Theme`/`Audience`/`Category` (traduzíveis),
  `ResourceGroup`, `BookmarkedResources`, `ResourcePermission`. Views FBV +
  DRF em `api/`. Depende de `authors`, `organisations`, `projects`,
  `utilities`.

- **authors** — catálogo simples de autores de recursos. Model único: `Author`.
  **Sem views/urls** (app só de dados). Consumido por `resources`.

### Conteúdo e comunicação

- **blog** — notícias/posts do portal. Model: `Post` (slug, FK `author`→user,
  `sticky`, `status`). View CBV `PostList` + FBV `post_detail`. Rotas `blog/`
  e `blog/<year>/<month>/<day>/<slug>/`. Templatetags em `my_tags.py`.

- **events** — eventos (criação, edição, moderação, destaque, listagem
  ongoing/upcoming). Model: `Event` (FK `creator`, datas, `approved`,
  `featured`). Manager com `ongoing_events()`/`upcoming_events()` (usados na
  home). Views FBV. Tem `signals.py`.

- **digest** — boletins periódicos agregando posts, eventos, organizações,
  projetos, recursos e treinamentos num intervalo de datas. Model: `Digest`.
  Views FBV `showDigests`/`showDigest`.

- **contact** — contato, inscrição de assinantes e envio/gestão de newsletters.
  Models: `Subscriber`, `Newsletter` (FK `blog`→`blog.Post`, FK
  `featured_resource`→`resources.Resource`). Views FBV (+1 CBV
  `NewsletterList`). Management command: `send_newsletter`. Depende de `blog`,
  `resources`.

- **pages** — CMS leve de páginas estáticas por idioma: páginas institucionais,
  **depoimentos** e **FAQ** (consumidos na home via
  `Section.objects.filter(page__slug=...)`). Models: `Page`, `Section`,
  `Article`. Views CBV `DepoimentosListView`, `PageDetailView`. **Incluído por
  último na raiz** (catch-all `<slug:slug>/`) — a ordem importa.

### Usuário e conta

- **accounts** — autenticação e ciclo de vida da conta (login, logout, signup,
  ativação por e-mail, reset de senha, exclusão). Model: `ActivationTask`.
  Views CBV sobre `authtools`/`braces` + classes de e-mail `djoser`. Rotas sob
  `app_name = "accounts"`.

- **profiles** — perfil público/privado do usuário, área "me" (submissões,
  bookmarks, permissões de projeto, privacidade) e equipe (`team`). Models:
  `Profile`/`BaseProfile` (OneToOne user, M2M `interestAreas`/`organisation`),
  `InterestArea`. Views CBV + FBV. **Incluído com prefixo `users/`**. Único app
  com `tests.py` de conteúdo. Tem `signals.py`.

### Infraestrutura interna

- **utilities** — utilitários transversais. Framework de **tradução genérica**
  via ContentType: `Translation` + `AbstractTranslatedModel` (base abstrata
  usada por organisations, projects, resources, platforms). Também
  `renderers.CSVRenderer` (DRF), `inspectors.SwaggerAutoSchema`, ações de admin,
  limpeza de arquivos, templatetags compartilhadas. **Sem views/urls** — é
  biblioteca interna. Tem `signals.py`.

## Roteamento (urls raiz)

- Maioria dos apps incluída com **prefixo vazio** (`path("", include(...))`):
  contact, accounts, organisations, diseases, projects, resources, blog, events,
  digest, platforms e **pages por último** (catch-all por slug).
- Exceção: **profiles** sob `users/`.
- Views raiz (`eucs_platform/views.py`): `home` (`/`), `all/`, `curated/`,
  `country_list/`, `imprint/`, `terms/`, `privacy/`, `moderation/`,
  `translations/`, além de páginas pt do SaúdesRaras (`about/`, `ajuda/`, etc.).
- Integrações na raiz: `admin/`, `admin_tools/`, `select2/`, `captcha/`,
  `summernote/`, `ckeditor/`, `o/` (oauth2), `openid/` (oidc), `api-auth/`,
  `api/auth/` (djoser + authtoken), `swagger`/`redoc` (drf-yasg, login-only),
  `i18n/`, `sitemap.xml`, `robots.txt`.

## Convenções

- **Views**: site principal usa **function-based (FBV)**; `accounts`,
  `profiles`, `blog` (lista), `pages` usam **class-based (CBV)**; as subpastas
  `api/` usam **DRF** (APIView + ViewSet + `DefaultRouter`).
- **Traduções de conteúdo**: via `utilities.AbstractTranslatedModel` /
  `Translation` (GenericForeignKey/ContentType), não i18n de template.
- **GIS**: PostGIS. `PointField` em `organisations`, `MultiPolygonField` em
  `projects`, com `latitude`/`longitude` Decimal espelhados.
- **Mapas**: **100% django-leaflet client-side** via `{% leaflet_map %}` nos
  templates de `organisations` e `projects`. Config em `LEAFLET_CONFIG`
  (`base.py`). Não há mapa server-side (folium) neste repositório.
- **Moderação**: vários models têm `approved`/`hidden`/`featured`; a home só
  mostra conteúdo aprovado/não oculto (managers `approved_*`).
- **Autocomplete**: cada app grande expõe um helper `get<App>Autocomplete`
  consumido por `home_autocomplete`.

## Onde encontrar coisas (quick map)

- `signals.py`: events, organisations, projects, resources, profiles, utilities.
- `api/` (DRF): organisations, platforms, projects, resources.
- `management/commands/`: contact (`send_newsletter`), projects
  (`populate_visao`).
- `templatetags/`: utilities (3), projects, blog, organisations, diseases.
- `fixtures/`: organisations, projects, resources.
- Testes: só `profiles/tests.py`.
