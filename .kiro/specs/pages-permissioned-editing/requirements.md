# Requirements Document

_Feature: Edição de Páginas com Permissões por Objeto (branch issue154)_

## Introduction

Esta spec documenta e completa a funcionalidade implementada na branch
`issue154`, que adiciona duas capacidades acopladas ao app `pages`:

1. **Permissões a nível de objeto** com `django-guardian`, geridas pelo admin,
   para conceder a usuários específicos o direito de editar determinadas
   páginas, seções e artigos.
2. **Edição front-end** (fora do admin) de páginas, seções e artigos por
   usuários autorizados, com um modelo de autorização em cascata
   (global → objeto; página → seção → artigo).

Como a branch já está implementada, os requisitos abaixo distinguem o que já
está **[IMPLEMENTADO]** do que é **[LACUNA]** — pontos encontrados na análise
do código que precisam ser fechados para a branch ser correta e deployável.

> Convenções e ambiente em `#django`; estrutura do app `pages` em `#structure`;
> princípios de produto (conteúdo moderado, multi-idioma) em `#product`.

## Glossary

- **Permissão global**: permissão de modelo do Django (`pages.change_page`,
  `pages.change_section`, `pages.change_article`) que vale para todos os objetos
  do tipo.
- **Permissão por objeto**: permissão concedida via guardian para uma instância
  específica (ex.: `change_page` apenas na Page "medicos").
- **Cascata de autorização**: quem pode editar uma entidade pai pode editar as
  filhas (quem tem `change_page` na página pode criar/editar suas seções e
  artigos).
- **page_mae**: a Page à qual uma Section pertence (FK `Section.page`).

## Requirements

### Requisito 1 — Gestão de permissões por objeto no admin [IMPLEMENTADO]
**User Story:** Como administrador, quero conceder a um usuário permissão para
editar páginas, seções e artigos específicos, para delegar a manutenção de
conteúdo sem dar acesso total.

#### Critérios de Aceitação
1. QUANDO o administrador abre a tela de edição de um usuário no admin O
   SISTEMA DEVE exibir três seletores múltiplos: páginas, seções e artigos
   permitidos.
2. QUANDO o administrador abre um usuário existente O SISTEMA DEVE pré-carregar
   nos seletores os objetos para os quais o usuário já tem a permissão
   correspondente (`get_objects_for_user` para `pages.change_page`,
   `pages.change_section`, `pages.change_article`).
3. QUANDO o administrador salva o usuário com objetos adicionados a um seletor O
   SISTEMA DEVE atribuir a permissão por objeto correspondente via `assign_perm`.
4. QUANDO o administrador salva o usuário com objetos removidos de um seletor O
   SISTEMA DEVE revogar a permissão por objeto correspondente via `remove_perm`.
5. O SISTEMA DEVE registrar o admin de `User` usando `GuardedModelAdminMixin`,
   preservando o `UserAdmin` do authtools e o inline de `Profile`.

### Requisito 2 — Edição front-end de páginas, seções e artigos [IMPLEMENTADO]
**User Story:** Como editor autorizado, quero criar e editar páginas, seções e
artigos pelo próprio site (fora do admin), para manter o conteúdo com uma
interface simples.

#### Critérios de Aceitação
1. QUANDO um usuário não autenticado acessa qualquer rota de edição O SISTEMA
   DEVE redirecioná-lo para `/login` (`@login_required`).
2. QUANDO um usuário autorizado submete o formulário de edição de página
   (`PageForm`: title, content, image) O SISTEMA DEVE salvar e redirecionar para
   o detalhe da página.
3. QUANDO um usuário autorizado cria uma seção (`SectionForm`: title, order,
   header, content, visible) O SISTEMA DEVE vinculá-la à página mãe e salvar.
4. QUANDO um usuário autorizado cria/edita um artigo (`ArticleForm`: title,
   order, header, content) O SISTEMA DEVE vinculá-lo à seção e salvar.
5. O SISTEMA DEVE usar o CKEditor (config `admin`) nos campos de conteúdo
   (`content`/`header`) dos formulários.
6. QUANDO uma seção é salva O SISTEMA DEVE herdar o idioma da página mãe; QUANDO
   um artigo é salvo O SISTEMA DEVE herdar o idioma da seção (comportamento dos
   `save()` dos models, que não mudam nesta branch).

### Requisito 3 — Modelo de autorização em cascata [IMPLEMENTADO]
**User Story:** Como editor com permissão numa página, quero poder gerir também
suas seções e artigos, para não depender do admin a cada subitem.

#### Critérios de Aceitação
1. SE o usuário é superuser ENTÃO O SISTEMA DEVE permitir todas as operações de
   edição de páginas/seções/artigos.
2. SE o usuário tem a permissão global do tipo (`pages.change_page`,
   `change_section` ou `change_article`) ENTÃO O SISTEMA DEVE permitir a
   operação correspondente em qualquer objeto daquele tipo.
3. SE o usuário tem `change_page` no objeto página ENTÃO O SISTEMA DEVE
   permitir editar a página e criar/editar suas seções e artigos.
4. SE o usuário tem `change_section` no objeto seção ENTÃO O SISTEMA DEVE
   permitir editar a seção e criar/editar seus artigos.
5. SE o usuário tem `change_article` no objeto artigo ENTÃO O SISTEMA DEVE
   permitir editar aquele artigo.
6. O SISTEMA DEVE avaliar a cascata exatamente na ordem implementada (global →
   objeto na página mãe → objeto na seção → objeto no artigo).

### Requisito 4 — Negação de acesso amigável [IMPLEMENTADO]
**User Story:** Como usuário sem permissão, quero uma mensagem clara e um meio
de solicitar acesso, para não ficar sem saber o que fazer.

#### Critérios de Aceitação
1. QUANDO um usuário autenticado sem permissão tenta uma operação de edição O
   SISTEMA DEVE responder com HTTP 403 e renderizar `pages/no_permission.html`.
2. O SISTEMA DEVE incluir na página 403 um link `mailto` pré-preenchido
   (assunto e corpo) para solicitar acesso ao item específico.
3. O SISTEMA DEVE preservar o idioma corrente nas mensagens (i18n).

### Requisito 5 — Navegação e visualização pública [IMPLEMENTADO]
**User Story:** Como visitante, quero navegar por seções e artigos e buscar
conteúdo, para encontrar informação.

#### Critérios de Aceitação
1. QUANDO um visitante acessa o detalhe de uma seção O SISTEMA DEVE listar seus
   artigos paginados (15 por página) e exigir que a seção esteja `visible=True`.
2. QUANDO um visitante acessa o detalhe de um artigo O SISTEMA DEVE exibi-lo no
   contexto de sua seção e página.
3. QUANDO um visitante informa um termo de busca (`?q=`) no detalhe da página O
   SISTEMA DEVE filtrar seções e artigos por `title`/`header`/`content`
   (icontains, sem duplicar seções) e expor a contagem de resultados.
4. O SISTEMA DEVE resolver as rotas sem ambiguidade, mantendo o catch-all
   `<slug:slug>/` (PageDetailView) por último.

### Requisito 6 — Páginas institucionais servidas do banco [IMPLEMENTADO]
**User Story:** Como editor, quero que páginas como "médicos", "diagnóstico" e
"justiça" venham do banco, para editá-las sem mexer em template.

#### Critérios de Aceitação
1. QUANDO uma rota institucional (`medicos`, `diagnostico`, `justica`) é
   acessada e existe Page correspondente no idioma atual O SISTEMA DEVE
   renderizá-la via `PageDetailView`.
2. SE a Page não existir ENTÃO O SISTEMA DEVE cair no fallback "página em
   construção" (`SafePageView` tratando `Http404`), sem erro 500.

### Requisito 7 — Dependência e configuração do django-guardian [LACUNA]
**User Story:** Como mantenedor, quero que o guardian esteja corretamente
declarado e configurado, para que a aplicação suba em produção.

#### Critérios de Aceitação
1. O SISTEMA DEVE declarar `django-guardian` em `requirements/base.txt` com
   versão compatível com Django 3.2, não apenas em `development.txt`.
   - *Instalado:* `django-guardian 3.5.2` (declara `django>=3.2`; verificado
     funcionando com Django 3.2.25). A recomendação anterior de 2.4.x era
     conservadora; a 3.5.2 também é compatível com esta linha do Django.
   - *Motivo:* hoje `guardian` está só em `development.txt` e sem pin; como o
     `manage.py` usa production por default e `guardian` está em
     `INSTALLED_APPS`, a app não sobe sem o pacote. Verificado: `manage.py check`
     falha com `ModuleNotFoundError: No module named 'guardian'`.
2. O SISTEMA DEVE ter o `guardian` instalado no ambiente de forma que
   `python manage.py check` passe sem `ModuleNotFoundError`.
3. O SISTEMA DEVE aplicar as migrations do guardian
   (`UserObjectPermission`/`GroupObjectPermission`). O SISTEMA NÃO DEVE aplicar
   `migrate` em produção sem confirmação explícita do usuário.
4. O SISTEMA DEVE configurar o guardian de forma compatível com o
   `AUTH_USER_MODEL = authtools.User` (login por email, sem `username`),
   definindo `ANONYMOUS_USER_NAME` apropriado (ou `None` para desabilitar o
   usuário anônimo) para evitar falha na criação do anonymous user.
5. O SISTEMA DEVE manter `AUTHENTICATION_BACKENDS` com `ModelBackend` seguido de
   `guardian.backends.ObjectPermissionBackend`.

### Requisito 8 — Verificação sem regressões [LACUNA]
**User Story:** Como mantenedor, quero garantir que a branch não introduz drift
nem quebra o consumo existente de conteúdo, para fazer merge com segurança.

#### Critérios de Aceitação
1. QUANDO `python manage.py check` roda (com guardian instalado) O SISTEMA DEVE
   terminar sem erros.
2. QUANDO `python manage.py makemigrations --check --dry-run` roda O SISTEMA
   DEVE acusar apenas (no máximo) migrations do próprio guardian, sem drift nos
   apps locais.
3. O SISTEMA DEVE continuar servindo a home e a página de depoimentos, que
   consomem `Section` por slug de página, sem regressão.
4. O SISTEMA DEVE manter a resolução das rotas de `pages` sem colisão entre
   `new_<slug:page_slug>/` e o catch-all `<slug:slug>/`.

## Fora de escopo (Out of Scope)

- Tradução automática do conteúdo das páginas/seções/artigos (o idioma é
  herdado da entidade pai; tradução de conteúdo via framework genérico não faz
  parte desta branch).
- Permissões separadas de `add_*`/`delete_*`: o modelo atual usa apenas
  `change_*`; criar seção/artigo depende de `change` na entidade pai. Rever esse
  design é trabalho futuro.
- Interface de autogestão de permissões fora do admin (a concessão continua
  sendo feita pelo admin).
- Fluxo de moderação/aprovação do conteúdo editado (o app `pages` não tem flags
  `approved`/`hidden` como outros apps).

## Impacto em dados (Data Impact)

- **Guardian**: aplica migration própria, criando as tabelas de permissão por
  objeto. Requer `migrate guardian`.
- **Models de `pages`**: nenhum campo novo ou alterado nesta branch; as
  permissões `change_page`/`change_section`/`change_article` são as default do
  Django por model. `makemigrations --check` não deve acusar mudança em `pages`.
- **Conteúdo institucional**: páginas `medicos`/`diagnostico`/`justica` passam a
  depender de registros `Page` no banco (com fallback "em construção" se
  ausentes).
