# Requirements Document

_Feature: Página "Sobre" com equipe e colaboradores (branch issue118)_

## Introduction

Esta spec documenta (engenharia reversa) a nova view `/about`, implementada na
branch `issue118`. A página "Sobre" deixou de ser um template estático e passou
a montar dinamicamente, a partir dos `Profile`:

- a **equipe atual** do projeto (integrantes), e
- os **demais colaboradores** agrupados por **período** (ex.: `2024.1`),
  extraído do campo `title` do perfil, com filtro por intervalo de período.

A spec registra o comportamento implementado e as correções aplicadas na
revisão (cobertura multi-idioma, caminhos de mídia, binários).

> Convenções em `#django`; estrutura dos apps em `#structure`; princípios de
> produto (multi-idioma pt-br/es/en) em `#product`.

## Glossary

- **Equipe**: perfis com `team` preenchido e `< 99` (integrantes atuais). Por
  convenção do model, `team == 99` indica ex-integrante.
- **Colaborador**: perfil com `title` preenchido; o `title` contém um ou mais
  períodos no formato `AAAA.S` (ano + semestre), ex.: "2024.1".
- **Período**: string `AAAA.S` extraída do `title` via regex
  `\b(\d{4})[./]([12])\b`.
- **InterestArea**: áreas de interesse (M2M em `Profile`); exibidas como a
  "função" do integrante, **excluindo** a área literal "Equipe".

## Requirements

### Requisito 1 — Listagem da equipe atual [IMPLEMENTADO]
**User Story:** Como visitante, quero ver os integrantes atuais do projeto na
página Sobre, para conhecer quem mantém a plataforma.

#### Acceptance Criteria
1. QUANDO a página `/about` é acessada O SISTEMA DEVE listar os `Profile` com
   `team < 99`, ordenados por `team` e depois por `user.name`.
2. O SISTEMA DEVE exibir, para cada integrante, nome, foto, áreas de interesse
   (exceto "Equipe") e bio.
3. O SISTEMA DEVE usar `prefetch_related` nas `interestAreas` para evitar
   consultas N+1.

### Requisito 2 — Colaboradores por período [IMPLEMENTADO]
**User Story:** Como visitante, quero ver os colaboradores históricos agrupados
por período, para acompanhar quem passou pelo projeto ao longo do tempo.

#### Acceptance Criteria
1. QUANDO a página é montada O SISTEMA DEVE considerar os `Profile` com `title`
   preenchido como colaboradores.
2. O SISTEMA DEVE extrair os períodos do `title` via regex `AAAA.S`
   (`\b(\d{4})[./]([12])\b`), aceitando separador `.` ou `/`.
3. QUANDO um colaborador tem mais de um período no `title` O SISTEMA DEVE
   associá-lo a cada período distinto, sem duplicar o perfil no mesmo período.
4. O SISTEMA DEVE ordenar os períodos do mais recente para o mais antigo e, em
   cada período, os colaboradores por `user.name`.
5. O SISTEMA DEVE oferecer um filtro de intervalo (De/Até) por período no
   front-end (client-side), com opção de limpar.

### Requisito 3 — Foto de perfil com fallback [IMPLEMENTADO/CORRIGIDO]
**User Story:** Como visitante, quero ver uma foto para cada pessoa, mesmo quem
não enviou imagem, para uma apresentação consistente.

#### Acceptance Criteria
1. SE o perfil tem `picture` ENTÃO O SISTEMA DEVE exibi-la via `picture.url`.
2. SE o perfil não tem `picture` ENTÃO O SISTEMA DEVE exibir
   `{{ MEDIA_URL }}default_profile.png`.
3. O SISTEMA NÃO DEVE usar caminhos de mídia hardcoded (`/media/...`); deve usar
   `picture.url` / `MEDIA_URL`.
   - *Correção aplicada:* o template usava `src="/media/..."` fixo; trocado por
     `picture.url` e `MEDIA_URL`.

### Requisito 4 — Multi-idioma (pt-br/es/en) [CORRIGIDO]
**User Story:** Como visitante em espanhol ou inglês, quero a mesma página Sobre
dinâmica, para ter a informação completa no meu idioma.

#### Acceptance Criteria
1. QUANDO a página é acessada em `pt-br`, `es` ou `en` O SISTEMA DEVE renderizar
   `pages/<lang>/about.html` usando as variáveis `equipe` e
   `equipe_por_periodo`.
2. O SISTEMA DEVE manter os três templates com a mesma estrutura dinâmica
   (equipe, timeline, filtros), variando apenas os rótulos de interface.
   - *Correção aplicada:* `es/about.html` e `en/about.html` estavam na versão
     estática antiga e ignoravam os dados da view; foram alinhados ao `pt-br`.
3. NOTA: a tradução do corpo institucional (texto denso sobre doenças raras) em
   `es`/`en` é trabalho editorial pendente, fora do escopo desta correção.

### Requisito 5 — Peso dos assets [CORRIGIDO]
**User Story:** Como mantenedor, quero evitar binários pesados no repositório,
para não inflá-lo sem necessidade.

#### Acceptance Criteria
1. O SISTEMA DEVE usar um `default_profile.png` leve (ordem de KB), não de ~1MB.
   - *Correção aplicada:* restaurado o `default_profile.png` de ~9KB.
2. O SISTEMA NÃO DEVE versionar um GIF de carregamento de ~1,3MB.
   - *Correção aplicada:* `loop-carregando.gif` removido e sua referência no
     `resource_form.html` retirada (overlay mantém o texto "Carregando...").

## Fora de escopo (Out of Scope)

- Tradução editorial do corpo institucional da página Sobre em es/en.
- Edição da equipe/colaboradores pela própria página (a fonte é o `Profile`,
  gerido no admin/perfil).
- Paginação dos colaboradores (hoje o agrupamento é por período, com filtro
  client-side).
- Otimização/responsividade avançada de imagens de perfil.

## Impacto em dados (Data Impact)

- Nenhuma mudança de schema. A view lê `Profile` (`team`, `title`, `bio`,
  `picture`, `interestAreas`) e `InterestArea`, todos já existentes.
- Depende de convenções de dados: `team < 99` = equipe atual; `title` contendo
  períodos no formato `AAAA.S`. Perfis sem esse padrão não aparecem na timeline.
