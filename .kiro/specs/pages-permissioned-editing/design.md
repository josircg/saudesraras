# Design Document

_Feature: Edição de Páginas com Permissões por Objeto (branch issue154)_

## Overview

A branch `issue154` adiciona edição de conteúdo do app `pages` fora do admin,
controlada por permissões a nível de objeto via `django-guardian`. O desenho
tem duas camadas:

1. **Concessão de permissões (admin)** — o `CustomUserAdmin` expõe seletores
   que traduzem a escolha do administrador em permissões por objeto do guardian
   (`assign_perm`/`remove_perm`).
2. **Verificação de permissões (front-end)** — cada view de edição em
   `pages/views.py` avalia uma cascata (superuser → permissão global → permissão
   por objeto na página/seção/artigo) antes de permitir a operação, caindo numa
   página 403 amigável quando negada.

O conteúdo (Page → Section → Article) já existia; esta branch não altera os
models. O foco do design é o fluxo de autorização e a correção das lacunas de
empacotamento/configuração do guardian para a app subir em produção.

## Architecture

## Components and Interfaces

- **settings/base.py**: `guardian` em `INSTALLED_APPS`; `AUTHENTICATION_BACKENDS`
  = (`ModelBackend`, `ObjectPermissionBackend`).
- **accounts/admin.py**:
  - `CustomUserChangeForm` — três `ModelMultipleChoiceField`
    (`allowed_pages`/`allowed_sections`/`allowed_articles`) com
    `FilteredSelectMultiple`. `__init__` pré-carrega via `get_objects_for_user`;
    `save()` sincroniza diffs com `assign_perm`/`remove_perm`.
  - `CustomUserAdmin(GuardedModelAdminMixin, AuthtoolsUserAdmin)` — mantém o
    inline de `Profile` e adiciona um fieldset de permissões de objeto.
  - `LogEntryAdmin` — somente leitura (sem add/change/delete).
- **pages/forms.py**: `PageForm`, `SectionForm`, `ArticleForm` com CKEditor
  (`config_name='admin'`).
- **pages/views.py**: views FBV com `@login_required`; helper
  `render_no_permission`; `PageDetailView` com busca; `section_detail`/
  `article_detail` para navegação pública.
- **pages/urls.py**: rotas nomeadas; catch-all `<slug:slug>/` por último.
- **eucs_platform/views.py**: `SafePageView` (fallback Http404 →
  "em construção") para páginas institucionais.

### Fluxo de autorização (cascata)

```
operação de edição
  → superuser?                         → permite
  → has_perm(global do tipo)?          → permite
  → has_perm(change_page, page_mae)?   → permite (página e descendentes)
  → has_perm(change_section, section)? → permite (seção e seus artigos)
  → has_perm(change_article, article)? → permite (apenas o artigo)
  → senão                              → render_no_permission (403 + mailto)
```

A granularidade segue o nível da operação: editar página checa até
`change_page`; criar/editar seção checa também `change_section`; criar/editar
artigo checa a cascata completa até `change_article`.

## Data Models

- **Sem mudanças nos models de `pages`**. `Page`/`Section`/`Article` usam as
  permissões default do Django (`change_*`). As FKs `Section.page` e
  `Article.section` são `PROTECT`; idioma herdado no `save()`.
- **Guardian**: adiciona `UserObjectPermission` e `GroupObjectPermission`
  (tabelas próprias). Requer `migrate guardian`. Usa ContentType + object_pk
  para relacionar a permissão ao objeto.
- **Migration esperada**: nenhuma nova em `pages`; apenas as migrations do
  pacote guardian. `makemigrations --check --dry-run` deve ficar limpo para os
  apps locais.

## Configuração do guardian (fechando as lacunas)

### Dependência (Requisito 7.1, 7.2)

- Declarar `django-guardian` em `requirements/base.txt` com versão
  compatível com Django 3.2. **Instalado: `django-guardian 3.5.2`** — a
  metadata do pacote declara `django>=3.2` e foi verificado funcionando com
  Django 3.2.25 (`manage.py check` sem erros). (A recomendação inicial de
  2.4.0 era conservadora; não é necessária.)
- Instalado no ambiente (uv); `import guardian` confirmado.

### AUTH_USER_MODEL customizado (Requisito 7.4)

- `AUTH_USER_MODEL = authtools.User` não tem `username` (login por email). O
  guardian cria um "anonymous user" usando `ANONYMOUS_USER_NAME`. Com usuário
  customizado, definir explicitamente em settings:
  - Opção A (recomendada): `ANONYMOUS_USER_NAME = "anonymous@saudesraras"`
    (um identificador válido para o campo usado como natural key do authtools).
  - Opção B: `GUARDIAN_GET_INIT_ANONYMOUS_USER` customizado, caso a criação
    default não preencha os campos obrigatórios de `authtools.User`.
- **Decisão tomada (implementada):** `ANONYMOUS_USER_NAME = None` em
  `base.py`, desabilitando a criação do anonymous user do guardian. As
  permissões por objeto desta feature são todas para usuários autenticados
  (views de edição usam `@login_required`), então não há caso para anônimos.
  Verificado: guardian lê `ANONYMOUS_USER_NAME = None` e `check` passa.

### Backends (Requisito 7.5)

- `AUTHENTICATION_BACKENDS` mantém `ModelBackend` primeiro (permissões globais e
  login) e `ObjectPermissionBackend` em seguida (permissões por objeto). Ordem
  importa: o ModelBackend precisa continuar resolvendo o login normal.

## Views / URLs (Components and Interfaces, cont.)

- Rotas de edição (todas `@login_required`, login_url=`/login`):
  `edit_page_generic`, `new_section_generic`, `edit_section_generic`,
  `new_article_generic`, `edit_article_generic`.
- Rotas públicas: `section_detail`, `article_detail`, `PageDetailView`
  (catch-all), `DepoimentosListView`.
- **Ordem das rotas**: prefixos específicos (`new_...`, `edit_page/...`,
  `<page_slug>/section/...`, `<page_slug>/edit/...`, `<page_slug>/detail/...`,
  `depoimentos/`) antes do catch-all `<slug:slug>/`. Risco: um slug de página
  igual a um prefixo reservado (ex.: uma página com slug `depoimentos` ou
  começando com `new_`) pode ser capturado pela rota específica. Mitigação:
  documentar os slugs reservados e evitar criá-los como Page.

## Templates

- Novos: `page.html`, `page_form.html`, `section.html`, `section_form.html`,
  `article.html`, `article_form.html`, `no_permission.html`, `_finder.html`,
  `_paginator.html`, `justica_cards.html`. `PageDetailView` tenta
  `pages/<slug>.html` e cai em `pages/page.html`.

## Riscos e decisões em aberto

1. **[RESOLVIDO] guardian não instalado / só em development.txt** — agora
   instalado (`django-guardian 3.5.2`) e a app sobe (`check` ok). Confirmar o
   pin em `base.txt` na finalização (Requisito 7.1).
2. **[RESOLVIDO] Anonymous user do guardian x authtools.User** —
   `ANONYMOUS_USER_NAME = None`; migrations do guardian já aplicadas em
   desenvolvimento.
3. **Colisão de rotas por slug reservado** — definir e documentar a lista de
   slugs reservados; opcionalmente validar no `save()`/admin de Page.
4. **Autorização só com change_*** — criar conteúdo exige `change` no pai; se no
   futuro quisermos separar criação de edição, migrar para `add_*`. Fora de
   escopo agora, mas registrado.
5. **Views de visualização públicas** — `section_detail`/`article_detail` não
   exigem login; confirmar que só expõem seções `visible=True` e que não vazam
   conteúdo não publicado.

## Error Handling

- **Permissão negada**: `render_no_permission` retorna HTTP 403 com
  `pages/no_permission.html` e link `mailto` para solicitar acesso
  (Requisito 4). Nunca retornar 500 por falta de permissão.
- **Página institucional inexistente**: `SafePageView` captura `Http404` e
  cai no fallback "em construção" (Requisito 6.2), evitando 500.
- **Objetos ausentes**: `get_object_or_404` para Page/Section/Article em todas
  as views; seção exige `visible=True` nas rotas públicas.
- **Guardian ausente/mal configurado**: se o pacote não estiver instalado a
  app falha no boot (ModuleNotFoundError) — mitigado pelo Requisito 7; a
  verificação (check) deve detectar isso antes do deploy.

## Testing Strategy

Rodar a partir de `src/`, com guardian instalado. Para reproduzir produção usar
`DJANGO_SETTINGS_MODULE=eucs_platform.settings.production` quando o `local.env`
estiver configurado; caso contrário, development.

1. `python manage.py check` — deve passar (sem ModuleNotFoundError).
2. `python manage.py makemigrations --check --dry-run` — sem drift nos apps
   locais; apenas migrations do guardian, se houver.
3. `python manage.py migrate guardian` — num banco de desenvolvimento (nunca em
   produção sem confirmação).
4. Testes manuais/automatizados do fluxo de permissão em cascata (ver tasks).
5. Conferir que home e `depoimentos/` continuam renderizando (consumo de
   `Section` por slug de página).
