# Implementation Plan

_Feature: Edição de Páginas com Permissões por Objeto (branch issue154)_

## Overview

A funcionalidade já está majoritariamente implementada na branch `issue154`.
Este plano foca em **fechar as lacunas** que impedem o deploy correto
(empacotamento e configuração do `django-guardian`) e em **verificar/validar**
o comportamento já implementado, sem regressões. Rodar comandos a partir de
`src/`.

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1"] },
    { "wave": 2, "tasks": ["2"] },
    { "wave": 3, "tasks": ["3"] },
    { "wave": 4, "tasks": ["4"] },
    { "wave": 5, "tasks": ["5", "6", "7"] },
    { "wave": 6, "tasks": ["8"] },
    { "wave": 7, "tasks": ["9"] }
  ],
  "dependencies": {
    "2": ["1"],
    "3": ["2"],
    "4": ["3"],
    "5": ["4"],
    "6": ["4"],
    "7": ["4"],
    "8": ["5", "6", "7"],
    "9": ["8"]
  }
}
```

- Tasks 1→4 são sequenciais e bloqueiam todo o resto (sem guardian instalado e
  configurado, a app não sobe).
- Tasks 5, 6 e 7 podem ser feitas em paralelo após a 4.
- Task 8 depende de 5, 6 e 7.

## Tasks

- [x] 1. Corrigir a dependência do django-guardian
  - Adicionar `django-guardian==2.4.0` em `requirements/base.txt` (linha
    compatível com Django 3.2; a 2.4.x não exige Django 4)
  - Ajustar `requirements/development.txt` para não duplicar sem pin (deixar o
    pin canônico em base; remover a linha `django-guardian` solta)
  - Instalar no ambiente (uv) e confirmar `python -c "import guardian"`
  - _Requisitos: 7.1, 7.2_

- [x] 2. Configurar o guardian para o AUTH_USER_MODEL customizado
  - Em `src/eucs_platform/settings/base.py`, definir a estratégia de anonymous
    user compatível com `authtools.User` (preferir `ANONYMOUS_USER_NAME = None`
    para desabilitar, salvo necessidade de permissões anônimas)
  - Confirmar `AUTHENTICATION_BACKENDS` = (`ModelBackend`,
    `ObjectPermissionBackend`), nessa ordem
  - _Requisitos: 7.4, 7.5_

- [x] 3. Aplicar e validar migrations do guardian
  - `python manage.py makemigrations --check --dry-run` — confirmar que não há
    drift nos apps locais (apenas guardian)
  - `python manage.py migrate guardian` em banco de desenvolvimento
    (NÃO aplicar em produção sem confirmação do usuário)
  - _Requisitos: 7.3, 8.2_

- [x] 4. Verificação de boot e ausência de regressão
  - `python manage.py check` deve passar sem `ModuleNotFoundError`
  - Conferir que a home (`/`) e `depoimentos/` renderizam (consumo de `Section`
    por slug de página) sem regressão
  - Conferir resolução de rotas de `pages` (sem colisão entre
    `new_<slug:page_slug>/` e o catch-all `<slug:slug>/`)
  - _Requisitos: 8.1, 8.3, 8.4_

- [x] 5. Testes do fluxo de permissões por objeto (admin)
  - Criar `src/pages/tests.py` (ou `src/accounts/tests.py`) com testes:
  - [x] 5.1 Salvar usuário no admin com objetos nos seletores
    (`allowed_pages`/`sections`/`articles`) atribui as permissões via guardian
    (`assign_perm`); remover desmarca (`remove_perm`)
    - _Requisitos: 1.2, 1.3, 1.4_
  - [x] 5.2 Pré-carregamento dos seletores reflete permissões existentes
    (`get_objects_for_user`)
    - _Requisitos: 1.1, 1.2_

- [x] 6. Testes do modelo de autorização em cascata (front-end)
  - Em `src/pages/tests.py`, cobrir a matriz de permissões por view:
  - [x] 6.1 Superuser e permissão global permitem edição em qualquer objeto
    - _Requisitos: 3.1, 3.2_
  - [x] 6.2 Permissão por objeto na página permite editar a página e
    criar/editar suas seções e artigos
    - _Requisitos: 3.3_
  - [x] 6.3 Permissão por objeto na seção permite editar a seção e criar/editar
    seus artigos; permissão no artigo permite editar só aquele artigo
    - _Requisitos: 3.4, 3.5, 3.6_
  - [x] 6.4 Usuário sem permissão recebe HTTP 403 com `no_permission.html` e
    link mailto; usuário não autenticado é redirecionado para `/login`
    - _Requisitos: 2.1, 4.1, 4.2_

- [x] 7. Testes de navegação e páginas institucionais
  - [x] 7.1 `section_detail` pagina artigos (15/página) e exige `visible=True`;
    `article_detail` exibe o artigo no contexto correto
    - _Requisitos: 5.1, 5.2_
  - [x] 7.2 Busca `?q=` em `PageDetailView` filtra seções/artigos por
    title/header/content (icontains) sem duplicar seções
    - _Requisitos: 5.3_
  - [x] 7.3 Rotas `medicos`/`diagnostico`/`justica` renderizam Page do banco e
    caem no fallback "em construção" quando a Page não existe (sem 500)
    - _Requisitos: 6.1, 6.2_

- [x] 8. Checkpoint final de verificação
  - A partir de `src/`: `python manage.py check`;
    `python manage.py makemigrations --check --dry-run`;
    `python manage.py test pages accounts --keepdb`
  - Garantir que todos os testes passam e não há drift
  - _Requisitos: 8.1, 8.2_

- [ ] 9. Compilar mensagens de tradução
  - A feature adiciona templates e strings traduzíveis (`_()`/`gettext` nas
    views de `pages`, mensagens do 403 e textos dos novos templates)
  - A partir de `src/`, rodar o script de tradução: `uv run bash translate.sh`
    (extrai com `makemessages --all --no-location`, limpa via
    `utilities/clean.py` e compila com `compilemessages`)
  - Revisar os `.po` de `es`/`en` para as entradas novas e rodar de novo para
    gerar os `.mo` atualizados
  - _Requisitos: produto multi-idioma (pt-br/es/en)_

## Notes

- Ordem recomendada: tasks 1→4 primeiro (sem elas a app não sobe), depois os
  testes (5→7) e o checkpoint (8).
- Nunca aplicar `migrate` em produção sem confirmação explícita do usuário.
- Ao mexer em strings traduzíveis/templates, rodar `uv run bash translate.sh`
  (de `src/`) para extrair, limpar e **compilar** as mensagens — sem o
  `compilemessages` (gera os `.mo`) as traduções não entram em runtime.
- O projeto usa PostGIS. Existe um banco de teste pré-criado **`raras_teste`**
  (vazio, com PostGIS) para a suíte. O settings aponta
  `DATABASES['default']['TEST']['NAME'] = 'raras_teste'`
  (via env `DATABASE_TEST_NAME`, default `raras_teste`). Rodar com
  `--keepdb` para reutilizar o banco sem recriá-lo (o usuário do banco
  pode não ter `CREATEDB`):
  `python manage.py test pages accounts --keepdb`
