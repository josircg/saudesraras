# Requirements Document

_Feature: Busca e filtros padronizados nas listagens (branch issue158)_

## Introduction

Esta spec documenta (engenharia reversa) a branch `issue158`, que padroniza a
**busca e os filtros** nas páginas de listagem do portal e unifica a barra de
busca (UI). O escopo cobre:

- **Busca/filtro nova na view**: `blog` e `events`.
- **Padronização de parâmetro**: `diseases` (de `q` para `keywords`).
- **Ajuste apenas de template/UI** (a busca já existia na view): `organisations`,
  `resources`, `profiles` (perfis).
- **UI compartilhada**: barra de busca em `base.html`/`_subnavbar.html`, parciais
  `_finder_*`, estilos em `eu-citizen_science.css` e ícones por seção.

> Convenções em `#django`; estrutura dos apps em `#structure`; princípios de
> produto (conteúdo moderado, multi-idioma) em `#product`.

## Glossary

- **keywords**: parâmetro GET padrão do termo de busca textual, usado em todas
  as listagens (substitui variações como `q`).
- **isSearchPage**: flag booleana no contexto que indica que a página exibe a
  barra/estado de busca.
- **filters**: dicionário no contexto com os valores correntes dos filtros
  (keywords, datas, ordenação, filtros específicos), usado para repopular o
  formulário e manter o estado na paginação.
- **_finder_**: parcial de template da barra de busca/filtros de cada app.

## Requirements

### Requisito 1 — Busca e filtros no blog [IMPLEMENTADO]
**User Story:** Como visitante, quero buscar e filtrar os posts do blog, para
encontrar conteúdo por termo, autor, data e ordenação.

#### Acceptance Criteria
1. QUANDO a listagem do blog recebe `keywords` O SISTEMA DEVE filtrar os posts
   (status publicado) por `title`, `excerpt`, `slug` ou `content` (icontains).
2. QUANDO recebe `author` O SISTEMA DEVE filtrar pelo autor correspondente.
3. QUANDO recebe `start_date` e/ou `end_date` O SISTEMA DEVE filtrar por
   `created_on` no intervalo.
4. QUANDO recebe `orderby` O SISTEMA DEVE ordenar por título ou data (asc/desc),
   sempre priorizando `sticky` primeiro; o padrão é `-created_on`.
5. O SISTEMA DEVE expor no contexto `all_authors` (autores com posts
   publicados), `filters` e `isSearchPage`, preservando o estado na paginação.

### Requisito 2 — Busca e filtros em eventos [IMPLEMENTADO]
**User Story:** Como visitante, quero buscar e filtrar eventos, para localizar
por termo, período, situação e ordenação.

#### Acceptance Criteria
1. QUANDO a listagem de eventos recebe `keywords` O SISTEMA DEVE filtrar por
   `title` ou `description` (icontains) nas três faixas (ongoing/upcoming/past).
2. QUANDO recebe `start_date`/`end_date` O SISTEMA DEVE filtrar por `start_date`
   no intervalo.
3. QUANDO recebe `status` (`ongoing`/`upcoming`/`past`) O SISTEMA DEVE restringir
   às faixas correspondentes.
4. QUANDO recebe `orderby` O SISTEMA DEVE ordenar por título ou `start_date`
   (asc/desc), com padrão `-start_date`.
5. O SISTEMA DEVE respeitar a moderação: para usuário não-staff, apenas eventos
   aprovados (`approved_events`).
6. O SISTEMA DEVE expor a contagem total de resultados e o dicionário `filters`
   no contexto.

### Requisito 3 — Padronização da busca em doenças [IMPLEMENTADO]
**User Story:** Como visitante, quero buscar doenças com o mesmo padrão das
demais listagens, para uma experiência consistente.

#### Acceptance Criteria
1. O SISTEMA DEVE usar o parâmetro `keywords` (antes era `q`) na busca de
   doenças, mantendo o filtro por sintoma e a ordenação existentes.
   O SISTEMA DEVE aceitar `q` como fallback (compatibilidade retroativa), com
   `keywords` tendo precedência quando ambos vierem.
2. O SISTEMA DEVE expor `isSearchPage` e o `filters` com `keywords` no contexto.

### Requisito 4 — Barra de busca e UI unificadas [IMPLEMENTADO]
**User Story:** Como visitante, quero uma barra de busca consistente em todas as
seções, para reconhecer o padrão em qualquer página.

#### Acceptance Criteria
1. O SISTEMA DEVE padronizar a barra/subnavbar (`base.html`/`_subnavbar.html`) e
   as parciais `_finder_*` de blog, events, diseases, organisations, resources e
   profiles.
2. O SISTEMA DEVE repopular os campos do formulário a partir de `filters` e
   preservar os parâmetros ativos ao paginar.
3. O SISTEMA DEVE usar os ícones por seção (azul = ativo / cinza = inativo) na
   navegação de busca.

### Requisito 5 — Higiene dos assets commitados [RESOLVIDO NA BRANCH]
**User Story:** Como mantenedor, quero evitar lixo de versionamento, para manter
o repositório limpo.

#### Acceptance Criteria
1. O SISTEMA NÃO DEVE versionar arquivos `*.Zone.Identifier` (metadados do
   Windows).
   - *Estado:* foram adicionados por engano no commit `49948d4b` e **já
     removidos** no commit seguinte `866cdbc5` ("ajuste na pasta static"). No
     HEAD da branch não há nenhum `*.Zone.Identifier` rastreado. O `.gitignore`
     (`*.Zone.Identifier`) cobre futuros. Nenhuma ação adicional necessária.

## Fora de escopo (Out of Scope)

- Mudança no modelo de dados ou nos índices de busca (a busca é via `icontains`
  em campos de texto; não há full-text search / Whoosh nesta branch).
- Busca unificada cross-app (cada listagem filtra seu próprio modelo).
- Autocomplete da home (já existente; não é objeto desta branch).

## Impacto em dados (Data Impact)

- Nenhuma mudança de schema; nenhuma migration. A busca usa `filter`/`Q` sobre
  campos existentes.
- A busca de `diseases` passou a usar `keywords`, mas mantém **compatibilidade
  retroativa** com `q` (fallback na view), então links antigos `?q=` continuam
  filtrando. `keywords` tem precedência. Sem quebra de contrato de URL.
