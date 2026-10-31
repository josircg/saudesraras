# Implementation Plan

_Feature: Chave de API da CARTO nos mapas leaflet (settings/base.py)_

## Overview

A parte principal já está implementada em `settings/base.py` (leitura da chave e
uso no `LEAFLET_CONFIG`). Resta a robustez à ausência da chave e a verificação.
Comandos a partir de `src/`.

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "2"] },
    { "wave": 2, "tasks": ["3"] },
    { "wave": 3, "tasks": ["4"] }
  ],
  "dependencies": {
    "3": ["1", "2"],
    "4": ["3"]
  }
}
```

## Tasks

- [x] 1. Ler CARTODB_API do ambiente
  - `environ.Env(... CARTODB_API=(str, None))` e `CARTODB_API = env("CARTODB_API")`
  - _Requisitos: 1.1_

- [x] 2. Usar a chave no basemap leaflet
  - `LEAFLET_CONFIG['TILES']` com CartoDB Positron + `?key=<CARTODB_API>`,
    `attribution` e `maxZoom`
  - _Requisitos: 2.1, 2.2, 2.3_

- [x] 3. Tornar o boot resiliente sem a chave
  - FEITO: default do `env(...)` alterado de `None` para `''` em
    `CARTODB_API=(str, '')`. Sem a chave, a URL fica `...?key=` (tiles com marca
    d'agua) e o settings NAO lanca `TypeError`. `manage.py check` ok
  - _Requisitos: 3.1, 3.2_

- [ ] 4. Verificação e referência de env
  - `uv run manage.py check` (com e sem a chave)
  - Garantir `CARTODB_API` documentada no `local.sample.reference.env`
  - Smoke-test: página com `{% leaflet_map %}` retorna 200
  - _Requisitos: 1.2, 2.3_

## Notes

- Feature client-side (django-leaflet); não há mapa server-side (folium) neste
  repositório — o steering `#django` descrevia folium como planejado/não feito.
- A chave é segredo: fica no `local.env` (git-ignored), nunca versionada.
