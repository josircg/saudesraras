# Design Document

_Feature: Chave de API da CARTO nos mapas leaflet (settings/base.py)_

## Overview

Ajuste de configuração em `src/eucs_platform/settings/base.py` para que os
basemaps da CARTO usem a API key agora exigida. Três mudanças:

1. Declarar `CARTODB_API` no `environ.Env(...)` e ler via `env("CARTODB_API")`.
2. Trocar o tile de CartoDB Light (sem chave) por CartoDB Positron com
   `?key=<CARTODB_API>` em `LEAFLET_CONFIG['TILES']`, no formato de tile com
   dict de opções (`attribution`, `maxZoom`).
3. (Lacuna) Tornar a montagem da URL robusta à ausência da chave.

A feature é 100% client-side (django-leaflet). Não há mapa server-side.

## Architecture

`local.env` (CARTODB_API) → `settings.base` lê a chave → `LEAFLET_CONFIG['TILES']`
monta a URL do basemap com `?key=` → `{% leaflet_map %}` nos templates de
organização/projeto renderiza o mapa com o basemap autenticado.

## Components and Interfaces

- **`environ.Env(...)`**: adiciona `CARTODB_API=(str, None)`.
- **`CARTODB_API = env("CARTODB_API")`**: variável de módulo no settings.
- **`LEAFLET_CONFIG['TILES']`**: tupla `('CartoDB Positron', <url+key>, {opts})`
  com `attribution` e `maxZoom`.
- **Consumidores**: templates de `organisations`/`projects` via
  `{% leaflet_map %}` (não mudam).

## Data Models

Nenhum. Mudança de configuração apenas.

## Error Handling

- **Chave ausente (`CARTODB_API` não setada)**: hoje o default `None` provoca
  `TypeError` ao concatenar `'...?key=' + None` no import do settings — falha de
  boot. Design-alvo: montar a URL de forma segura (default `''` ou f-string com
  `CARTODB_API or ''`) para **degradar** (tiles com marca d'água) em vez de
  derrubar a aplicação.
- **Chave inválida**: a CARTO serve tiles com marca d'água; não é erro de
  servidor (fora do controle da app).

## Correctness Properties

Property 1: URL do basemap inclui a chave quando configurada
_Para qualquer_ `CARTODB_API` não vazio, a URL de tiles em
`LEAFLET_CONFIG['TILES']` contém `?key=<CARTODB_API>`.
**Validates: Requirements 1.1, 2.1**

Property 2: Boot resiliente sem a chave
_Para qualquer_ ambiente sem `CARTODB_API`, o carregamento do settings não
lança exceção (a app sobe; os tiles degradam).
**Validates: Requirements 3.1, 3.2**

## Testing Strategy

### Validation Approach

A mudança é de settings; a verificação principal é de **boot** e de **conteúdo
da configuração**, mais um smoke-test de render de página com mapa.

### Tests

- **Com chave**: `manage.py check` passa; `LEAFLET_CONFIG['TILES'][0][1]`
  contém `?key=` + a chave do ambiente.
- **Sem chave (robustez)**: simular `CARTODB_API` ausente e confirmar que o
  settings carrega sem `TypeError` (após a correção do Requisito 3). Hoje este
  caso FALHA (documenta o bug).
- **Render**: GET de uma página de organização/projeto com `{% leaflet_map %}`
  retorna 200 (o mapa é client-side; valida que o template monta).

### Verificação

A partir de `src/`: `uv run manage.py check` (com e sem `CARTODB_API` no
ambiente, para cobrir o Requisito 3).
