# Design Document

_Feature: Visualização e edição de recursos (publicações), com tratamento da imagem de capa_

## Overview

A capa de um recurso segue a proporção A4 retrato (210:297) de ponta a ponta. O tamanho
de referência é **600x848 px**, que aparece em três lugares que precisam ficar
sincronizados:

1. o preset `2` do `static/site/js/modal-crop.js` (recorte no navegador);
2. a constante `RESOURCE_IMAGE_SIZE` em `resources/views.py` (gravação no servidor);
3. o texto de ajuda do campo `image1` em `resources/forms.py`.

A exibição não depende do tamanho do arquivo: listagem, detalhe e formulário mostram a
capa numa **moldura A4** definida no próprio template, com thumbnails gerados pelo
`easy_thumbnails` em proporção A4. Sem capa, a mesma moldura mostra o `publicacoes.svg`.

## Architecture

### Fluxo da imagem de capa

```
Formulário /editResource
  └─ <input type=file name=image1 data-image-suffix=1 data-image-width-option=2>
       │ change
       ▼
modal-crop.js (preset 2 = 600x848, aspectRatio 600/848)
  ├─ abre o modal _crop_zone.html com o cropper (moldura fixa, zoom pelo slider)
  └─ "Recortar": grava x1, y1, width1, height1 (campos hidden)
                 e troca o src de #imageResult1 pelo canvas 600x848
       │ submit (AJAX /saveResourceAjax, FormData com o arquivo original + recorte)
       ▼
views.saveImage(request, form, 'image1', '1')
  ├─ abre o arquivo, ImageOps.exif_transpose (orientação)
  ├─ crop((x, y, x+w, y+h))
  ├─ resize(RESOURCE_IMAGE_SIZE = 600x848, LANCZOS)
  ├─ preenche com transparência se o recorte passou das bordas da imagem
  └─ save_image_with_path → MEDIA_ROOT/images/<uuid>.<ext>
       │ caminho
       ▼
ResourceForm.save: grava em resource.image1 só se o caminho for novo (len > 6);
                   sem arquivo novo, a capa existente é mantida
       │
       ▼
Exibição (easy_thumbnails, THUMBNAIL_EXTENSION=png), sempre em moldura A4:
  ├─ listagem  resource_card_one.html  140px de largura  thumbnail 280x396
  ├─ detalhe   resource.html           col-md-3          thumbnail 420x594
  └─ formulário resource_form.html     até 300px         thumbnail 420x594
     (sem capa: publicacoes.svg centralizado na mesma moldura)
```

### Caminho do admin

O admin expõe `image1` como um `ImageField` comum: o arquivo é gravado como veio,
**sem** recorte nem redimensionamento. Para não furar a proporção A4, o
`ResourceAdminBase.get_readonly_fields` torna `image1` somente leitura para quem **não é
superuser** (vale para `ResourceAdmin` e `TrainingResourceAdmin`):

```
get_readonly_fields(request, obj)
  readonly = super()            # PowerModelAdmin: tudo readonly se o usuario so tem 'view'
  se nao request.user.is_superuser e 'image1' nao em readonly:
      readonly += ['image1']
```

- Usuário não superuser: vê o arquivo atual, sem campo de upload. Como campos readonly
  ficam fora do form, um `image1` enviado no POST é ignorado. Para trocar a capa, usa o
  power button "Edição Completa", que leva ao recorte A4 do site.
- Superuser: continua podendo enviar a capa pelo admin, gravada sem recorte; as molduras
  A4 da exibição compensam visualmente (`object-fit: cover`).

## Components and Interfaces

| Componente | Arquivo | Papel |
|---|---|---|
| Card da listagem | `resources/templates/resource_card_one.html` | Coluna única; moldura A4 140px; tags azuis de categoria/tópico; fallback svg |
| Detalhe | `resources/templates/resource.html` | Descrição sob o título; botões agrupados; moldura A4 `col-md-3` |
| Formulário | `resources/templates/resource_form.html` | Preview `#imageResult1` em moldura A4; botões `btn-blue3`; um único `modal-crop.js?v=2` |
| Botões de salvar | `templates/_save_zone.html` | Parâmetro `btn_class` (default `btn-blue`); recursos passam `btn-blue3` |
| Recorte (JS) | `static/site/js/modal-crop.js` | Tabela `CROP_PRESETS` {0: 600x400, 1: 1100x400, 2: 600x848}; `cropPreset()` |
| Campo da capa | `resources/forms.py` (`image1`) | `data-image-width-option: 2`; help text A4 |
| Gravação | `resources/views.py` (`saveImage`, `RESOURCE_IMAGE_SIZE`) | Recorte + resize para 600x848 |
| Admin | `resources/admin.py` (`ResourceAdminBase(PowerModelAdmin)`) | Power buttons; `safe_url` vazio sem id; `image1` readonly para não superuser |

Observação: `projects/views.py` define a **sua própria** `saveImage`; a de recursos não é
compartilhada.

## Data Models

Sem mudança de schema. Campos de `Resource` envolvidos:

| Campo | Uso |
|---|---|
| `image1` | capa (`ImageField`, `upload_to='images/'`) |
| `imageCredit1` | crédito da imagem (texto livre) |
| `category` | FK para `Category`; o site só oferece categorias raiz |
| `theme` | M2M de tópicos, exibidos como tags |
| `isTrainingResource` | define as rotas de detalhe/edição (resource vs training) |

Campos de formulário (não persistidos): `x1`, `y1`, `width1`, `height1` (área recortada,
hidden) e `withImage1`. Removidos: `choices`, `categorySelected`.

Migration `0055_alter_resource_options`: só `verbose_name_plural`, sem SQL.

## Correctness Properties

Property 1: Proporção A4 consistente entre recorte e gravação
_Para qualquer_ capa nova enviada pelo site, o preset de recorte do campo `image1` e o
tamanho gravado no servidor são ambos 600x848.
**Validates: Requirements 4.1, 4.2, 5.1**

Property 2: Presets dos outros apps preservados
_Para qualquer_ formulário de organização, projeto ou plataforma, os presets usados
continuam sendo `0` e `1`, com os mesmos tamanhos de antes.
**Validates: Requirements 4.3**

Property 3: Exibição sempre em moldura A4
_Para qualquer_ recurso, com ou sem capa, listagem, detalhe e formulário exibem a capa
(ou o fallback) numa moldura `aspect-ratio: 210 / 297`.
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

Property 4: Power buttons com rotas certas
_Para qualquer_ recurso salvo, os botões do admin apontam para as rotas de resource ou de
training resource conforme `isTrainingResource`; sem id, não aparecem.
**Validates: Requirements 7.1, 7.2, 7.3**

Property 5: Capa protegida no admin
_Para qualquer_ usuário do admin que não seja superuser, o campo `image1` é somente
leitura e um arquivo enviado no POST não altera a capa.
**Validates: Requirements 7.5, 7.6, 7.7**

## Error Handling

- **Sem capa**: fallback `publicacoes.svg` nas três telas; nenhum erro.
- **Sem arquivo novo no envio**: `saveImage` devolve `''` ou `'/'`; `save()` mantém a capa
  atual (só grava caminhos com mais de 6 caracteres).
- **Recorte além das bordas**: o servidor preenche a área excedente com transparência.
- **Imagem pequena**: o zoom do slider é bloqueado quando a imagem natural é menor que
  600x848; o recorte continua possível.
- **Imagem legada (600x400)**: seria exibida cortada no centro da moldura A4; na
  prática não ocorre, pois o banco de produção não tem imagens de recursos.
- **Cache do navegador**: o formulário carrega `modal-crop.js?v=2`; em produção o deploy
  roda `collectstatic`.

## Testing Strategy

Testes em `src/resources/tests.py`, rodados com
`uv run manage.py test resources --keepdb` (banco `raras_teste`):

- `ResourceAdminButtonsTest`: botões no admin para resource e training resource; ausência
  dos botões e do link `/editResource/None` na inclusão.
- `ResourceImageA4Test`: `saveImage` grava 600x848 a partir de um recorte real; o campo
  `image1` usa o preset `2`.
- `ResourceListCardA4Test`: com uma capa real de 600x848, a listagem renderiza a moldura
  A4 e gera thumbnail retrato 280x396.
- `ResourceAdminImageReadonlyTest`: superuser vê o campo de upload; staff não superuser
  vê `image1` somente leitura (resource e training resource); um POST de staff com
  arquivo salva os demais campos e mantém a capa.

Verificação manual pendente (navegador): abrir o modal de recorte, recortar uma capa,
salvar e conferir listagem, detalhe e preview; conferir os componentes reativados pela
correção do CSS (Requisito 8.1).
