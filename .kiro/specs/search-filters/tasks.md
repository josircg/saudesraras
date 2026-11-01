# Implementation Plan

_Feature: Busca e filtros padronizados nas listagens (branch issue158)_

## Overview

A feature já está implementada na branch `issue158`. Este plano registra o
estado (tasks 1–4 concluídas) e lista o que resta: higiene de assets, testes
automatizados e validação. Comandos a partir de `src/`; testes com `--keepdb`
(banco `raras_teste`).

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "2", "3", "4"] },
    { "wave": 2, "tasks": ["5"] },
    { "wave": 3, "tasks": ["6"] },
    { "wave": 4, "tasks": ["7"] }
  ],
  "dependencies": {
    "6": ["1", "2", "3"],
    "7": ["5", "6"]
  }
}
```

## Tasks

- [x] 1. Busca/filtros no blog (view)
  - `PostList.get_queryset`/`get_context_data`: keywords, author, datas,
    orderby (sticky-first), `all_authors`, `filters`, `isSearchPage`
  - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Busca/filtros em eventos (view)
  - `events()`: keywords, datas, status, orderby nas três faixas; moderação
    para não-staff; contagem e `filters`
  - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 3. Padronização da busca em doenças
  - `disease_list`: `q` → `keywords`; mantém symptom/orderby; `isSearchPage`
  - _Requisitos: 3.1, 3.2_

- [x] 4. Barra de busca e UI unificadas
  - `base.html`/`_subnavbar.html`, parciais `_finder_*`, CSS e ícones por seção;
    repopulação via `filters` e preservação na paginação
  - _Requisitos: 4.1, 4.2, 4.3_

- [x] 5. Remover arquivos `*.Zone.Identifier` versionados
  - JÁ FEITO NA BRANCH: adicionados em `49948d4b`, removidos em `866cdbc5`.
    No HEAD não há `*.Zone.Identifier` rastreado; `.gitignore` cobre futuros
  - _Requisitos: 5.1_

- [x] 6. Testes automatizados de busca/filtros
  - Implementado: `blog/tests.py` (7), `events/tests.py` (5), `diseases/tests.py`
    (6) — 18 testes. Cobrem keywords, filtros (author/status/symptom), intervalo
    de data, ordenação sticky-first, preservação de `filters`/paginação,
    moderação de eventos (não-staff) e a regressão do contrato `q`→`keywords`
  - NOTA: esta branch ainda NÃO tem a config `TEST.NAME=raras_teste` (vem da
    issue154 via dev-jhonatan). Até o merge com a dev, rode os testes com um
    settings que aponte `DATABASES['default']['TEST']['NAME']='raras_teste'`
    (ex.: um módulo de teste que herde de development). Após o merge com a dev,
    basta `uv run manage.py test blog events diseases --keepdb`
  - _Requisitos: 1.1, 1.5, 2.1, 2.5, 3.1_

- [ ] 7. Checkpoint de verificação
  - A partir de `src/`: `uv run manage.py check`;
    `uv run manage.py makemigrations --check --dry-run` (sem drift);
    `uv run manage.py test blog events diseases --keepdb`;
    `uv run manage.py compilemessages` (se houve strings novas)
  - _Requisitos: todos_

## Notes

- Sem mudança de schema; a feature é de leitura/apresentação (filtragem).
- **Contrato de URL**: `diseases` usa `?keywords=` mas mantém compatibilidade
  com `?q=` (fallback na view); links antigos continuam filtrando.
- Assets: a branch adicionou ícones da barra; vários vieram com
  `:Zone.Identifier` (lixo do Windows) — limpar (Task 5).
- A busca é `icontains` (sem full-text/Whoosh); adequada ao volume atual.
