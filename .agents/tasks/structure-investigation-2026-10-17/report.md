# Investigação READ-ONLY — Estrutura da aplicação "Saúdes Raras"

Data: 2026-10-17 • Base para gerar `.kiro/steering/structure.md`
Escopo: `/home/josir/bitbucket/saudesraras/src/` • Nenhum arquivo do repositório foi modificado.
Validação: `DJANGO_SETTINGS_MODULE=eucs_platform.settings.development uv run manage.py check` → **"System check identified no issues (0 silenced)"**.

---

## 1. Resumo (summary answer)

O projeto é um portal Django 3.2 (projeto `eucs_platform`) com **15 apps locais** em `src/`. A home agrega conteúdo de vários apps (posts, projetos, recursos, organizações, plataformas, eventos, depoimentos, FAQ, equipe) via `eucs_platform/views.py::home`.

**Divergências importantes entre o steering `django.md` e o código real** (precisam ser corrigidas no `structure.md`):

1. **Apps locais**: `django.md` lista 12 apps. O código tem **15**: os 12 citados **mais `diseases`, `pages` e `authors`** (este último sem `apps.py`, mas é app registrado e tem models/migrations). `diseases` e `pages` são centrais ao domínio de doenças raras.
2. **Mapas (folium) NÃO existem neste repositório**: não há `eucs_platform/maps.py`, nem `generate_map`, nem `map_view`, nem rota `/map/` (confirmado por `find`/`grep` — zero ocorrências). O único sistema de mapas é **django-leaflet client-side** via `{% leaflet_map %}` nos templates de organização e projeto, com `LEAFLET_CONFIG` em `base.py`. A seção de folium/CARTO do `django.md` descreve algo que não está presente aqui.
3. **`LEAFLET_CONFIG['TILES']`** usa a URL CARTO **sem** parâmetro `?key=` (`https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png`). Não há leitura de `CARTODB_API` no `base.py`. A observação do `django.md` sobre a chave CARTO não corresponde ao código atual.
4. **`poweradmin` está em `INSTALLED_APPS`** (`base.py`), contrariando a afirmação do `django.md` de que "não há poweradmin". `admin_tools` + `admin_tools.dashboard` também estão presentes (dashboard customizado em `eucs_platform/dashboard.py`).
5. Além dos itens do `django.md`, `INSTALLED_APPS` inclui: `django_select2`, `cookielaw`, `djoser`, `active_link`, `django_cron`, `django_cleanup`, `easy_thumbnails`.

O default de settings do `manage.py` é **production** (confirmado), consistente com o `django.md`.

---

## 2. Evidências por app (`src/`)

Convenção dominante: **views function-based (FBV)** no site principal; **class-based (CBV)** em `accounts`, `profiles`, `blog` (listas), `pages`; **DRF (APIView + ViewSet + DefaultRouter)** nas subpastas `api/`.

### 2.1 accounts
- **Responsabilidade**: autenticação e ciclo de vida da conta (login, logout, signup, ativação por e-mail, reset de senha, exclusão de conta).
- **Models** (`models.py`): `ActivationTask` — tarefa de ativação pendente (email, módulo/nome da task, kwargs JSON).
- **Views** (CBV, sobre `authtools`/`braces`): `LoginView`, `LogoutView`, `SignUpView`, `PasswordChangeView`, `PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`; FBV `delete_user`, `activate`. Classes de e-mail djoser: `PasswordResetEmail`, `ActivationEmail`, `ConfirmationEmail` (referenciadas em `DJOSER` no `base.py`).
- **urls.py**: `app_name = "accounts"`. Rotas: `login/`, `logout/`, `signup/`, `delete/`, `password-change/`, `password-reset/`, `password-reset-done/`, `activate/<uidb64>/<token>/`. Incluído na raiz com prefixo vazio (`include(accounts.urls)`).
- **Dependências**: `authtools` (base de forms/views), `djoser` (BaseEmailMessage), `braces`.
- **Templates**: pasta `templates/` própria. **Arquivos**: `admin.py`, `forms.py`, `messages.py`, `tokens.py`. Sem `apps.py`/`signals.py`.

### 2.2 authors
- **Responsabilidade**: catálogo simples de autores de recursos (publicações/materiais).
- **Models**: `Author` — campo único `author` (TextField).
- **Views/urls**: **não tem** `views.py` nem `urls.py` (app só de dados).
- **Dependências**: usado por `resources` (`resources/models.py`, `views.py`, `forms.py`, `api/serializers.py`) via M2M `Resource.authors`.
- Arquivos: `apps.py`, `models.py`, `migrations`. Sem admin/forms/signals próprios.

### 2.3 blog
- **Responsabilidade**: notícias/posts do portal (área "blog").
- **Models**: `Post` — notícia com `title`, `slug`, `author` (FK → `AUTH_USER_MODEL`, related_name `blog_posts`), `content`, `excerpt`, `image`, `created_on`, `sticky`, `status`. Ordenação `-created_on`.
- **Views**: CBV `PostList` (lista) + FBV `post_detail`.
- **urls.py**: `blog` (lista), `blog/<year>/<month>/<day>/<slug>/` (detalhe). Incluído via `include('blog.urls')`.
- **Templates**: pasta própria. **templatetags**: `my_tags.py`. Tem `admin.py`, `apps.py`. Sem forms/signals.

### 2.4 contact
- **Responsabilidade**: contato, inscrição de assinantes (subscribers) e envio/gestão de newsletters.
- **Models**: `Subscriber` (nome, email único, organisation, flags valid/opt_out, FK `last_newsletter`→`Newsletter`); `Newsletter` (título, headline, featured, FK `blog`→`blog.Post`, FK `featured_resource`→`resources.Resource`, html, status, contadores).
- **Views** (FBV + 1 CBV): `contactView`, `countView`, `import_csv`, `submitterContactView`, `subscribeView`, `confirm_email`, `unsubscribe`, `test_newsletter`, `render_newsletter`, `newsletter`, `NewsletterList` (CBV), `load_image`.
- **urls.py**: `contact/`, `count/<pk>`, `import_subscriber_csv/`, `subscribe/`, `confirm_email/...`, `unsubscribe/...`, `newsletter(s)`, `render_newsletter/...`, etc. Prefixo vazio na raiz.
- **Dependências**: `blog.Post`, `resources.Resource`.
- **Management command**: `contact/management/commands/send_newsletter.py`.
- Arquivos: `admin.py`, `apps.py`, `forms.py`, `managers.py`, `templates/`. Sem signals.

### 2.5 digest
- **Responsabilidade**: "digests" (boletins/recortes periódicos) agregando posts, eventos, organizações, projetos, recursos e treinamentos num intervalo de datas.
- **Models**: `Digest` — FK `creator`→user, intervalo de datas, flags `include*` e contadores `n*`, `slug`, `sent`.
- **Views**: FBV `showDigests`, `showDigest`.
- **urls.py**: `showDigests`, `showDigest/<pk>`. Prefixo vazio.
- Arquivos: `admin.py`, `apps.py`, `templates/`. Sem forms/signals/managers.

### 2.6 diseases  *(ausente do django.md)*
- **Responsabilidade**: núcleo do domínio — catálogo de **doenças raras** e seus **sintomas**; busca por sintoma.
- **Models**: `Symptom` (description); `Disease` (`name`, `ICD`, `other_names`, `description`, M2M `symptoms`→`Symptom`).
- **Views**: FBV `disease_list`, `disease_detail`, `symptom_search`.
- **urls.py**: `diseases/` e alias pt `doencas/` (ambos → `disease_list`); `disease/<pk>/`; `symptoms/` e alias `sintomas/` (→ `symptom_search`). Prefixo vazio.
- **Dependências**: referenciado por `organisations.models` (M2M `Organisation.diseases`→`Disease`).
- **templatetags**: `my_tags.py`. Tem `admin.py`, `apps.py`, `static/`, `templates/`. Sem forms/signals.

### 2.7 events
- **Responsabilidade**: eventos (criação, edição, aprovação/moderação, destaque, listagem ongoing/upcoming).
- **Models**: `Event` — FK `creator`→user, título, descrição, local, `start_date`/`end_date`, `hour`, `url`, `featured`, `approved`, `logo`. Manager customizado com `approved_events()/ongoing_events()/upcoming_events()` (usado em `eucs_platform/views.home`).
- **Views**: FBV `new_event`, `events`, `editEvent`, `deleteEvent`, `approve_event`, `setFeaturedEvent`.
- **urls.py**: `new_event`, `events`, `editEvent/<pk>`, `deleteEvent/<pk>`, `approve_event/<pk>/<status>`, `setFeaturedEvent/`. Prefixo vazio.
- Arquivos: `admin.py`, `apps.py`, `forms.py`, `managers.py`, **`signals.py`**, `templates/`.

### 2.8 organisations
- **Responsabilidade**: organizações atuantes em doenças raras (cadastro, moderação, permissões de edição por usuário, mapa leaflet).
- **Models**: `OrganisationType(AbstractTranslatedModel)`; `Organisation` (name, url, description, FK `orgType`, FK `creator`, `logo`, `location` **PointField** (GIS), `latitude`/`longitude` Decimal, **M2M `diseases`→`diseases.Disease`**, `approved`); `OrganisationPermission` (FK user + FK organisation).
- **Views**: FBV `new_organisation`, `edit_organisation`, `organisation`, `organisations`, `approve_organisation`, `delete_organisation`, `allowUserOrganisation`, helper `getOrganisationAutocomplete` (usado na home). **DRF** em `organisations/api/`.
- **urls.py**: rotas acima + `url(r'^api/', include('organisations.api.urls'))`. Prefixo vazio.
- **Dependências**: `diseases` (M2M). Consumido por `platforms`, `projects`, `resources`, `profiles` (todos têm M2M/FK para `Organisation`).
- **Mapa**: `{% leaflet_map %}` em `organisation.html` e `organisation_form.html`.
- Arquivos: `admin.py`, `apps.py`, `forms.py`, `managers.py`, **`signals.py`**, `api/`, `fixtures/`, `static/`, `templates/`, **templatetags** `test_image.py`.

### 2.9 pages  *(ausente do django.md)*
- **Responsabilidade**: CMS leve de páginas estáticas/semi-estáticas por idioma — páginas institucionais, **depoimentos** e **FAQ** (consumidos na home por `Section.objects.filter(page__slug='depoimentos'/'faq')`).
- **Models**: `Page` (slug, title, header, content, `language`, image); `Section` (FK `page`, `order`, conteúdo, `language`, `visible`); `Article` (FK `section`, order, conteúdo, `language`).
- **Views**: CBV `DepoimentosListView`, `PageDetailView`.
- **urls.py**: `depoimentos/`, `<slug:slug>/` (→ `PageDetailView`). **Incluído por último** na raiz (catch-all por slug) — ordem importa.
- Arquivos: `admin.py`, `apps.py`, `managers.py`, `templates/`. Sem forms/signals.

### 2.10 platforms
- **Responsabilidade**: plataformas (de ciência cidadã / iniciativas) com palavras-chave, extensão geográfica e vínculo a organizações.
- **Models**: `Keyword`; `GeographicExtend(AbstractTranslatedModel)`; `Platform` (name, url, FK `creator`, description, FK `geoExtend`→`GeographicExtend`, M2M `keywords`, **M2M `organisation`→`organisations.Organisation`**, logos, `active`).
- **Views**: FBV `newPlatform`, `savePlatformAjax`, `platform`, `platforms`, `editPlatform`, `deletePlatformAjax`, `platformsAutocompleteSearch`, helper `getPlatformsAutocomplete`. **DRF** em `platforms/api/`.
- **urls.py**: rotas acima + `api/` include. Prefixo vazio.
- **Dependências**: `organisations`.
- Arquivos: `admin.py`, `apps.py`, `forms.py`, `managers.py`, `api/`, `templates/`. Sem signals.

### 2.11 profiles
- **Responsabilidade**: perfil público/privado do usuário, área "me" (submissões, bookmarks, permissões de projeto, privacidade), equipe do projeto (`team`).
- **Models**: `InterestArea`; `BaseProfile` (OneToOne `user`, slug UUID, picture, bio, M2M `interestAreas`, orcid, **M2M `organisation`→`organisations.Organisation`**, flags de visibilidade, `team`); `Profile(BaseProfile)`.
- **Views**: CBV `ShowProfile`, `EditProfile`, `PrivacyCenter`, `Submissions`, `Bookmarks`, `ProjectPermissions`, `UsersSearch`; FBV `updatePrivacy`, `resources`, `followedProjects`, `organisations`, `usersAutocompleteSearch`, helper `getProfilesAutocomplete`.
- **urls.py**: `app_name = "profiles"`. **Incluído com prefixo `users/`** (`path("users/", include(profiles.urls))`). Rotas `me/...`, `<slug>/...`, raiz `userSearch`.
- **Dependências**: `organisations`, e (via views) `resources`/`projects`.
- Arquivos: `admin.py`, `apps.py`, `forms.py`, **`signals.py`**, **`tests.py`** (único app com testes), `templates/`.

### 2.12 projects
- **Responsabilidade**: projetos de ciência cidadã / iniciativas — o app mais complexo: cadastro, moderação, destaque, tradução de conteúdo, permissões/convites de editores, estatísticas, download, autocomplete, mapa leaflet.
- **Models (destaques)**: `Status`, `Topic`, `ParticipationTask` (todos `AbstractTranslatedModel`), `Keyword`, `FundingBody`, `OriginDatabase`, `CustomField`, `TranslatedProject`, `Project` (muitos campos; FK `creator`, FK `status`, M2M `keywords/topic/participationTask/organisation/fundingBody/customField/translatedProject`, FK `mainOrganisation`→`Organisation`, `projectGeographicLocation` **MultiPolygonField** GIS, lat/long Decimal, M2M `editors`→user, flags approved/hidden/featured), `FollowedProjects`, `ProjectPermission`.
- **Views**: FBV extensas (`newProject`, `editProject`, `saveProjectAjax`, `projects`, `projects_stats`, `project`, `approve_project`, `deleteProject`, `translateProject`, `getProjectTranslation`, `submitProjectTranslation`, `projectsAutocompleteSearch`, `setHidden/setFeatured/setFollowedProject/allowUser`, `downloadProjects`, `test_visao`, `project_invite`, `project_invitation`, permissões, etc.), helper `getProjectsAutocomplete`. **DRF** em `projects/api/` (APIView `ProjectList/Detail/Create/Translate` + ViewSets `Topic/Status/ParticipationTask` via `DefaultRouter`).
- **urls.py**: ~25 rotas + `url(r'^api/', include('projects.api.urls'))`. Prefixo vazio.
- **Dependências**: `organisations` (FK/M2M), `utilities` (AbstractTranslatedModel). Consumido por `resources` (M2M `Resource.project`) e `contact`.
- **Management command**: `projects/management/commands/populate_visao.py`.
- **Mapa**: `{% leaflet_map %}` em `project.html`/`project_form.html`.
- Arquivos: `admin.py`, `apps.py`, `forms.py`, `managers.py`, **`signals.py`**, `api/`, `fixtures/`, `templates/`, **templatetags** `project_tags.py`. Observação: há `project.html`, `projects.html`, `_finder_projects.html` soltos na raiz do app além de `templates/`.

### 2.13 resources
- **Responsabilidade**: recursos e **recursos de treinamento** (publicações, materiais), com categorias/temas/audiência, bookmarks, agrupamentos curados, moderação e download.
- **Models**: `Keyword`, `Theme/Audience/Category` (Category com `parent` auto-FK; `Theme`/`Audience`/`Category` são `AbstractTranslatedModel`), `Resource` (FK `creator`, M2M `keywords/theme/authors`→`authors.Author`, FK `category`, **M2M `organisation`→Organisation**, **M2M `project`→projects.Project**, `isTrainingResource`, flags approved/hidden/featured), `TrainingResource(Resource)` (proxy/MTI), `ResourceGroup`, `ResourcesGrouped`, `BookmarkedResources`, `SavedResources`, `ResourcePermission`. Manager com `approved_resources()/approved_training_resources()` (usado na home).
- **Views**: FBV extensas (`resources`, `resource`, `newResource`, `editResource`, `approve_resource`, `saveResourceAjax`, `setFeaturedResource`, `setTrainingResource`, `deleteResource`, `bookmarkResource`, `downloadResources`, `training_resources`, etc.), helper `getResourcesAutocomplete`. **DRF** em `resources/api/`.
- **urls.py**: ~30 rotas + `url(r'^api/', include('resources.api.urls'))`. Prefixo vazio.
- **Dependências**: `authors`, `organisations`, `projects`, `utilities`.
- Arquivos: `admin.py`, `apps.py`, `forms.py`, `managers.py`, **`signals.py`**, `api/`, `fixtures/`, `templates/`.

### 2.14 utilities
- **Responsabilidade**: utilitários transversais — framework de **tradução genérica** (ContentType), renderer CSV p/ DRF, inspector Swagger, ações de admin, limpeza de arquivos, templatetags compartilhadas.
- **Models**: `Translation` (tradução genérica via GenericForeignKey/ContentType; tabela `translation`); `AbstractTranslatedModel` (base abstrata usada por `organisations`, `projects`, `resources`, `platforms`).
- **Sem** `views.py`/`urls.py`. É biblioteca interna.
- **Módulos relevantes**: `renderers.py` (`CSVRenderer`, usado em `REST_FRAMEWORK.DEFAULT_RENDERER_CLASSES`), `inspectors.py` (`SwaggerAutoSchema`, usado em `SWAGGER_SETTINGS`), `actions.py`, `clean.py`, `file.py`, `get_emails.py`, `maint_fields.py`, `managers.py`, **`signals.py`**, `test_email.py`.
- **templatetags**: `eucs_platform_tags.py`, `eucs_platform_translate.py`, `eucs_platform_admin_list.py`.
- Arquivos: `admin.py`, `apps.py`. (Nota: `ugettext_lazy` ainda importado em `models.py` — removido no Django 4; relevante p/ migração.)

### 2.15 (resumo de sinais por app)
- **`signals.py`**: events, organisations, projects, resources, profiles, utilities.
- **`api/` (DRF)**: organisations, platforms, projects, resources.
- **`management/commands/`**: contact (`send_newsletter`), projects (`populate_visao`).
- **`templatetags/`**: utilities (3), projects, blog, organisations, diseases.
- **`fixtures/`**: organisations, projects, resources.
- **`tests.py` com conteúdo**: apenas profiles.

---

## 3. Projeto `eucs_platform`

### 3.1 urls.py raiz (`eucs_platform/urls.py`)
- A maioria dos apps é incluída com **prefixo vazio** `path("", include(...))`: contact, accounts, organisations, diseases, projects, resources, blog, events, digest, platforms, **pages (por último — catch-all `<slug>/`)**.
- Exceção: **profiles** sob `path("users/", include(profiles.urls))`.
- Rotas raiz de páginas (views em `eucs_platform/views.py`): `home` (`/`), `all/`, `curated/`, `country_list/`, `imprint/`, `terms/`, `privacy/`, `home_autocomplete/`, `moderation/`, `translations/`, `development/`, e páginas SaúdesRaras pt (`riofarmes/`, `about/`, `projeto/`, `ajuda/`, `parceiro/`, muitas apontando para `pag_em_construcao`, mais variantes `*dev/`).
- Integrações montadas na raiz: `admin/` (`admin.site`), `admin_tools/`, `select2/`, `captcha/`, `summernote/`, `ckeditor/`, `o/` (oauth2_provider), `openid/` (oidc_provider), `api-auth/`, `api/auth/` (djoser + authtoken), `swagger`/`redoc`/`swagger.json|yaml` (drf-yasg, protegidos por login), `i18n/`, `sitemap.xml`, `robots.txt`, `500/`, `403/`, `coming_soon/`.
- Em `DEBUG`: serve `MEDIA_URL` e monta `debug_toolbar`.
- Título/header do admin sobrescritos para "Administração".
- Schema DRF: `drf_yasg` (`get_schema_view`, `public=False`, `IsAuthenticated`). `rest_framework_swagger` está em INSTALLED_APPS mas **não** é usado nas urls (pacote morto, como o django.md observa).

### 3.2 views raiz e mapas
- `eucs_platform/views.py`: FBV. `home` agrega e pagina Posts, Projects (approved/not hidden), Resources + TrainingResources (managers `approved_*`), Organisations (com busca por keyword), Platforms (active), Events (ongoing ∪ upcoming), Sections de `depoimentos`/`faq` por idioma, contagem de `Profile`. `home_autocomplete` encadeia autocompletes dos apps. `country_list` usa `django_countries` (staff-only). Views de páginas renderizam templates por idioma `pages/<lang>/<arquivo>.html`.
- **Mapas**: **NÃO há folium / `maps.py` / `map_view` / `/map/`** neste repositório (verificado por `find -name maps.py` → vazio e `grep generate_map|map_view` → zero). Mapas são **100% client-side via django-leaflet** (`{% leaflet_map %}`) em templates de `organisations` e `projects`, config em `LEAFLET_CONFIG` (`base.py`). **`LEAFLET_CONFIG['TILES']`** usa CartoDB Light **sem `?key=`** e não lê `CARTODB_API`.

### 3.3 Settings e INSTALLED_APPS
- Pacote `eucs_platform/settings/`: `base.py` (comum, lê `local.env` via `django-environ` se existir), `development.py` (herda base; adiciona `debug_toolbar` a INSTALLED_APPS/MIDDLEWARE; validações de senha mais fracas; logging para `logs/django.log`), `production.py` (herda base; `cached.Loader` nos templates + `APP_DIRS=False`; Argon2 + validadores de senha; logging para `logs/project.log`).
- `manage.py` **default = `eucs_platform.settings.production`** (confirmado; o comentário no arquivo diz "development" mas o código usa production).
- `AUTH_USER_MODEL = "authtools.User"`. `LANGUAGE_CODE = pt-br`; idiomas pt-br/es/en; `FORMAT_MODULE_PATH = 'formats'`; `TIME_ZONE America/Sao_Paulo`.
- DB: `django.contrib.gis.db.backends.postgis` (PostGIS), parâmetros via env.
- `REST_FRAMEWORK`: TokenAuth + SessionAuth; renderers JSON + `utilities.renderers.CSVRenderer`; `IsAuthenticated` default. `SWAGGER_SETTINGS` usa `utilities.inspectors.SwaggerAutoSchema`.
- `DJOSER` mapeia e-mails para classes em `accounts.views`. OIDC via `oidc_provider` (`OIDC_USERINFO = eucs_platform.oidc_provider_settings.userinfo`).
- `django_cron`: `CRON_CLASSES`/`CRONJOBS` referenciam `eucs_platform.cron` (ExpiredUsersCronJob, CleanExpiredCaptchaCronJob; `NewForumResponseCronJob` é citada em settings mas **não** encontrada como classe em `cron.py` — possível referência quebrada a investigar).
- `ADMIN_TOOLS_*_DASHBOARD` → `eucs_platform.dashboard.Custom*Dashboard`.
- **INSTALLED_APPS completo** (ordem do arquivo):
  `admin_tools`, `admin_tools.dashboard`, **`poweradmin`**, `django.contrib.auth`, `django.contrib.admin`, `contenttypes`, `sessions`, `messages`, `staticfiles`, `sitemaps`, `authtools`, `crispy_forms`, `crispy_bootstrap3`, `easy_thumbnails`, **`profiles`**, **`accounts`**, **`digest`**, `django_select2`, **`blog`**, **`events`**, **`diseases`**, **`projects`**, **`organisations`**, **`platforms`**, **`resources`**, **`authors`**, **`contact`**, **`pages`**, `django_summernote`, `leaflet`, `django_countries`, `django.contrib.sites`, `cookielaw`, `rest_framework`, `rest_framework.authtoken`, `djoser`, `rest_framework_swagger`, `oidc_provider`, `drf_yasg`, `captcha`, `active_link`, `oauth2_provider`, `django.contrib.gis`, `django_cron`, `ckeditor`, `ckeditor_uploader`, `django_cleanup.apps.CleanupConfig`, `utilities`.
  (Apps locais: `profiles, accounts, digest, blog, events, diseases, projects, organisations, platforms, resources, authors, contact, pages, utilities`. Falta `authors`/`diseases`/`pages` no `django.md`.)

### 3.4 Outros arquivos de `eucs_platform`
`context_processors.py` (`global_settings`: TRANSLATED_LANGUAGES, FEATURED_MGT, FORUM_ENABLED), `dashboard.py` (admin-tools), `cron.py`, `logger.py`, `oidc_provider_settings.py`, `sitemaps.py`, `utils.py`, `visao.py` (integração "Visão"/geoserver usada por `projects`), `wsgi.py`.

---

## 4. Mapa de dependências entre apps (ForeignKey/M2M)

- **diseases** ← organisations (`Organisation.diseases`)
- **organisations** ← platforms (`Platform.organisation`), projects (`Project.organisation`, `mainOrganisation`), resources (`Resource.organisation`), profiles (`Profile.organisation`)
- **projects** ← resources (`Resource.project`), contact (indireto)
- **authors** ← resources (`Resource.authors`)
- **blog** ← contact (`Newsletter.blog`)
- **resources** ← contact (`Newsletter.featured_resource`)
- **utilities** ← organisations, projects, resources, platforms (via `AbstractTranslatedModel`/`Translation`)
- **AUTH_USER_MODEL (authtools.User)** ← quase todos (`creator`/`editors`/`user`)
- **eucs_platform.views.home** importa de: blog, events, organisations, platforms, profiles, projects, resources, pages (acoplamento central da home).

Ordem de dependência sugerida (folha → raiz): `utilities`, `authors`, `diseases` → `organisations` → `platforms`/`projects` → `resources` → `blog`/`events`/`digest`/`contact`/`pages`/`profiles` → `eucs_platform`.

---

## 5. Conclusões e recomendações para o `structure.md`

1. **Corrigir a lista de apps** no steering: são **15** (incluir `diseases`, `pages`, `authors`).
2. **Remover/retrabalhar a seção de mapas folium**: neste repositório não existe `maps.py`/`generate_map`/`map_view`/`/map/`. Documentar que o mapa é **django-leaflet client-side** (`{% leaflet_map %}` em organisations/projects) e que `LEAFLET_CONFIG['TILES']` **não** usa `CARTODB_API`/`?key=` atualmente. (Se o comportamento folium/CARTO é esperado, isso é uma divergência entre `django.md` e o código que vale sinalizar ao usuário — pode ser steering herdado de outro projeto.)
3. **Corrigir "não há poweradmin"**: `poweradmin` está em INSTALLED_APPS. Admin usa `admin_tools` + dashboard customizado.
4. **Documentar convenções reais**: site = FBV; auth/profiles/blog/pages = CBV; `api/` = DRF (APIView + ViewSet + DefaultRouter); traduções via `utilities.AbstractTranslatedModel`/`Translation` (ContentType); GIS via PostGIS (`PointField` em organisations, `MultiPolygonField` em projects) com lat/long Decimal espelhados.
5. **Registrar integrações montadas na raiz** (admin_tools, select2, captcha, summernote, ckeditor, oauth2/oidc, djoser, drf-yasg swagger/redoc, sitemaps, i18n).
6. **Itens a investigar** (fora do escopo desta leitura): `CRON_CLASSES` referencia `NewForumResponseCronJob` não encontrada em `cron.py`; `utilities/models.py` usa `ugettext_lazy` (removido no Django 4 — relevante para a migração planejada).

Nenhum arquivo foi alterado. `manage.py check` (development) passou sem erros.
