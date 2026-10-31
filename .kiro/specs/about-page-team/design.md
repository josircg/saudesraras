# Design Document

_Feature: Página "Sobre" com equipe e colaboradores (branch issue118)_

## Overview

A view `about` (`src/eucs_platform/views.py`) monta a página "Sobre"
dinamicamente a partir de `profiles.Profile`:

1. **Equipe atual** — `Profile.objects.filter(team__lt=99)` ordenada por
   `team`, `user__name`, com `prefetch_related` das `interestAreas` (excluindo
   a área "Equipe").
2. **Colaboradores por período** — `Profile.objects.filter(title__isnull=False)`;
   para cada perfil, extrai períodos do `title` via regex `AAAA.S` e monta um
   `OrderedDict` período → lista de perfis, ordenado do mais recente ao mais
   antigo.

O resultado é renderizado em `pages/<lang>/about.html` (um template por idioma),
com a listagem da equipe, uma timeline de colaboradores por período e um filtro
client-side (JS) por intervalo de período.

## Architecture

Fluxo: rota `/about/` → `eucs_platform.views.about` → querysets sobre `Profile`
→ contexto (`equipe`, `equipe_por_periodo`) → template `pages/<lang>/about.html`.

Não há novos models, migrations, forms ou URLs além da rota `/about/` já
existente. A feature é de **leitura/apresentação**.

## Components and Interfaces

- **View** `about(request)` (`src/eucs_platform/views.py`):
  - `prefetch_funcoes = Prefetch('interestAreas', queryset=InterestArea.objects.exclude(interestArea__iexact='Equipe'))`
  - `equipe = Profile.objects.filter(team__lt=99).prefetch_related(prefetch_funcoes).order_by('team','user__name')`
  - `todos_colaboradores = Profile.objects.filter(title__isnull=False).prefetch_related(prefetch_funcoes)`
  - monta `periodos_dict` com `re.compile(r'\b(\d{4})[./]([12])\b')` sobre
    `perfil.title`; normaliza para `f"{ano}.{semestre}"`; evita duplicar o
    perfil no mesmo período.
  - `equipe_por_periodo = OrderedDict` com chaves ordenadas `reverse=True` e
    perfis ordenados por `user.name.lower()`.
  - `render(request, 'pages/%s/about.html' % get_language(), {...})`.
- **Templates** `src/templates/pages/{pt-br,es,en}/about.html`:
  - secção da equipe (loop `equipe`), timeline (loop `equipe_por_periodo.items`),
    selects de filtro (`filterFrom`/`filterTo`) e `<script>` de filtragem.
  - estilos da timeline em `static/site/css/eu-citizen_science.css`
    (`.timeline-clean-container`, `.period-*`).
- **Model** `profiles.Profile` (não alterado): usa `team`, `title`, `bio`,
  `picture`, `interestAreas`.

## Data Models

Sem alterações de schema. Campos consumidos de `Profile`:

| Campo | Uso na view |
|---|---|
| `team` (SmallInteger) | `team < 99` seleciona a equipe atual (99 = ex-integrante) |
| `title` (Char) | fonte dos períodos `AAAA.S` dos colaboradores |
| `bio` (Text) | descrição exibida |
| `picture` (Image) | foto; fallback `MEDIA_URL + default_profile.png` |
| `interestAreas` (M2M) | "funções" exibidas, exceto "Equipe" |

## Error Handling

- **Sem foto**: fallback para `{{ MEDIA_URL }}default_profile.png` (Requisito 3).
- **`title` sem período válido**: o perfil simplesmente não entra na timeline
  (a regex não casa); não gera erro.
- **Idioma sem template**: a view usa `pages/<lang>/about.html`; os três idiomas
  suportados (pt-br/es/en) têm template. (Idiomas fora desses cairiam em erro de
  template — fora do escopo, só pt-br/es/en são oferecidos.)

## Correctness Properties

Property 1: Equipe atual corresponde a `team < 99`
_Para qualquer_ conjunto de `Profile`, `equipe` contém exatamente os perfis com
`team` não nulo e `< 99`, ordenados por `team` e `user.name`.
**Validates: Requirements 1.1, 1.2, 1.3**

Property 2: Agrupamento por período é fiel ao `title`
_Para qualquer_ `title`, cada período `AAAA.S` presente (separador `.` ou `/`)
gera uma entrada período→perfil, sem duplicar o perfil no mesmo período, e os
períodos saem ordenados do mais recente ao mais antigo.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 3: Equivalência entre idiomas
_Para qualquer_ idioma em {pt-br, es, en}, a página expõe a mesma estrutura
dinâmica (equipe + timeline + filtro), variando apenas rótulos de interface.
**Validates: Requirements 4.1, 4.2**

## Testing Strategy

### Validation Approach

Testes de view/template sobre o banco `raras_teste` (ver `#django`), com
`--keepdb`. Como a feature é de apresentação, o foco é: seleção correta dos
perfis, agrupamento por período e renderização nos três idiomas.

### Unit / View Tests

- **Equipe**: criar perfis com `team` 1, 2, 99 e nulo ⇒ `equipe` contém só os
  `< 99`, na ordem `team`, `user.name`.
- **Período**: `title` "2024.1", "2023/2", "2024.1 e 2023.2", e um sem período
  ⇒ `equipe_por_periodo` com as chaves certas, perfil não duplicado, ordem
  decrescente de período.
- **InterestArea "Equipe" excluída**: um perfil com área "Equipe" e outra ⇒ só a
  outra aparece.

### Integration Tests

- GET `/about/` em pt-br, es e en ⇒ HTTP 200 e presença do bloco dinâmico
  (`timeline-period-block` / `team-horizontal`) no HTML.
- Fallback de foto: perfil sem `picture` ⇒ HTML referencia
  `default_profile.png` via `MEDIA_URL` (não `/media/` hardcoded).

### Verificação

A partir de `src/`: `uv run manage.py check`;
`uv run manage.py test <app> --keepdb`.
