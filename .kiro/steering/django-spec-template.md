---
inclusion: manual
---

# Template de Spec para Django 

Use este template como ponto de partida ao criar uma spec de feature neste
projeto. Ele adapta o fluxo padrão de spec do Kiro (Requirements → Design →
Tasks) às particularidades de um CMS em Django 3.2.

Para usar: copie as três seções abaixo para os arquivos
`.kiro/specs/<nome-da-feature>/requirements.md`, `design.md` e `tasks.md`,
e preencha os trechos marcados com `TODO`.

---

## 1. requirements.md

```markdown
# Requisitos — <Nome da Feature>

## Contexto
Este é um programa em Django..

## User Stories

### Requisito 1 — <título>
**User Story:** Como <papel>, quero <ação>, para <benefício>.

#### Critérios de Aceitação (EARS)
1. QUANDO <evento> O SISTEMA DEVE <resposta>.
2. SE <condição> ENTÃO O SISTEMA DEVE <resposta>.
3. ENQUANTO <estado> O SISTEMA DEVE <resposta>.

### Requisito 2 — <título>
...

## Fora de escopo
- O que explicitamente NÃO será feito nesta iteração.

## Impacto em dados
- Novos models / campos? Migrations necessárias?
- Afeta sites já instalados em versões anteriores (ver política de versões no README)?
```

---

## 2. design.md

```markdown
# Design — <Nome da Feature>

## Visão geral
Resumo da abordagem técnica em 2-3 parágrafos.

## App(s) afetado(s)


## Modelo de dados
- Novos models / alterações em `cms/models.py` (ou outro app).
- Relações (lembre: o projeto usa `mptt` para hierarquia e
  `taggit`/`tagging` para tags — confirme qual se aplica).
- Migration: número esperado (próximo após o último em `cms/migrations/`).
- Compatibilidade: a migration quebra sites existentes? Precisa de data migration?

## Admin
- Como aparece no admin? O projeto usa `poweradmin`, `admin_tools` e
  `django-tabbed-admin`. Defina abas, inlines, list_display, filtros.
- Registra em `cms/admin.py`?

## Views / URLs / API
- Context processors ou middleware impactados (ver `MIDDLEWARE` em settings).

## Temas e templates
- Precisa de novo template? Onde (ver `TEMPLATES['DIRS']`: `templates/` e
  `theme/templates/`).
- Afeta a estrutura obrigatória de tema (`TEMA_STRUCTURE` em settings:
  `home.html`, `article.html`, `section.html`, `search.html`)?
- Templatetags novas em `cms/templatetags/`?

## Static / assets
- CSS/JS novo? Lembre que `django-compressor` está ativo
  (`COMPRESS_ENABLED = True`).

## Dependências
- Precisa de novo pacote? Adicionar em `pyproject.toml` com versão pinada,
  seguindo o padrão do projeto. Confirmar compatibilidade com Django < 4.

## Riscos e decisões em aberto
- Liste pontos que precisam de decisão antes da implementação.
```

---

## 3. tasks.md

```markdown
# Plano de Implementação — <Nome da Feature>

- [ ] 1. Modelos e migrations
  - Alterar/criar models em `cms/models.py`
  - Gerar migration: `python manage.py makemigrations cms`
  - Revisar o arquivo de migration gerado antes de aplicar
  - _Requisitos: 1, 2_

- [ ] 2. Admin
  - Registrar/ajustar em `cms/admin.py` (abas via tabbed_admin, inlines)
  - _Requisitos: 1_

- [ ] 3. Views / URLs / API
  - Implementar views em `cms/views.py` e rotas em `cms/urls.py`
  - _Requisitos: 2_

- [ ] 4. Templates / tema
  - Criar/ajustar templates e templatetags
  - _Requisitos: 2_

- [ ] 5. Verificação
  - `python manage.py check`
  - `python manage.py makemigrations --check --dry-run` (garante que não
    faltou migration)
  - Rodar testes relevantes: `python manage.py test cms`
  - _Requisitos: 1, 2_
```

---

## Convenções de verificação no PowerCMS

Sempre que fechar uma task, rode nesta ordem (com a venv ativa e `local.py` configurado):

1. `python manage.py check` — valida configuração e apps.
2. `python manage.py makemigrations --check --dry-run` — garante que o schema
   em código bate com as migrations.
3. `python manage.py test <app>` — testes do app afetado.

Nunca aplique `migrate` em um banco de produção sem o usuário confirmar.
