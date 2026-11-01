# Requirements Document

_Feature: Chave de API da CARTO nos mapas leaflet (settings/base.py)_

## Introduction

Os basemaps da CARTO (CartoDB) passaram a exigir uma **API key** na URL do tile
(`?key=<KEY>`); sem ela, os tiles vêm com marca d'água "API KEY REQUIRED". Este
ajuste em `src/eucs_platform/settings/base.py` adiciona a leitura da chave
(`CARTODB_API`) do ambiente e passa a usá-la no `LEAFLET_CONFIG['TILES']`,
trocando o basemap CartoDB Light (sem chave) por CartoDB Positron com a chave.

Até aqui, o steering `#django` descrevia essa funcionalidade como *planejada,
ainda não implementada*. Esta spec documenta a implementação (parte leaflet /
client-side) e registra as lacunas de robustez.

> Mapas: o projeto usa django-leaflet client-side (`#django`/`#structure`). Não
> há mapa server-side (folium) neste repositório.

## Glossary

- **CARTODB_API**: chave de API da CARTO, lida do `local.env` (não versionado).
- **LEAFLET_CONFIG['TILES']**: configuração do(s) basemap(s) do django-leaflet,
  usada por `{% leaflet_map %}` nas páginas de organização/projeto.
- **tile URL**: URL do template de tiles; agora inclui `?key=<CARTODB_API>`.

## Requirements

### Requisito 1 — Leitura da chave do ambiente [IMPLEMENTADO]
**User Story:** Como mantenedor, quero que a chave da CARTO venha de variável de
ambiente, para não versionar segredo e configurar por ambiente.

#### Acceptance Criteria
1. O SISTEMA DEVE declarar `CARTODB_API` no `environ.Env(...)` e lê-la via
   `CARTODB_API = env("CARTODB_API")`.
2. O SISTEMA DEVE manter a chave no `local.env` (não versionado), com entrada
   correspondente no arquivo de referência (`local.sample.reference.env`).

### Requisito 2 — Basemap com a chave [IMPLEMENTADO]
**User Story:** Como visitante, quero ver os mapas sem a marca d'água "API KEY
REQUIRED", para uma visualização limpa.

#### Acceptance Criteria
1. O SISTEMA DEVE usar, em `LEAFLET_CONFIG['TILES']`, a URL CartoDB Positron
   `https://basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}{r}.png?key=<CARTODB_API>`.
2. O SISTEMA DEVE fornecer `attribution` (OpenStreetMap + CARTO) e `maxZoom` nas
   opções do tile.
3. Os mapas de organização e projeto (`{% leaflet_map %}`) DEVEM renderizar com
   o basemap com chave.

### Requisito 3 — Robustez quando a chave está ausente [LACUNA]
**User Story:** Como mantenedor, quero que a aplicação não quebre no boot quando
a chave não estiver configurada, para não derrubar ambientes sem a chave.

#### Acceptance Criteria
1. QUANDO `CARTODB_API` não está definida O SISTEMA NÃO DEVE lançar `TypeError`
   no carregamento do settings.
   - *Problema atual:* o default é `None` e a URL é montada com
     `'...?key=' + CARTODB_API`. Com `None`, isso lança
     `TypeError: can only concatenate str (not "NoneType")` e a app não sobe.
   - *Correção sugerida:* usar default `''` (string vazia) em vez de `None`, ou
     validar/formatar a URL de modo seguro (ex.: `f"...?key={CARTODB_API or ''}"`).
2. SE a chave estiver vazia ENTÃO o comportamento esperado é degradar (tiles com
   marca d'água), não derrubar a aplicação.

## Fora de escopo (Out of Scope)

- Mapa server-side com **folium** (`maps.py`, `generate_map`, rota `/map/`):
  continua não implementado neste repositório; esta spec cobre apenas o leaflet
  client-side.
- Troca de provedor de tiles ou cache de tiles.
- Rotação/gestão de segredos além de ler do `local.env`.

## Impacto em dados (Data Impact)

- Nenhuma mudança de schema. Ajuste apenas de configuração em `settings/base.py`.
- **Ambiente**: requer `CARTODB_API` no `local.env` de cada ambiente (dev e
  produção). Sem a chave, ver Requisito 3 (hoje quebra; deve degradar).
