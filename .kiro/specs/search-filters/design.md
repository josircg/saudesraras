# Design Document

_Feature: Busca e filtros padronizados nas listagens (branch issue158)_

## Overview

A branch padroniza busca e filtros nas listagens. O padrão de design é
consistente entre apps:

1. A view lê parâmetros GET: `keywords` (termo), filtros específicos
   (`author`/`symptom`/`status`), intervalo de data (`start_date`/`end_date`) e
   `orderby`.
2. Aplica filtragem com `Q(...) __icontains` sobre campos de texto e `filter`
   para os demais; ordena conforme um mapa de ordenação com default seguro.
3. Monta um dicionário `filters` (valores correntes) e `isSearchPage = True` no
   contexto; a listagem repopula o formulário a partir de `filters` e preserva
   os parâmetros na paginação (removendo apenas `page`).

A UI é unificada: barra/subnavbar e parciais `_finder_*`, com ícones por seção.

## Architecture

Cada listagem é independente e filtra seu próprio modelo. Não há busca
cross-app nem índice full-text. Fluxo por app: `GET ?keywords=...` → view aplica
filtros/ordenação → contexto (`object_list`/listas, `filters`, `isSearchPage`) →
template de listagem + parcial `_finder_<app>` repopula o formulário.

## Components and Interfaces

- **blog** (`blog/views.py::PostList`, CBV): `get_queryset` filtra
  `status=1` por `keywords` (title/excerpt/slug/content), `author_id`, intervalo
  `created_on`, `orderby` (mapa, sticky-first, default `-created_on`),
  `select_related('author')`. `get_context_data` expõe `all_authors`,
  `query_params` (sem `page`), `filters`, `isSearchPage`. `paginate_by = 12`.
- **events** (`events/views.py::events`, FBV): aplica `keywords`
  (title/description) + intervalo de `start_date` + `status`
  (ongoing/upcoming/past) + `orderby` às três faixas; respeita
  `approved_events()` para não-staff; pagina cada faixa (10) e expõe `counter` e
  `filters`.
- **diseases** (`diseases/views.py::disease_list`, FBV): usa `keywords` com
  fallback para `q` (`get('keywords') or get('q','')`, compatibilidade
  retroativa); mantém filtro por `symptom` e `orderby`; adiciona `isSearchPage`.
- **organisations / resources / profiles**: busca pré-existente na view; a
  branch altera **somente** os templates/parciais `_finder_*` e a UI.
- **UI compartilhada**: `templates/base.html`, `templates/_subnavbar.html`,
  `static/site/css/eu-citizen_science.css`, ícones em `static/site/icons/`.

## Data Models

Sem alterações de schema. A busca usa campos de texto já existentes:

| App | Campos buscados (icontains) | Filtros extras | Ordenação |
|---|---|---|---|
| blog | title, excerpt, slug, content | author, datas | sticky + title/created_on |
| events | title, description | status, datas | title/start_date |
| diseases | (nome/descrição) + symptom | symptom | name/orderby |

## Error Handling

- Parâmetros ausentes/vazios: cada filtro só é aplicado quando o valor existe
  (`.strip()`), então busca vazia devolve a listagem completa.
- `orderby` inválido: cai no default via mapa de ordenação (sem erro).
- `author`/datas inválidos: o ORM simplesmente não casa; não deve gerar 500
  (ver Testing para datas malformadas).
- Moderação (events): não-staff nunca vê não-aprovados, mesmo filtrando.

## Correctness Properties

Property 1: Busca textual filtra por icontains
_Para qualquer_ `keywords` não vazio, a listagem contém apenas itens cujo texto
(campos definidos por app) casa `icontains`, e busca vazia devolve todos.
**Validates: Requirements 1.1, 2.1, 3.1**

Property 2: Estado dos filtros preservado
_Para qualquer_ combinação de filtros, o contexto `filters` reflete os valores
correntes e a paginação preserva os parâmetros (menos `page`).
**Validates: Requirements 1.5, 2.6, 3.2, 4.2**

Property 3: Moderação respeitada em eventos
_Para qualquer_ usuário não-staff, a listagem de eventos nunca inclui eventos
não aprovados, independentemente dos filtros.
**Validates: Requirements 2.5**

## Testing Strategy

### Validation Approach

Testes de view/listagem sobre `raras_teste` (`--keepdb`). Foco: filtragem por
keywords, filtros específicos, ordenação, preservação de estado e moderação.

### Unit / View Tests

- **blog**: posts com títulos/autores/datas variados ⇒ `keywords`, `author`,
  intervalo de data e `orderby` retornam o subconjunto correto; `sticky` vem
  primeiro; `all_authors` só autores com post publicado.
- **events**: `keywords` filtra as três faixas; `status` restringe à faixa;
  não-staff não vê não-aprovados; `orderby` aplica a ordenação.
- **diseases**: `?keywords=` filtra (e `?q=` NÃO filtra mais — registrar a
  mudança de contrato); filtro por `symptom` mantido.
- **Preservação**: `filters` no contexto bate com os parâmetros; `query_params`
  não contém `page`.

### Integration Tests

- GET das listagens com e sem parâmetros ⇒ 200 e contagem coerente.
- Datas malformadas (`start_date=abc`) ⇒ não deve gerar 500 (validar
  comportamento; se o backend lançar, tratar).

### Verificação

A partir de `src/`: `uv run manage.py check`;
`uv run manage.py test blog events diseases --keepdb`.
