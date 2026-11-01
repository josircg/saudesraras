# Implementation Plan

_Feature: Visualização e edição de recursos (publicações), com tratamento da imagem de capa_

## Overview

As tarefas 1 a 10 estão concluídas na `dev-jhonatan` (ainda não commitadas). Resta o
checkpoint final (11): conferência no navegador e commit. Comandos a partir de `src/`;
testes com `--keepdb` (banco `raras_teste`).

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "2", "3", "4", "5", "6"] },
    { "wave": 2, "tasks": ["7", "8", "9", "10"] },
    { "wave": 3, "tasks": ["11"] }
  ],
  "dependencies": {
    "7": ["1", "2", "3"],
    "8": ["5"],
    "9": ["1", "2", "3"],
    "10": ["6"],
    "11": ["7", "8", "9", "10"]
  }
}
```

## Tasks

- [x] 1. Card da listagem em coluna única
  - Título sempre visível, descrição, tags azuis de categoria e tópico; sem tipo e sem
    "Saiba mais"
  - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Detalhe do recurso
  - Descrição sob o título; "Ir para publicação", "Contatar" e "Editar" agrupados;
    capa em `col-md-3`
  - _Requisitos: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Formulário de edição
  - `_save_zone.html` com `btn_class`; recursos usam `btn-blue3`
  - Remoção da subcategoria, de `choices`, de `categorySelected`, da view e da rota
    `get_sub_category`
  - Um único `modal-crop.js?v=2`; remoção do overlay "Carregando" e do CSS órfão
  - _Requisitos: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Recorte A4 no navegador
  - `CROP_PRESETS` no `modal-crop.js` com o preset `2` (600x848); `image1` com
    `data-image-width-option: 2`; help text A4
  - _Requisitos: 4.1, 4.2, 4.3, 4.4_

- [x] 5. Gravação A4 no servidor e exibição
  - `RESOURCE_IMAGE_SIZE = (600, 848)` na `saveImage`
  - Molduras A4 inline: listagem 280x396, detalhe 420x594, formulário 420x594;
    fallback `publicacoes.svg`
  - _Requisitos: 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6. Admin de recursos
  - `ResourceAdminBase(PowerModelAdmin)` com "Edição Completa" e "Visualizar no site";
    rotas de training resource; `safe_url` vazio sem id; msgids `Full edit` /
    `View on site`
  - Testes em `resources/tests.py` (6 testes)
  - _Requisitos: 7.1, 7.2, 7.3, 7.4_

- [x] 7. Corrigir os 2 blocos sem fechamento no CSS global
  - Acrescentados os `}` após `.period-line` e `.btn4:hover` em
    `eu-citizen_science.css`; saldo de chaves zerado e regras seguintes de volta ao
    nível superior
  - Removida a classe `resource-img` da imagem do detalhe: a regra reativada tem
    `min-height: 380px`, que estourava a moldura A4 em telas médias
  - Pendente: conferência visual no navegador (barra de busca, botões de sintomas,
    FAQ, página Sobre)
  - _Requisitos: 8.1_

- [x] 8. Proteger a capa no admin
  - Decisão: `image1` somente leitura para quem não é superuser
    (`ResourceAdminBase.get_readonly_fields`), em resource e training resource
  - Superuser continua podendo enviar a capa pelo admin (sem recorte)
  - Testes em `ResourceAdminImageReadonlyTest` (4), incluindo POST com arquivo ignorado
  - _Requisitos: 7.5, 7.6, 7.7, 8.2_

- [x] 9. Decidir sobre imagens legadas
  - Não se aplica: o banco de produção não tem imagens de recursos; mantido
    `object-fit: cover`
  - _Requisitos: 8.5_

- [x] 10. Aplicar a migration `0055_alter_resource_options`
  - Aplicada (só metadado, sem SQL)
  - _Requisitos: 8.6_

- [ ] 11. Checkpoint de verificação e commit
  - `uv run manage.py check`; `uv run manage.py makemigrations --check --dry-run`;
    `uv run manage.py test resources --keepdb`; `uv run manage.py compilemessages`
  - Verificação manual no navegador do fluxo de recorte e das três telas
  - Commit na `dev-jhonatan` ou em branch com PR (a decidir)
  - _Requisitos: todos_

## Notes

- O tamanho 600x848 precisa ficar igual em três lugares: preset `2` do `modal-crop.js`,
  `RESOURCE_IMAGE_SIZE` em `views.py` e o help text de `image1`.
- As subcategorias (8.3) e a remoção de capa pelo site (8.4) ficam registradas como
  limitações conhecidas; não há tarefa para elas nesta spec.
- Ficaram sem uso no CSS as regras `.resource-img`, `.cursor-pointer` e
  `.card-hover-overlay` (do card antigo); podem ser removidas numa limpeza futura.
