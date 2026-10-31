# Implementation Plan

_Feature: Página "Sobre" com equipe e colaboradores (branch issue118)_

## Overview

A feature já está implementada na branch `issue118` e teve correções aplicadas
na revisão (multi-idioma, caminhos de mídia, binários). Este plano registra o
estado e lista o que resta (testes automatizados e tradução editorial).
Rodar comandos a partir de `src/`, testes com `--keepdb` (banco `raras_teste`).

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "2", "3"] },
    { "wave": 2, "tasks": ["4"] },
    { "wave": 3, "tasks": ["5"] }
  ],
  "dependencies": {
    "4": ["1", "2", "3"],
    "5": ["4"]
  }
}
```

## Tasks

- [x] 1. View dinâmica da página Sobre
  - `about()` em `src/eucs_platform/views.py`: equipe (`team < 99`) e
    colaboradores por período (regex `AAAA.S` sobre `title`), com
    `prefetch_related` das `interestAreas` (exceto "Equipe")
  - _Requisitos: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4_

- [x] 2. Templates e filtro client-side (pt-br/es/en)
  - Estrutura dinâmica (equipe + timeline + filtro JS) nos três idiomas;
    es/en alinhados ao pt-br (eram estáticos antigos)
  - Caminhos de mídia via `picture.url` / `MEDIA_URL` (sem `/media/` fixo)
  - _Requisitos: 2.5, 3.1, 3.2, 3.3, 4.1, 4.2_

- [x] 3. Limpeza de assets
  - `default_profile.png` restaurado para versão leve (~9KB)
  - `loop-carregando.gif` (~1,3MB) removido e referência retirada do
    `resource_form.html`
  - _Requisitos: 5.1, 5.2_

- [x] 4. Testes automatizados da view/templates
  - Criar testes (app `eucs_platform` ou `profiles`) cobrindo: seleção da
    equipe (`team < 99`, ordenação), agrupamento por período (regex, sem
    duplicar, ordem decrescente), exclusão da área "Equipe", fallback de foto,
    e GET `/about/` 200 nos três idiomas com o bloco dinâmico presente
  - Implementado em `src/profiles/tests.py` (classe `AboutViewTestCase`,
    6 testes). Rodar: `uv run manage.py test profiles --keepdb`
  - _Requisitos: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 4.1, 4.2_

- [ ] 5. Tradução editorial do corpo institucional (es/en)
  - Traduzir o texto denso da seção "Sobre o projeto" para espanhol e inglês
    (hoje permanece em português nesses idiomas). Trabalho editorial do
    autor/tradutor; não inventar tradução automaticamente
  - _Requisitos: 4.3 (nota)_

## Notes

- Sem mudança de schema; a feature é de leitura/apresentação sobre `Profile`.
- Depende de convenções de dados: `team < 99` = equipe atual (99 = ex-integrante);
  `title` com períodos `AAAA.S`.
- Assets pesados são um risco recorrente nesta branch; revisar imagens novas
  antes de versionar.
